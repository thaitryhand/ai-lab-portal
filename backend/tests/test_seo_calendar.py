"""Tests for SEO analytics and Content Calendar API endpoints."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from backend.app.admin_boundary import (
    ADMIN_IDENTITY_HEADER,
    ADMIN_SIGNATURE_HEADER,
    sign_admin_identity,
)
from backend.app.blog import BlogRepository
from backend.app.blog_ideas import BlogIdeaCreate, BlogIdeaRepository
from backend.app.blog_tags import BlogTagRepository
from backend.app.main import create_app
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
# SEO Analytics
# ===========================================================================


class TestSeoAnalyticsAPI:
    """Verify the SEO analytics API endpoints."""

    def test_stats_requires_auth(self):
        """Stats endpoint returns 401 without admin headers."""
        settings = _test_settings()
        app = create_app(settings)
        client = TestClient(app)
        response = client.get("/admin/seo-analytics/stats")
        assert response.status_code == 401

    def test_stats_returns_aggregates(self):
        """Stats endpoint returns aggregate metrics."""
        settings = _test_settings()
        app = create_app(settings)
        client = TestClient(app)
        headers = _admin_headers()

        # Seed an idea with marketing metadata
        ideas_repo = BlogIdeaRepository()
        idea = ideas_repo.create(
            BlogIdeaCreate(
                title="SEO Test Post",
                angle="Test",
                target_reader="Test",
                article_goal="Test",
            )
        )
        # Update with marketing metadata directly
        idea.marketing_metadata = {
            "seo_title": "SEO Test Post - AI Lab",
            "meta_description": "A test post for SEO analytics with sufficient length.",
            "excerpt": "Test excerpt",
            "linkedin_post": "Check this out!",
            "x_post": "Great post!",
            "cta": "Read more",
            "keywords": ["seo", "test", "analytics"],
        }
        ideas_repo._ideas[idea.id] = idea  # type: ignore[attr-defined]

        response = client.get(
            "/admin/seo-analytics/stats", headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_posts" in data
        assert "avg_seo_score" in data
        assert "total_seo_issues" in data

    def test_keywords_returns_list(self):
        """Keywords endpoint returns a list of keyword items."""
        settings = _test_settings()
        app = create_app(settings)
        client = TestClient(app)
        headers = _admin_headers()

        response = client.get(
            "/admin/seo-analytics/keywords", headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


# ===========================================================================
# Content Calendar
# ===========================================================================


class TestContentCalendarAPI:
    """Verify the content calendar API endpoint."""

    def test_calendar_requires_auth(self):
        """Calendar endpoint returns 401 without admin headers."""
        settings = _test_settings()
        app = create_app(settings)
        client = TestClient(app)
        response = client.get("/admin/content-calendar/posts")
        assert response.status_code == 401

    def test_calendar_returns_posts(self):
        """Calendar endpoint returns published and pipeline posts."""
        settings = _test_settings()

        # Create seeded repositories and pass them to create_app
        from backend.app.blog import BlogPostCreate
        blog_repo = BlogRepository()
        from backend.app.blog_ideas import BlogIdeaRepository, BlogIdeaCreate
        ideas_repo = BlogIdeaRepository()

        post = blog_repo.create(
            BlogPostCreate(
                slug="test-post",
                title="Test Blog Post",
                excerpt="Test excerpt",
                author_name="Tester",
                content_markdown="# Test",
            )
        )
        blog_repo.publish(post.id)
        ideas_repo.create(
            BlogIdeaCreate(
                title="Pipeline Idea",
                angle="Test",
                target_reader="Test",
                article_goal="Test",
            )
        )

        app = create_app(settings, blog_repository=blog_repo, blog_idea_repository=ideas_repo)
        client = TestClient(app)
        headers = _admin_headers()

        response = client.get(
            "/admin/content-calendar/posts", headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "published" in data
        assert "pipeline" in data
        assert "month_counts" in data
        assert len(data["published"]) >= 1
        assert len(data["pipeline"]) >= 1
