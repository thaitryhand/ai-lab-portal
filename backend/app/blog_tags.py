"""Blog tag taxonomy and post-tag assignments."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import Engine, delete, func, insert, select

from backend.app.admin_boundary import (
    ADMIN_IDENTITY_HEADER,
    ADMIN_SIGNATURE_HEADER,
    AdminIdentity,
    require_admin_identity_with_settings,
)
from backend.app.blog import BlogRepositoryProtocol
from backend.app.database import blog_post_tags, blog_posts, blog_tags
from backend.app.settings import Settings

_SLUG_PATTERN = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"


def slugify_tag(value: str) -> str:
    slug = re.sub(r"[^a-z0-9\s-]", "", value.lower().strip())
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")[:80]
    return slug or "tag"


class BlogTag(BaseModel):
    id: str
    slug: str = Field(pattern=_SLUG_PATTERN)
    name: str
    created_at: datetime


class BlogTagCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    slug: str | None = Field(default=None, pattern=_SLUG_PATTERN, max_length=80)


class BlogTagSummary(BaseModel):
    id: str
    slug: str
    name: str
    post_count: int = 0


class BlogPostTagsUpdate(BaseModel):
    tag_ids: list[str] = Field(default_factory=list)


class BlogTagRepository(ABC):
    @abstractmethod
    def list_public_tags(self, *, published_post_ids: set[str] | None = None) -> list[BlogTagSummary]: ...

    @abstractmethod
    def list_admin_tags(self) -> list[BlogTagSummary]: ...

    @abstractmethod
    def create_tag(self, request: BlogTagCreate) -> BlogTag: ...

    @abstractmethod
    def get_tag_by_slug(self, slug: str) -> BlogTag | None: ...

    @abstractmethod
    def get_tags_for_post(self, post_id: str) -> list[BlogTagSummary]: ...

    @abstractmethod
    def set_post_tags(self, post_id: str, tag_ids: list[str]) -> list[BlogTagSummary] | None: ...

    @abstractmethod
    def get_post_ids_for_tag_slug(self, slug: str) -> set[str]: ...


class InMemoryBlogTagRepository(BlogTagRepository):
    def __init__(self) -> None:
        self._tags: dict[str, BlogTag] = {}
        self._post_tags: dict[str, set[str]] = {}
        self._published_post_ids: set[str] = set()

    def list_public_tags(self, *, published_post_ids: set[str] | None = None) -> list[BlogTagSummary]:
        return self._summaries(published_post_ids=published_post_ids)

    def list_admin_tags(self) -> list[BlogTagSummary]:
        return self._summaries(published_only=False)

    def create_tag(self, request: BlogTagCreate) -> BlogTag:
        slug = request.slug or slugify_tag(request.name)
        if any(tag.slug == slug for tag in self._tags.values()):
            raise ValueError("Tag slug already exists")
        tag = BlogTag(id=f"tag_{uuid4().hex}", slug=slug, name=request.name.strip(), created_at=datetime.now(UTC))
        self._tags[tag.id] = tag
        return tag

    def get_tag_by_slug(self, slug: str) -> BlogTag | None:
        return next((tag for tag in self._tags.values() if tag.slug == slug), None)

    def get_tags_for_post(self, post_id: str) -> list[BlogTagSummary]:
        tag_ids = self._post_tags.get(post_id, set())
        tags = [self._tags[tag_id] for tag_id in tag_ids if tag_id in self._tags]
        return [BlogTagSummary(id=t.id, slug=t.slug, name=t.name, post_count=0) for t in sorted(tags, key=lambda t: t.name.lower())]

    def set_post_tags(self, post_id: str, tag_ids: list[str]) -> list[BlogTagSummary] | None:
        if any(tag_id not in self._tags for tag_id in tag_ids):
            return None
        self._post_tags[post_id] = set(tag_ids)
        return self.get_tags_for_post(post_id)

    def get_post_ids_for_tag_slug(self, slug: str) -> set[str]:
        tag = self.get_tag_by_slug(slug)
        if tag is None:
            return set()
        return {post_id for post_id, tag_ids in self._post_tags.items() if tag.id in tag_ids}

    def _summaries(self, *, published_post_ids: set[str] | None = None) -> list[BlogTagSummary]:
        rows: list[BlogTagSummary] = []
        for tag in self._tags.values():
            count = sum(
                1
                for post_id, tag_ids in self._post_tags.items()
                if tag.id in tag_ids and (published_post_ids is None or post_id in published_post_ids)
            )
            if published_post_ids is None or count > 0:
                rows.append(BlogTagSummary(id=tag.id, slug=tag.slug, name=tag.name, post_count=count))
        return sorted(rows, key=lambda row: row.name.lower())


class PostgresBlogTagRepository(BlogTagRepository):
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def list_public_tags(self, *, published_post_ids: set[str] | None = None) -> list[BlogTagSummary]:
        void_published_post_ids = published_post_ids
        del void_published_post_ids
        with self.engine.begin() as conn:
            rows = conn.execute(
                select(
                    blog_tags.c.id,
                    blog_tags.c.slug,
                    blog_tags.c.name,
                    func.count(blog_posts.c.id).label("post_count"),
                )
                .select_from(
                    blog_tags.join(blog_post_tags, blog_tags.c.id == blog_post_tags.c.tag_id).join(
                        blog_posts, blog_posts.c.id == blog_post_tags.c.post_id
                    )
                )
                .where(blog_posts.c.status == "published", blog_posts.c.published_at.is_not(None))
                .group_by(blog_tags.c.id, blog_tags.c.slug, blog_tags.c.name)
                .order_by(blog_tags.c.name.asc())
            ).mappings()
            return [BlogTagSummary(**dict(row)) for row in rows]

    def list_admin_tags(self) -> list[BlogTagSummary]:
        with self.engine.begin() as conn:
            rows = conn.execute(
                select(
                    blog_tags.c.id,
                    blog_tags.c.slug,
                    blog_tags.c.name,
                    func.count(blog_post_tags.c.post_id).label("post_count"),
                )
                .select_from(blog_tags.outerjoin(blog_post_tags, blog_tags.c.id == blog_post_tags.c.tag_id))
                .group_by(blog_tags.c.id, blog_tags.c.slug, blog_tags.c.name)
                .order_by(blog_tags.c.name.asc())
            ).mappings()
            return [BlogTagSummary(**dict(row)) for row in rows]

    def create_tag(self, request: BlogTagCreate) -> BlogTag:
        slug = request.slug or slugify_tag(request.name)
        tag = BlogTag(id=f"tag_{uuid4().hex}", slug=slug, name=request.name.strip(), created_at=datetime.now(UTC))
        with self.engine.begin() as conn:
            if conn.execute(select(blog_tags.c.id).where(blog_tags.c.slug == slug)).first():
                raise ValueError("Tag slug already exists")
            conn.execute(insert(blog_tags).values(**tag.model_dump()))
        return tag

    def get_tag_by_slug(self, slug: str) -> BlogTag | None:
        with self.engine.begin() as conn:
            row = conn.execute(select(blog_tags).where(blog_tags.c.slug == slug)).mappings().first()
        return BlogTag(**dict(row)) if row else None

    def get_tags_for_post(self, post_id: str) -> list[BlogTagSummary]:
        with self.engine.begin() as conn:
            rows = conn.execute(
                select(blog_tags.c.id, blog_tags.c.slug, blog_tags.c.name)
                .select_from(blog_tags.join(blog_post_tags, blog_tags.c.id == blog_post_tags.c.tag_id))
                .where(blog_post_tags.c.post_id == post_id)
                .order_by(blog_tags.c.name.asc())
            ).mappings()
            return [BlogTagSummary(id=row["id"], slug=row["slug"], name=row["name"], post_count=0) for row in rows]

    def set_post_tags(self, post_id: str, tag_ids: list[str]) -> list[BlogTagSummary] | None:
        unique_tag_ids = list(dict.fromkeys(tag_ids))
        with self.engine.begin() as conn:
            existing_post = conn.execute(select(blog_posts.c.id).where(blog_posts.c.id == post_id)).first()
            if existing_post is None:
                return None
            if unique_tag_ids:
                existing_tags = {
                    row.id
                    for row in conn.execute(select(blog_tags.c.id).where(blog_tags.c.id.in_(unique_tag_ids))).fetchall()
                }
                if existing_tags != set(unique_tag_ids):
                    return None
            conn.execute(delete(blog_post_tags).where(blog_post_tags.c.post_id == post_id))
            if unique_tag_ids:
                conn.execute(insert(blog_post_tags), [{"post_id": post_id, "tag_id": tag_id} for tag_id in unique_tag_ids])
        return self.get_tags_for_post(post_id)

    def get_post_ids_for_tag_slug(self, slug: str) -> set[str]:
        with self.engine.begin() as conn:
            rows = conn.execute(
                select(blog_post_tags.c.post_id)
                .select_from(blog_post_tags.join(blog_tags, blog_tags.c.id == blog_post_tags.c.tag_id))
                .where(blog_tags.c.slug == slug)
            ).fetchall()
        return {row.post_id for row in rows}


def create_blog_tag_routes(tag_repo: BlogTagRepository, blog_repo: BlogRepositoryProtocol) -> APIRouter:
    router = APIRouter(prefix="/public")

    @router.get("/blog-tags")
    async def public_blog_tags() -> list[BlogTagSummary]:
        published_post_ids = {
            post.id for post in blog_repo.list_all() if post.status == "published" and post.published_at is not None
        }
        return tag_repo.list_public_tags(published_post_ids=published_post_ids)

    @router.get("/blog-posts/{slug}/tags")
    async def public_blog_post_tags(slug: str) -> list[BlogTagSummary]:
        post = blog_repo.get_published_by_slug(slug)
        if post is None:
            raise HTTPException(status_code=404, detail="Published blog post not found")
        return tag_repo.get_tags_for_post(post.id)

    return router


def create_blog_tag_admin_routes(tag_repo: BlogTagRepository, settings: Settings) -> APIRouter:
    def require_admin(
        identity_payload: Annotated[str | None, Header(alias=ADMIN_IDENTITY_HEADER)] = None,
        signature: Annotated[str | None, Header(alias=ADMIN_SIGNATURE_HEADER)] = None,
    ) -> AdminIdentity:
        return require_admin_identity_with_settings(settings, identity_payload, signature)

    router = APIRouter(prefix="/admin")

    @router.get("/blog-tags")
    async def admin_blog_tags(_identity: AdminIdentity = Depends(require_admin)) -> list[BlogTagSummary]:
        return tag_repo.list_admin_tags()

    @router.post("/blog-tags")
    async def admin_create_blog_tag(
        request: BlogTagCreate,
        _identity: AdminIdentity = Depends(require_admin),
    ) -> BlogTag:
        try:
            return tag_repo.create_tag(request)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @router.get("/blog-posts/{post_id}/tags")
    async def admin_get_post_tags(
        post_id: str,
        _identity: AdminIdentity = Depends(require_admin),
    ) -> list[BlogTagSummary]:
        return tag_repo.get_tags_for_post(post_id)

    @router.put("/blog-posts/{post_id}/tags")
    async def admin_set_post_tags(
        post_id: str,
        request: BlogPostTagsUpdate,
        _identity: AdminIdentity = Depends(require_admin),
    ) -> list[BlogTagSummary]:
        tags = tag_repo.set_post_tags(post_id, request.tag_ids)
        if tags is None:
            raise HTTPException(status_code=404, detail="Post or tag not found")
        return tags

    return router
