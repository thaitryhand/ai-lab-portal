"""Additional coverage tests for streaming_routes.py.

Targets uncovered paths:
- Auth (401) test on each streaming endpoint (missing admin identity headers)
- SEO audit streaming endpoint (completely untested)
- Save failure for review and marketing streaming endpoints
- The _streaming_response helper and _make_identity_dep factory
- SSE event format verification
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

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
def app(mock_repo: MagicMock, mock_settings: Settings) -> FastAPI:
    from backend.app.streaming_routes import _build_streaming_router

    router = _build_streaming_router(mock_repo, mock_settings)
    _app = FastAPI()
    _app.include_router(router, prefix="/admin/blog-ideas")
    # No dependency overrides — real auth runs
    _app.dependency_overrides = {}
    return _app


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest_asyncio.fixture
async def auth_client(
    app: FastAPI, mock_settings: Settings
) -> AsyncIterator[AsyncClient]:
    """Client pre-configured with valid auth headers."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        import hashlib
        import hmac
        import time
        now = int(time.time())
        from backend.app.admin_boundary import (
            ADMIN_IDENTITY_HEADER,
            ADMIN_SIGNATURE_HEADER,
        )
        payload = json.dumps(
            {"user_id": "admin_1", "email": "admin@test.com",
             "role": "admin", "issued_at": now},
            separators=(",", ":"),
        )
        secret = mock_settings.admin_boundary_secret.get_secret_value()
        sig = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
        c.headers.update({
            ADMIN_IDENTITY_HEADER: payload,
            ADMIN_SIGNATURE_HEADER: sig,
        })
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
            "outline_sections",
            [{"section": "Intro", "points": ["Background"]}],
        ),
        draft_markdown=overrides.get("draft_markdown", "# Draft content"),
        marketing_metadata=overrides.get("marketing_metadata", {"seo_title": "SEO Title"}),
        positioning_notes=overrides.get("positioning_notes", []),
        created_at=overrides.get("created_at", "2026-06-01T00:00:00Z"),
        updated_at=overrides.get("updated_at", "2026-06-01T00:00:00Z"),
    )


def _mock_stream_generate(events: list[str] | None = None, *, result_data: dict | None = None):
    if events is None:
        if result_data is None:
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


# ── Auth tests (401) ────────────────────────────────────────────────────


class TestAuthRequired:
    """All streaming endpoints require valid admin identity."""

    @pytest.mark.asyncio
    async def test_outline_requires_auth(self, client: AsyncClient):
        resp = await client.post("/admin/blog-ideas/idea_123/generate-stream/outline")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_draft_requires_auth(self, client: AsyncClient):
        resp = await client.post("/admin/blog-ideas/idea_123/generate-stream/draft")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_review_requires_auth(self, client: AsyncClient):
        resp = await client.post("/admin/blog-ideas/idea_123/generate-stream/review")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_marketing_requires_auth(self, client: AsyncClient):
        resp = await client.post("/admin/blog-ideas/idea_123/generate-stream/marketing")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_seo_requires_auth(self, client: AsyncClient):
        resp = await client.post("/admin/blog-ideas/idea_123/generate-stream/seo")
        assert resp.status_code == 401


# ── SEO streaming endpoint ──────────────────────────────────────────────


