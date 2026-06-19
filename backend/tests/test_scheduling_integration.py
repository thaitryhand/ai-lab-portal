"""Integration tests for Auto-Scheduling Agent routes (US-108)."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from backend.app.admin_boundary import ADMIN_IDENTITY_HEADER, ADMIN_SIGNATURE_HEADER
from backend.app.blog import BlogPost, BlogRepository
from backend.app.blog_ideas import BlogIdea, BlogIdeaRepository
from backend.app.scheduling_agent import FakeSchedulingService
from backend.app.scheduling_routes import (
    create_scheduling_routes,
    create_blog_idea_scheduling_routes,
)
from backend.app.settings import Settings


# ── Test Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def settings() -> Settings:
    """Test settings with admin boundary secret."""
    return Settings(
        environment="test",
        llm_backend="agents_sdk", 
        llm_model="gpt-4o",
        admin_boundary_secret="test-secret-at-least-32-characters-long!!",
    )


@pytest.fixture
def blog_repo() -> BlogRepository:
    """Blog repository with test posts."""
    from datetime import datetime, UTC
    
    test_posts = [
        BlogPost(
            id="test-post-1",
            title="Test Blog Post",
            slug="test-blog-post",
            excerpt="Test excerpt",
            content_markdown="# Test\n\nContent here.",
            status="published",
            author_name="test-author",
            published_at=datetime.now(UTC),
        ),
    ]
    return BlogRepository(posts=test_posts)


@pytest.fixture
def ideas_repo() -> BlogIdeaRepository:
    """Blog ideas repository with test ideas."""
    from datetime import datetime, UTC
    
    now = datetime.now(UTC)
    test_ideas = [
        BlogIdea(
            id="test-idea-1",
            title="Test Blog Idea",
            angle="AI Testing",
            target_reader="Developers",
            article_goal="Show testing approach",
            positioning_notes=[],
            source="manual",
            status="pending",
            created_at=now,
            updated_at=now,
        ),
    ]
    return BlogIdeaRepository(ideas=test_ideas)


@pytest.fixture
def auth_headers(settings: Settings) -> dict[str, str]:
    """Generate admin auth headers."""
    now = int(time.time())
    identity_payload = json.dumps(
        {"user_id": "admin_1", "email": "admin@test.com", "role": "admin", "issued_at": now},
        separators=(",", ":"),
    )
    secret = settings.admin_boundary_secret.get_secret_value()
    signature = hmac.new(
        secret.encode("utf-8"),
        identity_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return {
        ADMIN_IDENTITY_HEADER: identity_payload,
        ADMIN_SIGNATURE_HEADER: signature,
    }


@pytest.fixture
def scheduling_app(
    blog_repo: BlogRepository,
    settings: Settings,
) -> FastAPI:
    """Build minimal FastAPI app with scheduling router."""
    service = FakeSchedulingService()
    router = create_scheduling_routes(service, blog_repo, settings)
    
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def idea_scheduling_app(
    ideas_repo: BlogIdeaRepository,
    settings: Settings,
) -> FastAPI:
    """Build minimal FastAPI app with idea scheduling router."""
    service = FakeSchedulingService()
    router = create_blog_idea_scheduling_routes(service, ideas_repo, settings)
    
    app = FastAPI()
    app.include_router(router)
    return app


@pytest_asyncio.fixture
async def client(scheduling_app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Async test client for blog post scheduling."""
    transport = ASGITransport(app=scheduling_app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def idea_client(idea_scheduling_app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Async test client for idea scheduling."""
    transport = ASGITransport(app=idea_scheduling_app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ── Integration Tests - Blog Posts ────────────────────────────────────────


@pytest.mark.asyncio
async def test_suggest_schedule_for_blog_post_success(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """POST /admin/blog-posts/{id}/suggest-schedule returns 200."""
    response = await client.post(
        "/admin/blog-posts/test-post-1/suggest-schedule",
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    assert data["blog_post_id"] == "test-post-1"
    assert "id" in data
    assert "suggested_date" in data
    assert "suggested_time" in data  
    assert "rationale" in data
    assert "confidence" in data
    assert "created_at" in data
    
    # Verify data formats
    import re
    assert re.match(r"^\d{4}-\d{2}-\d{2}$", data["suggested_date"])
    assert re.match(r"^\d{2}:\d{2}$", data["suggested_time"])
    assert 0.0 <= data["confidence"] <= 1.0
    assert len(data["rationale"]) > 0


@pytest.mark.asyncio
async def test_suggest_schedule_nonexistent_post_fails(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """POST /admin/blog-posts/{id}/suggest-schedule returns 404 for nonexistent post."""
    response = await client.post(
        "/admin/blog-posts/nonexistent/suggest-schedule",
        headers=auth_headers,
    )
    
    assert response.status_code == 404
    assert "Blog post not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_suggest_schedule_requires_admin_auth(
    client: AsyncClient,
) -> None:
    """POST /admin/blog-posts/{id}/suggest-schedule requires admin authentication."""
    response = await client.post(
        "/admin/blog-posts/test-post-1/suggest-schedule",
        # No auth headers
    )
    
    assert response.status_code == 401


# ── Integration Tests - Blog Ideas ────────────────────────────────────────


@pytest.mark.asyncio
async def test_suggest_schedule_for_idea_success(
    idea_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """POST /admin/blog-ideas/{id}/suggest-schedule returns 200."""
    response = await idea_client.post(
        "/admin/blog-ideas/test-idea-1/suggest-schedule",
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    assert data["blog_post_id"] == "test-idea-1"  # service uses blog_post_id field
    assert "id" in data
    assert "suggested_date" in data
    assert "suggested_time" in data
    assert "rationale" in data
    assert "confidence" in data
    assert "created_at" in data
    
    # Verify data formats
    import re
    assert re.match(r"^\d{4}-\d{2}-\d{2}$", data["suggested_date"])
    assert re.match(r"^\d{2}:\d{2}$", data["suggested_time"])
    assert 0.0 <= data["confidence"] <= 1.0


@pytest.mark.asyncio
async def test_suggest_schedule_nonexistent_idea_fails(
    idea_client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """POST /admin/blog-ideas/{id}/suggest-schedule returns 404 for nonexistent idea."""
    response = await idea_client.post(
        "/admin/blog-ideas/nonexistent/suggest-schedule",
        headers=auth_headers,
    )
    
    assert response.status_code == 404
    assert "Blog idea not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_suggest_schedule_idea_requires_admin_auth(
    idea_client: AsyncClient,
) -> None:
    """POST /admin/blog-ideas/{id}/suggest-schedule requires admin authentication."""
    response = await idea_client.post(
        "/admin/blog-ideas/test-idea-1/suggest-schedule",
        # No auth headers
    )
    
    assert response.status_code == 401