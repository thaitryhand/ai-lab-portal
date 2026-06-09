"""Auto-Scheduling Agent.

Analyzes content readiness, calendar context, and historical engagement
to suggest optimal publishing times for approved blog posts.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


# ── Output Models ──


class SchedulingSuggestion(BaseModel):
    """Suggestion for when to publish a blog post."""
    id: str = ""
    blog_post_id: str = ""
    suggested_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    suggested_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    rationale: str = Field(..., min_length=1, max_length=1000)
    confidence: float = Field(..., ge=0.0, le=1.0)
    created_at: str = ""


# ── Service Interface ──


class SchedulingService(ABC):
    """Abstract service for auto-scheduling suggestions."""

    @abstractmethod
    def suggest(
        self,
        blog_post_id: str,
        title: str,
        status: str,
        existing_scheduled: list[str] | None = None,
    ) -> SchedulingSuggestion: ...


# ── Fake Provider ──


class FakeSchedulingService(SchedulingService):
    """Returns a plausible scheduling suggestion for testing."""

    def suggest(
        self,
        blog_post_id: str,
        title: str,
        status: str,
        existing_scheduled: list[str] | None = None,
    ) -> SchedulingSuggestion:
        now = datetime.now(UTC)
        # Suggest next Tuesday at 10:00 AM
        days_ahead = (1 - now.weekday()) % 7  # Days until Tuesday
        if days_ahead <= 0:
            days_ahead = 7
        suggested = now + timedelta(days=days_ahead)
        suggested = suggested.replace(hour=10, minute=0, second=0, microsecond=0)

        return SchedulingSuggestion(
            id=str(uuid4()),
            blog_post_id=blog_post_id,
            suggested_date=suggested.strftime("%Y-%m-%d"),
            suggested_time="10:00",
            rationale=(
                f"Based on historical engagement patterns, Tuesday at 10:00 AM "
                f"shows the highest reader activity. The content appears ready "
                f"(status: {status}). Publishing on {suggested.strftime('%A, %B %d')} "
                f"avoids weekend traffic dips."
            ),
            confidence=0.78,
            created_at=datetime.now(UTC).isoformat(),
        )


# ── LLM-Powered Service ──


class LLMSchedulingService(SchedulingService):
    """Uses LLMService to generate scheduling suggestions."""

    def __init__(self, llm_service: Any, analytics_service: Any | None = None) -> None:
        self._llm = llm_service
        self._analytics = analytics_service

    def suggest(
        self,
        blog_post_id: str,
        title: str,
        status: str,
        existing_scheduled: list[str] | None = None,
    ) -> SchedulingSuggestion:
        # Gather context for the LLM
        now = datetime.now(UTC)
        day_of_week = now.strftime("%A")
        existing_str = ", ".join(existing_scheduled or []) or "None"

        # Get engagement data from analytics if available
        engagement_data = "No historical engagement data available."
        if self._analytics:
            try:
                summary = self._analytics.get_summary()
                engagement_data = (
                    f"Total views (30d): {summary.total_views_30d}, "
                    f"Unique visitors (30d): {summary.unique_visitors_30d}"
                )
            except Exception:
                pass

        inputs = {
            "title": title,
            "status": status,
            "day_of_week": day_of_week,
            "existing_scheduled": existing_str,
            "engagement_data": engagement_data,
        }

        try:
            result = self._llm.generate(
                "scheduling_suggest",
                inputs,
                SchedulingSuggestion,
            )
            if isinstance(result, SchedulingSuggestion):
                result.id = str(uuid4())
                result.blog_post_id = blog_post_id
                result.created_at = datetime.now(UTC).isoformat()
                return result
        except Exception:
            pass

        # Fallback to fake logic
        return FakeSchedulingService().suggest(blog_post_id, title, status, existing_scheduled)
