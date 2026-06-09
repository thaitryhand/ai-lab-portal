"""FastAPI router for related article recommendations."""
from __future__ import annotations

from fastapi import APIRouter

from backend.app.blog import BlogRepositoryProtocol
from backend.app.blog_tags import BlogTagRepository
from backend.app.page_views import PageViewRepository
from backend.app.related_posts import get_related_posts


def create_related_posts_routes(
    blog_repo: BlogRepositoryProtocol,
    tag_repo: BlogTagRepository,
    page_view_repo: PageViewRepository | None = None,
) -> APIRouter:
    router = APIRouter(prefix="/api/blog", tags=["related-posts"])

    @router.get("/{slug}/related")
    async def related_posts(slug: str) -> list[dict]:
        """Get related posts for a published blog post by slug."""
        posts = get_related_posts(
            post_slug=slug,
            blog_repo=blog_repo,
            tag_repo=tag_repo,
            page_view_repo=page_view_repo,
            limit=5,
        )
        return [
            {
                "slug": p.slug,
                "title": p.title,
                "excerpt": p.excerpt,
                "published_at": p.published_at.isoformat() if p.published_at else None,
                "image_url": p.image_url,
                "reading_time_minutes": p.reading_time_minutes,
                "shared_tags": p.shared_tags,
                "view_count": p.view_count,
            }
            for p in posts
        ]

    return router
