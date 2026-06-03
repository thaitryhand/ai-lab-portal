"""Article extraction from news raw items (US-038)."""

from __future__ import annotations

import hashlib
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Literal
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

from pydantic import BaseModel
from sqlalchemy import Engine, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from backend.app.database import news_extracted_articles as extracted_table
from backend.app.news_crawl import NewsRawItemRepository, NewsRawItemSummary, validate_fetch_url
from backend.app.settings import Settings

if TYPE_CHECKING:
    from backend.app.news_scoring import NewsReviewRepository
    from backend.app.news_sources import NewsSourceRepository

ExtractionProvider = Literal["fake", "firecrawl"]
ExtractionStatus = Literal["success", "failed"]
DuplicateStatus = Literal["unique", "url_duplicate", "content_duplicate"]


class ExtractionError(RuntimeError):
    """Raised when article extraction fails."""


@dataclass(frozen=True)
class ExtractionOutput:
    final_url: str | None
    canonical_url: str | None
    title: str
    author: str | None
    site_name: str | None
    published_at: datetime | None
    content_markdown: str
    content_text: str
    provider: ExtractionProvider
    provider_latency_ms: int
    provider_payload: dict | None


class ExtractedArticle(BaseModel):
    id: str
    raw_item_id: str
    source_url: str
    final_url: str | None = None
    canonical_url: str | None = None
    title: str
    author: str | None = None
    site_name: str | None = None
    published_at: datetime | None = None
    content_markdown: str
    content_text: str
    content_hash: str
    provider: ExtractionProvider
    extraction_status: ExtractionStatus
    extraction_error: str | None = None
    provider_latency_ms: int | None = None
    extracted_at: datetime
    canonical_url_normalized: str = ""
    duplicate_status: DuplicateStatus = "unique"
    duplicate_of_id: str | None = None


class ExtractionResult(BaseModel):
    raw_item_id: str
    extraction_id: str | None = None
    status: ExtractionStatus
    error: str | None = None


class ExtractionQueuedResponse(BaseModel):
    status: str = "queued"
    task_id: str


class ArticleExtractor(ABC):
    @abstractmethod
    def extract(self, raw_item: NewsRawItemSummary) -> ExtractionOutput:
        ...


class FakeArticleExtractor(ArticleExtractor):
    """Deterministic extractor for tests and local dev without Firecrawl."""

    def extract(self, raw_item: NewsRawItemSummary) -> ExtractionOutput:
        started = time.perf_counter()
        markdown = (
            f"# {raw_item.title}\n\n"
            f"Stub article body extracted from [{raw_item.link_url}]({raw_item.link_url}).\n"
        )
        text = f"{raw_item.title}\n\nStub article body extracted from {raw_item.link_url}."
        latency_ms = int((time.perf_counter() - started) * 1000)
        return ExtractionOutput(
            final_url=raw_item.link_url,
            canonical_url=raw_item.link_url,
            title=raw_item.title,
            author=None,
            site_name="fixture",
            published_at=raw_item.published_at,
            content_markdown=markdown,
            content_text=text,
            provider="fake",
            provider_latency_ms=latency_ms,
            provider_payload={"mode": "fake"},
        )


