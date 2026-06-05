"""Blog social features: reactions, bookmarks, comments."""

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Annotated, Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import Engine, func, select, update

from backend.app.admin_boundary import (
    ADMIN_IDENTITY_HEADER,
    ADMIN_SIGNATURE_HEADER,
    USER_IDENTITY_HEADER,
    USER_SIGNATURE_HEADER,
    SignedIdentity,
    require_admin_identity_with_settings,
    require_user_identity_with_settings,
)
from backend.app.blog import BlogRepositoryProtocol
from backend.app.database import (
    blog_bookmarks as bookmarks_table,
    blog_comment_reactions as comment_reactions_table,
    blog_comments as comments_table,
    blog_reactions as reactions_table,
)
from backend.app.settings import Settings, get_settings
from backend.app.user_profiles import UserProfileRepository, default_name_from_identity

# ─── Models ───────────────────────────────────────────────────────────────────

ALLOWED_EMOJIS = {"👍", "❤️", "🚀", "👀", "🎯"}

ReactionCount = dict[str, int]  # emoji -> count


class ReactionCreate(BaseModel):
    emoji: str = Field(min_length=1, max_length=32)


class BlogReaction(BaseModel):
    id: str
    post_id: str
    user_id: str
    user_email: str | None = None
    emoji: str
    created_at: datetime


class BlogBookmark(BaseModel):
    id: str
    post_id: str
    slug: str = ""
    title: str = ""
    user_id: str
    created_at: datetime


class BlogComment(BaseModel):
    id: str
    post_id: str
    user_id: str
    user_email: str | None = None
    user_name: str | None = None
    parent_id: str | None = None
    content: str
    status: Literal["pending", "approved", "rejected"]
    created_at: datetime
    updated_at: datetime | None = None


class BlogCommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=5000)
    parent_id: str | None = Field(default=None, max_length=64)


class BlogCommentPublic(BaseModel):
    id: str
    user_id: str
    user_name: str | None = None
    avatar_url: str | None = None
    content: str
    parent_id: str | None = None
    created_at: datetime
    reaction_count: int = 0
    user_reacted: bool = False


class BlogSocialStats(BaseModel):
    post_id: str
    reaction_counts: ReactionCount = {}
    user_reactions: list[str] = []
    is_bookmarked: bool = False
    comment_count: int = 0


class BlogSocialStatsCreate(BaseModel):
    post_id: str


class AdminCommentSummary(BaseModel):
    id: str
    post_id: str
    post_title: str = ""
    user_id: str
    user_email: str | None = None
    user_name: str | None = None
    content: str
    status: Literal["pending", "approved", "rejected"]
    created_at: datetime


# ─── Repository ───────────────────────────────────────────────────────────────


class BlogSocialRepository(ABC):
    """Abstract repository for blog social features."""

    @abstractmethod
    def get_reaction_counts(self, post_id: str) -> ReactionCount: ...

    @abstractmethod
    def get_user_reactions(self, post_id: str, user_id: str) -> list[str]: ...

    @abstractmethod
    def toggle_reaction(self, post_id: str, user_id: str, user_email: str | None, emoji: str) -> bool:
        """Returns True if reaction was added, False if removed."""
        ...

    @abstractmethod
    def is_bookmarked(self, post_id: str, user_id: str) -> bool: ...

    @abstractmethod
    def toggle_bookmark(self, post_id: str, user_id: str, user_email: str | None) -> bool:
        """Returns True if bookmark was added, False if removed."""
        ...

    @abstractmethod
    def list_user_bookmarks(self, user_id: str) -> list[BlogBookmark]: ...

    @abstractmethod
    def list_comments(self, post_id: str, *, status: str | None = None) -> list[BlogComment]: ...

    @abstractmethod
    def create_comment(
        self,
        post_id: str,
        user_id: str,
        user_email: str | None,
        user_name: str | None,
        content: str,
        parent_id: str | None = None,
    ) -> BlogComment: ...

    @abstractmethod
    def admin_list_all_comments(self) -> list[AdminCommentSummary]: ...

    @abstractmethod
    def get_comment_by_id(self, comment_id: str) -> BlogComment | None: ...

    @abstractmethod
    def set_comment_status(self, comment_id: str, status: str) -> BlogComment | None: ...

    # ── Comment reactions ──

    @abstractmethod
    def get_comment_reaction_count(self, comment_id: str) -> int: ...

    @abstractmethod
    def has_user_reacted_to_comment(self, comment_id: str, user_id: str) -> bool: ...

    @abstractmethod
    def toggle_comment_reaction(self, comment_id: str, user_id: str, user_email: str | None) -> bool:
        """Returns True if reaction added, False if removed."""
        ...

    # ── Comment edit/delete ──

    @abstractmethod
    def update_comment_content(self, comment_id: str, content: str) -> BlogComment | None: ...

    @abstractmethod
    def delete_comment(self, comment_id: str) -> bool: ...


