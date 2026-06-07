"""Streaming SSE endpoint for LLM-based news article scoring.

Provides a real-time streaming endpoint that scores a news article using the
Agents SDK ``Runner.run_streamed()``. Results are saved to the review queue.

Endpoint:
    POST /admin/news/scoring/stream?article_id={id}
"""

from __future__ import annotations

import json as _json
from collections.abc import Callable
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import StreamingResponse

from backend.app.admin_boundary import (
    ADMIN_IDENTITY_HEADER,
    ADMIN_SIGNATURE_HEADER,
    AdminIdentity,
    require_admin_identity_with_settings,
)
from backend.app.llm.schemas import NewsScoring
from backend.app.llm.streaming import stream_generate
from backend.app.news_extraction import (
    ExtractedArticleRepository,
)
from backend.app.news_scoring import (
    InMemoryNewsReviewRepository,
    NewsReviewRepository,
    ScoreDimensions,
    _build_summary,
    _build_why_it_matters,
)
from backend.app.news_sources import NewsSourceRepository
from backend.app.settings import Settings
from backend.app.task_support import _build_mcp_servers
from backend.app.news_crawl import NewsRawItemRepository


def _make_identity_dep(
    settings: Settings,
) -> Callable[[str | None, str | None], AdminIdentity]:
    """Create a FastAPI dependency that validates admin identity headers."""

    def _dep(
        identity_payload: Annotated[
            str | None, Header(alias=ADMIN_IDENTITY_HEADER)
        ] = None,
        signature: Annotated[
            str | None, Header(alias=ADMIN_SIGNATURE_HEADER)
        ] = None,
    ) -> AdminIdentity:
        return require_admin_identity_with_settings(
            settings, identity_payload, signature
        )

    return _dep


def create_news_streaming_router(
    settings: Settings,
) -> APIRouter:
    """Return an APIRouter with the news streaming endpoint.

    The caller mounts this under the ``/admin/news`` or similar prefix.
    """
    router = APIRouter()
    _identity = _make_identity_dep(settings)

    @router.post("/scoring/stream")
    async def score_article_stream(
        article_id: str = Query(description="The extracted article ID"),
        _: AdminIdentity = Depends(_identity),
    ) -> StreamingResponse:
        """Score an extracted article with real-time token streaming.

        Args:
            article_id: The extracted article ID to score.

        Returns:
            SSE stream with token, result, saved events.
        """
        # Fetch the article and related entities
        articles_repo = ExtractedArticleRepository()
        article = articles_repo.get_by_id(article_id)
        if article is None:
            raise HTTPException(
                status_code=404,
                detail=f"Extracted article '{article_id}' not found",
            )

        raw_repo = NewsRawItemRepository()
        raw_item = raw_repo.get_by_id(article.raw_item_id)

        sources_repo = NewsSourceRepository()
        source = (
            sources_repo.get_by_id(raw_item.source_id)
            if raw_item
            else None
        )
        source_name = source.name if source else "Unknown Source"
        source_credibility = (
            str(source.credibility_base_score) if source else "0.5"
        )

        mcp_servers = _build_mcp_servers(settings)

        async def event_stream():
            _result_json: str | None = None

            async for event in stream_generate(
                prompt_name="ai_news_scoring",
                inputs={
                    "source_name": source_name,
                    "source_credibility_score": source_credibility,
                    "title": article.title,
                    "published_at": (
                        article.published_at.isoformat()
                        if article.published_at
                        else "unknown"
                    ),
                    "content_text": article.content_text[:8000],
                },
                output_schema=NewsScoring,
                model=settings.llm_model,
                recorder=None,
                entity_id=article_id,
                entity_type="news_scoring",
                provider="agents_sdk",
                mcp_servers=mcp_servers,
            ):
                if event.startswith('{"type": "result"'):
                    _result_json = event
                yield f"data: {event}\n\n"

            # Save score to review repository
            if _result_json is not None:
                try:
                    parsed = _json.loads(_result_json)
                    result = NewsScoring.model_validate(parsed["data"])

                    scores = ScoreDimensions(
                        source_credibility_score=result.source_credibility_score,
                        engagement_score=result.engagement_score,
                        relevance_score=result.relevance_score,
                        novelty_score=result.novelty_score,
                        technical_depth_score=result.technical_depth_score,
                        business_value_score=result.business_value_score,
                        spam_risk_score=result.spam_risk_score,
                        final_publish_score=result.final_publish_score,
                    )
                    summary = result.summary or _build_summary(article, scores)
                    why = result.why_it_matters or _build_why_it_matters(scores)

                    review_repo = InMemoryNewsReviewRepository()
                    review_repo.upsert_scored(
                        article=article,
                        source=source,
                        scores=scores,
                        review_status="candidate"
                        if scores.final_publish_score >= 0.55
                        else "low_score",
                        summary=summary,
                        why_it_matters=why,
                        scorer_version="llm_streaming_v1",
                        social_metadata_json=None,
                    )

                    saved_event = _json.dumps({
                        "type": "saved",
                        "article_id": article_id,
                        "redirect_url": "/admin/news/review-items",
                    })
                    yield f"data: {saved_event}\n\n"
                except Exception as exc:
                    err_event = _json.dumps({
                        "type": "error",
                        "data": f"Failed to save score: {exc}",
                    })
                    yield f"data: {err_event}\n\n"

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    return router
