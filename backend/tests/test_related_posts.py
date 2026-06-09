"""Tests for related article recommendations (US-105)."""

import pytest

from backend.app.blog import BlogPost, BlogRepository
from backend.app.blog_tags import InMemoryBlogTagRepository, BlogTagCreate
from backend.app.page_views import InMemoryPageViewRepository, PageView
from backend.app.related_posts import get_related_posts
from datetime import UTC, datetime


@pytest.fixture
def blog_repo():
    """Create blog repo with seed posts for testing."""
    now = datetime.now(UTC)
    posts = [
        BlogPost(
            id="post-1", slug="post-one", title="Post One", excerpt="First post",
            author_name="Alice", status="published", published_at=now,
            content_markdown="# Post One\nContent here.",
        ),
        BlogPost(
            id="post-2", slug="post-two", title="Post Two", excerpt="Second post",
            author_name="Alice", status="published", published_at=now,
            content_markdown="# Post Two\nContent here.",
        ),
        BlogPost(
            id="post-3", slug="post-three", title="Post Three", excerpt="Third post",
            author_name="Bob", status="published", published_at=now,
            content_markdown="# Post Three\nContent here.",
        ),
        BlogPost(
            id="post-4", slug="post-four", title="Post Four", excerpt="Fourth post",
            author_name="Charlie", status="published", published_at=now,
            content_markdown="# Post Four\nContent here.",
        ),
        BlogPost(
            id="post-5", slug="post-five", title="Post Five", excerpt="Fifth post",
            author_name="Alice", status="draft", published_at=None,
            content_markdown="# Post Five\nContent here.",
        ),
    ]
    return BlogRepository(posts)


@pytest.fixture
def tag_repo():
    repo = InMemoryBlogTagRepository()
    # Ensure specific tags exist
    for name in ["AI", "Python", "Tutorial", "News", "Research"]:
        try:
            repo.create_tag(BlogTagCreate(name=name))
        except ValueError:
            pass
    return repo


def _tag_id_by_name(repo: InMemoryBlogTagRepository, name: str) -> str:
    for t in repo._tags.values():
        if t.name == name:
            return t.id
    raise ValueError(f"Tag {name} not found")


class TestGetRelatedPosts:
    """get_related_posts basic functionality."""

    def test_no_related_when_no_tags(self, blog_repo, tag_repo):
        """Post with no tags should return empty."""
        related = get_related_posts("post-one", blog_repo, tag_repo)
        assert related == []

    def test_related_by_shared_tags(self, blog_repo, tag_repo):
        """Posts sharing tags should appear as related."""
        ai_id = _tag_id_by_name(tag_repo, "AI")
        py_id = _tag_id_by_name(tag_repo, "Python")

        # Post 1 gets AI + Python tags
        tag_repo.set_post_tags("post-1", [ai_id, py_id])
        # Post 2 gets AI tag (1 shared)
        tag_repo.set_post_tags("post-2", [ai_id])
        # Post 3 gets Python tag (1 shared)
        tag_repo.set_post_tags("post-3", [py_id])
        # Post 4 gets no tags (0 shared — should be excluded)
        tag_repo.set_post_tags("post-4", [])

        related = get_related_posts("post-one", blog_repo, tag_repo)
        assert len(related) == 2
        slugs = {r.slug for r in related}
        assert "post-two" in slugs
        assert "post-three" in slugs
        assert "post-four" not in slugs

    def test_limits_results(self, blog_repo, tag_repo):
        """Should respect limit parameter."""
        ai_id = _tag_id_by_name(tag_repo, "AI")
        tag_repo.set_post_tags("post-1", [ai_id])
        tag_repo.set_post_tags("post-2", [ai_id])
        tag_repo.set_post_tags("post-3", [ai_id])
        tag_repo.set_post_tags("post-4", [ai_id])

        related = get_related_posts("post-one", blog_repo, tag_repo, limit=2)
        assert len(related) == 2

    def test_excludes_current_post(self, blog_repo, tag_repo):
        """Should not include the current post."""
        ai_id = _tag_id_by_name(tag_repo, "AI")
        tag_repo.set_post_tags("post-1", [ai_id])
        tag_repo.set_post_tags("post-2", [ai_id])

        related = get_related_posts("post-one", blog_repo, tag_repo)
        slugs = {r.slug for r in related}
        assert "post-one" not in slugs

    def test_excludes_draft_posts(self, blog_repo, tag_repo):
        """Should only return published posts (no drafts)."""
        ai_id = _tag_id_by_name(tag_repo, "AI")
        tag_repo.set_post_tags("post-1", [ai_id])
        tag_repo.set_post_tags("post-5", [ai_id])  # post-5 is draft

        related = get_related_posts("post-one", blog_repo, tag_repo)
        slugs = {r.slug for r in related}
        assert "post-five" not in slugs

    def test_returns_summary_fields(self, blog_repo, tag_repo):
        """Returned posts should have slug, title, excerpt, published_at."""
        ai_id = _tag_id_by_name(tag_repo, "AI")
        tag_repo.set_post_tags("post-1", [ai_id])
        tag_repo.set_post_tags("post-2", [ai_id])

        related = get_related_posts("post-one", blog_repo, tag_repo)
        assert len(related) == 1
        post = related[0]
        assert post.slug == "post-two"
        assert "Post Two" in post.title
        assert post.published_at is not None
        assert post.shared_tags == 1

    def test_sorts_by_tag_count(self, blog_repo, tag_repo):
        """Posts with more shared tags should rank higher."""
        ai_id = _tag_id_by_name(tag_repo, "AI")
        py_id = _tag_id_by_name(tag_repo, "Python")
        tut_id = _tag_id_by_name(tag_repo, "Tutorial")

        # Post 1 has AI + Python + Tutorial
        tag_repo.set_post_tags("post-1", [ai_id, py_id, tut_id])
        # Post 2 has AI only (1 shared)
        tag_repo.set_post_tags("post-2", [ai_id])
        # Post 3 has AI + Python (2 shared)
        tag_repo.set_post_tags("post-3", [ai_id, py_id])
        # Post 4 has AI + Python + Tutorial (3 shared)
        tag_repo.set_post_tags("post-4", [ai_id, py_id, tut_id])

        related = get_related_posts("post-one", blog_repo, tag_repo)
        assert len(related) == 3
        # Should be sorted by shared_tags desc: post-4 (3), post-3 (2), post-2 (1)
        assert related[0].slug == "post-four"
        assert related[2].slug == "post-two"
        assert related[0].shared_tags == 3
        assert related[1].shared_tags == 2
        assert related[2].shared_tags == 1

    def test_nonexistent_slug(self, blog_repo, tag_repo):
        """Nonexistent slug should return empty list."""
        related = get_related_posts("nonexistent-slug", blog_repo, tag_repo)
        assert related == []
