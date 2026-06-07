"""Content Calendar API — blog post scheduling and publish timeline.

Exposes:
- ``GET /admin/content-calendar/posts`` — posts grouped by date for calendar view

Mounted by ``create_app()`` under the default FastAPI app.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Header

from backend.app.admin_boundary import (
    ADMIN_IDENTITY_HEADER,
    ADMIN_SIGNATURE_HEADER,
    AdminIdentity,
    require_admin_identity_with_settings,
)
from backend.app.blog import BlogRepository
from backend.app.blog_ideas import BlogIdeaRepository
from backend.app.settings import Settings


# ── Router factory ─────────────────────────────────────────────────


def create_content_calendar_routes(
    settings: Settings,
    blog_repository: BlogRepository | None = None,
    blog_idea_repository: BlogIdeaRepository | None = None,
) -> APIRouter:
    """Create a router with content calendar endpoints."""

    def require_identity(
        identity_payload: str | None = Header(None, alias=ADMIN_IDENTITY_HEADER),
        signature: str | None = Header(None, alias=ADMIN_SIGNATURE_HEADER),
    ) -> AdminIdentity:
        return require_admin_identity_with_settings(
            settings, identity_payload, signature
        )

    router = APIRouter(prefix="/admin/content-calendar")

    @router.get("/posts")
    async def list_calendar_posts(
        _identity: AdminIdentity = Depends(require_identity),
    ) -> dict[str, Any]:
        """Return blog posts and pipeline ideas grouped by date.

        Returns:
            dict with:
            - published: list of published posts
            - pipeline: list of blog ideas in active pipeline stages
            - months: list of month keys with post counts
        """
        blog_repo = blog_repository or BlogRepository()
        ideas_repo = blog_idea_repository or BlogIdeaRepository()

        # Published posts
        all_posts = blog_repo.list_all()
        published = [
            {
                "id": p.id,
                "title": p.title,
                "slug": p.slug,
                "type": "post",
                "status": p.status,
                "date": (
                    p.published_at.isoformat() if p.published_at else None
                ),
            }
            for p in all_posts
            if p.status == "published" and p.published_at
        ]
        published.sort(key=lambda p: p["date"] or "", reverse=True)

        # Pipeline ideas (in-progress stages) — fetch full objects
        all_summaries = ideas_repo.list_all()
        pipeline = []
        for summary in all_summaries:
            if summary.status == "rejected":
                continue
            idea = ideas_repo.get_by_id(summary.id)
            if idea is None:
                continue
            pipeline.append(
                {
                    "id": idea.id,
                    "title": idea.title,
                    "type": "idea",
                    "stage": _idea_stage(idea),
                    "scheduled_at": idea.scheduled_at.isoformat() if idea.scheduled_at else None,
                    "status": idea.status,
                    "outline_status": idea.outline_status,
                    "draft_status": idea.draft_status,
                    "review_status": idea.technical_review_status,
                    "marketing_status": idea.marketing_status,
                    "created_at": idea.created_at.isoformat(),
                }
            )
        pipeline.sort(
            key=lambda i: i["created_at"], reverse=True
        )

        # Monthly aggregation for the calendar heatmap
        month_counts: dict[str, int] = {}
        for p in published:
            if p["date"]:
                month_key = p["date"][:7]  # YYYY-MM
                month_counts[month_key] = month_counts.get(month_key, 0) + 1

        scheduled = [
            p for p in pipeline if p.get("scheduled_at")
        ]

        return {
            "published": published,
            "pipeline": pipeline,
            "scheduled": scheduled,
            "month_counts": month_counts,
        }

    return router


def _idea_stage(idea: Any) -> str:
    """Determine the current pipeline stage of a blog idea."""
    if idea.published_blog_post_id:
        return "published"
    if idea.scheduled_at:
        return "scheduled"
    if idea.marketing_status == "approved":
        return "marketing_done"
    if idea.technical_review_status == "approved":
        return "reviewed"
    if idea.draft_status == "approved":
        return "draft_done"
    if idea.outline_status == "approved":
        return "outline_done"
    if idea.status == "approved":
        return "approved"
    return "idea"
