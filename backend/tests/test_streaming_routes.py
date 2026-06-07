"""Integration tests for streaming_routes.py — SSE endpoints for pipeline stages.

Uses ``httpx.AsyncClient`` with fixtures for the app and client.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from collections.abc import AsyncIterator
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

from backend.app.admin_boundary import ADMIN_IDENTITY_HEADER, ADMIN_SIGNATURE_HEADER
from backend.app.blog_ideas import BlogIdea
from backend.app.settings import Settings


# ── Fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture
def mock_repo() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_settings() -> Settings:
    return Settings(
        environment="test",
        llm_backend="agents_sdk",
        llm_model="gpt-4o",
        admin_boundary_secret="test-secret-at-least-32-characters-long!!",
    )


@pytest.fixture
def auth_headers(mock_settings: Settings) -> dict[str, str]:
    return _admin_headers(mock_settings)


@pytest.fixture
def app(mock_repo: MagicMock, mock_settings: Settings) -> FastAPI:
    from backend.app.admin_boundary import AdminIdentity
    from backend.app.streaming_routes import _build_streaming_router

    router = _build_streaming_router(mock_repo, mock_settings)
    _app = FastAPI()
    _app.include_router(router, prefix="/admin/blog-ideas")

    # Override the admin identity dependency to bypass auth
    async def _fake_admin() -> AdminIdentity:
        return AdminIdentity(user_id="admin_1", email="admin@test.com", role="admin")
    _app.dependency_overrides = {}
    return _app


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    """AsyncClient fixture — requires @pytest.mark.asyncio on the test."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


def _make_idea(**overrides) -> BlogIdea:
    return BlogIdea(
        id=overrides.get("id", "idea_123"),
        title=overrides.get("title", "Test Idea"),
        status=overrides.get("status", "approved"),
        angle=overrides.get("angle", "AI Testing"),
        target_reader=overrides.get("target_reader", "Developers"),
        article_goal=overrides.get("article_goal", "Show testing approach"),
        outline_status=overrides.get("outline_status", "approved"),
        draft_status=overrides.get("draft_status", "approved"),
        outline_sections=overrides.get(
            "outline_sections", [{"section": "Intro", "points": ["Background"]}],
        ),
        draft_markdown=overrides.get("draft_markdown", "# Draft content"),
        positioning_notes=overrides.get("positioning_notes", []),
        created_at=overrides.get("created_at", "2026-06-01T00:00:00Z"),
        updated_at=overrides.get("updated_at", "2026-06-01T00:00:00Z"),
    )


def _admin_headers(settings: Settings) -> dict[str, str]:
    """Create signed admin identity headers for test requests."""
    import time
    now = int(time.time())
    payload = json.dumps(
        {"user_id": "admin_1", "email": "admin@test.com", "role": "admin", "issued_at": now},
        separators=(",", ":"),
    )
    secret = settings.admin_boundary_secret.get_secret_value()
    sig = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return {ADMIN_IDENTITY_HEADER: payload, ADMIN_SIGNATURE_HEADER: sig}


def _mock_stream_generate(events: list[str] | None = None, *, result_data: dict | None = None):
    if events is None:
        if result_data is None:
            # Default result data matches BlogOutline schema
            result_data = {
                "title": "Test Outline",
                "outline": [{"section": "Intro", "points": ["Background"]}],
            }
        events = [
            json.dumps({"type": "token", "data": "Hello"}),
            json.dumps({"type": "status", "status": "streaming", "data": "Done"}),
            json.dumps({"type": "result", "data": result_data}),
        ]

    async def _gen():
        for e in events:
            yield e

    return patch(
        "backend.app.streaming_routes.stream_generate",
        side_effect=lambda *a, **kw: _gen(),
    )


# ── Tests ───────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_404_when_idea_not_found(client: AsyncClient, mock_repo: MagicMock, auth_headers: dict[str, str]):
    mock_repo.get_by_id.return_value = None
    resp = await client.post(
        "/admin/blog-ideas/nonexistent/generate-stream/outline",
        headers=auth_headers,
    )
    assert resp.status_code == 404
    assert "not found" in resp.text.lower()


