from datetime import UTC, datetime
from typing import Literal, Protocol
from uuid import uuid4

from pydantic import BaseModel, Field
from sqlalchemy import Engine, insert, select, update

from backend.app.database import audit_events, blog_posts

BlogStatus = Literal["draft", "published"]


class BlogPost(BaseModel):
    id: str
    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    title: str
    excerpt: str
    author_name: str
    status: BlogStatus
    published_at: datetime | None
    content_markdown: str
    image_url: str | None = None
    author_user_id: str | None = None


class BlogPostCreate(BaseModel):
    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    title: str = Field(min_length=1, max_length=240)
    excerpt: str = Field(min_length=1)
    author_name: str = Field(min_length=1, max_length=120)
    content_markdown: str = Field(min_length=1)
    image_url: str | None = Field(default=None, max_length=2048)
    author_user_id: str | None = Field(default=None, max_length=255)


class BlogPostUpdate(BaseModel):
    slug: str | None = Field(default=None, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    title: str | None = Field(default=None, min_length=1, max_length=240)
    excerpt: str | None = Field(default=None, min_length=1)
    author_name: str | None = Field(default=None, min_length=1, max_length=120)
    content_markdown: str | None = Field(default=None, min_length=1)
    image_url: str | None = Field(default=None, max_length=2048)
    author_user_id: str | None = Field(default=None, max_length=255)


class BlogPostSummary(BaseModel):
    slug: str
    title: str
    excerpt: str
    author_name: str
    published_at: datetime
    image_url: str | None = None
    author_user_id: str | None = None


class BlogPostDetail(BlogPostSummary):
    id: str
    content_markdown: str


class AdminBlogPostSummary(BaseModel):
    id: str
    slug: str
    title: str
    status: BlogStatus
    published_at: datetime | None
    image_url: str | None = None


class AdminBlogPostDetail(AdminBlogPostSummary):
    excerpt: str
    author_name: str
    content_markdown: str
    author_user_id: str | None = None


class AuditEvent(BaseModel):
    id: str
    actor_user_id: str
    actor_email: str
    action: str
    entity_type: str
    entity_id: str
    created_at: datetime


class BlogRepositoryProtocol(Protocol):
    def get_by_id(self, post_id: str) -> AdminBlogPostDetail | None: ...

    def get_by_slug(self, slug: str) -> AdminBlogPostDetail | None: ...

    def list_all(self) -> list[AdminBlogPostSummary]: ...

    def list_published(self, *, post_ids: set[str] | None = None, author_user_ids: set[str] | None = None) -> list[BlogPostSummary]: ...

    def get_published_by_slug(self, slug: str) -> BlogPostDetail | None: ...

    def create(self, request: BlogPostCreate) -> BlogPost: ...

    def update(self, post_id: str, request: BlogPostUpdate) -> BlogPost | None: ...

    def publish(self, post_id: str) -> BlogPost | None: ...

    def unpublish(self, post_id: str) -> BlogPost | None: ...

    def record_audit(
        self, actor_user_id: str, actor_email: str, action: str, entity_id: str
    ) -> AuditEvent: ...

    def list_audit_events(self) -> list[AuditEvent]: ...


class BlogRepository:
    def __init__(self, posts: list[BlogPost] | None = None) -> None:
        seed_posts = list(DEFAULT_BLOG_POSTS) if posts is None else posts
        self.posts: dict[str, BlogPost] = {post.id: post for post in seed_posts}
        self.audit_events: list[AuditEvent] = []

    def get_by_id(self, post_id: str) -> AdminBlogPostDetail | None:
        post = self.posts.get(post_id)
        if post is None:
            return None
        return AdminBlogPostDetail(
            id=post.id,
            slug=post.slug,
            title=post.title,
            status=post.status,
            published_at=post.published_at,
            excerpt=post.excerpt,
            author_name=post.author_name,
            content_markdown=post.content_markdown,
            image_url=post.image_url,
            author_user_id=post.author_user_id,
        )

    def get_by_slug(self, slug: str) -> AdminBlogPostDetail | None:
        for post in self.posts.values():
            if post.slug == slug:
                return self.get_by_id(post.id)
        return None

    def list_all(self) -> list[AdminBlogPostSummary]:
        posts = sorted(
            self.posts.values(),
            key=lambda post: post.published_at or datetime.min.replace(tzinfo=UTC),
            reverse=True,
        )
        return [
            AdminBlogPostSummary(
                id=post.id,
                slug=post.slug,
                title=post.title,
                status=post.status,
                published_at=post.published_at,
            )
            for post in posts
        ]

    def list_published(self, *, post_ids: set[str] | None = None, author_user_ids: set[str] | None = None) -> list[BlogPostSummary]:
        posts = [
            post
            for post in self.posts.values()
            if post.status == "published"
            and post.published_at
            and (post_ids is None or post.id in post_ids)
            and (author_user_ids is None or (post.author_user_id is not None and post.author_user_id in author_user_ids))
        ]
        posts.sort(
            key=lambda post: post.published_at or datetime.min.replace(tzinfo=UTC),
            reverse=True,
        )
        return [
            BlogPostSummary(
                slug=post.slug,
                title=post.title,
                excerpt=post.excerpt,
                author_name=post.author_name,
                published_at=post.published_at,
                image_url=post.image_url,
                author_user_id=post.author_user_id,
            )
            for post in posts
            if post.published_at is not None
        ]

    def get_published_by_slug(self, slug: str) -> BlogPostDetail | None:
        for post in self.posts.values():
            if (
                post.slug == slug
                and post.status == "published"
                and post.published_at is not None
            ):
                return BlogPostDetail(
                    slug=post.slug,
                    title=post.title,
                    excerpt=post.excerpt,
                    author_name=post.author_name,
                    published_at=post.published_at,
                    id=post.id,
                    content_markdown=post.content_markdown,
                    image_url=post.image_url,
                    author_user_id=post.author_user_id,
                )
        return None

    def create(self, request: BlogPostCreate) -> BlogPost:
        slug = request.slug
        # Ensure slug uniqueness by appending a suffix if needed
        existing_slugs = {p.slug for p in self.posts.values()}
        if slug in existing_slugs:
            suffix = 2
            while f"{slug}-{suffix}" in existing_slugs:
                suffix += 1
            slug = f"{slug}-{suffix}"
        post = BlogPost(
            id=f"post_{uuid4().hex}",
            slug=slug,
            status="draft",
            published_at=None,
            title=request.title,
            excerpt=request.excerpt,
            author_name=request.author_name,
            content_markdown=request.content_markdown,
            image_url=request.image_url,
            author_user_id=request.author_user_id,
        )
        self.posts[post.id] = post
        return post

    def update(self, post_id: str, request: BlogPostUpdate) -> BlogPost | None:
        post = self.posts.get(post_id)
        if post is None:
            return None
        update_data = request.model_dump(exclude_unset=True)
        updated = post.model_copy(update=update_data)
        self.posts[post_id] = updated
        return updated

    def publish(self, post_id: str) -> BlogPost | None:
        post = self.posts.get(post_id)
        if post is None:
            return None
        published = post.model_copy(
            update={"status": "published", "published_at": datetime.now(UTC)}
        )
        self.posts[post_id] = published
        return published

    def unpublish(self, post_id: str) -> BlogPost | None:
        post = self.posts.get(post_id)
        if post is None:
            return None
        draft = post.model_copy(update={"status": "draft", "published_at": None})
        self.posts[post_id] = draft
        return draft

    def record_audit(
        self, actor_user_id: str, actor_email: str, action: str, entity_id: str
    ) -> AuditEvent:
        event = AuditEvent(
            id=f"audit_{uuid4().hex}",
            actor_user_id=actor_user_id,
            actor_email=actor_email,
            action=action,
            entity_type="blog_post",
            entity_id=entity_id,
            created_at=datetime.now(UTC),
        )
        self.audit_events.append(event)
        return event

    def list_audit_events(self) -> list[AuditEvent]:
        return list(self.audit_events)


class PostgresBlogRepository:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def seed_defaults_when_empty(self) -> None:
        with self.engine.begin() as connection:
            for post in DEFAULT_BLOG_POSTS:
                existing = connection.execute(
                    select(blog_posts.c.id).where(blog_posts.c.slug == post.slug)
                ).first()
                if existing is None:
                    connection.execute(insert(blog_posts).values(**post.model_dump()))

    def get_by_id(self, post_id: str) -> AdminBlogPostDetail | None:
        self.seed_defaults_when_empty()
        with self.engine.begin() as connection:
            row = (
                connection.execute(select(blog_posts).where(blog_posts.c.id == post_id))
                .mappings()
                .first()
            )
            if row is None:
                return None
            return AdminBlogPostDetail(
                id=row["id"],
                slug=row["slug"],
                title=row["title"],
                status=row["status"],
                published_at=row["published_at"],
                excerpt=row["excerpt"],
                author_name=row["author_name"],
                content_markdown=row["content_markdown"],
            )

    def get_by_slug(self, slug: str) -> AdminBlogPostDetail | None:
        self.seed_defaults_when_empty()
        with self.engine.begin() as connection:
            row = (
                connection.execute(select(blog_posts).where(blog_posts.c.slug == slug))
                .mappings()
                .first()
            )
            if row is None:
                return None
            return AdminBlogPostDetail(
                id=row["id"],
                slug=row["slug"],
                title=row["title"],
                status=row["status"],
                published_at=row["published_at"],
                excerpt=row["excerpt"],
                author_name=row["author_name"],
                content_markdown=row["content_markdown"],
                image_url=row.get("image_url") if hasattr(row, "get") else row["image_url"],
            )

    def list_all(self) -> list[AdminBlogPostSummary]:
        self.seed_defaults_when_empty()
        with self.engine.begin() as connection:
            rows = connection.execute(
                select(blog_posts).order_by(
                    blog_posts.c.published_at.desc().nullslast()
                )
            ).mappings()
            return [
                AdminBlogPostSummary(
                    id=row["id"],
                    slug=row["slug"],
                    title=row["title"],
                    status=row["status"],
                    published_at=row["published_at"],
                )
                for row in rows
            ]

    def list_published(self, *, post_ids: set[str] | None = None, author_user_ids: set[str] | None = None) -> list[BlogPostSummary]:
        self.seed_defaults_when_empty()
        with self.engine.begin() as connection:
            filters = [
                blog_posts.c.status == "published",
                blog_posts.c.published_at.is_not(None),
            ]
            if post_ids is not None:
                if not post_ids:
                    return []
                filters.append(blog_posts.c.id.in_(post_ids))
            if author_user_ids is not None:
                if not author_user_ids:
                    return []
                filters.append(blog_posts.c.author_user_id.in_(author_user_ids))
            rows = connection.execute(
                select(blog_posts)
                .where(*filters)
                .order_by(blog_posts.c.published_at.desc())
            ).mappings()
            return [
                BlogPostSummary(
                    slug=row["slug"],
                    title=row["title"],
                    excerpt=row["excerpt"],
                    author_name=row["author_name"],
                    published_at=row["published_at"],
                    image_url=row.get("image_url") if hasattr(row, "get") else row["image_url"],
                    author_user_id=row.get("author_user_id") if hasattr(row, "get") else row["author_user_id"],
                )
                for row in rows
            ]

    def get_published_by_slug(self, slug: str) -> BlogPostDetail | None:
        self.seed_defaults_when_empty()
        with self.engine.begin() as connection:
            row = (
                connection.execute(
                    select(blog_posts).where(
                        blog_posts.c.slug == slug,
                        blog_posts.c.status == "published",
                        blog_posts.c.published_at.is_not(None),
                    )
                )
                .mappings()
                .first()
            )
            if row is None:
                return None
            return BlogPostDetail(
                slug=row["slug"],
                title=row["title"],
                excerpt=row["excerpt"],
                author_name=row["author_name"],
                published_at=row["published_at"],
                id=row["id"],
                content_markdown=row["content_markdown"],
                image_url=row.get("image_url") if hasattr(row, "get") else row["image_url"],
                author_user_id=row.get("author_user_id") if hasattr(row, "get") else row["author_user_id"],
            )

    def create(self, request: BlogPostCreate) -> BlogPost:
        slug = request.slug
        # Ensure slug uniqueness by appending a suffix if needed
        with self.engine.begin() as connection:
            existing = connection.execute(
                select(blog_posts.c.slug).where(blog_posts.c.slug == slug)
            ).first()
            if existing is not None:
                suffix = 2
                while True:
                    candidate = f"{slug}-{suffix}"
                    dup = connection.execute(
                        select(blog_posts.c.slug).where(blog_posts.c.slug == candidate)
                    ).first()
                    if dup is None:
                        slug = candidate
                        break
                    suffix += 1
        post = BlogPost(
            id=f"post_{uuid4().hex}",
            slug=slug,
            status="draft",
            published_at=None,
            title=request.title,
            excerpt=request.excerpt,
            author_name=request.author_name,
            content_markdown=request.content_markdown,
            image_url=request.image_url,
            author_user_id=request.author_user_id,
        )
        with self.engine.begin() as connection:
            connection.execute(insert(blog_posts).values(**post.model_dump()))
        return post

    def update(self, post_id: str, request: BlogPostUpdate) -> BlogPost | None:
        update_data = request.model_dump(exclude_unset=True)
        with self.engine.begin() as connection:
            existing = (
                connection.execute(select(blog_posts).where(blog_posts.c.id == post_id))
                .mappings()
                .first()
            )
            if existing is None:
                return None
            if update_data:
                connection.execute(
                    update(blog_posts)
                    .where(blog_posts.c.id == post_id)
                    .values(**update_data)
                )
            row = (
                connection.execute(select(blog_posts).where(blog_posts.c.id == post_id))
                .mappings()
                .one()
            )
        return BlogPost.model_validate(dict(row))

    def publish(self, post_id: str) -> BlogPost | None:
        published_at = datetime.now(UTC)
        with self.engine.begin() as connection:
            result = connection.execute(
                update(blog_posts)
                .where(blog_posts.c.id == post_id)
                .values(status="published", published_at=published_at)
            )
            if result.rowcount == 0:
                return None
            row = (
                connection.execute(select(blog_posts).where(blog_posts.c.id == post_id))
                .mappings()
                .one()
            )
        return BlogPost.model_validate(dict(row))

    def unpublish(self, post_id: str) -> BlogPost | None:
        with self.engine.begin() as connection:
            result = connection.execute(
                update(blog_posts)
                .where(blog_posts.c.id == post_id)
                .values(status="draft", published_at=None)
            )
            if result.rowcount == 0:
                return None
            row = (
                connection.execute(select(blog_posts).where(blog_posts.c.id == post_id))
                .mappings()
                .one()
            )
        return BlogPost.model_validate(dict(row))

    def record_audit(
        self, actor_user_id: str, actor_email: str, action: str, entity_id: str
    ) -> AuditEvent:
        event = AuditEvent(
            id=f"audit_{uuid4().hex}",
            actor_user_id=actor_user_id,
            actor_email=actor_email,
            action=action,
            entity_type="blog_post",
            entity_id=entity_id,
            created_at=datetime.now(UTC),
        )
        with self.engine.begin() as connection:
            connection.execute(insert(audit_events).values(**event.model_dump()))
        return event

    def list_audit_events(self) -> list[AuditEvent]:
        with self.engine.begin() as connection:
            rows = connection.execute(
                select(audit_events).order_by(audit_events.c.created_at.asc())
            ).mappings()
            return [AuditEvent.model_validate(dict(row)) for row in rows]


DEFAULT_BLOG_POSTS: tuple[BlogPost, ...] = (
    BlogPost(
        id="post_001",
        slug="building-an-ai-lab-with-human-review",
        title="Building an AI Lab with Human Review at the Center",
        excerpt="A practical note on launching AI workflows without giving up editorial control, evidence checks, or trust.",
        author_name="AI Lab Team",
        status="published",
        published_at=datetime(2026, 6, 2, 9, 0, tzinfo=UTC),
        content_markdown="""The first AI Lab workflows should make human review stronger, not optional.

For the portal MVP, publishing remains a deliberate act: AI can help draft, review, and summarize, but a person approves what becomes public.

That constraint keeps the system credible while the team gathers evaluation data.""",
    ),
    BlogPost(
        id="post_002",
        slug="draft-provider-scorecards",
        title="Draft Provider Scorecards",
        excerpt="Draft content that must not be public yet.",
        author_name="AI Lab Team",
        status="draft",
        published_at=None,
        content_markdown="Draft only.",
    ),
)
