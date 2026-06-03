"""Tests for RSS crawl and raw item storage (US-037)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.admin_boundary import (
    ADMIN_IDENTITY_HEADER,
    ADMIN_SIGNATURE_HEADER,
    sign_admin_identity,
)
from backend.app.main import create_app
from backend.app.news_crawl import (
    NewsRawItemRepository,
    UnsafeUrlError,
    parse_rss_or_atom_xml,
    run_crawl_due_rss_sources,
    run_rss_crawl,
    validate_fetch_url,
)
from backend.app.news_sources import NewsSource, NewsSourceCreate, NewsSourceRepository
from backend.app.settings import Settings

TEST_SECRET = "test-admin-boundary-secret-at-least-32-chars"
FIXTURE_RSS = Path(__file__).parent / "fixtures" / "sample.rss.xml"


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


def _rss_source(repo: NewsSourceRepository) -> NewsSource:
    return repo.create(
        NewsSourceCreate(
            name="Fixture RSS",
            source_type="rss",
            url_or_identifier="https://example.com/feed.xml",
            crawl_frequency_minutes=60,
            is_enabled=True,
        )
    )


def test_validate_fetch_url_blocks_loopback() -> None:
    with pytest.raises(UnsafeUrlError):
        validate_fetch_url("http://127.0.0.1/feed.xml")


def test_parse_rss_fixture() -> None:
    items = parse_rss_or_atom_xml(FIXTURE_RSS.read_bytes())
    assert len(items) == 2
    assert items[0].external_id == "post-first"
    assert items[0].link_url == "https://example.com/posts/first"


def test_run_rss_crawl_stores_items_and_updates_last_crawled() -> None:
    sources = NewsSourceRepository(sources=[])
    raw = NewsRawItemRepository()
    source = _rss_source(sources)

    def fetch(_url: str) -> bytes:
        return FIXTURE_RSS.read_bytes()

    result = run_rss_crawl(source.id, sources=sources, raw_items=raw, fetcher=fetch)
    assert result.items_seen == 2
    assert result.items_stored == 2
    assert result.items_skipped == 0

    stored = raw.list_for_source(source.id)
    assert len(stored) == 2

    updated = sources.get_by_id(source.id)
    assert updated is not None
    assert updated.last_crawled_at is not None

    second = run_rss_crawl(source.id, sources=sources, raw_items=raw, fetcher=fetch)
    assert second.items_seen == 2
    assert second.items_stored == 0
    assert second.items_skipped == 2


def test_run_crawl_due_rss_sources_respects_frequency() -> None:
    now = datetime.now(UTC)
    sources = NewsSourceRepository(sources=[])
    raw = NewsRawItemRepository()
    source = _rss_source(sources)
    sources.touch_last_crawled(source.id, now)

    def fetch(_url: str) -> bytes:
        return FIXTURE_RSS.read_bytes()

    assert run_crawl_due_rss_sources(sources=sources, raw_items=raw, fetcher=fetch) == []

    crawled_at = now - timedelta(minutes=120)
    sources.touch_last_crawled(source.id, crawled_at)
    results = run_crawl_due_rss_sources(sources=sources, raw_items=raw, fetcher=fetch)
    assert len(results) == 1
    assert results[0].items_stored == 2


def test_admin_crawl_endpoint_sync_for_rss(monkeypatch: pytest.MonkeyPatch) -> None:
    repo = NewsSourceRepository(sources=[])
    client = TestClient(create_app(settings=_test_settings(), news_source_repository=repo))
    source = _rss_source(repo)

    monkeypatch.setattr(
        "backend.app.news_crawl.default_fetch_url",
        lambda _url: FIXTURE_RSS.read_bytes(),
    )

    response = client.post(
        f"/admin/news-sources/{source.id}/crawl",
        headers=_admin_headers(),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["items_seen"] == 2
    assert body["items_stored"] == 2


def test_admin_crawl_rejects_non_rss_source() -> None:
    repo = NewsSourceRepository(sources=[])
    client = TestClient(create_app(settings=_test_settings(), news_source_repository=repo))
    website = repo.create(
        NewsSourceCreate(
            name="Website",
            source_type="website",
            url_or_identifier="https://example.com/news",
        )
    )
    response = client.post(
        f"/admin/news-sources/{website.id}/crawl",
        headers=_admin_headers(),
    )
    assert response.status_code == 400
    assert "RSS" in response.json()["detail"]
