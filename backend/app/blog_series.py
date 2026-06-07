"""Blog series / multi-part article grouping.

Allows grouping blog posts into ordered series with part navigation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import Engine, RowMapping, delete, insert, select, update

from backend.app.admin_boundary import (
    ADMIN_IDENTITY_HEADER,
    ADMIN_SIGNATURE_HEADER,
    AdminIdentity,
    require_admin_identity_with_settings,
)
from backend.app.blog import BlogRepositoryProtocol
from backend.app.database import blog_series, blog_series_posts
from backend.app.settings import Settings


# ── Pydantic models ──


class BlogSeries(BaseModel):
    id: str
    title: str = Field(max_length=240)
    description: str | None = None
    slug: str = Field(max_length=160)
    cover_image_url: str | None = None
    created_at: datetime
    updated_at: datetime


class BlogSeriesCreate(BaseModel):
    title: str = Field(min_length=1, max_length=240)
    description: str | None = Field(default=None)
    slug: str = Field(min_length=1, max_length=160)
    cover_image_url: str | None = Field(default=None, max_length=2048)


class BlogSeriesUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=240)
    description: str | None = Field(default=None)
    slug: str | None = Field(default=None, min_length=1, max_length=160)
    cover_image_url: str | None = Field(default=None, max_length=2048)


class BlogSeriesPost(BaseModel):
    id: str
    series_id: str
    post_id: str
    part_number: int
    created_at: datetime


class SeriesPostItem(BaseModel):
    part_number: int
    post_id: str
    post_title: str
    post_slug: str


class BlogSeriesDetail(BlogSeries):
    posts: list[SeriesPostItem] = []


class BlogSeriesPublicSummary(BaseModel):
    id: str
    title: str
    description: str | None = None
    slug: str
    cover_image_url: str | None = None
    post_count: int = 0
    created_at: datetime
    updated_at: datetime


# ── Repository ──


class BlogSeriesRepository(ABC):
    @abstractmethod
    def list_all(self) -> list[BlogSeries]: ...

    @abstractmethod
    def get_by_id(self, series_id: str) -> BlogSeries | None: ...

    @abstractmethod
    def get_by_slug(self, slug: str) -> BlogSeries | None: ...

    @abstractmethod
    def create(self, request: BlogSeriesCreate) -> BlogSeries: ...

    @abstractmethod
    def update(self, series_id: str, request: BlogSeriesUpdate) -> BlogSeries | None: ...

    @abstractmethod
    def delete(self, series_id: str) -> bool: ...

    @abstractmethod
    def add_post_to_series(self, series_id: str, post_id: str, part_number: int) -> BlogSeriesPost: ...

    @abstractmethod
    def remove_post_from_series(self, series_id: str, post_id: str) -> bool: ...

    @abstractmethod
    def get_with_posts(self, series_id: str) -> BlogSeriesDetail | None: ...

    @abstractmethod
    def get_by_slug_with_posts(self, slug: str) -> BlogSeriesDetail | None: ...

    @abstractmethod
    def list_for_post(self, post_id: str) -> list[BlogSeriesDetail]: ...

    @abstractmethod
    def list_public_summaries(self) -> list[BlogSeriesPublicSummary]: ...

    @abstractmethod
    def slug_exists(self, slug: str, exclude_id: str | None = None) -> bool: ...


class InMemoryBlogSeriesRepository(BlogSeriesRepository):
    """In-memory repository for testing."""

    def __init__(self) -> None:
        self._series: dict[str, BlogSeries] = {}
        self._posts: list[BlogSeriesPost] = []

    def list_all(self) -> list[BlogSeries]:
        return sorted(self._series.values(), key=lambda s: s.created_at, reverse=True)

    def get_by_id(self, series_id: str) -> BlogSeries | None:
        return self._series.get(series_id)

    def get_by_slug(self, slug: str) -> BlogSeries | None:
        for s in self._series.values():
            if s.slug == slug:
                return s
        return None

    def create(self, request: BlogSeriesCreate) -> BlogSeries:
        now = datetime.now(UTC)
        series = BlogSeries(
            id=f"series_{uuid4().hex}",
            title=request.title,
            description=request.description,
            slug=request.slug,
            cover_image_url=request.cover_image_url,
            created_at=now,
            updated_at=now,
        )
        self._series[series.id] = series
        return series

    def update(self, series_id: str, request: BlogSeriesUpdate) -> BlogSeries | None:
        existing = self._series.get(series_id)
        if existing is None:
            return None
        data = request.model_dump(exclude_unset=True)
        if not data:
            return existing
        updated = existing.model_copy(update={**data, "updated_at": datetime.now(UTC)})
        self._series[series_id] = updated
        return updated

    def delete(self, series_id: str) -> bool:
        if series_id not in self._series:
            return False
        del self._series[series_id]
        self._posts = [p for p in self._posts if p.series_id != series_id]
        return True

    def add_post_to_series(self, series_id: str, post_id: str, part_number: int) -> BlogSeriesPost:
        if series_id not in self._series:
            raise ValueError("Series not found")
        # Check for duplicate post
        for p in self._posts:
            if p.series_id == series_id and p.post_id == post_id:
                raise ValueError("Post already in series")
            if p.series_id == series_id and p.part_number == part_number:
                raise ValueError("Part number already used in series")
        post = BlogSeriesPost(
            id=f"sp_{uuid4().hex}",
            series_id=series_id,
            post_id=post_id,
            part_number=part_number,
            created_at=datetime.now(UTC),
        )
        self._posts.append(post)
        return post

    def remove_post_from_series(self, series_id: str, post_id: str) -> bool:
        before = len(self._posts)
        self._posts = [p for p in self._posts if not (p.series_id == series_id and p.post_id == post_id)]
        return len(self._posts) < before

    def get_with_posts(self, series_id: str) -> BlogSeriesDetail | None:
        series = self._series.get(series_id)
        if series is None:
            return None
        posts = sorted([p for p in self._posts if p.series_id == series_id], key=lambda p: p.part_number)
        return BlogSeriesDetail(
            **series.model_dump(),
            posts=[
                SeriesPostItem(part_number=p.part_number, post_id=p.post_id, post_title="", post_slug="")
                for p in posts
            ],
        )

    def get_by_slug_with_posts(self, slug: str) -> BlogSeriesDetail | None:
        series = self.get_by_slug(slug)
        if series is None:
            return None
        return self.get_with_posts(series.id)

    def list_for_post(self, post_id: str) -> list[BlogSeriesDetail]:
        series_ids = {p.series_id for p in self._posts if p.post_id == post_id}
        return [self.get_with_posts(sid) for sid in series_ids if self.get_with_posts(sid) is not None]

    def list_public_summaries(self) -> list[BlogSeriesPublicSummary]:
        series_ids_with_posts = {p.series_id for p in self._posts}
        results: list[BlogSeriesPublicSummary] = []
        for s in self._series.values():
            if s.id not in series_ids_with_posts:
                continue
            count = len([p for p in self._posts if p.series_id == s.id])
            results.append(
                BlogSeriesPublicSummary(
                    id=s.id,
                    title=s.title,
                    description=s.description,
                    slug=s.slug,
                    cover_image_url=s.cover_image_url,
                    post_count=count,
                    created_at=s.created_at,
                    updated_at=s.updated_at,
                )
            )
        return sorted(results, key=lambda s: s.created_at, reverse=True)

    def slug_exists(self, slug: str, exclude_id: str | None = None) -> bool:
        for s in self._series.values():
            if s.slug == slug and (exclude_id is None or s.id != exclude_id):
                return True
        return False


class PostgresBlogSeriesRepository(BlogSeriesRepository):
    """PostgreSQL-backed repository for blog series."""

    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def list_all(self) -> list[BlogSeries]:
        with self.engine.begin() as conn:
            rows = conn.execute(
                select(blog_series).order_by(blog_series.c.created_at.desc())
            ).mappings().fetchall()
        return [BlogSeries(**dict(row)) for row in rows]

    def get_by_id(self, series_id: str) -> BlogSeries | None:
        with self.engine.begin() as conn:
            row = conn.execute(
                select(blog_series).where(blog_series.c.id == series_id)
            ).mappings().first()
        return BlogSeries(**dict(row)) if row else None

    def get_by_slug(self, slug: str) -> BlogSeries | None:
        with self.engine.begin() as conn:
            row = conn.execute(
                select(blog_series).where(blog_series.c.slug == slug)
            ).mappings().first()
        return BlogSeries(**dict(row)) if row else None

    def create(self, request: BlogSeriesCreate) -> BlogSeries:
        now = datetime.now(UTC)
        series = BlogSeries(
            id=f"series_{uuid4().hex}",
            title=request.title,
            description=request.description,
            slug=request.slug,
            cover_image_url=request.cover_image_url,
            created_at=now,
            updated_at=now,
        )
        with self.engine.begin() as conn:
            conn.execute(insert(blog_series).values(**series.model_dump()))
        return series

    def update(self, series_id: str, request: BlogSeriesUpdate) -> BlogSeries | None:
        data = request.model_dump(exclude_unset=True)
        if not data:
            return self.get_by_id(series_id)
        data["updated_at"] = datetime.now(UTC)
        with self.engine.begin() as conn:
            result = conn.execute(
                update(blog_series).where(blog_series.c.id == series_id).values(**data)
            )
            if result.rowcount == 0:
                return None
        return self.get_by_id(series_id)

    def delete(self, series_id: str) -> bool:
        with self.engine.begin() as conn:
            result = conn.execute(
                delete(blog_series).where(blog_series.c.id == series_id)
            )
            conn.execute(
                delete(blog_series_posts).where(blog_series_posts.c.series_id == series_id)
            )
        return result.rowcount > 0

    def add_post_to_series(self, series_id: str, post_id: str, part_number: int) -> BlogSeriesPost:
        now = datetime.now(UTC)
        sp = BlogSeriesPost(
            id=f"sp_{uuid4().hex}",
            series_id=series_id,
            post_id=post_id,
            part_number=part_number,
            created_at=now,
        )
        with self.engine.begin() as conn:
            conn.execute(insert(blog_series_posts).values(**sp.model_dump()))
        return sp

    def remove_post_from_series(self, series_id: str, post_id: str) -> bool:
        with self.engine.begin() as conn:
            result = conn.execute(
                delete(blog_series_posts).where(
                    blog_series_posts.c.series_id == series_id,
                    blog_series_posts.c.post_id == post_id,
                )
            )
        return result.rowcount > 0

    def get_with_posts(self, series_id: str) -> BlogSeriesDetail | None:
        series = self.get_by_id(series_id)
        if series is None:
            return None
        with self.engine.begin() as conn:
            rows = conn.execute(
                select(blog_series_posts).where(blog_series_posts.c.series_id == series_id)
                .order_by(blog_series_posts.c.part_number)
            ).mappings().fetchall()
        return BlogSeriesDetail(
            **series.model_dump(),
            posts=[
                SeriesPostItem(part_number=row["part_number"], post_id=row["post_id"], post_title="", post_slug="")
                for row in rows
            ],
        )

    def get_by_slug_with_posts(self, slug: str) -> BlogSeriesDetail | None:
        series = self.get_by_slug(slug)
        if series is None:
            return None
        return self.get_with_posts(series.id)

    def list_for_post(self, post_id: str) -> list[BlogSeriesDetail]:
        with self.engine.begin() as conn:
            rows = conn.execute(
                select(blog_series_posts.c.series_id)
                .where(blog_series_posts.c.post_id == post_id)
            ).fetchall()
        results: list[BlogSeriesDetail] = []
        for (series_id,) in rows:
            detail = self.get_with_posts(series_id)
            if detail is not None:
                results.append(detail)
        return results

    def list_public_summaries(self) -> list[BlogSeriesPublicSummary]:
        with self.engine.begin() as conn:
            rows = conn.execute(
                select(
                    blog_series.c.id,
                    blog_series.c.title,
                    blog_series.c.description,
                    blog_series.c.slug,
                    blog_series.c.cover_image_url,
                    blog_series.c.created_at,
                    blog_series.c.updated_at,
                )
                .select_from(blog_series.join(
                    blog_series_posts, blog_series.c.id == blog_series_posts.c.series_id
                ))
                .distinct()
                .order_by(blog_series.c.created_at.desc())
            ).mappings().fetchall()
        results: list[BlogSeriesPublicSummary] = []
        for row in rows:
            with self.engine.begin() as conn:
                count = conn.execute(
                    select(blog_series_posts.c.id)
                    .where(blog_series_posts.c.series_id == row["id"])
                ).fetchall()
            results.append(
                BlogSeriesPublicSummary(
                    id=row["id"],
                    title=row["title"],
                    description=row["description"],
                    slug=row["slug"],
                    cover_image_url=row["cover_image_url"],
                    post_count=len(count),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
            )
        return results

    def slug_exists(self, slug: str, exclude_id: str | None = None) -> bool:
        with self.engine.begin() as conn:
            query = select(blog_series.c.id).where(blog_series.c.slug == slug)
            if exclude_id:
                query = query.where(blog_series.c.id != exclude_id)
            row = conn.execute(query).first()
        return row is not None


# ── Route factories ──


def create_blog_series_admin_routes(
    series_repo: BlogSeriesRepository,
    blog_repo: BlogRepositoryProtocol,
    settings: Settings,
) -> APIRouter:
    """Admin routes for managing blog series."""

    def require_admin(
        identity_payload: Annotated[str | None, Header(alias=ADMIN_IDENTITY_HEADER)] = None,
        signature: Annotated[str | None, Header(alias=ADMIN_SIGNATURE_HEADER)] = None,
    ) -> AdminIdentity:
        return require_admin_identity_with_settings(settings, identity_payload, signature)

    router = APIRouter(prefix="/admin/blog-series")

    @router.get("")
    async def admin_list_series(
        _identity: AdminIdentity = Depends(require_admin),
    ) -> list[BlogSeries]:
        return series_repo.list_all()

    @router.post("")
    async def admin_create_series(
        request: BlogSeriesCreate,
        _identity: AdminIdentity = Depends(require_admin),
    ) -> BlogSeries:
        if series_repo.slug_exists(request.slug):
            raise HTTPException(status_code=409, detail="Series slug already exists")
        return series_repo.create(request)

    @router.get("/{series_id}")
    async def admin_get_series(
        series_id: str,
        _identity: AdminIdentity = Depends(require_admin),
    ) -> BlogSeriesDetail:
        detail = series_repo.get_with_posts(series_id)
        if detail is None:
            raise HTTPException(status_code=404, detail="Series not found")
        # Enrich posts with blog post info
        enriched_posts: list[SeriesPostItem] = []
        for sp in detail.posts:
            post = blog_repo.get_by_id(sp.post_id)
            enriched_posts.append(
                SeriesPostItem(
                    part_number=sp.part_number,
                    post_id=sp.post_id,
                    post_title=post.title if post else "(deleted)",
                    post_slug=post.slug if post else "",
                )
            )
        detail.posts = enriched_posts
        return detail

    @router.patch("/{series_id}")
    async def admin_update_series(
        series_id: str,
        request: BlogSeriesUpdate,
        _identity: AdminIdentity = Depends(require_admin),
    ) -> BlogSeries:
        if request.slug and series_repo.slug_exists(request.slug, exclude_id=series_id):
            raise HTTPException(status_code=409, detail="Series slug already exists")
        series = series_repo.update(series_id, request)
        if series is None:
            raise HTTPException(status_code=404, detail="Series not found")
        return series

    @router.delete("/{series_id}")
    async def admin_delete_series(
        series_id: str,
        _identity: AdminIdentity = Depends(require_admin),
    ) -> dict[str, bool]:
        deleted = series_repo.delete(series_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Series not found")
        return {"ok": True}

    @router.post("/{series_id}/posts")
    async def admin_add_post_to_series(
        series_id: str,
        body: dict[str, str | int],
        _identity: AdminIdentity = Depends(require_admin),
    ) -> BlogSeriesPost:
        post_id = str(body.get("post_id", ""))
        part_number = int(body.get("part_number", 1))
        if not post_id:
            raise HTTPException(status_code=422, detail="post_id is required")
        # Verify series and post exist
        series = series_repo.get_by_id(series_id)
        if series is None:
            raise HTTPException(status_code=404, detail="Series not found")
        post = blog_repo.get_by_id(post_id)
        if post is None:
            raise HTTPException(status_code=404, detail="Blog post not found")
        try:
            return series_repo.add_post_to_series(series_id, post_id, part_number)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @router.delete("/{series_id}/posts/{post_id}")
    async def admin_remove_post_from_series(
        series_id: str,
        post_id: str,
        _identity: AdminIdentity = Depends(require_admin),
    ) -> dict[str, bool]:
        removed = series_repo.remove_post_from_series(series_id, post_id)
        if not removed:
            raise HTTPException(status_code=404, detail="Post not found in series")
        return {"ok": True}

    return router


def create_blog_series_public_routes(
    series_repo: BlogSeriesRepository,
    blog_repo: BlogRepositoryProtocol,
) -> APIRouter:
    """Public routes for reading blog series."""

    router = APIRouter(prefix="/public/blog-series")

    @router.get("")
    async def public_list_series() -> list[BlogSeriesPublicSummary]:
        return series_repo.list_public_summaries()

    @router.get("/{slug}")
    async def public_get_series(slug: str) -> BlogSeriesDetail:
        detail = series_repo.get_by_slug_with_posts(slug)
        if detail is None:
            raise HTTPException(status_code=404, detail="Blog series not found")
        # Filter to only published posts and enrich with titles/slugs
        enriched_posts: list[SeriesPostItem] = []
        for sp in detail.posts:
            admin_p = blog_repo.get_by_id(sp.post_id)
            if admin_p is None or admin_p.status != "published":
                continue
            enriched_posts.append(
                SeriesPostItem(
                    part_number=sp.part_number,
                    post_id=admin_p.id,
                    post_title=admin_p.title,
                    post_slug=admin_p.slug,
                )
            )
        detail.posts = enriched_posts
        return detail

    return router


def create_blog_series_post_routes(
    series_repo: BlogSeriesRepository,
    blog_repo: BlogRepositoryProtocol,
) -> APIRouter:
    """Routes for querying series by post (used internally and by frontend)."""

    router = APIRouter(prefix="/public")

    @router.get("/blog-posts/{post_slug}/series")
    async def public_post_series(post_slug: str) -> list[BlogSeriesDetail]:
        """Get all series that include the given post."""
        post = blog_repo.get_published_by_slug(post_slug)
        if post is None:
            raise HTTPException(status_code=404, detail="Published blog post not found")
        series_list = series_repo.list_for_post(post.id)
        # Enrich each series' posts with titles
        for detail in series_list:
            enriched_posts: list[SeriesPostItem] = []
            for sp in detail.posts:
                admin_p = blog_repo.get_by_id(sp.post_id)
                if admin_p is None or admin_p.status != "published":
                    continue
                enriched_posts.append(
                    SeriesPostItem(
                        part_number=sp.part_number,
                        post_id=admin_p.id,
                        post_title=admin_p.title,
                        post_slug=admin_p.slug,
                    )
                )
            detail.posts = enriched_posts
        return series_list

    return router