# ─── InMemory Repository ──────────────────────────────────────────────────────


def _now() -> datetime:
    return datetime.now(UTC)


class InMemoryBlogSocialRepository(BlogSocialRepository):
    def __init__(self) -> None:
        self._reactions: dict[str, BlogReaction] = {}  # id -> reaction
        self._bookmarks: dict[str, BlogBookmark] = {}
        self._comments: dict[str, BlogComment] = {}
        self._comment_reactions: dict[str, dict[str, str]] = {}  # comment_id -> {user_id -> reaction_id}

    # ── Reactions ──

    def get_reaction_counts(self, post_id: str) -> ReactionCount:
        counts: ReactionCount = {}
        for r in self._reactions.values():
            if r.post_id == post_id:
                counts[r.emoji] = counts.get(r.emoji, 0) + 1
        return counts

    def get_user_reactions(self, post_id: str, user_id: str) -> list[str]:
        return [r.emoji for r in self._reactions.values() if r.post_id == post_id and r.user_id == user_id]

    def toggle_reaction(self, post_id: str, user_id: str, user_email: str | None, emoji: str) -> bool:
        # Find existing
        for rid, r in list(self._reactions.items()):
            if r.post_id == post_id and r.user_id == user_id and r.emoji == emoji:
                del self._reactions[rid]
                return False
        # Add new
        self._reactions[f"rxn_{uuid4().hex}"] = BlogReaction(
            id=f"rxn_{uuid4().hex}",
            post_id=post_id,
            user_id=user_id,
            user_email=user_email,
            emoji=emoji,
            created_at=_now(),
        )
        return True

    # ── Bookmarks ──

    def is_bookmarked(self, post_id: str, user_id: str) -> bool:
        return any(b.post_id == post_id and b.user_id == user_id for b in self._bookmarks.values())

    def toggle_bookmark(self, post_id: str, user_id: str, user_email: str | None) -> bool:
        for bid, b in list(self._bookmarks.items()):
            if b.post_id == post_id and b.user_id == user_id:
                del self._bookmarks[bid]
                return False
        self._bookmarks[f"bmk_{uuid4().hex}"] = BlogBookmark(
            id=f"bmk_{uuid4().hex}",
            post_id=post_id,
            user_id=user_id,
            created_at=_now(),
        )
        return True

    def list_user_bookmarks(self, user_id: str) -> list[BlogBookmark]:
        return sorted(
            [b for b in self._bookmarks.values() if b.user_id == user_id],
            key=lambda b: b.created_at,
            reverse=True,
        )

    # ── Comments ──

    def list_comments(self, post_id: str, *, status: str | None = None) -> list[BlogComment]:
        results = [c for c in self._comments.values() if c.post_id == post_id]
        if status:
            results = [c for c in results if c.status == status]
        return sorted(results, key=lambda c: c.created_at)

    def create_comment(
        self,
        post_id: str,
        user_id: str,
        user_email: str | None,
        user_name: str | None,
        content: str,
        parent_id: str | None = None,
    ) -> BlogComment:
        now = _now()
        comment = BlogComment(
            id=f"cmt_{uuid4().hex}",
            post_id=post_id,
            user_id=user_id,
            user_email=user_email,
            user_name=user_name,
            parent_id=parent_id,
            content=content,
            status="approved",
            created_at=now,
            updated_at=now,
        )
        self._comments[comment.id] = comment
        return comment

    def admin_list_all_comments(self) -> list[AdminCommentSummary]:
        return [
            AdminCommentSummary(
                id=c.id,
                post_id=c.post_id,
                user_id=c.user_id,
                user_email=c.user_email,
                user_name=c.user_name,
                content=c.content,
                status=c.status,
                created_at=c.created_at,
            )
            for c in sorted(self._comments.values(), key=lambda c: c.created_at, reverse=True)
        ]

    def get_comment_by_id(self, comment_id: str) -> BlogComment | None:
        return self._comments.get(comment_id)

    def set_comment_status(self, comment_id: str, status: str) -> BlogComment | None:
        comment = self._comments.get(comment_id)
        if comment is None:
            return None
        comment.status = status  # type: ignore[assignment]
        comment.updated_at = _now()
        return comment

    # ── Comment reactions (InMemory) ──

    def get_comment_reaction_count(self, comment_id: str) -> int:
        reactions = self._comment_reactions.get(comment_id, {})
        return len(reactions)

    def has_user_reacted_to_comment(self, comment_id: str, user_id: str) -> bool:
        reactions = self._comment_reactions.get(comment_id, {})
        return user_id in reactions

    def toggle_comment_reaction(self, comment_id: str, user_id: str, user_email: str | None) -> bool:
        if comment_id not in self._comment_reactions:
            self._comment_reactions[comment_id] = {}
        if user_id in self._comment_reactions[comment_id]:
            del self._comment_reactions[comment_id][user_id]
            return False
        self._comment_reactions[comment_id][user_id] = f"cmt_rxn_{uuid4().hex}"
        return True

    # ── Comment edit/delete (InMemory) ──

    def update_comment_content(self, comment_id: str, content: str) -> BlogComment | None:
        comment = self._comments.get(comment_id)
        if comment is None:
            return None
        comment.content = content
        comment.updated_at = _now()
        return comment

    def delete_comment(self, comment_id: str) -> bool:
        if comment_id in self._comments:
            del self._comments[comment_id]
            # Clean up reactions
            self._comment_reactions.pop(comment_id, None)
            return True
        return False


