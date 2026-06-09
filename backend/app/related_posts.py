"""Related article recommendations for the public blog.

Finds published posts that share tags with the current post.
Uses tag overlap count as primary sort, view count as tiebreaker.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.app.blog import BlogRepositoryProtocol
    from backend.app.blog_tags import BlogTagRepository
    from backend.app.page_views import PageViewRepository


class RelatedPostResult:
    """A recommended related article."""

    def __init__(
        self,
        slug: str,
        title: str,
        excerpt: str,
        published_at: datetime,
        image_url: str | None = None,
        reading_time_minutes: int = 0,
        shared_tags: int = 0,
        view_count: int = 0,
    ) -> None:
        self.slug = slug
        self.title = title
        self.excerpt = excerpt[:120] + "…" if len(excerpt) > 120 else excerpt
        self.published_at = published_at
        self.image_url = image_url
        self.reading_time_minutes = reading_time_minutes
        self.shared_tags = shared_tags
        self.view_count = view_count


def get_related_posts(
    post_slug: str,
    blog_repo: BlogRepositoryProtocol,
    tag_repo: BlogTagRepository,
    page_view_repo: PageViewRepository | None = None,
    limit: int = 5,
) -> list[RelatedPostResult]:
    """Find related posts by tag overlap, sorted by relevance.

    Args:
        post_slug: Slug of the current post.
        blog_repo: Blog repository for fetching posts.
        tag_repo: Tag repository for tag overlap queries.
        page_view_repo: Optional page view repository for view count tiebreaker.
        limit: Maximum number of related posts to return.

    Returns:
        List of RelatedPostResult, sorted by shared_tags desc, view_count desc.
    """
    # Get current post detail (has id)
    current = blog_repo.get_published_by_slug(post_slug)
    if current is None:
        return []

    # Get tags for current post
    current_tag_ids = _get_tag_ids(tag_repo, current.id)
    if not current_tag_ids:
        return []

    # Get all posts with IDs (use list_all which has id + status)
    all_posts = blog_repo.list_all()
    published_posts = [p for p in all_posts if p.status == "published"]

    candidates: list[tuple[int, int, str, str, str, datetime, str | None]] = []

    for post in published_posts:
        if post.slug == post_slug:
            continue

        # Get tags for candidate post
        candidate_tags = _get_tag_ids(tag_repo, post.id)
        shared = len(current_tag_ids & candidate_tags)
        if shared == 0:
            continue

        # Get view count (tiebreaker)
        view_count = 0
        if page_view_repo is not None:
            since = datetime.now(UTC) - timedelta(days=30)
            view_count = page_view_repo.count_by_path(f"/blog/{post.slug}", since=since)

        candidates.append((
            shared,
            view_count,
            post.slug,
            post.title,
            post.excerpt or "",
            post.published_at or datetime.now(UTC),
            post.image_url,
        ))

    # Sort by shared_tags desc, view_count desc
    candidates.sort(key=lambda x: (-x[0], -x[1]))

    results = []
    for shared, views, slug, title, excerpt, published_at, image_url in candidates[:limit]:
        results.append(
            RelatedPostResult(
                slug=slug,
                title=title,
                excerpt=excerpt,
                published_at=published_at,
                image_url=image_url,
                reading_time_minutes=0,  # Content not available to compute
                shared_tags=shared,
                view_count=views,
            )
        )

    return results


def _get_tag_ids(tag_repo: BlogTagRepository, post_id: str) -> set[str]:
    """Get set of tag IDs for a post."""
    try:
        tags = tag_repo.get_tags_for_post(post_id)
        return {t.id for t in tags}
    except Exception:
        return set()
