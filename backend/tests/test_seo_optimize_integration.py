"""Integration tests for SEO Auto-Optimize Agent routes (US-109)."""

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
from backend.app.blog_ideas import BlogIdea, BlogIdeaRepository
from backend.app.seo_optimizer import FakeSeoOptimizerService, SeoChange, SeoApplyRequest
from backend.app.seo_optimizer_routes import create_seo_optimizer_routes
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
def ideas_repo() -> BlogIdeaRepository:
    """Blog ideas repository with test ideas."""
    from datetime import datetime, UTC
    
    now = datetime.now(UTC)
    test_ideas = [
        BlogIdea(
            id="test-idea-1",
            title="Basic SEO Title",
            angle="SEO Testing",
            target_reader="Marketers",
            article_goal="Show SEO approach",
            positioning_notes=[],
            source="manual",
            status="pending",
            draft_markdown="# Basic Content\n\nSome content here.",
            seo_audit={"keyword_density": 0.5, "readability_score": 60},
            created_at=now,
            updated_at=now,
        ),
        BlogIdea(
            id="test-idea-minimal",
            title="Minimal Idea",
            angle="Minimal Testing",
            target_reader="Everyone",
            article_goal="Simple test",
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
def seo_optimizer_app(
    ideas_repo: BlogIdeaRepository,
    settings: Settings,
) -> FastAPI:
    """Build minimal FastAPI app with SEO optimizer router."""
    service = FakeSeoOptimizerService()
    router = create_seo_optimizer_routes(service, ideas_repo, settings)
    
    app = FastAPI()
    app.include_router(router)
    return app


@pytest_asyncio.fixture
async def client(seo_optimizer_app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Async test client."""
    transport = ASGITransport(app=seo_optimizer_app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


# ── Integration Tests - SEO Optimization ───────────────────────────────────


@pytest.mark.asyncio
async def test_optimize_seo_success(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """POST /admin/blog-ideas/{idea_id}/optimize-seo returns 200."""
    response = await client.post(
        "/admin/blog-ideas/test-idea-1/optimize-seo",
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure (SeoOptimizationResult)
    assert data["blog_idea_id"] == "test-idea-1"
    assert "id" in data
    assert "changes" in data
    assert "overall_summary" in data
    assert "created_at" in data
    
    # Verify changes structure
    assert len(data["changes"]) >= 1
    for change in data["changes"]:
        assert "section" in change
        assert "before" in change
        assert "after" in change
        assert "rationale" in change
        assert len(change["rationale"]) > 0
    
    # Verify expected SEO sections are present
    sections = {change["section"] for change in data["changes"]}
    expected_sections = {"title", "meta_description", "headings", "internal_links", "keywords"}
    assert sections >= expected_sections  # should contain at least these sections


@pytest.mark.asyncio
async def test_optimize_seo_minimal_content(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """POST /admin/blog-ideas/{idea_id}/optimize-seo works with minimal content."""
    response = await client.post(
        "/admin/blog-ideas/test-idea-minimal/optimize-seo", 
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["blog_idea_id"] == "test-idea-minimal"
    assert len(data["changes"]) >= 1


@pytest.mark.asyncio
async def test_optimize_seo_nonexistent_idea_fails(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """POST /admin/blog-ideas/{idea_id}/optimize-seo returns 404 for nonexistent idea."""
    response = await client.post(
        "/admin/blog-ideas/nonexistent/optimize-seo",
        headers=auth_headers,
    )
    
    assert response.status_code == 404
    assert "Blog idea not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_optimize_seo_requires_admin_auth(
    client: AsyncClient,
) -> None:
    """POST /admin/blog-ideas/{idea_id}/optimize-seo requires admin authentication."""
    response = await client.post(
        "/admin/blog-ideas/test-idea-1/optimize-seo",
        # No auth headers
    )
    
    assert response.status_code == 401


# ── Integration Tests - Apply SEO Changes ──────────────────────────────────


@pytest.mark.asyncio
async def test_apply_seo_changes_success(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """POST /admin/blog-ideas/{id}/apply-seo-changes returns 200."""
    # First get optimization suggestions
    opt_response = await client.post(
        "/admin/blog-ideas/test-idea-1/optimize-seo",
        headers=auth_headers,
    )
    assert opt_response.status_code == 200
    changes = opt_response.json()["changes"]
    
    # Apply subset of changes
    apply_payload = {
        "accepted_sections": ["title", "meta_description"],
        "changes": changes,
    }
    
    response = await client.post(
        "/admin/blog-ideas/test-idea-1/apply-seo-changes",
        headers=auth_headers,
        json=apply_payload,
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response structure
    assert "applied_sections" in data
    assert "new_title" in data
    assert "new_draft_markdown" in data
    assert "new_metadata" in data
    assert "summary" in data
    
    # Should only have changes for accepted sections
    assert set(data["applied_sections"]) <= {"title", "meta_description"}


@pytest.mark.asyncio
async def test_apply_seo_changes_single_section(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """POST /admin/blog-ideas/{id}/apply-seo-changes works with single section."""
    # Create a minimal valid change
    changes = [
        SeoChange(section="title", before="Old Title", after="New Title", rationale="Better title").model_dump()
    ]
    
    apply_payload = {
        "accepted_sections": ["title"],
        "changes": changes,
    }
    
    response = await client.post(
        "/admin/blog-ideas/test-idea-1/apply-seo-changes",
        headers=auth_headers,
        json=apply_payload,
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["applied_sections"]) == 1
    assert "title" in data["applied_sections"]


@pytest.mark.asyncio
async def test_apply_seo_changes_invalid_payload(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """POST /admin/blog-ideas/{id}/apply-seo-changes returns 422 for invalid payload."""
    response = await client.post(
        "/admin/blog-ideas/test-idea-1/apply-seo-changes",
        headers=auth_headers,
        json={},  # Missing required fields
    )
    
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_apply_seo_changes_nonexistent_idea_fails(
    client: AsyncClient,
    auth_headers: dict[str, str],
) -> None:
    """POST /admin/blog-ideas/{id}/apply-seo-changes returns 404 for nonexistent idea."""
    apply_payload = {
        "accepted_sections": ["title"],
        "changes": [SeoChange(section="title", before="Old", after="New", rationale="Better").model_dump()],
    }
    
    response = await client.post(
        "/admin/blog-ideas/nonexistent/apply-seo-changes",
        headers=auth_headers,
        json=apply_payload,
    )
    
    assert response.status_code == 404
    assert "Blog idea not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_apply_seo_changes_requires_admin_auth(
    client: AsyncClient,
) -> None:
    """POST /admin/blog-ideas/{id}/apply-seo-changes requires admin authentication."""
    apply_payload = {
        "accepted_sections": ["title"], 
        "changes": [],
    }
    
    response = await client.post(
        "/admin/blog-ideas/test-idea-1/apply-seo-changes",
        json=apply_payload,
        # No auth headers
    )
    
    assert response.status_code == 401