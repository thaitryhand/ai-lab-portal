"""Integration tests for Content Repurposing Agent routes (US-107)."""

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
from backend.app.content_repurpose import FakeContentRepurposeService
from backend.app.content_repurpose_routes import create_content_repurpose_routes
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
            id="published-post",
            title="Test Published Post",
            slug="test-published-post",
            excerpt="A test excerpt",
            content_markdown="# Test Content\n\nThis is test content.",
            status="published",
            author_name="test-author",
            published_at=datetime.now(UTC),
        ),
        BlogPost(
            id="draft-post",
            title="Test Draft Post",
            slug="test-draft-post",
            excerpt="Draft excerpt",
            content_markdown="# Draft\n\nDraft content.",
            status="draft",
            author_name="test-author",
            published_at=None,
        ),
    ]
    return BlogRepository(posts=test_posts)


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
def content_repurpose_app(
    blog_repo: BlogRepository,
    settings: Settings,
) -> FastAPI:
    """Build minimal FastAPI app with content repurpose router."""
    service = FakeContentRepurposeService()
    router = create_content_repurpose_routes(service, blog_repo, settings)
    
    app = FastAPI()
    app.include_router(router)
    return app


@pytest_asyncio.fixture
async def client(content_repurpose_app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Async test client."""
    transport = ASGITransport(app=content_repurpose_app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ── Integration Tests ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_repurpose_published_post_success(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """POST /admin/blog-posts/{id}/repurpose returns 200 for published post."""
    response = await client.post(
        "/admin/blog-posts/published-post/repurpose",
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure (RepurposedContent)
    assert data["blog_post_id"] == "published-post"
    assert "id" in data
    assert "created_at" in data
    assert "twitter_thread" in data
    assert "linkedin_article" in data
    assert "summary_snippet" in data
    
    # Verify twitter thread
    if data["twitter_thread"]:
        assert "tweets" in data["twitter_thread"]
        assert len(data["twitter_thread"]["tweets"]) >= 1
        for tweet in data["twitter_thread"]["tweets"]:
            assert len(tweet["content"]) <= 280
            assert "number" in tweet
            assert tweet["number"] >= 1
            
    # Verify linkedin article
    if data["linkedin_article"]:
        assert "headline" in data["linkedin_article"]
        assert "summary" in data["linkedin_article"]
        assert "key_takeaways" in data["linkedin_article"]
        assert isinstance(data["linkedin_article"]["key_takeaways"], list)


@pytest.mark.asyncio
async def test_repurpose_draft_post_fails(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """POST /admin/blog-posts/{id}/repurpose returns 400 for draft post."""
    response = await client.post(
        "/admin/blog-posts/draft-post/repurpose",
        headers=auth_headers,
    )
    
    assert response.status_code == 400
    assert "Only published posts can be repurposed" in response.json()["detail"]


@pytest.mark.asyncio
async def test_repurpose_nonexistent_post_fails(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """POST /admin/blog-posts/{id}/repurpose returns 404 for nonexistent post."""
    response = await client.post(
        "/admin/blog-posts/nonexistent/repurpose",
        headers=auth_headers,
    )
    
    assert response.status_code == 404
    assert "Blog post not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_repurpose_requires_admin_auth(
    client: AsyncClient,
) -> None:
    """POST /admin/blog-posts/{id}/repurpose requires admin authentication."""
    response = await client.post(
        "/admin/blog-posts/published-post/repurpose",
        # No auth headers
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_repurpose_invalid_auth_signature(
    client: AsyncClient,
) -> None:
    """POST /admin/blog-posts/{id}/repurpose fails with invalid signature."""
    invalid_headers = {
        ADMIN_IDENTITY_HEADER: json.dumps({"user": "test-admin", "role": "admin"}),
        ADMIN_SIGNATURE_HEADER: "invalid-signature",
    }
    
    response = await client.post(
        "/admin/blog-posts/published-post/repurpose",
        headers=invalid_headers,
    )
    
    assert response.status_code == 401