# ─── Postgres Repository ─────────────────────────────────────────────────────


class PostgresBlogSocialRepository(BlogSocialRepository):
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def _conn(self):
        return self._engine.connect()

    # ── Reactions ──

    def get_reaction_counts(self, post_id: str) -> ReactionCount:
        with self._conn() as conn:
            rows = conn.execute(
                select(reactions_table.c.emoji, func.count().label("cnt"))
                .where(reactions_table.c.post_id == post_id)
                .group_by(reactions_table.c.emoji)
            ).fetchall()
        return {row.emoji: row.cnt for row in rows}

    def get_user_reactions(self, post_id: str, user_id: str) -> list[str]:
        with self._conn() as conn:
            rows = conn.execute(
                select(reactions_table.c.emoji).where(
                    reactions_table.c.post_id == post_id,
                    reactions_table.c.user_id == user_id,
                )
            ).fetchall()
        return [row.emoji for row in rows]

    def toggle_reaction(self, post_id: str, user_id: str, user_email: str | None, emoji: str) -> bool:
        with self._conn() as conn:
            existing = conn.execute(
                select(reactions_table.c.id).where(
                    reactions_table.c.post_id == post_id,
                    reactions_table.c.user_id == user_id,
                    reactions_table.c.emoji == emoji,
                )
            ).first()
            if existing:
                conn.execute(reactions_table.delete().where(reactions_table.c.id == existing.id))
                conn.commit()
                return False
            conn.execute(
                reactions_table.insert().values(
                    id=f"rxn_{uuid4().hex}",
                    post_id=post_id,
                    user_id=user_id,
                    user_email=user_email,
                    emoji=emoji,
                    created_at=_now(),
                )
            )
            conn.commit()
        return True

    # ── Bookmarks ──

    def is_bookmarked(self, post_id: str, user_id: str) -> bool:
        with self._conn() as conn:
            row = conn.execute(
                select(bookmarks_table.c.id).where(
                    bookmarks_table.c.post_id == post_id,
                    bookmarks_table.c.user_id == user_id,
                )
            ).first()
            return row is not None

    def toggle_bookmark(self, post_id: str, user_id: str, user_email: str | None) -> bool:
        with self._conn() as conn:
            existing = conn.execute(
                select(bookmarks_table.c.id).where(
                    bookmarks_table.c.post_id == post_id,
                    bookmarks_table.c.user_id == user_id,
                )
            ).first()
            if existing:
                conn.execute(bookmarks_table.delete().where(bookmarks_table.c.id == existing.id))
                conn.commit()
                return False
            conn.execute(
                bookmarks_table.insert().values(
                    id=f"bmk_{uuid4().hex}",
                    post_id=post_id,
                    user_id=user_id,
                    user_email=user_email,
                    created_at=_now(),
                )
            )
            conn.commit()
        return True

    def list_user_bookmarks(self, user_id: str) -> list[BlogBookmark]:
        with self._conn() as conn:
            rows = conn.execute(
                select(
                    bookmarks_table.c.id,
                    bookmarks_table.c.post_id,
                    bookmarks_table.c.user_id,
                    bookmarks_table.c.created_at,
                )
                .where(bookmarks_table.c.user_id == user_id)
                .order_by(bookmarks_table.c.created_at.desc())
            ).fetchall()
        return [
            BlogBookmark(
                id=row.id,
                post_id=row.post_id,
                user_id=row.user_id,
                created_at=row.created_at,
            )
            for row in rows
        ]

    # ── Comments ──

    def list_comments(self, post_id: str, *, status: str | None = None) -> list[BlogComment]:
        with self._conn() as conn:
            query = select(comments_table).where(comments_table.c.post_id == post_id)
            if status:
                query = query.where(comments_table.c.status == status)
            query = query.order_by(comments_table.c.created_at)
            rows = conn.execute(query).fetchall()
        return [self._row_to_comment(row) for row in rows]

    def create_comment(
        self,
        post_id: str,
        user_id: str,
        user_email: str | None,
        user_name: str | None,
        content: str,
        parent_id: str | None = None,
    ) -> BlogComment:
        now = _now()
        with self._conn() as conn:
            result = conn.execute(
                comments_table.insert().returning(*comments_table.c),
                {
                    "id": f"cmt_{uuid4().hex}",
                    "post_id": post_id,
                    "user_id": user_id,
                    "user_email": user_email,
                    "user_name": user_name,
                    "parent_id": parent_id,
                    "content": content,
                    "status": "approved",
                    "created_at": now,
                    "updated_at": now,
                },
            )
            conn.commit()
            row = result.fetchone()
        return self._row_to_comment(row)

    def admin_list_all_comments(self) -> list[AdminCommentSummary]:
        with self._conn() as conn:
            rows = conn.execute(
                select(comments_table).order_by(comments_table.c.created_at.desc())
            ).fetchall()
        return [
            AdminCommentSummary(
                id=row.id,
                post_id=row.post_id,
                user_id=row.user_id,
                user_email=row.user_email,
                user_name=row.user_name,
                content=row.content,
                status=row.status,
                created_at=row.created_at,
            )
            for row in rows
        ]

    def get_comment_by_id(self, comment_id: str) -> BlogComment | None:
        with self._conn() as conn:
            row = conn.execute(
                select(comments_table).where(comments_table.c.id == comment_id)
            ).first()
        return self._row_to_comment(row) if row else None

    def set_comment_status(self, comment_id: str, status: str) -> BlogComment | None:
        with self._conn() as conn:
            result = conn.execute(
                update(comments_table)
                .where(comments_table.c.id == comment_id)
                .values(status=status, updated_at=_now())
                .returning(*comments_table.c)
            )
            conn.commit()
            row = result.fetchone()
        return self._row_to_comment(row) if row else None

    # ── Comment reactions (Postgres) ──

    def get_comment_reaction_count(self, comment_id: str) -> int:
        with self._conn() as conn:
            row = conn.execute(
                select(func.count())
                .select_from(comment_reactions_table)
                .where(comment_reactions_table.c.comment_id == comment_id)
            ).scalar()
        return row or 0

    def has_user_reacted_to_comment(self, comment_id: str, user_id: str) -> bool:
        with self._conn() as conn:
            row = conn.execute(
                select(comment_reactions_table.c.id)
                .where(
                    comment_reactions_table.c.comment_id == comment_id,
                    comment_reactions_table.c.user_id == user_id,
                )
            ).first()
        return row is not None

    def toggle_comment_reaction(self, comment_id: str, user_id: str, user_email: str | None) -> bool:
        with self._conn() as conn:
            existing = conn.execute(
                select(comment_reactions_table.c.id)
                .where(
                    comment_reactions_table.c.comment_id == comment_id,
                    comment_reactions_table.c.user_id == user_id,
                )
            ).first()
            if existing:
                conn.execute(comment_reactions_table.delete().where(comment_reactions_table.c.id == existing.id))
                conn.commit()
                return False
            conn.execute(
                comment_reactions_table.insert().values(
                    id=f"cmt_rxn_{uuid4().hex}",
                    comment_id=comment_id,
                    user_id=user_id,
                    user_email=user_email,
                    created_at=_now(),
                )
            )
            conn.commit()
        return True

    # ── Comment edit/delete (Postgres) ──

    def update_comment_content(self, comment_id: str, content: str) -> BlogComment | None:
        with self._conn() as conn:
            result = conn.execute(
                update(comments_table)
                .where(comments_table.c.id == comment_id)
                .values(content=content, updated_at=_now())
                .returning(*comments_table.c)
            )
            conn.commit()
            row = result.fetchone()
        return self._row_to_comment(row) if row else None

    def delete_comment(self, comment_id: str) -> bool:
        with self._conn() as conn:
            # Delete reactions first
            conn.execute(
                comment_reactions_table.delete().where(
                    comment_reactions_table.c.comment_id == comment_id
                )
            )
            # Delete the comment itself
            result = conn.execute(
                comments_table.delete()
                .where(comments_table.c.id == comment_id)
                .returning(comments_table.c.id)
            )
            conn.commit()
            return result.fetchone() is not None

    @staticmethod
    def _row_to_comment(row) -> BlogComment:
        return BlogComment(
            id=row.id,
            post_id=row.post_id,
            user_id=row.user_id,
            user_email=row.user_email,
            user_name=row.user_name,
            parent_id=row.parent_id,
            content=row.content,
            status=row.status,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )


