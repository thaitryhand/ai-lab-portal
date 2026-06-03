"""RSS crawl and raw item storage for AI News (US-037)."""

from __future__ import annotations

import hashlib
import ipaddress
import json
import socket
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Protocol
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from uuid import uuid4
from xml.etree import ElementTree

from pydantic import BaseModel
from sqlalchemy import Engine, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from backend.app.database import news_raw_items as raw_items_table


class NewsSourceRepoProtocol(Protocol):
    def get_by_id(self, source_id: str): ...

    def list_due_rss(self, *, now: datetime | None = None): ...

    def touch_last_crawled(self, source_id: str, crawled_at: datetime) -> None: ...


MAX_RESPONSE_BYTES = 2 * 1024 * 1024
FETCH_TIMEOUT_SECONDS = 30
USER_AGENT = "AI-Lab-Portal-NewsCrawler/1.0"


class UnsafeUrlError(ValueError):
    """Raised when a URL fails SSRF or scheme validation."""


class RssFetchError(RuntimeError):
    """Raised when RSS fetch or parse fails."""


@dataclass(frozen=True)
class ParsedFeedItem:
    external_id: str
    title: str
    link_url: str
    published_at: datetime | None
    raw_payload: dict[str, str]


class CrawlResult(BaseModel):
    source_id: str
    items_seen: int = 0
    items_stored: int = 0
    items_skipped: int = 0


class CrawlQueuedResponse(BaseModel):
    status: str = "queued"
    task_id: str


class NewsRawItemSummary(BaseModel):
    id: str
    source_id: str
    external_id: str
    title: str
    link_url: str
    published_at: datetime | None
    fetched_at: datetime


Fetcher = Callable[[str], bytes]


def validate_fetch_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise UnsafeUrlError("Only http and https URLs are allowed")
    hostname = parsed.hostname
    if not hostname:
        raise UnsafeUrlError("URL must include a hostname")
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        infos = socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise UnsafeUrlError(f"Cannot resolve host: {hostname}") from exc
    for info in infos:
        sockaddr = info[4]
        if not sockaddr:
            continue
        ip = ipaddress.ip_address(sockaddr[0])
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
        ):
            raise UnsafeUrlError(f"Blocked address for crawl: {ip}")


def default_fetch_url(url: str) -> bytes:
    validate_fetch_url(url)
    request = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(request, timeout=FETCH_TIMEOUT_SECONDS) as response:
        chunks: list[bytes] = []
        total = 0
        while True:
            block = response.read(65536)
            if not block:
                break
            total += len(block)
            if total > MAX_RESPONSE_BYTES:
                raise RssFetchError("Response exceeds maximum allowed size")
            chunks.append(block)
    return b"".join(chunks)


def _local_name(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[-1]
    return tag


def _text(element: ElementTree.Element | None) -> str:
    if element is None:
        return ""
    return (element.text or "").strip()


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)
    except (TypeError, ValueError, OverflowError):
        pass
    try:
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)
    except ValueError:
        return None


def parse_rss_or_atom_xml(body: bytes) -> list[ParsedFeedItem]:
    try:
        root = ElementTree.fromstring(body)
    except ElementTree.ParseError as exc:
        raise RssFetchError("Invalid RSS/Atom XML") from exc

    root_name = _local_name(root.tag).lower()
    if root_name == "rss":
        channel = root.find("channel")
        if channel is None:
            return []
        entries = channel.findall("item")
        parser = _parse_rss_item
    elif root_name == "feed":
        entries = root.findall("{*}entry") or root.findall("entry")
        parser = _parse_atom_entry
    else:
        raise RssFetchError(f"Unsupported feed root element: {root_name}")

    items: list[ParsedFeedItem] = []
    for entry in entries:
        parsed = parser(entry)
        if parsed is not None:
            items.append(parsed)
    return items