@pytest.mark.asyncio
async def test_outline_requires_approved_status(client: AsyncClient, mock_repo: MagicMock, auth_headers: dict[str, str]):
    mock_repo.get_by_id.return_value = _make_idea(status="pending")
    resp = await client.post(
        "/admin/blog-ideas/idea_123/generate-stream/outline",
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert "requires an approved idea" in resp.text.lower()


@pytest.mark.asyncio
async def test_draft_requires_approved_outline(client: AsyncClient, mock_repo: MagicMock, auth_headers: dict[str, str]):
    mock_repo.get_by_id.return_value = _make_idea(outline_status="pending")
    resp = await client.post(
        "/admin/blog-ideas/idea_123/generate-stream/draft",
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert "requires an approved outline" in resp.text.lower()


@pytest.mark.asyncio
async def test_review_requires_approved_draft(client: AsyncClient, mock_repo: MagicMock, auth_headers: dict[str, str]):
    mock_repo.get_by_id.return_value = _make_idea(draft_status="pending")
    resp = await client.post(
        "/admin/blog-ideas/idea_123/generate-stream/review",
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert "requires an approved draft" in resp.text.lower()


@pytest.mark.asyncio
async def test_marketing_requires_approved_draft(client: AsyncClient, mock_repo: MagicMock, auth_headers: dict[str, str]):
    mock_repo.get_by_id.return_value = _make_idea(draft_status="pending")
    resp = await client.post(
        "/admin/blog-ideas/idea_123/generate-stream/marketing",
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert "requires an approved draft" in resp.text.lower()


@pytest.mark.asyncio
async def test_outline_streams_and_saves(client: AsyncClient, mock_repo: MagicMock, auth_headers: dict[str, str]):
    mock_repo.get_by_id.return_value = _make_idea()
    with _mock_stream_generate(result_data={
        "title": "Test Outline",
        "outline": [{"section": "Intro", "points": ["Background"]}],
    }):
        resp = await client.post(
            "/admin/blog-ideas/idea_123/generate-stream/outline",
            headers=auth_headers,
        )
    assert resp.status_code == 200
    assert "data:" in resp.text
    mock_repo.set_outline.assert_called_once()


@pytest.mark.asyncio
async def test_outline_save_failure_yields_error(client: AsyncClient, mock_repo: MagicMock, auth_headers: dict[str, str]):
    mock_repo.get_by_id.return_value = _make_idea()
    mock_repo.set_outline.side_effect = ValueError("DB error")
    with _mock_stream_generate(result_data={
        "title": "Outline",
        "outline": [{"section": "S", "points": ["P"]}],
    }):
        resp = await client.post(
            "/admin/blog-ideas/idea_123/generate-stream/outline",
            headers=auth_headers,
        )
    assert resp.status_code == 200
    assert '"type": "error"' in resp.text
    assert "DB error" in resp.text


@pytest.mark.asyncio
async def test_draft_streams_and_saves(client: AsyncClient, mock_repo: MagicMock, auth_headers: dict[str, str]):
    mock_repo.get_by_id.return_value = _make_idea()
    with _mock_stream_generate(result_data={
        "title": "Draft Title",
        "markdown": "# Draft\n\nContent.",
    }):
        resp = await client.post(
            "/admin/blog-ideas/idea_123/generate-stream/draft",
            headers=auth_headers,
        )
    assert resp.status_code == 200
    assert "data:" in resp.text
    mock_repo.set_draft.assert_called_once()


@pytest.mark.asyncio
async def test_draft_save_failure_yields_error(client: AsyncClient, mock_repo: MagicMock, auth_headers: dict[str, str]):
    mock_repo.get_by_id.return_value = _make_idea()
    mock_repo.set_draft.side_effect = RuntimeError("Save failed")
    with _mock_stream_generate(result_data={
        "title": "Draft",
        "markdown": "# Draft",
    }):
        resp = await client.post(
            "/admin/blog-ideas/idea_123/generate-stream/draft",
            headers=auth_headers,
        )
    assert resp.status_code == 200
    assert '"type": "error"' in resp.text
    assert "Save failed" in resp.text


@pytest.mark.asyncio
async def test_review_streams_and_saves(client: AsyncClient, mock_repo: MagicMock, auth_headers: dict[str, str]):
    mock_repo.get_by_id.return_value = _make_idea()
    with _mock_stream_generate(result_data={
        "overall_risk": "low",
        "issues": [],
        "approval_recommendation": "approve",
    }):
        resp = await client.post(
            "/admin/blog-ideas/idea_123/generate-stream/review",
            headers=auth_headers,
        )
    assert resp.status_code == 200
    assert "data:" in resp.text
    mock_repo.set_technical_review.assert_called_once()


@pytest.mark.asyncio
async def test_marketing_streams_and_saves(client: AsyncClient, mock_repo: MagicMock, auth_headers: dict[str, str]):
    mock_repo.get_by_id.return_value = _make_idea()
    with _mock_stream_generate(result_data={
        "seo_title": "SEO Title",
        "meta_description": "A meta description.",
        "excerpt": "An excerpt.",
        "linkedin_post": "LinkedIn post.",
        "x_post": "X post.",
        "cta": "Contact us.",
    }):
        resp = await client.post(
            "/admin/blog-ideas/idea_123/generate-stream/marketing",
            headers=auth_headers,
        )
    assert resp.status_code == 200
    assert "data:" in resp.text
    mock_repo.set_marketing_metadata.assert_called_once()


@pytest.mark.asyncio
async def test_saved_event_contains_redirect_url(client: AsyncClient, mock_repo: MagicMock, auth_headers: dict[str, str]):
    mock_repo.get_by_id.return_value = _make_idea()

    result_event = json.dumps({
        "type": "result",
        "data": {
            "title": "Test Outline",
            "outline": [{"section": "Intro", "points": ["Background"]}],
        },
    })
    with _mock_stream_generate(events=[result_event]):
        resp = await client.post(
            "/admin/blog-ideas/idea_123/generate-stream/outline",
            headers=auth_headers,
        )

    assert '"type": "saved"' in resp.text
    assert '"redirect_url"' in resp.text
    assert "/admin/blog-ideas/idea_123" in resp.text