class FirecrawlArticleExtractor(ArticleExtractor):
    """Firecrawl scrape API for markdown article extraction."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def extract(self, raw_item: NewsRawItemSummary) -> ExtractionOutput:
        validate_fetch_url(raw_item.link_url)
        started = time.perf_counter()
        body = json.dumps({"url": raw_item.link_url, "formats": ["markdown"]}).encode("utf-8")
        request = Request(
            "https://api.firecrawl.dev/v1/scrape",
            data=body,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=60) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise ExtractionError(f"Firecrawl request failed: {exc}") from exc

        latency_ms = int((time.perf_counter() - started) * 1000)
        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, dict):
            raise ExtractionError("Firecrawl response missing data object")

        metadata = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
        markdown = data.get("markdown") or ""
        if not isinstance(markdown, str) or not markdown.strip():
            raise ExtractionError("Firecrawl returned empty markdown")

        title = str(metadata.get("title") or raw_item.title)
        text = markdown.replace("#", "").strip()
        return ExtractionOutput(
            final_url=str(metadata.get("sourceURL") or metadata.get("url") or raw_item.link_url),
            canonical_url=str(metadata.get("canonical") or metadata.get("url") or raw_item.link_url),
            title=title[:512],
            author=(str(metadata["author"]) if metadata.get("author") else None),
            site_name=(str(metadata["siteName"]) if metadata.get("siteName") else None),
            published_at=raw_item.published_at,
            content_markdown=markdown,
            content_text=text[:50000],
            provider="firecrawl",
            provider_latency_ms=latency_ms,
            provider_payload={"success": payload.get("success"), "keys": sorted(data.keys())},
        )


def extractor_for_settings(settings: Settings) -> ArticleExtractor:
    if settings.environment == "test":
        return FakeArticleExtractor()
    api_key = settings.firecrawl_api_key.get_secret_value()
    if api_key:
        return FirecrawlArticleExtractor(api_key)
    return FakeArticleExtractor()


def content_hash(markdown: str, text: str) -> str:
    payload = f"{markdown}\n{text}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _best_article_url(
    *, source_url: str, final_url: str | None, canonical_url: str | None
) -> str:
    return canonical_url or final_url or source_url


class ExtractedArticleRepository:
    def __init__(self) -> None:
        self._rows: dict[str, ExtractedArticle] = {}

    def get_by_raw_item_id(self, raw_item_id: str) -> ExtractedArticle | None:
        for row in self._rows.values():
            if row.raw_item_id == raw_item_id:
                return row
        return None

    def get_by_id(self, extraction_id: str) -> ExtractedArticle | None:
        return self._rows.get(extraction_id)

    def save_success(
        self,
        raw_item: NewsRawItemSummary,
        output: ExtractionOutput,
    ) -> ExtractedArticle:
        from backend.app.news_dedup import canonicalize_url

        extracted_at = datetime.now(UTC)
        article_url = _best_article_url(
            source_url=raw_item.link_url,
            final_url=output.final_url,
            canonical_url=output.canonical_url,
        )
        row = ExtractedArticle(
            id=f"newsext_{uuid4().hex}",
            raw_item_id=raw_item.id,
            source_url=raw_item.link_url,
            final_url=output.final_url,
            canonical_url=output.canonical_url,
            title=output.title,
            author=output.author,
            site_name=output.site_name,
            published_at=output.published_at,
            content_markdown=output.content_markdown,
            content_text=output.content_text,
            content_hash=content_hash(output.content_markdown, output.content_text),
            provider=output.provider,
            extraction_status="success",
            provider_latency_ms=output.provider_latency_ms,
            extracted_at=extracted_at,
            canonical_url_normalized=canonicalize_url(article_url),
        )
        self._rows[row.id] = row
        return row

    def save_failure(
        self,
        raw_item: NewsRawItemSummary,
        *,
        provider: ExtractionProvider,
        error: str,
        latency_ms: int | None = None,
    ) -> ExtractedArticle:
        extracted_at = datetime.now(UTC)
        row = ExtractedArticle(
            id=f"newsext_{uuid4().hex}",
            raw_item_id=raw_item.id,
            source_url=raw_item.link_url,
            title=raw_item.title,
            content_markdown="",
            content_text="",
            content_hash=content_hash("", ""),
            provider=provider,
            extraction_status="failed",
            extraction_error=error[:2000],
            provider_latency_ms=latency_ms,
            extracted_at=extracted_at,
        )
        self._rows[row.id] = row
        return row

    def find_earliest_by_canonical_url(
        self, canonical_url_normalized: str, *, exclude_id: str
    ) -> str | None:
        matches = [
            row
            for row in self._rows.values()
            if row.id != exclude_id
            and row.extraction_status == "success"
            and row.canonical_url_normalized == canonical_url_normalized
        ]
        if not matches:
            return None
        return min(matches, key=lambda r: r.extracted_at).id

    def find_earliest_by_content_hash(self, content_hash_value: str, *, exclude_id: str) -> str | None:
        matches = [
            row
            for row in self._rows.values()
            if row.id != exclude_id
            and row.extraction_status == "success"
            and row.content_hash == content_hash_value
            and row.duplicate_status == "unique"
        ]
        if not matches:
            return None
        return min(matches, key=lambda r: r.extracted_at).id

    def update_dedup_fields(
        self,
        extraction_id: str,
        *,
        canonical_url_normalized: str,
        duplicate_status: DuplicateStatus,
        duplicate_of_id: str | None,
    ) -> ExtractedArticle | None:
        row = self._rows.get(extraction_id)
        if row is None:
            return None
        updated = row.model_copy(
            update={
                "canonical_url_normalized": canonical_url_normalized,
                "duplicate_status": duplicate_status,
                "duplicate_of_id": duplicate_of_id,
            }
        )
        self._rows[extraction_id] = updated
        return updated


class PostgresExtractedArticleRepository(ExtractedArticleRepository):
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def get_by_raw_item_id(self, raw_item_id: str) -> ExtractedArticle | None:
        with self._engine.connect() as conn:
            row = (
                conn.execute(
                    select(extracted_table).where(extracted_table.c.raw_item_id == raw_item_id)
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                return None
            return ExtractedArticle(**dict(row))

    def get_by_id(self, extraction_id: str) -> ExtractedArticle | None:
        with self._engine.connect() as conn:
            row = (
                conn.execute(
                    select(extracted_table).where(extracted_table.c.id == extraction_id)
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                return None
            return ExtractedArticle(**dict(row))

    def _upsert(self, values: dict) -> ExtractedArticle:
        stmt = pg_insert(extracted_table).values(**values)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_news_extracted_articles_raw_item",
            set_={k: values[k] for k in values if k not in {"id", "raw_item_id"}},
        )
        with self._engine.begin() as conn:
            conn.execute(stmt)
        return ExtractedArticle(**values)

    def save_success(self, raw_item: NewsRawItemSummary, output: ExtractionOutput) -> ExtractedArticle:
        from backend.app.news_dedup import canonicalize_url

        extracted_at = datetime.now(UTC)
        article_url = _best_article_url(
            source_url=raw_item.link_url,
            final_url=output.final_url,
            canonical_url=output.canonical_url,
        )
        values = {
            "id": f"newsext_{uuid4().hex}",
            "raw_item_id": raw_item.id,
            "source_url": raw_item.link_url,
            "final_url": output.final_url,
            "canonical_url": output.canonical_url,
            "title": output.title,
            "author": output.author,
            "site_name": output.site_name,
            "published_at": output.published_at,
            "content_markdown": output.content_markdown,
            "content_text": output.content_text,
            "content_hash": content_hash(output.content_markdown, output.content_text),
            "provider": output.provider,
            "extraction_status": "success",
            "extraction_error": None,
            "provider_latency_ms": output.provider_latency_ms,
            "provider_payload": json.dumps(output.provider_payload or {}),
            "extracted_at": extracted_at,
            "canonical_url_normalized": canonicalize_url(article_url),
            "duplicate_status": "unique",
            "duplicate_of_id": None,
        }
        existing = self.get_by_raw_item_id(raw_item.id)
        if existing is not None:
            values["id"] = existing.id
        return self._upsert(values)

    def save_failure(
        self,
        raw_item: NewsRawItemSummary,
        *,
        provider: ExtractionProvider,
        error: str,
        latency_ms: int | None = None,
    ) -> ExtractedArticle:
        extracted_at = datetime.now(UTC)
        values = {
            "id": f"newsext_{uuid4().hex}",
            "raw_item_id": raw_item.id,
            "source_url": raw_item.link_url,
            "final_url": None,
            "canonical_url": None,
            "title": raw_item.title,
            "author": None,
            "site_name": None,
            "published_at": raw_item.published_at,
            "content_markdown": "",
            "content_text": "",
            "content_hash": content_hash("", ""),
            "provider": provider,
            "extraction_status": "failed",
            "extraction_error": error[:2000],
            "provider_latency_ms": latency_ms,
            "provider_payload": None,
            "extracted_at": extracted_at,
            "canonical_url_normalized": "",
            "duplicate_status": "unique",
            "duplicate_of_id": None,
        }
        existing = self.get_by_raw_item_id(raw_item.id)
        if existing is not None:
            values["id"] = existing.id
        return self._upsert(values)

    def find_earliest_by_canonical_url(
        self, canonical_url_normalized: str, *, exclude_id: str
    ) -> str | None:
        with self._engine.connect() as conn:
            row = conn.execute(
                select(extracted_table.c.id)
                .where(
                    extracted_table.c.id != exclude_id,
                    extracted_table.c.extraction_status == "success",
                    extracted_table.c.canonical_url_normalized == canonical_url_normalized,
                )
                .order_by(extracted_table.c.extracted_at.asc())
                .limit(1)
            ).first()
            return row[0] if row else None

    def find_earliest_by_content_hash(
        self, content_hash_value: str, *, exclude_id: str
    ) -> str | None:
        with self._engine.connect() as conn:
            row = conn.execute(
                select(extracted_table.c.id)
                .where(
                    extracted_table.c.id != exclude_id,
                    extracted_table.c.extraction_status == "success",
                    extracted_table.c.content_hash == content_hash_value,
                    extracted_table.c.duplicate_status == "unique",
                )
                .order_by(extracted_table.c.extracted_at.asc())
                .limit(1)
            ).first()
            return row[0] if row else None

    def update_dedup_fields(
        self,
        extraction_id: str,
        *,
        canonical_url_normalized: str,
        duplicate_status: DuplicateStatus,
        duplicate_of_id: str | None,
    ) -> ExtractedArticle | None:
        with self._engine.begin() as conn:
            conn.execute(
                update(extracted_table)
                .where(extracted_table.c.id == extraction_id)
                .values(
                    canonical_url_normalized=canonical_url_normalized,
                    duplicate_status=duplicate_status,
                    duplicate_of_id=duplicate_of_id,
                )
            )
        return self.get_by_id(extraction_id)


def run_extract_raw_item(
    raw_item_id: str,
    *,
    raw_items: NewsRawItemRepository,
    extracted: ExtractedArticleRepository,
    extractor: ArticleExtractor,
    sources: NewsSourceRepository | None = None,
    review: NewsReviewRepository | None = None,
) -> ExtractionResult:
    raw_item = raw_items.get_by_id(raw_item_id)
    if raw_item is None:
        raise ValueError(f"Raw item not found: {raw_item_id}")

    provider: ExtractionProvider = (
        "firecrawl" if isinstance(extractor, FirecrawlArticleExtractor) else "fake"
    )
    try:
        output = extractor.extract(raw_item)
        row = extracted.save_success(raw_item, output)
        from backend.app.news_dedup import apply_dedup

        apply_dedup(row.id, extracted=extracted)
        scored = extracted.get_by_id(row.id)
        if (
            scored is not None
            and scored.duplicate_status == "unique"
            and sources is not None
            and review is not None
        ):
            from backend.app.news_scoring import run_score_extracted_article

            run_score_extracted_article(
                scored.id,
                extracted=extracted,
                raw_items=raw_items,
                sources=sources,
                review=review,
            )
        return ExtractionResult(
            raw_item_id=raw_item_id,
            extraction_id=row.id,
            status="success",
        )
    except (ExtractionError, ValueError) as exc:
        row = extracted.save_failure(
            raw_item,
            provider=provider,
            error=str(exc),
        )
        return ExtractionResult(
            raw_item_id=raw_item_id,
            extraction_id=row.id,
            status="failed",
            error=str(exc),
        )


def run_extract_pending_raw_items(
    *,
    raw_items: NewsRawItemRepository,
    extracted: ExtractedArticleRepository,
    extractor: ArticleExtractor,
    source_id: str | None = None,
    sources: NewsSourceRepository | None = None,
    review: NewsReviewRepository | None = None,
) -> list[ExtractionResult]:
    pending = raw_items.list_without_extraction(extracted, source_id=source_id)
    return [
        run_extract_raw_item(
            item.id,
            raw_items=raw_items,
            extracted=extracted,
            extractor=extractor,
            sources=sources,
            review=review,
        )
        for item in pending
    ]
