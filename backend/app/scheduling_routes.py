"""FastAPI routes for auto-scheduling."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException

from backend.app.admin_boundary import (
    ADMIN_IDENTITY_HEADER,
    ADMIN_SIGNATURE_HEADER,
    AdminIdentity,
    require_admin_identity_with_settings,
)
from backend.app.blog import BlogRepositoryProtocol
from backend.app.scheduling_agent import SchedulingService, SchedulingSuggestion
from backend.app.settings import Settings


def create_scheduling_routes(
    service: SchedulingService,
    blog_repo: BlogRepositoryProtocol,
    settings: Settings,
) -> APIRouter:
    def require_admin(
        identity_payload: str | None = Header(default=None, alias=ADMIN_IDENTITY_HEADER),
        signature: str | None = Header(default=None, alias=ADMIN_SIGNATURE_HEADER),
    ) -> AdminIdentity:
        return require_admin_identity_with_settings(settings, identity_payload, signature)

    router = APIRouter(prefix="/admin/blog-posts", tags=["scheduling"])

    @router.post("/{post_id}/suggest-schedule")
    async def suggest_schedule(
        post_id: str,
        _identity: AdminIdentity = Depends(require_admin),
    ) -> SchedulingSuggestion:
        """Get a scheduling suggestion for a blog post."""
        post = blog_repo.get_by_id(post_id)
        if post is None:
            raise HTTPException(status_code=404, detail="Blog post not found")

        return service.suggest(
            blog_post_id=post_id,
            title=post.title,
            status=post.status,
        )

    return router
