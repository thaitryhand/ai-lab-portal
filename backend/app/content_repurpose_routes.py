"""FastAPI routes for content repurposing."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException

from backend.app.admin_boundary import (
    ADMIN_IDENTITY_HEADER,
    ADMIN_SIGNATURE_HEADER,
    AdminIdentity,
    require_admin_identity_with_settings,
)
from backend.app.blog import BlogRepositoryProtocol
from backend.app.content_repurpose import (
    ContentRepurposeService,
    FakeContentRepurposeService,
    RepurposedContent,
)
from backend.app.settings import Settings


def create_content_repurpose_routes(
    service: ContentRepurposeService,
    blog_repo: BlogRepositoryProtocol,
    settings: Settings,
) -> APIRouter:
    def require_admin(
        identity_payload: str | None = Header(default=None, alias=ADMIN_IDENTITY_HEADER),
        signature: str | None = Header(default=None, alias=ADMIN_SIGNATURE_HEADER),
    ) -> AdminIdentity:
        return require_admin_identity_with_settings(settings, identity_payload, signature)

    router = APIRouter(prefix="/admin/blog-posts", tags=["content-repurpose"])

    @router.post("/{post_id}/repurpose")
    async def repurpose_content(
        post_id: str,
        _identity: AdminIdentity = Depends(require_admin),
    ) -> RepurposedContent:
        """Repurpose a blog post into social media content."""
        post = blog_repo.get_by_id(post_id)
        if post is None:
            raise HTTPException(status_code=404, detail="Blog post not found")
        if post.status != "published":
            raise HTTPException(status_code=400, detail="Only published posts can be repurposed")

        return service.repurpose(
            blog_post_id=post_id,
            title=post.title,
            excerpt=post.excerpt,
            content_markdown=post.content_markdown,
        )

    return router
