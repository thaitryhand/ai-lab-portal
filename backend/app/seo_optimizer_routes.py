"""FastAPI routes for SEO auto-optimization."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException

from backend.app.admin_boundary import (
    ADMIN_IDENTITY_HEADER,
    ADMIN_SIGNATURE_HEADER,
    AdminIdentity,
    require_admin_identity_with_settings,
)
from backend.app.blog_ideas import BlogIdeaRepository
from backend.app.seo_optimizer import SeoOptimizerService, SeoOptimizationResult
from backend.app.settings import Settings


def create_seo_optimizer_routes(
    service: SeoOptimizerService,
    ideas_repo: BlogIdeaRepository,
    settings: Settings,
) -> APIRouter:
    def require_admin(
        identity_payload: str | None = Header(default=None, alias=ADMIN_IDENTITY_HEADER),
        signature: str | None = Header(default=None, alias=ADMIN_SIGNATURE_HEADER),
    ) -> AdminIdentity:
        return require_admin_identity_with_settings(settings, identity_payload, signature)

    router = APIRouter(prefix="/admin/blog-ideas", tags=["seo-optimizer"])

    @router.post("/{idea_id}/optimize-seo")
    async def optimize_seo(
        idea_id: str,
        _identity: AdminIdentity = Depends(require_admin),
    ) -> SeoOptimizationResult:
        """Get SEO optimization suggestions for a blog idea."""
        idea = ideas_repo.get_by_id(idea_id)
        if idea is None:
            raise HTTPException(status_code=404, detail="Blog idea not found")

        return service.optimize(
            blog_idea_id=idea_id,
            title=idea.title,
            content_markdown=idea.draft_markdown or "",
            seo_audit=idea.seo_audit,
        )

    return router