def _parse_rss_item(item: ElementTree.Element) -> ParsedFeedItem | None:
    title = _text(item.find("title")) or "Untitled"
    link = _text(item.find("link"))
    guid = _text(item.find("guid")) or link
    if not guid and not link:
        return None
    external_id = guid or link
    link_url = link or guid
    published_at = _parse_datetime(_text(item.find("pubDate")))
    description = _text(item.find("description"))
    return ParsedFeedItem(
        external_id=external_id[:512],
        title=title[:512],
        link_url=link_url[:1024],
        published_at=published_at,
        raw_payload={
            "format": "rss2",
            "title": title,
            "link": link,
            "guid": guid,
            "description": description,
        },
    )


def _parse_atom_entry(entry: ElementTree.Element) -> ParsedFeedItem | None:
    title = _text(entry.find("{*}title")) or _text(entry.find("title")) or "Untitled"
    entry_id = _text(entry.find("{*}id")) or _text(entry.find("id"))
    link_el = entry.find("{*}link") or entry.find("link")
    link = link_el.get("href", "") if link_el is not None else ""
    if not entry_id and not link:
        return None
    external_id = (entry_id or link)[:512]
    link_url = (link or entry_id)[:1024]
    updated = _text(entry.find("{*}updated")) or _text(entry.find("updated"))
    published = _text(entry.find("{*}published")) or _text(entry.find("published"))
    published_at = _parse_datetime(published or updated)
    summary = _text(entry.find("{*}summary")) or _text(entry.find("summary"))
    return ParsedFeedItem(
        external_id=external_id,
        title=title[:512],
        link_url=link_url,
        published_at=published_at,
        raw_payload={
            "format": "atom",
            "title": title,
            "id": entry_id,
            "link": link,
            "summary": summary,
        },
    )


def content_hash_for_item(item: ParsedFeedItem) -> str:
    payload = f"{item.title}\n{item.link_url}\n{json.dumps(item.raw_payload, sort_keys=True)}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class NewsRawItemRepository:
    def __init__(self) -> None:
        self._items: dict[tuple[str, str], NewsRawItemSummary] = {}

    def upsert_item(
        self,
        *,
        source_id: str,
        item: ParsedFeedItem,
        content_hash: str,
        fetched_at: datetime,
    ) -> bool:
        key = (source_id, item.external_id)
        is_new = key not in self._items
        self._items[key] = NewsRawItemSummary(
            id=f"newsraw_{uuid4().hex}",
            source_id=source_id,
            external_id=item.external_id,
            title=item.title,
            link_url=item.link_url,
            published_at=item.published_at,
            fetched_at=fetched_at,
        )
        return is_new

    def get_by_id(self, raw_item_id: str) -> NewsRawItemSummary | None:
        for row in self._items.values():
            if row.id == raw_item_id:
                return row
        return None

    def list_for_source(self, source_id: str) -> list[NewsRawItemSummary]:
        return [
            row
            for (sid, _), row in self._items.items()
            if sid == source_id
        ]

    def list_without_extraction(self, extracted_repo, *, source_id: str | None = None) -> list[NewsRawItemSummary]:
        rows = self.list_for_source(source_id) if source_id else list(self._items.values())
        return [row for row in rows if extracted_repo.get_by_raw_item_id(row.id) is None]