# ─── Routers ──────────────────────────────────────────────────────────────────


def create_blog_social_routes(
    social_repo: BlogSocialRepository,
    blog_repo: BlogRepositoryProtocol,
    settings: Settings,
    profile_repo: UserProfileRepository | None = None,
) -> APIRouter:
    """Public routes for blog social features (requires user auth via signed identity)."""

    def require_user(
        identity_payload: Annotated[str | None, Header(alias=USER_IDENTITY_HEADER)] = None,
        signature: Annotated[str | None, Header(alias=USER_SIGNATURE_HEADER)] = None,
    ) -> SignedIdentity:
        return require_user_identity_with_settings(settings, identity_payload, signature)

    router = APIRouter(prefix="/public/blog-posts")

    @router.get("/{slug}/social-stats")
    async def get_social_stats(
        slug: str,
        _identity: SignedIdentity = Depends(require_user),
    ) -> BlogSocialStats:
        post = blog_repo.get_by_slug(slug)
        if post is None:
            raise HTTPException(status_code=404, detail="Post not found")
        user_reactions = social_repo.get_user_reactions(post.id, _identity.user_id)
        return BlogSocialStats(
            post_id=post.id,
            reaction_counts=social_repo.get_reaction_counts(post.id),
            user_reactions=user_reactions,
            is_bookmarked=social_repo.is_bookmarked(post.id, _identity.user_id),
            comment_count=len(social_repo.list_comments(post.id, status="approved")),
        )

    @router.post("/{slug}/reactions")
    async def toggle_reaction(
        slug: str,
        body: ReactionCreate,
        _identity: SignedIdentity = Depends(require_user),
    ) -> BlogSocialStats:
        if body.emoji not in ALLOWED_EMOJIS:
            raise HTTPException(status_code=422, detail=f"Emoji must be one of: {', '.join(sorted(ALLOWED_EMOJIS))}")
        post = blog_repo.get_by_slug(slug)
        if post is None:
            raise HTTPException(status_code=404, detail="Post not found")
        social_repo.toggle_reaction(post.id, _identity.user_id, _identity.email, body.emoji)
        return BlogSocialStats(
            post_id=post.id,
            reaction_counts=social_repo.get_reaction_counts(post.id),
            user_reactions=social_repo.get_user_reactions(post.id, _identity.user_id),
            is_bookmarked=social_repo.is_bookmarked(post.id, _identity.user_id),
            comment_count=len(social_repo.list_comments(post.id, status="approved")),
        )

    @router.post("/{slug}/bookmarks")
    async def toggle_bookmark(
        slug: str,
        _identity: SignedIdentity = Depends(require_user),
    ) -> BlogSocialStats:
        post = blog_repo.get_by_slug(slug)
        if post is None:
            raise HTTPException(status_code=404, detail="Post not found")
        social_repo.toggle_bookmark(post.id, _identity.user_id, _identity.email)
        return BlogSocialStats(
            post_id=post.id,
            reaction_counts=social_repo.get_reaction_counts(post.id),
            user_reactions=social_repo.get_user_reactions(post.id, _identity.user_id),
            is_bookmarked=social_repo.is_bookmarked(post.id, _identity.user_id),
            comment_count=len(social_repo.list_comments(post.id, status="approved")),
        )

    @router.get("/{slug}/comments")
    async def list_comments(slug: str) -> list[BlogCommentPublic]:
        post = blog_repo.get_by_slug(slug)
        if post is None:
            raise HTTPException(status_code=404, detail="Post not found")
        comments = social_repo.list_comments(post.id, status="approved")
        result: list[BlogCommentPublic] = []
        for c in comments:
            profile = profile_repo.get_by_user_id(c.user_id) if profile_repo else None
            result.append(
                BlogCommentPublic(
                    id=c.id,
                    user_id=c.user_id,
                    user_name=profile.display_name if profile else c.user_name,
                    avatar_url=profile.avatar_url if profile else None,
                    content=c.content,
                    parent_id=c.parent_id,
                    created_at=c.created_at,
                    reaction_count=social_repo.get_comment_reaction_count(c.id),
                )
            )
        return result

    @router.post("/{slug}/comments")
    async def create_comment(
        slug: str,
        body: BlogCommentCreate,
        _identity: SignedIdentity = Depends(require_user),
    ) -> BlogComment:
        post = blog_repo.get_by_slug(slug)
        if post is None:
            raise HTTPException(status_code=404, detail="Post not found")
        if body.parent_id:
            parent = social_repo.get_comment_by_id(body.parent_id)
            if parent is None or parent.post_id != post.id:
                raise HTTPException(status_code=422, detail="Invalid parent comment")
        profile = profile_repo.get_or_create(
            _identity.user_id,
            default_name=default_name_from_identity(_identity),
        ) if profile_repo else None
        return social_repo.create_comment(
            post_id=post.id,
            user_id=_identity.user_id,
            user_email=_identity.email,
            user_name=profile.display_name if profile else (_identity.email.split("@")[0] if _identity.email else None),
            content=body.content,
            parent_id=body.parent_id,
        )

    # ── Comment reactions ──

    @router.post("/{slug}/comments/{comment_id}/react")
    async def toggle_comment_reaction(
        slug: str,
        comment_id: str,
        _identity: SignedIdentity = Depends(require_user),
    ) -> dict:
        post = blog_repo.get_by_slug(slug)
        if post is None:
            raise HTTPException(status_code=404, detail="Post not found")
        comment = social_repo.get_comment_by_id(comment_id)
        if comment is None or comment.post_id != post.id:
            raise HTTPException(status_code=404, detail="Comment not found")
        is_reacted = social_repo.toggle_comment_reaction(comment_id, _identity.user_id, _identity.email)
        return {
            "reacted": is_reacted,
            "count": social_repo.get_comment_reaction_count(comment_id),
        }

    # ── Comment edit/delete ──

    @router.patch("/{slug}/comments/{comment_id}")
    async def edit_comment(
        slug: str,
        comment_id: str,
        body: BlogCommentCreate,
        _identity: SignedIdentity = Depends(require_user),
    ) -> BlogCommentPublic:
        post = blog_repo.get_by_slug(slug)
        if post is None:
            raise HTTPException(status_code=404, detail="Post not found")
        comment = social_repo.get_comment_by_id(comment_id)
        if comment is None or comment.post_id != post.id:
            raise HTTPException(status_code=404, detail="Comment not found")
        if comment.user_id != _identity.user_id:
            raise HTTPException(status_code=403, detail="Not your comment")
        updated = social_repo.update_comment_content(comment_id, body.content)
        if updated is None:
            raise HTTPException(status_code=500, detail="Failed to update comment")
        profile = profile_repo.get_by_user_id(comment.user_id) if profile_repo else None
        return BlogCommentPublic(
            id=updated.id,
            user_id=updated.user_id,
            user_name=profile.display_name if profile else updated.user_name,
            avatar_url=profile.avatar_url if profile else None,
            content=updated.content,
            parent_id=updated.parent_id,
            created_at=updated.created_at,
            reaction_count=social_repo.get_comment_reaction_count(comment_id),
            user_reacted=social_repo.has_user_reacted_to_comment(comment_id, _identity.user_id),
        )

    @router.delete("/{slug}/comments/{comment_id}")
    async def delete_comment(
        slug: str,
        comment_id: str,
        _identity: SignedIdentity = Depends(require_user),
    ) -> dict:
        post = blog_repo.get_by_slug(slug)
        if post is None:
            raise HTTPException(status_code=404, detail="Post not found")
        comment = social_repo.get_comment_by_id(comment_id)
        if comment is None or comment.post_id != post.id:
            raise HTTPException(status_code=404, detail="Comment not found")
        if comment.user_id != _identity.user_id:
            raise HTTPException(status_code=403, detail="Not your comment")
        social_repo.delete_comment(comment_id)
        return {"deleted": True}

    @router.get("/{slug}/user-reactions")
    async def get_user_reactions(
        slug: str,
        _identity: SignedIdentity = Depends(require_user),
    ) -> list[str]:
        post = blog_repo.get_by_slug(slug)
        if post is None:
            raise HTTPException(status_code=404, detail="Post not found")
        return social_repo.get_user_reactions(post.id, _identity.user_id)

    return router


