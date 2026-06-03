"""Tests for article extraction from news raw items (US-038)."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from backend.app.admin_boundary import (
    ADMIN_IDENTITY_HEADER,
    ADMIN_SIGNATURE_HEADER,
    sign_admin_identity,
)
from backend.app.main import create_app
from backend.app.news_crawl import NewsRawItemRepository, run_rss_crawl
from backend.app.news_extraction import (
    ExtractedArticleRepository,
    FakeArticleExtractor,
    run_extract_pending_raw_items,
    run_extract_raw_item,
)
from backend.app.news_sources import NewsSourceRepository
from backend.app.settings import Settings
from backend.tests.test_news_crawl import FIXTURE_RSS, _rss_source

TEST_SECRET = "test-admin-boundary-secret-at-least-32-chars"


def _test_settings() -> Settings:
    return Settings(environment="test", admin_boundary_secret=TEST_SECRET)


def _admin_headers() -> dict[str, str]:
    payload = json.dumps(
        {
            "user_id": "user_123",
            "email": "admin@example.com",
            "role": "admin",
            "issued_at": int(datetime.now(UTC).timestamp()),
        }
    )
    return {
        ADMIN_IDENTITY_HEADER: payload,
        ADMIN_SIGNATURE_HEADER: sign_admin_identity(payload, TEST_SECRET),
    }


def _seed_raw_item() -> tuple[NewsSourceRepository, NewsRawItemRepository, str, str]:
    sources = NewsSourceRepository(sources=[])
    raw = NewsRawItemRepository()
    source = _rss_source(sources)
    run_rss_crawl(
        source.id,
        sources=sources,
        raw_items=raw,
        fetcher=lambda _url: FIXTURE_RSS.read_bytes(),
    )
    raw_item = raw.list_for_source(source.id)[0]
    return sources, raw, source.id, raw_item.id


def test_run_extract_raw_item_success() -> None:
    _sources, raw, _source_id, raw_item_id = _seed_raw_item()
    extracted = ExtractedArticleRepository()
    result = run_extract_raw_item(
        raw_item_id,
        raw_items=raw,
        extracted=extracted,
        extractor=FakeArticleExtractor(),
    )
    assert result.status == "success"
    row = extracted.get_by_raw_item_id(raw_item_id)
    assert row is not None
    assert row.extraction_status == "success"
    assert "Stub article body" in row.content_markdown


def test_run_extract_pending_only_unextracted() -> None:
    sources, raw, source_id, raw_item_id = _seed_raw_item()
    extracted = ExtractedArticleRepository()
    extractor = FakeArticleExtractor()
    run_extract_raw_item(raw_item_id, raw_items=raw, extracted=extracted, extractor=extractor)
    results = run_extract_pending_raw_items(
        raw_items=raw,
        extracted=extracted,
        extractor=extractor,
        source_id=source_id,
    )
    assert len(results) == 1
    assert results[0].status == "success"

    for item in raw.list_for_source(source_id):
        run_extract_raw_item(item.id, raw_items=raw, extracted=extracted, extractor=extractor)
    assert (
        run_extract_pending_raw_items(
            raw_items=raw,
            extracted=extracted,
            extractor=extractor,
            source_id=source_id,
        )
        == []
    )


def test_admin_extract_and_list_endpoints() -> None:
    sources, raw, source_id, raw_item_id = _seed_raw_item()
    extracted = ExtractedArticleRepository()
    client = TestClient(
        create_app(
            settings=_test_settings(),
            news_source_repository=sources,
            news_raw_item_repository=raw,
            extracted_article_repository=extracted,
        )
    )

    listed = client.get(
        f"/admin/news-sources/{source_id}/raw-items",
        headers=_admin_headers(),
    )
    assert listed.status_code == 200
    assert len(listed.json()) == 2

    extract_resp = client.post(
        f"/admin/news-sources/raw-items/{raw_item_id}/extract",
        headers=_admin_headers(),
    )
    assert extract_resp.status_code == 200
    assert extract_resp.json()["status"] == "success"

    got = client.get(
        f"/admin/news-sources/raw-items/{raw_item_id}/extraction",
        headers=_admin_headers(),
    )
    assert got.status_code == 200
    assert got.json()["extraction_status"] == "success"
