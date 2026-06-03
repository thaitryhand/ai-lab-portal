"""Tests for URL canonicalization and exact deduplication (US-039)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from backend.app.news_dedup import apply_dedup, canonicalize_url
from backend.app.news_extraction import (
    ExtractedArticle,
    ExtractedArticleRepository,
    FakeArticleExtractor,
    content_hash,
    run_extract_raw_item,
)
from backend.app.news_sources import NewsSourceCreate, NewsSourceRepository
from backend.tests.test_news_crawl import FIXTURE_RSS, _rss_source
from backend.app.news_crawl import NewsRawItemRepository, run_rss_crawl


def test_canonicalize_url_strips_tracking_and_normalizes() -> None:
    assert (
        canonicalize_url("HTTPS://Example.COM/path/?utm_source=x&b=2&a=1")
        == "https://example.com/path?a=1&b=2"
    )
    assert canonicalize_url("https://example.com:443/post/") == "https://example.com/post"


def test_canonicalize_url_rejects_invalid() -> None:
    with pytest.raises(ValueError, match="http or https"):
        canonicalize_url("not-a-url")


def _insert_success(
    repo: ExtractedArticleRepository,
    *,
    article_id: str,
    raw_item_id: str,
    url: str,
    markdown: str,
    text: str,
    extracted_at: datetime,
) -> ExtractedArticle:
    from backend.app.news_dedup import canonicalize_url

    row = ExtractedArticle(
        id=article_id,
        raw_item_id=raw_item_id,
        source_url=url,
        final_url=url,
        canonical_url=url,
        title="Title",
        content_markdown=markdown,
        content_text=text,
        content_hash=content_hash(markdown, text),
        provider="fake",
        extraction_status="success",
        extracted_at=extracted_at,
        canonical_url_normalized=canonicalize_url(url),
        duplicate_status="unique",
    )
    repo._rows[row.id] = row
    return row


def test_apply_dedup_marks_url_duplicate() -> None:
    repo = ExtractedArticleRepository()
    base_time = datetime(2026, 6, 3, 12, 0, tzinfo=UTC)
    first = _insert_success(
        repo,
        article_id="ext_first",
        raw_item_id="raw_a",
        url="https://example.com/article?utm_source=newsletter",
        markdown="# A",
        text="A",
        extracted_at=base_time,
    )
    second = _insert_success(
        repo,
        article_id="ext_second",
        raw_item_id="raw_b",
        url="https://example.com/article/?utm_campaign=social",
        markdown="# B",
        text="B",
        extracted_at=base_time + timedelta(minutes=5),
    )

    result = apply_dedup(second.id, extracted=repo)
    assert result.duplicate_status == "url_duplicate"
    assert result.duplicate_of_id == first.id
    updated = repo.get_by_id(second.id)
    assert updated is not None
    assert updated.duplicate_status == "url_duplicate"


def test_apply_dedup_marks_content_duplicate_when_urls_differ() -> None:
    repo = ExtractedArticleRepository()
    base_time = datetime(2026, 6, 3, 12, 0, tzinfo=UTC)
    body_md = "# Shared\n\nSame body."
    body_text = "Shared\n\nSame body."
    shared_hash = content_hash(body_md, body_text)
    first = _insert_success(
        repo,
        article_id="ext_owner",
        raw_item_id="raw_1",
        url="https://example.com/one",
        markdown=body_md,
        text=body_text,
        extracted_at=base_time,
    )
    assert first.content_hash == shared_hash
    second = _insert_success(
        repo,
        article_id="ext_dup",
        raw_item_id="raw_2",
        url="https://other.example.com/two",
        markdown=body_md,
        text=body_text,
        extracted_at=base_time + timedelta(minutes=1),
    )

    result = apply_dedup(second.id, extracted=repo)
    assert result.duplicate_status == "content_duplicate"
    assert result.duplicate_of_id == first.id


def _set_raw_link_url(raw: NewsRawItemRepository, raw_item_id: str, link_url: str) -> None:
    for key, item in raw._items.items():
        if item.id == raw_item_id:
            raw._items[key] = item.model_copy(update={"link_url": link_url})
            return
    raise AssertionError(f"raw item not found: {raw_item_id}")


def test_run_extract_raw_item_applies_dedup_on_second_same_url() -> None:
    sources = NewsSourceRepository(sources=[])
    raw = NewsRawItemRepository()
    source = _rss_source(sources)
    run_rss_crawl(
        source.id,
        sources=sources,
        raw_items=raw,
        fetcher=lambda _url: FIXTURE_RSS.read_bytes(),
    )
    items = raw.list_for_source(source.id)
    assert len(items) >= 2

    extracted = ExtractedArticleRepository()
    extractor = FakeArticleExtractor()
    _set_raw_link_url(
        raw, items[0].id, "https://example.com/posts/shared?utm_source=a"
    )
    _set_raw_link_url(
        raw, items[1].id, "https://example.com/posts/shared?utm_medium=b"
    )

    run_extract_raw_item(items[0].id, raw_items=raw, extracted=extracted, extractor=extractor)
    run_extract_raw_item(items[1].id, raw_items=raw, extracted=extracted, extractor=extractor)

    first = extracted.get_by_raw_item_id(items[0].id)
    second = extracted.get_by_raw_item_id(items[1].id)
    assert first is not None and second is not None
    assert second.duplicate_status == "url_duplicate"
    assert second.duplicate_of_id == first.id
