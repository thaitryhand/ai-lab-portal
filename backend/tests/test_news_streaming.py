"""E2E integration tests for News Pipeline Agents SDK: streaming + MCP tools.

Tests cover:
1. News streaming SSE endpoint routes and auth
2. News MCP tools (source reliability, trending topics, article context)
3. End-to-end streaming save flow with mocked LLM
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from backend.app.admin_boundary import (
    ADMIN_IDENTITY_HEADER,
    ADMIN_SIGNATURE_HEADER,
    sign_admin_identity,
)
from backend.app.main import create_app
from backend.app.news_crawl import NewsRawItemRepository
from backend.app.news_extraction import (
    ExtractedArticle,
    ExtractedArticleRepository,
)
from backend.app.news_sources import NewsSource, NewsSourceCreate, NewsSourceRepository
from backend.app.settings import Settings

TEST_SECRET = "test-admin-boundary-secret-at-least-32-chars"


def _test_settings() -> Settings:
    return Settings(
        environment="test",
        admin_boundary_secret=TEST_SECRET,
    )


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


def _fake_article(article_id: str = "article_test_001") -> ExtractedArticle:
    """Create a fake ExtractedArticle for testing."""
    return ExtractedArticle(
        id=article_id,
        raw_item_id="raw_test_001",
        source_url="https://example.com/ai-test",
        final_url="https://example.com/ai-test",
        title="Test AI Article About Agents",
        author="Test Author",
        site_name="Test Blog",
        published_at=datetime(2026, 6, 1, tzinfo=UTC),
        content_text="This is a test article about artificial intelligence "
        "and machine learning agents. It discusses how AI agents "
        "can be used for autonomous task completion and "
        "decision-making in enterprise environments. The article "
        "highlights recent advances from OpenAI and Anthropic.",
        content_markdown="# Test AI Article\n\nTest content...",
        content_hash="abc123",
        provider="fake",
        extraction_status="success",
        duplicate_status="unique",
        extraction_error=None,
        provider_latency_ms=100,
        extracted_at=datetime.now(UTC),
    )


# ===========================================================================
# News Streaming Tests
# ===========================================================================


class TestNewsStreamingRoutes:
    """Verify the news streaming SSE endpoint."""

    def test_streaming_requires_auth(self):
        """Streaming endpoint returns 401 without admin headers."""
        settings = _test_settings()
        app = create_app(settings)
        client = TestClient(app)

        response = client.post("/admin/news/scoring/stream?article_id=test_123")
        assert response.status_code == 401

    def test_streaming_returns_404_for_missing_article(self):
        """Streaming endpoint returns 404 for unknown article_id."""
        settings = _test_settings()
        app = create_app(settings)
        client = TestClient(app)

        headers = _admin_headers()
        response = client.post(
            "/admin/news/scoring/stream?article_id=nonexistent_123",
            headers=headers,
        )
        assert response.status_code == 404

    def test_streaming_returns_sse_response(self):
        """Streaming endpoint returns SSE content type with valid article."""
        settings = _test_settings()
        app = create_app(settings)
        client = TestClient(app)
        headers = _admin_headers()

        with patch.object(
            ExtractedArticleRepository,
            "get_by_id",
            return_value=_fake_article(),
        ):
            raw_item_mock = MagicMock()
            raw_item_mock.source_id = "source_test_001"
            raw_item_mock.id = "raw_test_001"
            with patch.object(
                NewsRawItemRepository, "get_by_id", return_value=raw_item_mock
            ):
                source_mock = MagicMock()
                source_mock.id = "source_test_001"
                source_mock.name = "Test AI Blog"
                source_mock.credibility_base_score = 0.8
                with patch.object(
                    NewsSourceRepository,
                    "get_by_id",
                    return_value=source_mock,
                ):
                    async def fake_events():
                        yield json.dumps({"type": "status", "status": "starting"})
                        yield json.dumps({"type": "token", "data": "test"})
                        yield json.dumps({"type": "result", "data": {
                            "source_credibility_score": 0.8,
                            "engagement_score": 0.6,
                            "relevance_score": 0.9,
                            "novelty_score": 0.5,
                            "technical_depth_score": 0.7,
                            "business_value_score": 0.6,
                            "spam_risk_score": 0.1,
                            "final_publish_score": 0.75,
                            "summary": "Test summary.",
                            "why_it_matters": "Relevant.",
                        }})

                    with patch(
                        "backend.app.news_streaming.stream_generate",
                        return_value=fake_events(),
                    ):
                        with client.stream(
                            "POST",
                            "/admin/news/scoring/stream?article_id=article_test_001",
                            headers=headers,
                        ) as response:
                            assert response.status_code == 200
                            content_type = response.headers.get("content-type", "")
                            assert content_type.startswith("text/event-stream"), (
                                f"Expected text/event-stream, got {content_type}"
                            )

                            # Verify we receive at least some SSE events
                            events_received = 0
                            for line in response.iter_lines():
                                if line.startswith("data: "):
                                    events_received += 1
                            assert events_received >= 1, "No SSE events received"

    def test_streaming_route_validation(self):
        """Streaming endpoint validates the article_id query parameter."""
        settings = _test_settings()
        app = create_app(settings)
        client = TestClient(app)
        headers = _admin_headers()

        # Missing article_id should return 422 validation error
        response = client.post("/admin/news/scoring/stream", headers=headers)
        assert response.status_code == 422


# ===========================================================================
# News MCP Tools Tests
# ===========================================================================


class TestNewsMCPTools:
    """Verify the 3 news MCP tools work correctly."""

    def test_source_reliability_known_source(self):
        """Source reliability returns info for a known source by name."""
        from backend.mcp_server.server import get_source_reliability

        # Mock _get_engine to return None (DB unavailable) so the
        # function uses the fallback path, then verify no crash
        from unittest.mock import patch

        with patch(
            "backend.mcp_server.server._get_engine",
            return_value=None,
        ):
            result = get_source_reliability("AI Test Blog MCP")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_source_reliability_unknown_source(self):
        """Source reliability returns helpful message for unknown source."""
        from backend.mcp_server.server import get_source_reliability

        result = get_source_reliability("Totally Unknown Source 42")
        # Should return a helpful message, not crash
        assert isinstance(result, str)
        assert len(result) > 0

    def test_trending_topics_returns_string(self):
        """Trending topics returns a message (may be empty if no data)."""
        from backend.mcp_server.server import get_trending_topics

        result = get_trending_topics(days=1, max_topics=5)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_article_context_unknown(self):
        """Article context returns helpful message for unknown ID."""
        from backend.mcp_server.server import get_article_context

        result = get_article_context("nonexistent_article_xyz")
        assert isinstance(result, str)
        assert "not found" in result.lower() or "unable" in result.lower()

    def test_mcp_tools_registered(self):
        """All news MCP tools are registered on the server instance."""
        from backend.mcp_server.server import mcp

        tool_names = [t.name for t in mcp._tool_manager.list_tools()]
        assert "news__source_reliability" in tool_names
        assert "news__trending_topics" in tool_names
        assert "news__article_context" in tool_names


# ===========================================================================
# E2E Streaming Save Flow
# ===========================================================================


class TestNewsStreamingSaveFlow:
    """Verify the streaming endpoint saves scores correctly."""

    def test_stream_saves_to_review_queue(self):
        """After streaming, a saved SSE event is emitted with redirect."""
        article_id = "article_save_test"
        settings = _test_settings()
        app = create_app(settings)
        client = TestClient(app)
        headers = _admin_headers()

        with patch.object(
            ExtractedArticleRepository,
            "get_by_id",
            return_value=_fake_article(article_id),
        ):
            raw_repo_mock = MagicMock()
            raw_repo_mock.get_by_id.return_value = MagicMock(
                source_id="source_save_test",
            )
            with patch.object(
                NewsRawItemRepository, "get_by_id", return_value=raw_repo_mock.get_by_id()
            ):
                source_mock = MagicMock()
                source_mock.id = "source_save_test"
                source_mock.name = "Test AI Blog"
                source_mock.credibility_base_score = 0.8
                with patch.object(
                    NewsSourceRepository,
                    "get_by_id",
                    return_value=source_mock,
                ):
                    async def fake_gen():
                        yield json.dumps({"type": "result", "data": {
                            "source_credibility_score": 0.8,
                            "engagement_score": 0.6,
                            "relevance_score": 0.9,
                            "novelty_score": 0.5,
                            "technical_depth_score": 0.7,
                            "business_value_score": 0.6,
                            "spam_risk_score": 0.1,
                            "final_publish_score": 0.75,
                            "summary": "Test article summary.",
                            "why_it_matters": "Strong relevance.",
                        }})

                    with patch(
                        "backend.app.news_streaming.stream_generate",
                        return_value=fake_gen(),
                    ):
                        with client.stream(
                            "POST",
                            f"/admin/news/scoring/stream?article_id={article_id}",
                            headers=headers,
                        ) as response:
                            assert response.status_code == 200

                            saved_event = None
                            for line in response.iter_lines():
                                if line.startswith("data: "):
                                    raw = line[6:].strip()
                                    try:
                                        evt = json.loads(raw)
                                        if evt.get("type") == "saved":
                                            saved_event = evt
                                    except json.JSONDecodeError:
                                        pass

                            assert saved_event is not None, "No saved event"
                            assert saved_event["type"] == "saved"
                            assert saved_event["article_id"] == article_id


# ===========================================================================
# Multi-agent news review tests
# ===========================================================================


class TestNewsMultiAgentReview:
    """Verify the multi-agent news review pattern (Agent-as-tool)."""

    def test_build_news_claim_extractor(self):
        """NewsClaimExtractor agent builds with correct output type."""
        from backend.app.llm.news_review_agent import (
            NewsQualityReport,
            build_news_claim_extractor,
        )

        agent = build_news_claim_extractor()
        assert agent.name == "NewsClaimExtractor"
        assert agent.output_type is NewsQualityReport

    def test_build_news_quality_reviewer(self):
        """NewsQualityReviewer agent builds with ClaimExtractor as tool."""
        from backend.app.llm.news_review_agent import (
            NewsQualityReport,
            build_news_quality_reviewer,
        )

        agent = build_news_quality_reviewer(mcp_servers=[])
        assert agent.name == "NewsQualityReviewer"
        assert agent.output_type is NewsQualityReport
        assert agent.tools is not None
        tool_names = [getattr(t, "name", "") for t in agent.tools]
        assert "extract_claims" in tool_names

    def test_quality_report_schema(self):
        """NewsQualityReport schema has expected fields."""
        from backend.app.llm.news_review_agent import (
            BiasIndicator,
            NewsQualityReport,
        )

        report = NewsQualityReport(
            overall_assessment="Good article",
            credibility_score=0.8,
            concerns=[
                BiasIndicator(
                    category="bias",
                    excerpt="Sample text",
                    concern="Potential bias",
                    severity="low",
                )
            ],
            positive_notes=["Well-researched"],
            recommendation="approve",
        )
        assert report.overall_assessment == "Good article"
        assert report.credibility_score == 0.8
        assert len(report.concerns) == 1
        assert report.concerns[0].category == "bias"
        assert report.recommendation == "approve"
