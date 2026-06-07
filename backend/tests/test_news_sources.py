"""Tests for news source admin API (MVP 3 slice 1)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from backend.app.admin_boundary import (
    ADMIN_IDENTITY_HEADER,
    ADMIN_SIGNATURE_HEADER,
    sign_admin_identity,
)
from backend.app.main import create_app
from backend.app.news_sources import (
    NewsSource,
    NewsSourceCreate,
    NewsSourceRepository,
    NewsSourceUpdate,
    _to_summary,
)
from backend.app.settings import Settings

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


# ===========================================================================
# Existing tests (preserved)
# ===========================================================================


def test_list_news_sources_returns_seeded_defaults() -> None:
    app = create_app(settings=_test_settings())
    items = TestClient(app).get("/admin/news-sources", headers=_admin_headers()).json()
    assert len(items) >= 1
    assert items[0]["source_type"] in {"rss", "github", "website"}


def test_create_and_update_news_source() -> None:
    repo = NewsSourceRepository(sources=[])
    client = TestClient(create_app(settings=_test_settings(), news_source_repository=repo))
    created = client.post(
        "/admin/news-sources",
        headers=_admin_headers(),
        json={
            "name": "Hacker News AI",
            "source_type": "rss",
            "url_or_identifier": "https://hnrss.org/newest?q=AI",
            "priority": "medium",
            "is_enabled": True,
        },
    )
    assert created.status_code == 200
    source_id = created.json()["id"]
    updated = client.patch(
        f"/admin/news-sources/{source_id}",
        headers=_admin_headers(),
        json={"is_enabled": False, "priority": "low"},
    )
    assert updated.status_code == 200
    assert updated.json()["is_enabled"] is False
    assert updated.json()["priority"] == "low"


# ===========================================================================
# Additional: NewsSourceRepository CRUD
# ===========================================================================


class TestNewsSourceRepository:
    """Tests for the in-memory NewsSourceRepository."""

    def test_list_all_returns_empty_when_empty(self) -> None:
        repo = NewsSourceRepository(sources=[])
        assert repo.list_all() == []

    def test_list_all_sorted_by_name(self) -> None:
        repo = NewsSourceRepository(sources=[])
        src_b = repo.create(
            NewsSourceCreate(name="B Source", source_type="rss", url_or_identifier="https://b.com")
        )
        src_a = repo.create(
            NewsSourceCreate(name="A Source", source_type="rss", url_or_identifier="https://a.com")
        )
        items = repo.list_all()
        assert items[0].name == "A Source"
        assert items[1].name == "B Source"

    def test_get_by_id_returns_none_for_missing(self) -> None:
        repo = NewsSourceRepository(sources=[])
        assert repo.get_by_id("nonexistent") is None

    def test_get_by_id_returns_source(self) -> None:
        repo = NewsSourceRepository(sources=[])
        created = repo.create(
            NewsSourceCreate(name="Test", source_type="rss", url_or_identifier="https://test.com")
        )
        fetched = repo.get_by_id(created.id)
        assert fetched is not None
        assert fetched.name == "Test"

    def test_create_sets_id_and_timestamps(self) -> None:
        repo = NewsSourceRepository(sources=[])
        source = repo.create(
            NewsSourceCreate(name="New", source_type="github",
                             url_or_identifier="org/repo")
        )
        assert source.id.startswith("newssrc_")
        assert source.created_at is not None
        assert source.updated_at is not None

    def test_create_persists_all_fields(self) -> None:
        repo = NewsSourceRepository(sources=[])
        source = repo.create(
            NewsSourceCreate(
                name="Full Source",
                source_type="rss",
                url_or_identifier="https://full.com/feed",
                description="A full source",
                priority="high",
                crawl_frequency_minutes=60,
                is_enabled=False,
                credibility_base_score=0.5,
            )
        )
        fetched = repo.get_by_id(source.id)
        assert fetched is not None
        assert fetched.name == "Full Source"
        assert fetched.description == "A full source"
        assert fetched.priority == "high"
        assert fetched.crawl_frequency_minutes == 60
        assert fetched.is_enabled is False
        assert fetched.credibility_base_score == 0.5

    def test_update_returns_none_for_missing(self) -> None:
        repo = NewsSourceRepository(sources=[])
        result = repo.update("nonexistent", NewsSourceUpdate(name="Renamed"))
        assert result is None

    def test_update_partial_fields(self) -> None:
        repo = NewsSourceRepository(sources=[])
        source = repo.create(
            NewsSourceCreate(name="Original", source_type="rss",
                             url_or_identifier="https://orig.com")
        )
        updated = repo.update(source.id, NewsSourceUpdate(name="Renamed"))
        assert updated is not None
        assert updated.name == "Renamed"
        # Other fields remain unchanged
        assert updated.source_type == "rss"
        assert updated.url_or_identifier == "https://orig.com"

    def test_update_credibility_score(self) -> None:
        repo = NewsSourceRepository(sources=[])
        source = repo.create(
            NewsSourceCreate(name="Cred", source_type="rss",
                             url_or_identifier="https://cred.com")
        )
        updated = repo.update(source.id, NewsSourceUpdate(credibility_base_score=0.9))
        assert updated is not None
        assert updated.credibility_base_score == 0.9

    def test_touch_last_crawled_non_existent_does_nothing(self) -> None:
        repo = NewsSourceRepository(sources=[])
        # Should not raise
        repo.touch_last_crawled("nonexistent", datetime.now(UTC))

    def test_touch_last_crawled_updates_timestamp(self) -> None:
        repo = NewsSourceRepository(sources=[])
        source = repo.create(
            NewsSourceCreate(name="Crawlable", source_type="rss",
                             url_or_identifier="https://crawl.com")
        )
        now = datetime.now(UTC)
        repo.touch_last_crawled(source.id, now)
        fetched = repo.get_by_id(source.id)
        assert fetched is not None
        assert fetched.last_crawled_at is not None
        assert fetched.last_crawled_at == now


# ===========================================================================
# Additional: NewsSourceRepository list_due_by_type
# ===========================================================================


class TestListDueByType:
    """Tests for list_due_by_type and list_due_rss / list_due_github."""

    def test_never_crawled_is_due(self) -> None:
        repo = NewsSourceRepository(sources=[])
        repo.create(
            NewsSourceCreate(name="Fresh", source_type="rss",
                             url_or_identifier="https://fresh.com")
        )
        due = repo.list_due_rss()
        assert len(due) == 1

    def test_disabled_source_not_due(self) -> None:
        repo = NewsSourceRepository(sources=[])
        repo.create(
            NewsSourceCreate(name="Disabled RSS", source_type="rss",
                             url_or_identifier="https://disabled.com",
                             is_enabled=False)
        )
        due = repo.list_due_rss()
        assert due == []

    def test_different_type_not_included(self) -> None:
        repo = NewsSourceRepository(sources=[])
        repo.create(
            NewsSourceCreate(name="Git", source_type="github",
                             url_or_identifier="org/repo")
        )
        assert repo.list_due_rss() == []
        assert len(repo.list_due_github()) == 1

    def test_recently_crawled_not_due(self) -> None:
        repo = NewsSourceRepository(sources=[])
        src = repo.create(
            NewsSourceCreate(name="Recent", source_type="rss",
                             url_or_identifier="https://recent.com",
                             crawl_frequency_minutes=60)
        )
        now = datetime.now(UTC)
        repo.touch_last_crawled(src.id, now)
        due = repo.list_due_rss(now=now)
        assert due == []

    def test_old_crawl_is_due(self) -> None:
        repo = NewsSourceRepository(sources=[])
        src = repo.create(
            NewsSourceCreate(name="Old", source_type="rss",
                             url_or_identifier="https://old.com",
                             crawl_frequency_minutes=60)
        )
        past = datetime.now(UTC) - timedelta(minutes=120)
        repo.touch_last_crawled(src.id, past)
        due = repo.list_due_rss()
        assert len(due) == 1
        assert due[0].id == src.id

    def test_list_due_by_type_custom_now(self) -> None:
        repo = NewsSourceRepository(sources=[])
        src = repo.create(
            NewsSourceCreate(name="Future", source_type="rss",
                             url_or_identifier="https://future.com",
                             crawl_frequency_minutes=60)
        )
        now = datetime.now(UTC)
        repo.touch_last_crawled(src.id, now)
        # Looking from a future time, it's due
        future = now + timedelta(minutes=120)
        due = repo.list_due_rss(now=future)
        assert len(due) == 1


# ===========================================================================
# Additional: _to_summary helper
# ===========================================================================


class TestToSummary:
    """Tests for the _to_summary helper."""

    def test_converts_to_summary(self) -> None:
        now = datetime.now(UTC)
        source = NewsSource(
            id="src1",
            name="Test Source",
            source_type="rss",
            url_or_identifier="https://example.com/feed",
            priority="high",
            is_enabled=True,
            last_crawled_at=now,
            created_at=now,
            updated_at=now,
        )
        summary = _to_summary(source)
        assert summary.id == "src1"
        assert summary.name == "Test Source"
        assert summary.source_type == "rss"
        assert summary.last_crawled_at == now
        # Should not have fields beyond summary
        assert not hasattr(summary, "created_at")


# ===========================================================================
# Additional: API endpoint tests
# ===========================================================================


class TestNewsSourcesAPI:
    """Additional API-level tests for news sources."""

    def test_get_source_returns_source(self) -> None:
        repo = NewsSourceRepository(sources=[])
        client = TestClient(
            create_app(settings=_test_settings(), news_source_repository=repo)
        )
        created = client.post(
            "/admin/news-sources",
            headers=_admin_headers(),
            json={
                "name": "Get Test",
                "source_type": "rss",
                "url_or_identifier": "https://gettest.com",
            },
        ).json()

        response = client.get(
            f"/admin/news-sources/{created['id']}",
            headers=_admin_headers(),
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Get Test"

    def test_get_source_returns_404(self) -> None:
        repo = NewsSourceRepository(sources=[])
        client = TestClient(
            create_app(settings=_test_settings(), news_source_repository=repo)
        )
        response = client.get(
            "/admin/news-sources/nonexistent",
            headers=_admin_headers(),
        )
        assert response.status_code == 404

    def test_create_source_with_all_fields(self) -> None:
        repo = NewsSourceRepository(sources=[])
        client = TestClient(
            create_app(settings=_test_settings(), news_source_repository=repo)
        )
        response = client.post(
            "/admin/news-sources",
            headers=_admin_headers(),
            json={
                "name": "Full Create",
                "source_type": "github",
                "url_or_identifier": "org/repo",
                "description": "A GitHub source",
                "priority": "high",
                "crawl_frequency_minutes": 120,
                "is_enabled": False,
                "credibility_base_score": 0.8,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Full Create"
        assert data["description"] == "A GitHub source"
        assert data["priority"] == "high"
        assert data["crawl_frequency_minutes"] == 120
        assert data["is_enabled"] is False
        assert data["credibility_base_score"] == 0.8

    def test_create_source_minimal_fields(self) -> None:
        repo = NewsSourceRepository(sources=[])
        client = TestClient(
            create_app(settings=_test_settings(), news_source_repository=repo)
        )
        response = client.post(
            "/admin/news-sources",
            headers=_admin_headers(),
            json={
                "name": "Minimal",
                "source_type": "website",
                "url_or_identifier": "https://minimal.com",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["priority"] == "medium"  # default
        assert data["is_enabled"] is True  # default
        assert data["crawl_frequency_minutes"] == 360  # default

    def test_update_source_returns_404(self) -> None:
        repo = NewsSourceRepository(sources=[])
        client = TestClient(
            create_app(settings=_test_settings(), news_source_repository=repo)
        )
        response = client.patch(
            "/admin/news-sources/nonexistent",
            headers=_admin_headers(),
            json={"name": "Renamed"},
        )
        assert response.status_code == 404

    def test_update_source_clear_description(self) -> None:
        repo = NewsSourceRepository(sources=[])
        client = TestClient(
            create_app(settings=_test_settings(), news_source_repository=repo)
        )
        created = client.post(
            "/admin/news-sources",
            headers=_admin_headers(),
            json={
                "name": "With Desc",
                "source_type": "rss",
                "url_or_identifier": "https://desc.com",
                "description": "Original desc",
            },
        ).json()
        # Update without description (leave unchanged)
        updated = client.patch(
            f"/admin/news-sources/{created['id']}",
            headers=_admin_headers(),
            json={"crawl_frequency_minutes": 30},
        )
        assert updated.status_code == 200
        assert updated.json()["description"] == "Original desc"
        assert updated.json()["crawl_frequency_minutes"] == 30

    def test_create_source_validation_name_empty(self) -> None:
        repo = NewsSourceRepository(sources=[])
        client = TestClient(
            create_app(settings=_test_settings(), news_source_repository=repo)
        )
        response = client.post(
            "/admin/news-sources",
            headers=_admin_headers(),
            json={
                "name": "",
                "source_type": "rss",
                "url_or_identifier": "https://x.com",
            },
        )
        assert response.status_code == 422  # Validation error

    def test_create_source_validation_bad_type(self) -> None:
        repo = NewsSourceRepository(sources=[])
        client = TestClient(
            create_app(settings=_test_settings(), news_source_repository=repo)
        )
        response = client.post(
            "/admin/news-sources",
            headers=_admin_headers(),
            json={
                "name": "Bad Type",
                "source_type": "invalid_type",
                "url_or_identifier": "https://x.com",
            },
        )
        assert response.status_code == 422

    def test_create_source_validation_crawl_frequency_too_low(self) -> None:
        repo = NewsSourceRepository(sources=[])
        client = TestClient(
            create_app(settings=_test_settings(), news_source_repository=repo)
        )
        response = client.post(
            "/admin/news-sources",
            headers=_admin_headers(),
            json={
                "name": "Fast",
                "source_type": "rss",
                "url_or_identifier": "https://fast.com",
                "crawl_frequency_minutes": 5,  # below minimum 15
            },
        )
        assert response.status_code == 422

    def test_create_source_validation_credibility_out_of_range(self) -> None:
        repo = NewsSourceRepository(sources=[])
        client = TestClient(
            create_app(settings=_test_settings(), news_source_repository=repo)
        )
        response = client.post(
            "/admin/news-sources",
            headers=_admin_headers(),
            json={
                "name": "Bad Cred",
                "source_type": "rss",
                "url_or_identifier": "https://bad.com",
                "credibility_base_score": 1.5,
            },
        )
        assert response.status_code == 422


# ===========================================================================
# Additional: NewsSource Pydantic models validation
# ===========================================================================


class TestNewsSourceModels:
    """Direct validation tests for NewsSource Pydantic models."""

    def test_news_source_create_validates_min_length_name(self) -> None:
        with pytest.raises(ValidationError):
            NewsSourceCreate(name="", source_type="rss", url_or_identifier="https://x.com")

    def test_news_source_create_validates_name_max_length(self) -> None:
        with pytest.raises(ValidationError):
            NewsSourceCreate(
                name="x" * 161, source_type="rss", url_or_identifier="https://x.com",
            )

    def test_news_source_create_validates_url_max_length(self) -> None:
        with pytest.raises(ValidationError):
            NewsSourceCreate(
                name="Test", source_type="rss", url_or_identifier="x" * 513,
            )

    def test_news_source_create_defaults(self) -> None:
        payload = NewsSourceCreate(name="Test", source_type="rss", url_or_identifier="https://x.com")
        assert payload.priority == "medium"
        assert payload.crawl_frequency_minutes == 360
        assert payload.is_enabled is True
        assert payload.credibility_base_score == 0.7

    def test_news_source_update_validates_crawl_frequency(self) -> None:
        with pytest.raises(ValidationError):
            NewsSourceUpdate(crawl_frequency_minutes=5)

    def test_news_source_update_allows_partial(self) -> None:
        payload = NewsSourceUpdate(name="Renamed")
        assert payload.name == "Renamed"
        assert payload.source_type is None
        assert payload.is_enabled is None

    def test_news_source_model_creates(self) -> None:
        now = datetime.now(UTC)
        source = NewsSource(
            id="test_id",
            name="Test",
            source_type="rss",
            url_or_identifier="https://x.com",
            created_at=now,
            updated_at=now,
        )
        assert source.crawl_frequency_minutes == 360
        assert source.is_enabled is True


# ===========================================================================
# Additional: Default sources seeded in empty repository
# ===========================================================================


class TestDefaultSources:
    """Tests for the default sources seeded by NewsSourceRepository."""

    def test_default_repo_contains_default_sources(self) -> None:
        repo = NewsSourceRepository()  # no sources=[] means use defaults
        all_sources = repo.list_all()
        names = [s.name for s in all_sources]
        assert "OpenAI Blog RSS" in names
        assert "Anthropic News" in names
        assert "User Submissions" in names

    def test_default_sources_include_varied_types(self) -> None:
        repo = NewsSourceRepository()
        all_sources = repo.list_all()
        types = {s.source_type for s in all_sources}
        assert "rss" in types
        assert "github" in types
        assert "website" in types
        assert "user_submit" in types
        assert "social_x" in types
        assert "hackernews" in types


# ===========================================================================
# Additional: Crawl endpoint edge cases
# ===========================================================================


class TestNewsSourceCrawlEndpoint:
    """Edge cases for the crawl endpoint."""

    def test_crawl_missing_source_returns_404(self) -> None:
        repo = NewsSourceRepository(sources=[])
        client = TestClient(
            create_app(settings=_test_settings(), news_source_repository=repo)
        )
        response = client.post(
            "/admin/news-sources/nonexistent/crawl",
            headers=_admin_headers(),
        )
        assert response.status_code == 404

    def test_crawl_disabled_source_returns_400(self) -> None:
        repo = NewsSourceRepository(sources=[])
        client = TestClient(
            create_app(settings=_test_settings(), news_source_repository=repo)
        )
        disabled = repo.create(
            NewsSourceCreate(
                name="Disabled RSS",
                source_type="rss",
                url_or_identifier="https://disabled.com",
                is_enabled=False,
            )
        )
        response = client.post(
            f"/admin/news-sources/{disabled.id}/crawl",
            headers=_admin_headers(),
        )
        assert response.status_code == 400
        assert "disabled" in response.json()["detail"]