class TestGenerateSeoStream:
    """POST /admin/blog-ideas/{idea_id}/generate-stream/seo"""

    @pytest.mark.asyncio
    async def test_404_when_idea_not_found(self, auth_client: AsyncClient, mock_repo: MagicMock):
        mock_repo.get_by_id.return_value = None
        resp = await auth_client.post("/admin/blog-ideas/nonexistent/generate-stream/seo")
        assert resp.status_code == 404
        assert "not found" in resp.text.lower()

    @pytest.mark.asyncio
    async def test_requires_approved_draft(self, auth_client: AsyncClient, mock_repo: MagicMock):
        mock_repo.get_by_id.return_value = _make_idea(draft_status="pending")
        resp = await auth_client.post("/admin/blog-ideas/idea_123/generate-stream/seo")
        assert resp.status_code == 400
        assert "requires an approved draft" in resp.text.lower()

    @pytest.mark.asyncio
    async def test_requires_marketing_metadata(self, auth_client: AsyncClient, mock_repo: MagicMock):
        mock_repo.get_by_id.return_value = _make_idea(marketing_metadata=None)
        resp = await auth_client.post("/admin/blog-ideas/idea_123/generate-stream/seo")
        assert resp.status_code == 400
        assert "marketing metadata" in resp.text.lower()

    @pytest.mark.asyncio
    async def test_streams_and_saves(self, auth_client: AsyncClient, mock_repo: MagicMock):
        mock_repo.get_by_id.return_value = _make_idea(
            marketing_metadata={"seo_title": "SEO Title", "meta_description": "Desc"},
        )
        result_data = {
            "overall_score": 85.0,
            "title_analysis": "Good title length",
            "meta_description_analysis": "Needs improvement",
            "heading_structure": "Clear hierarchy",
            "keyword_analysis": "Keyword present in title",
            "readability_assessment": "Readable",
            "internal_linking": "No internal links found",
            "approval_recommendation": "approve",
            "issues": [
                {
                    "severity": "minor",
                    "category": "meta_description",
                    "text": "Meta description is too short",
                    "suggestion": "Expand to 150 characters",
                }
            ],
            "suggestions": ["Improve heading structure"],
        }
        with _mock_stream_generate(result_data=result_data):
            resp = await auth_client.post("/admin/blog-ideas/idea_123/generate-stream/seo")
        assert resp.status_code == 200
        assert "data:" in resp.text
        mock_repo.set_seo_audit.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_failure_yields_error(self, auth_client: AsyncClient, mock_repo: MagicMock):
        mock_repo.get_by_id.return_value = _make_idea(
            marketing_metadata={"seo_title": "SEO", "meta_description": "Desc"},
        )
        mock_repo.set_seo_audit.side_effect = RuntimeError("Save failed")
        result_data = {
            "overall_score": 85.0,
            "title_analysis": "Good",
            "meta_description_analysis": "OK",
            "heading_structure": "Fine",
            "keyword_analysis": "OK",
            "readability_assessment": "Good",
            "internal_linking": "None",
            "approval_recommendation": "approve",
            "issues": [],
            "suggestions": [],
        }
        with _mock_stream_generate(result_data=result_data):
            resp = await auth_client.post("/admin/blog-ideas/idea_123/generate-stream/seo")
        assert resp.status_code == 200
        assert '"type": "error"' in resp.text
        assert "Save failed" in resp.text


# ── Save failure for review and marketing ───────────────────────────────


class TestGenerateReviewStreamSaveFailure:
    """POST /admin/blog-ideas/{idea_id}/generate-stream/review — save failures."""

    @pytest.mark.asyncio
    async def test_save_failure_yields_error(self, auth_client: AsyncClient, mock_repo: MagicMock):
        mock_repo.get_by_id.return_value = _make_idea()
        mock_repo.set_technical_review.side_effect = RuntimeError("Review save failed")
        with _mock_stream_generate(result_data={
            "overall_risk": "low", "issues": [], "approval_recommendation": "approve",
        }):
            resp = await auth_client.post("/admin/blog-ideas/idea_123/generate-stream/review")
        assert resp.status_code == 200
        assert '"type": "error"' in resp.text
        assert "Review save failed" in resp.text


class TestGenerateMarketingStreamSaveFailure:
    """POST /admin/blog-ideas/{idea_id}/generate-stream/marketing — save failures."""

    @pytest.mark.asyncio
    async def test_save_failure_yields_error(self, auth_client: AsyncClient, mock_repo: MagicMock):
        mock_repo.get_by_id.return_value = _make_idea()
        mock_repo.set_marketing_metadata.side_effect = RuntimeError("Mkt save failed")
        with _mock_stream_generate(result_data={
            "seo_title": "SEO", "meta_description": "Desc",
            "excerpt": "Excerpt", "linkedin_post": "LI",
            "x_post": "X", "cta": "CTA",
        }):
            resp = await auth_client.post("/admin/blog-ideas/idea_123/generate-stream/marketing")
        assert resp.status_code == 200
        assert '"type": "error"' in resp.text
        assert "Mkt save failed" in resp.text


# ── _streaming_response helper ──────────────────────────────────────────


class TestStreamingResponseHelper:
    """Direct test for the _streaming_response wrapper."""

    def test_returns_streaming_response_with_correct_headers(self):
        from backend.app.streaming_routes import _streaming_response

        async def dummy_gen():
            yield "data: hello\n\n"

        resp = _streaming_response(dummy_gen())
        assert resp.media_type == "text/event-stream"
        assert resp.headers.get("cache-control") == "no-cache"
        assert resp.headers.get("connection") == "keep-alive"
        assert resp.headers.get("x-accel-buffering") == "no"


class TestMakeIdentityDep:
    """Direct test for the _make_identity_dep factory."""

    def test_factory_returns_callable(self):
        from backend.app.streaming_routes import _make_identity_dep

        settings = Settings(
            environment="test",
            admin_boundary_secret="test-secret-at-least-32-characters-long!!",
        )
        dep = _make_identity_dep(settings)
        assert callable(dep)
        # Verify it raises with no headers (returns 401)
        from fastapi import HTTPException
        try:
            dep(identity_payload=None, signature=None)
            assert False, "Should have raised HTTPException"
        except HTTPException as e:
            assert e.status_code == 401