def create_blog_social_admin_routes(
    social_repo: BlogSocialRepository,
    blog_repo: BlogRepositoryProtocol,
    settings: Settings,
) -> APIRouter:
    """Admin routes for blog comment moderation."""

    def require_admin(
        identity_payload: Annotated[str | None, Header(alias=ADMIN_IDENTITY_HEADER)] = None,
        signature: Annotated[str | None, Header(alias=ADMIN_SIGNATURE_HEADER)] = None,
    ) -> SignedIdentity:
        return require_admin_identity_with_settings(settings, identity_payload, signature)

    router = APIRouter(prefix="/admin/blog-comments")

    @router.get("")
    async def admin_list_comments(
        status_filter: str | None = Query(None),
        _identity: SignedIdentity = Depends(require_admin),
    ) -> list[AdminCommentSummary]:
        comments = social_repo.admin_list_all_comments()
        if status_filter:
            comments = [c for c in comments if c.status == status_filter]
        return comments

    @router.post("/{comment_id}/approve")
    async def admin_approve_comment(
        comment_id: str,
        _identity: SignedIdentity = Depends(require_admin),
    ) -> AdminCommentSummary:
        comment = social_repo.set_comment_status(comment_id, "approved")
        if comment is None:
            raise HTTPException(status_code=404, detail="Comment not found")
        return AdminCommentSummary(
            id=comment.id,
            post_id=comment.post_id,
            user_id=comment.user_id,
            user_email=comment.user_email,
            user_name=comment.user_name,
            content=comment.content,
            status=comment.status,
            created_at=comment.created_at,
        )

    @router.post("/{comment_id}/reject")
    async def admin_reject_comment(
        comment_id: str,
        _identity: SignedIdentity = Depends(require_admin),
    ) -> AdminCommentSummary:
        comment = social_repo.set_comment_status(comment_id, "rejected")
        if comment is None:
            raise HTTPException(status_code=404, detail="Comment not found")
        return AdminCommentSummary(
            id=comment.id,
            post_id=comment.post_id,
            user_id=comment.user_id,
            user_email=comment.user_email,
            user_name=comment.user_name,
            content=comment.content,
            status=comment.status,
            created_at=comment.created_at,
        )

    return router


