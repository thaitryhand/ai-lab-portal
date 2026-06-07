"""Blog content performance analytics — page views, engagement, trending.

Tracks page views for published blog posts via a simple database counter.
No external analytics service required for MVP.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from pydantic import BaseModel
from sqlalchemy import Engine, delete, func, insert, select
from sqlalchemy.engine import Engine as SAEngine

from backend.app.database import blog_page_views

# ─── Models ────────────────────────────────────────────────────────────────


class PageViewRecord(BaseModel):
    id: str
    post_id: str
    viewed_at: datetime
    visitor_id: str | None = None
    referrer: str | None = None
    user_agent: str | None = None
    path: str | None = None


class PostAnalytics(BaseModel):
    post_id: str
    title: str
    total_views: int
    unique_visitors: int
    last_viewed_at: datetime | None = None
    views_today: int = 0
    views_this_week: int = 0


class AnalyticsSummary(BaseModel):
    total_views: int
    total_unique_visitors: int
    views_today: int
    views_this_week: int
    views_this_month: int
    top_posts: list[PostAnalytics] = []


# ─── Repository ────────────────────────────────────────────────────────────


class BlogAnalyticsRepository:
    """In-memory blog analytics repository for tests."""

    def __init__(self) -> None:
        self._views: list[PageViewRecord] = []

    def record_view(
        self,
        post_id: str,
        *,
        visitor_id: str | None = None,
        referrer: str | None = None,
        user_agent: str | None = None,
        path: str | None = None,
    ) -> PageViewRecord:
        record = PageViewRecord(
            id=f"pv_{uuid4().hex}",
            post_id=post_id,
            viewed_at=datetime.now(UTC),
            visitor_id=visitor_id,
            referrer=referrer,
            user_agent=user_agent,
            path=path,
        )
        self._views.append(record)
        return record

    def get_post_analytics(self, post_id: str) -> PostAnalytics:
        now = datetime.now(UTC)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=today_start.weekday())
        post_views = [v for v in self._views if v.post_id == post_id]
        return PostAnalytics(
            post_id=post_id,
            title="",
            total_views=len(post_views),
            unique_visitors=len({v.visitor_id for v in post_views if v.visitor_id}),
            last_viewed_at=max((v.viewed_at for v in post_views), default=None),
            views_today=sum(1 for v in post_views if v.viewed_at >= today_start),
            views_this_week=sum(1 for v in post_views if v.viewed_at >= week_start),
        )

    def get_summary(self, top_n: int = 10) -> AnalyticsSummary:
        now = datetime.now(UTC)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=today_start.weekday())
        month_start = today_start.replace(day=1)

        return AnalyticsSummary(
            total_views=len(self._views),
            total_unique_visitors=len({v.visitor_id for v in self._views if v.visitor_id}),
            views_today=sum(1 for v in self._views if v.viewed_at >= today_start),
            views_this_week=sum(1 for v in self._views if v.viewed_at >= week_start),
            views_this_month=sum(1 for v in self._views if v.viewed_at >= month_start),
        )


class PostgresBlogAnalyticsRepository(BlogAnalyticsRepository):
    """Postgres-backed blog analytics repository."""

    def __init__(self, engine: SAEngine) -> None:
        self._engine = engine

    def record_view(
        self,
        post_id: str,
        *,
        visitor_id: str | None = None,
        referrer: str | None = None,
        user_agent: str | None = None,
        path: str | None = None,
    ) -> PageViewRecord:
        now = datetime.now(UTC)
        record = PageViewRecord(
            id=f"pv_{uuid4().hex}",
            post_id=post_id,
            viewed_at=now,
            visitor_id=visitor_id,
            referrer=referrer,
            user_agent=user_agent,
            path=path,
        )
        with self._engine.begin() as conn:
            conn.execute(insert(blog_page_views).values(**record.model_dump()))
        return record

    def get_post_analytics(self, post_id: str) -> PostAnalytics:
        with self._engine.begin() as conn:
            now = datetime.now(UTC)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            week_start = today_start - timedelta(days=today_start.weekday())

            total = conn.execute(
                select(func.count()).where(blog_page_views.c.post_id == post_id)
            ).scalar() or 0
            unique = conn.execute(
                select(func.count(func.distinct(blog_page_views.c.visitor_id)))
                .where(
                    blog_page_views.c.post_id == post_id,
                    blog_page_views.c.visitor_id.is_not(None),
                )
            ).scalar() or 0
            last = conn.execute(
                select(blog_page_views.c.viewed_at)
                .where(blog_page_views.c.post_id == post_id)
                .order_by(blog_page_views.c.viewed_at.desc())
                .limit(1)
            ).scalar()
            today = conn.execute(
                select(func.count()).where(
                    blog_page_views.c.post_id == post_id,
                    blog_page_views.c.viewed_at >= today_start,
                )
            ).scalar() or 0
            week = conn.execute(
                select(func.count()).where(
                    blog_page_views.c.post_id == post_id,
                    blog_page_views.c.viewed_at >= week_start,
                )
            ).scalar() or 0

        return PostAnalytics(
            post_id=post_id,
            title="",
            total_views=total,
            unique_visitors=unique,
            last_viewed_at=last,
            views_today=today,
            views_this_week=week,
        )

    def get_summary(self, top_n: int = 10) -> AnalyticsSummary:
        with self._engine.begin() as conn:
            now = datetime.now(UTC)
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            week_start = today_start - timedelta(days=today_start.weekday())
            month_start = today_start.replace(day=1)

            total = conn.execute(select(func.count())).scalar() or 0
            unique = conn.execute(
                select(func.count(func.distinct(blog_page_views.c.visitor_id)))
                .where(blog_page_views.c.visitor_id.is_not(None))
            ).scalar() or 0
            today = conn.execute(
                select(func.count()).where(blog_page_views.c.viewed_at >= today_start)
            ).scalar() or 0
            week = conn.execute(
                select(func.count()).where(blog_page_views.c.viewed_at >= week_start)
            ).scalar() or 0
            month = conn.execute(
                select(func.count()).where(blog_page_views.c.viewed_at >= month_start)
            ).scalar() or 0

        return AnalyticsSummary(
            total_views=total,
            total_unique_visitors=unique,
            views_today=today,
            views_this_week=week,
            views_this_month=month,
        )


# ─── Routes factory ────────────────────────────────────────────────────────


def create_blog_analytics_routes(
    analytics_repo: BlogAnalyticsRepository,
    engine: Engine | None = None,
):
    """Create FastAPI router for blog analytics endpoints."""
    from fastapi import APIRouter, Depends, HTTPException

    from backend.app.admin_boundary import (
        ADMIN_IDENTITY_HEADER,
        AdminIdentity,
        require_admin_identity_with_settings,
    )
    from backend.app.settings import Settings

    router = APIRouter(prefix="/admin/blog-analytics", tags=["blog-analytics"])

    def _identity() -> AdminIdentity:
        return require_admin_identity_with_settings(
            Settings(), None, None
        )

    @router.get("/summary")
    async def analytics_summary(
        _identity: AdminIdentity = Depends(require_admin_identity_with_settings),
    ) -> AnalyticsSummary:
        return analytics_repo.get_summary()

    @router.get("/posts/{post_id}")
    async def post_analytics(
        post_id: str,
        _identity: AdminIdentity = Depends(require_admin_identity_with_settings),
    ) -> PostAnalytics:
        return analytics_repo.get_post_analytics(post_id)

    return router
