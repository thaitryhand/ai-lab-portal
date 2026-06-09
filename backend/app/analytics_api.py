"""Analytics aggregation API for page view data.

Provides endpoints for the admin analytics dashboard:
- Summary stats (today, 7d, 30d, all-time)
- Top content by views
- Daily view trends
- Referrer breakdown

Uses PageViewRepository for data access (injected by main.py).
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Header, Query
from pydantic import BaseModel

from backend.app.admin_boundary import (
    ADMIN_IDENTITY_HEADER,
    ADMIN_SIGNATURE_HEADER,
    AdminIdentity,
    require_admin_identity_with_settings,
)
from backend.app.events import EventRepository
from backend.app.page_views import PageViewRepository
from backend.app.settings import Settings


# ── Response Models ──


class AnalyticsSummary(BaseModel):
    total_views_today: int
    total_views_7d: int
    total_views_30d: int
    total_views_all: int
    unique_visitors_30d: int
    total_events_30d: int = 0
    shares_30d: int = 0
    clicks_30d: int = 0
    comments_30d: int = 0


# ── Router Factory ──


class AnalyticsService:
    """Wraps PageViewRepository with analytics aggregation logic."""

    def __init__(self, repo: PageViewRepository, event_repo: EventRepository | None = None) -> None:
        self._repo = repo
        self._event_repo = event_repo

    def get_summary(self) -> AnalyticsSummary:
        now = datetime.now(UTC)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_ago = today_start - timedelta(days=7)
        month_ago = today_start - timedelta(days=30)

        result = AnalyticsSummary(
            total_views_today=self._repo.count_total(since=today_start),
            total_views_7d=self._repo.count_total(since=week_ago),
            total_views_30d=self._repo.count_total(since=month_ago),
            total_views_all=self._repo.count_total(),
            unique_visitors_30d=self._repo.distinct_sessions(since=month_ago),
        )

        if self._event_repo is not None:
            result.total_events_30d = self._event_repo.count_total(since=month_ago)
            result.shares_30d = self._event_repo.count_by_type("share", since=month_ago)
            result.clicks_30d = self._event_repo.count_by_type("click", since=month_ago)
            result.comments_30d = self._event_repo.count_by_type("comment", since=month_ago)

        return result

    def get_top_content(self, days: int = 30, limit: int = 10) -> list[dict]:
        since = datetime.now(UTC) - timedelta(days=days)
        return self._repo.top_paths(since=since, limit=limit)

    def get_trends(self, days: int = 30) -> list[dict]:
        since = datetime.now(UTC) - timedelta(days=days)
        return self._repo.daily_counts(since=since, days=days)

    def get_referrers(self, days: int = 30, limit: int = 10) -> list[dict]:
        since = datetime.now(UTC) - timedelta(days=days)
        return self._repo.top_referrers(since=since, limit=limit)


def create_analytics_routes(
    service: AnalyticsService,
    settings: Settings,
    event_repo: EventRepository | None = None,
) -> APIRouter:
    def require_admin(
        identity_payload: str | None = Header(default=None, alias=ADMIN_IDENTITY_HEADER),
        signature: str | None = Header(default=None, alias=ADMIN_SIGNATURE_HEADER),
    ) -> AdminIdentity:
        return require_admin_identity_with_settings(settings, identity_payload, signature)

    router = APIRouter(prefix="/admin/analytics", tags=["analytics"])

    @router.get("/summary")
    async def get_summary(
        _identity: AdminIdentity = Depends(require_admin),
    ) -> AnalyticsSummary:
        return service.get_summary()

    @router.get("/top-content")
    async def get_top_content(
        days: int = Query(30, ge=1, le=365),
        limit: int = Query(10, ge=1, le=100),
        _identity: AdminIdentity = Depends(require_admin),
    ) -> list[dict]:
        return service.get_top_content(days=days, limit=limit)

    @router.get("/trends")
    async def get_trends(
        days: int = Query(30, ge=1, le=365),
        _identity: AdminIdentity = Depends(require_admin),
    ) -> list[dict]:
        return service.get_trends(days=days)

    @router.get("/referrers")
    async def get_referrers(
        days: int = Query(30, ge=1, le=365),
        limit: int = Query(10, ge=1, le=50),
        _identity: AdminIdentity = Depends(require_admin),
    ) -> list[dict]:
        return service.get_referrers(days=days, limit=limit)

    return router