def create_user_bookmarks_routes(
    social_repo: BlogSocialRepository,
    blog_repo: BlogRepositoryProtocol,
    settings: Settings,
) -> APIRouter:
    """Authenticated user routes for managing bookmarks."""

    def require_user(
        identity_payload: Annotated[str | None, Header(alias=USER_IDENTITY_HEADER)] = None,
        signature: Annotated[str | None, Header(alias=USER_SIGNATURE_HEADER)] = None,
    ) -> SignedIdentity:
        return require_user_identity_with_settings(settings, identity_payload, signature)

    router = APIRouter(prefix="/user/bookmarks")

    @router.get("")
    async def list_bookmarks(
        _identity: SignedIdentity = Depends(require_user),
    ) -> list[BlogBookmark]:
        bookmarks = social_repo.list_user_bookmarks(_identity.user_id)
        # Enrich with post info
        for bm in bookmarks:
            post = blog_repo.get_by_id(bm.post_id)
            if post:
                bm.slug = post.slug
                bm.title = post.title
        return bookmarks

    @router.get("/check/{slug}")
    async def check_bookmark(
        slug: str,
        _identity: SignedIdentity = Depends(require_user),
    ) -> bool:
        post = blog_repo.get_by_slug(slug)
        if post is None:
            raise HTTPException(status_code=404, detail="Post not found")
        return social_repo.is_bookmarked(post.id, _identity.user_id)

    return router