class PostgresNewsRawItemRepository(NewsRawItemRepository):
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def upsert_item(
        self,
        *,
        source_id: str,
        item: ParsedFeedItem,
        content_hash: str,
        fetched_at: datetime,
    ) -> bool:
        row_id = f"newsraw_{uuid4().hex}"
        values = {
            "id": row_id,
            "source_id": source_id,
            "external_id": item.external_id,
            "title": item.title,
            "link_url": item.link_url,
            "published_at": item.published_at,
            "raw_payload": json.dumps(item.raw_payload),
            "content_hash": content_hash,
            "fetched_at": fetched_at,
        }
        stmt = pg_insert(raw_items_table).values(**values)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_news_raw_items_source_external",
            set_={
                "title": item.title,
                "link_url": item.link_url,
                "published_at": item.published_at,
                "raw_payload": json.dumps(item.raw_payload),
                "content_hash": content_hash,
                "fetched_at": fetched_at,
            },
        )
        with self._engine.begin() as conn:
            before = conn.execute(
                select(raw_items_table.c.id).where(
                    raw_items_table.c.source_id == source_id,
                    raw_items_table.c.external_id == item.external_id,
                )
            ).first()
            conn.execute(stmt)
        return before is None

    def get_by_id(self, raw_item_id: str) -> NewsRawItemSummary | None:
        with self._engine.connect() as conn:
            row = (
                conn.execute(
                    select(raw_items_table).where(raw_items_table.c.id == raw_item_id)
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                return None
            return NewsRawItemSummary(**dict(row))

    def list_for_source(self, source_id: str) -> list[NewsRawItemSummary]:
        with self._engine.connect() as conn:
            rows = conn.execute(
                select(raw_items_table)
                .where(raw_items_table.c.source_id == source_id)
                .order_by(raw_items_table.c.fetched_at.desc())
            ).mappings()
            return [NewsRawItemSummary(**dict(row)) for row in rows]

    def list_without_extraction(self, extracted_repo, *, source_id: str | None = None) -> list[NewsRawItemSummary]:
        from backend.app.database import news_extracted_articles as extracted_table

        with self._engine.connect() as conn:
            query = select(raw_items_table)
            if source_id is not None:
                query = query.where(raw_items_table.c.source_id == source_id)
            rows = conn.execute(query.order_by(raw_items_table.c.fetched_at.desc())).mappings()
            pending: list[NewsRawItemSummary] = []
            for row in rows:
                item = NewsRawItemSummary(**dict(row))
                exists = conn.execute(
                    select(extracted_table.c.id).where(
                        extracted_table.c.raw_item_id == item.id
                    )
                ).first()
                if exists is None:
                    pending.append(item)
            return pending


def run_rss_crawl(
    source_id: str,
    *,
    sources: NewsSourceRepoProtocol,
    raw_items: NewsRawItemRepository,
    fetcher: Fetcher | None = None,
) -> CrawlResult:
    source = sources.get_by_id(source_id)
    if source is None:
        raise ValueError(f"News source not found: {source_id}")
    if source.source_type != "rss":
        raise ValueError(f"Source {source_id} is not an RSS source")
    if not source.is_enabled:
        raise ValueError(f"Source {source_id} is disabled")

    fetch = fetcher or default_fetch_url
    try:
        body = fetch(source.url_or_identifier)
    except (UnsafeUrlError, URLError, TimeoutError, RssFetchError) as exc:
        raise RssFetchError(str(exc)) from exc

    parsed_items = parse_rss_or_atom_xml(body)
    fetched_at = datetime.now(UTC)
    stored = 0
    skipped = 0
    for item in parsed_items:
        digest = content_hash_for_item(item)
        if raw_items.upsert_item(
            source_id=source_id,
            item=item,
            content_hash=digest,
            fetched_at=fetched_at,
        ):
            stored += 1
        else:
            skipped += 1

    sources.touch_last_crawled(source_id, fetched_at)
    return CrawlResult(
        source_id=source_id,
        items_seen=len(parsed_items),
        items_stored=stored,
        items_skipped=skipped,
    )


def run_crawl_due_rss_sources(
    *,
    sources: NewsSourceRepoProtocol,
    raw_items: NewsRawItemRepository,
    fetcher: Fetcher | None = None,
) -> list[CrawlResult]:
    results: list[CrawlResult] = []
    for source in sources.list_due_rss():
        try:
            results.append(
                run_rss_crawl(
                    source.id,
                    sources=sources,
                    raw_items=raw_items,
                    fetcher=fetcher,
                )
            )
        except RssFetchError:
            continue
    return results
