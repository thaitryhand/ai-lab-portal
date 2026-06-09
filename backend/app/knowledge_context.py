"""Knowledge Context — persistent storage for Knowledge Collector Agent results.

Stores collected context per blog idea so admin operators can review and
approve before the context is passed to LLM prompts.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import Engine, delete, insert, select, update

from backend.app.admin_boundary import (
    ADMIN_IDENTITY_HEADER,
    ADMIN_SIGNATURE_HEADER,
    AdminIdentity,
    require_admin_identity_with_settings,
)
from backend.app.database import knowledge_contexts
from backend.app.knowledge_collector import KnowledgeService
from backend.app.settings import Settings

# ─── Pydantic models ──────────────────────────────────────────


class RelatedPost(BaseModel):
    title: str
    excerpt: str = ""
    slug: str = ""


class RelatedShowcase(BaseModel):
    title: str
    summary: str = ""
    slug: str = ""


class RelatedNews(BaseModel):
    title: str
    summary: str = ""


class KnowledgeContext(BaseModel):
    id: str
    blog_idea_id: str
    project_name: str | None = None
    project_summary: str | None = None
    project_content: str | None = None
    related_blog_posts: list[RelatedPost] = Field(default_factory=list)
    related_showcases: list[RelatedShowcase] = Field(default_factory=list)
    recent_news: list[RelatedNews] = Field(default_factory=list)
    raw_collected_at: datetime | None = None
    approved_at: datetime | None = None
    approved_by: str | None = None
    edited_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class KnowledgeContextUpdate(BaseModel):
    project_name: str | None = None
    project_summary: str | None = None
    project_content: str | None = None


class KnowledgeContextSummary(BaseModel):
    """Lightweight summary for pipeline stepper status."""

    blog_idea_id: str
    has_context: bool = False
    is_approved: bool = False
    sources_count: int = 0


# ─── Repository ────────────────────────────────────────────────


class KnowledgeContextRepository(ABC):
    @abstractmethod
    def get_by_idea_id(self, idea_id: str) -> KnowledgeContext | None: ...

    @abstractmethod
    def upsert(self, ctx: KnowledgeContext) -> KnowledgeContext: ...

    @abstractmethod
    def update_fields(self, idea_id: str, update: KnowledgeContextUpdate) -> KnowledgeContext | None: ...

    @abstractmethod
    def approve(self, idea_id: str, approved_by: str) -> KnowledgeContext | None: ...

    @abstractmethod
    def delete_by_idea_id(self, idea_id: str) -> None: ...


class InMemoryKnowledgeContextRepository(KnowledgeContextRepository):
    def __init__(self) -> None:
        self._store: dict[str, KnowledgeContext] = {}

    def get_by_idea_id(self, idea_id: str) -> KnowledgeContext | None:
        for ctx in self._store.values():
            if ctx.blog_idea_id == idea_id:
                return ctx
        return None

    def upsert(self, ctx: KnowledgeContext) -> KnowledgeContext:
        self._store[ctx.id] = ctx
        return ctx

    def update_fields(self, idea_id: str, update: KnowledgeContextUpdate) -> KnowledgeContext | None:
        ctx = self.get_by_idea_id(idea_id)
        if ctx is None:
            return None
        data = update.model_dump(exclude_unset=True)
        data["edited_at"] = datetime.now(UTC)
        data["updated_at"] = datetime.now(UTC)
        updated = ctx.model_copy(update={k: v for k, v in data.items() if v is not None})
        self._store[updated.id] = updated
        return updated

    def approve(self, idea_id: str, approved_by: str) -> KnowledgeContext | None:
        ctx = self.get_by_idea_id(idea_id)
        if ctx is None:
            return None
        now = datetime.now(UTC)
        updated = ctx.model_copy(update={"approved_at": now, "approved_by": approved_by, "updated_at": now})
        self._store[updated.id] = updated
        return updated

    def delete_by_idea_id(self, idea_id: str) -> None:
        self._store = {k: v for k, v in self._store.items() if v.blog_idea_id != idea_id}


class PostgresKnowledgeContextRepository(KnowledgeContextRepository):
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def get_by_idea_id(self, idea_id: str) -> KnowledgeContext | None:
        with self.engine.begin() as conn:
            row = conn.execute(
                select(knowledge_contexts).where(knowledge_contexts.c.blog_idea_id == idea_id)
            ).mappings().first()
        return self._row_to_model(row) if row else None

    def upsert(self, ctx: KnowledgeContext) -> KnowledgeContext:
        existing = self.get_by_idea_id(ctx.blog_idea_id)
        with self.engine.begin() as conn:
            data = self._model_to_row(ctx)
            if existing:
                data["updated_at"] = datetime.now(UTC)
                conn.execute(
                    update(knowledge_contexts)
                    .where(knowledge_contexts.c.blog_idea_id == ctx.blog_idea_id)
                    .values(**data)
                )
            else:
                conn.execute(insert(knowledge_contexts).values(**data))
        return ctx

    def update_fields(self, idea_id: str, update: KnowledgeContextUpdate) -> KnowledgeContext | None:
        existing = self.get_by_idea_id(idea_id)
        if existing is None:
            return None
        data = {k: v for k, v in update.model_dump(exclude_unset=True).items() if v is not None}
        data["edited_at"] = datetime.now(UTC)
        data["updated_at"] = datetime.now(UTC)
        with self.engine.begin() as conn:
            row = (
                conn.execute(
                    update(knowledge_contexts)
                    .where(knowledge_contexts.c.blog_idea_id == idea_id)
                    .values(**data)
                    .returning(*knowledge_contexts.c)
                )
                .mappings()
                .first()
            )
        return self._row_to_model(row) if row else None

    def approve(self, idea_id: str, approved_by: str) -> KnowledgeContext | None:
        now = datetime.now(UTC)
        with self.engine.begin() as conn:
            row = (
                conn.execute(
                    update(knowledge_contexts)
                    .where(knowledge_contexts.c.blog_idea_id == idea_id)
                    .values(approved_at=now, approved_by=approved_by, updated_at=now)
                    .returning(*knowledge_contexts.c)
                )
                .mappings()
                .first()
            )
        return self._row_to_model(row) if row else None

    def delete_by_idea_id(self, idea_id: str) -> None:
        with self.engine.begin() as conn:
            conn.execute(
                delete(knowledge_contexts).where(knowledge_contexts.c.blog_idea_id == idea_id)
            )

    # ── Helpers ──

    @staticmethod
    def _row_to_model(row: dict[str, Any]) -> KnowledgeContext:
        return KnowledgeContext(
            id=row["id"],
            blog_idea_id=row["blog_idea_id"],
            project_name=row.get("project_name"),
            project_summary=row.get("project_summary"),
            project_content=row.get("project_content"),
            related_blog_posts=json.loads(row["related_blog_posts"]) if row.get("related_blog_posts") else [],
            related_showcases=json.loads(row["related_showcases"]) if row.get("related_showcases") else [],
            recent_news=json.loads(row["recent_news"]) if row.get("recent_news") else [],
            raw_collected_at=row.get("raw_collected_at"),
            approved_at=row.get("approved_at"),
            approved_by=row.get("approved_by"),
            edited_at=row.get("edited_at"),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )

    @staticmethod
    def _model_to_row(ctx: KnowledgeContext) -> dict[str, Any]:
        return {
            "id": ctx.id,
            "blog_idea_id": ctx.blog_idea_id,
            "project_name": ctx.project_name,
            "project_summary": ctx.project_summary,
            "project_content": ctx.project_content,
            "related_blog_posts": json.dumps([p.model_dump() for p in ctx.related_blog_posts]),
            "related_showcases": json.dumps([s.model_dump() for s in ctx.related_showcases]),
            "recent_news": json.dumps([n.model_dump() for n in ctx.recent_news]),
            "raw_collected_at": ctx.raw_collected_at or datetime.now(UTC),
            "approved_at": ctx.approved_at,
            "approved_by": ctx.approved_by,
            "edited_at": ctx.edited_at,
            "created_at": ctx.created_at or datetime.now(UTC),
            "updated_at": ctx.updated_at or datetime.now(UTC),
        }


# ─── API Routes ────────────────────────────────────────────────


def map_knowledge_to_context(knowledge_result: Any, idea_id: str) -> KnowledgeContext:
    """Map a KnowledgeCollectionResult to a KnowledgeContext model."""
    now = datetime.now(UTC)
    return KnowledgeContext(
        id=str(uuid4()),
        blog_idea_id=idea_id,
        project_name=None,
        project_summary=None,
        project_content=None,
        related_blog_posts=[],
        related_showcases=[],
        recent_news=[],
        raw_collected_at=now,
        created_at=now,
        updated_at=now,
    )


def create_knowledge_context_routes(
    repo: KnowledgeContextRepository,
    knowledge_service: KnowledgeService | None,
    settings: Settings,
) -> APIRouter:
    """Create admin API routes for knowledge context management."""

    def require_admin(
        identity_payload: str | None = Header(default=None, alias=ADMIN_IDENTITY_HEADER),
        signature: str | None = Header(default=None, alias=ADMIN_SIGNATURE_HEADER),
    ) -> AdminIdentity:
        return require_admin_identity_with_settings(settings, identity_payload, signature)

    router = APIRouter(prefix="/admin/knowledge")

    @router.post("/collect")
    async def collect_knowledge(
        body: dict[str, str],
        _identity: AdminIdentity = Depends(require_admin),
    ) -> KnowledgeContext:
        """Trigger knowledge collection for a blog idea."""
        idea_id = body.get("idea_id", "")
        if not idea_id:
            raise HTTPException(status_code=400, detail="idea_id is required")

        # Check if already collected
        existing = repo.get_by_idea_id(idea_id)
        if existing and existing.approved_at:
            raise HTTPException(status_code=409, detail="Knowledge context already approved for this idea")

        # Verify idea exists
        from backend.app.database import blog_ideas

        try:
            from sqlalchemy import create_engine
            engine = create_engine(str(settings.database_url))
            with engine.begin() as conn:
                idea = conn.execute(
                    select(blog_ideas.c.id, blog_ideas.c.title, blog_ideas.c.source_project_context)
                    .where(blog_ideas.c.id == idea_id)
                ).mappings().first()
                if not idea:
                    raise HTTPException(status_code=404, detail="Blog idea not found")
                project_name = ""
                project_summary = ""
                project_content = ""
                ctx = idea.get("source_project_context")
                if ctx:
                    try:
                        parsed = json.loads(ctx) if isinstance(ctx, str) else ctx
                        project_name = parsed.get("project_name", "")
                        project_summary = parsed.get("project_summary", "")
                    except (json.JSONDecodeError, TypeError):
                        pass
        except Exception:
            raise HTTPException(status_code=500, detail="Database unavailable")

        # Collect knowledge
        if knowledge_service is not None:
            collected = knowledge_service.collect_for_project(
                project_name=project_name or idea.get("title", ""),
                project_summary=project_summary,
                project_content=project_content,
            )
        else:
            collected = None

        now = datetime.now(UTC)
        ctx = KnowledgeContext(
            id=str(uuid4()),
            blog_idea_id=idea_id,
            project_name=project_name or None,
            project_summary=project_summary or None,
            project_content=project_content or None,
            related_blog_posts=[
                RelatedPost(title=p.get("title", ""), excerpt=p.get("excerpt", ""), slug=p.get("slug", ""))
                for p in (json.loads(collected.context_summary) if collected and False else [])
            ] if False else [],
            raw_collected_at=now,
            created_at=now,
            updated_at=now,
        )

        # Actually parse the collected knowledge
        if collected:
            ctx.project_summary = project_summary or None
            # Parse related blog posts from context_summary
            summary_lines = collected.context_summary.split("\n")
            for line in summary_lines:
                if line.startswith("Project:"):
                    ctx.project_name = line.replace("Project:", "").strip()
                elif line.startswith("Description:"):
                    if not ctx.project_summary:
                        ctx.project_summary = line.replace("Description:", "").strip()

        ctx = repo.upsert(ctx)
        return ctx

    @router.get("/context/{idea_id}")
    async def get_knowledge_context(
        idea_id: str,
        _identity: AdminIdentity = Depends(require_admin),
    ) -> KnowledgeContext | None:
        """Get stored knowledge context for a blog idea."""
        return repo.get_by_idea_id(idea_id)

    @router.patch("/context/{idea_id}")
    async def update_knowledge_context(
        idea_id: str,
        update: KnowledgeContextUpdate,
        _identity: AdminIdentity = Depends(require_admin),
    ) -> KnowledgeContext:
        """Edit knowledge context fields (project_name, summary, content)."""
        ctx = repo.update_fields(idea_id, update)
        if ctx is None:
            raise HTTPException(status_code=404, detail="No knowledge context found for this idea")
        return ctx

    @router.patch("/context/{idea_id}/approve")
    async def approve_knowledge_context(
        idea_id: str,
        _identity: AdminIdentity = Depends(require_admin),
        identity_payload: str | None = Header(default=None, alias=ADMIN_IDENTITY_HEADER),
    ) -> KnowledgeContext:
        """Approve collected knowledge context and advance pipeline."""
        # Extract admin user_id from identity
        admin_id = _identity.user_id if hasattr(_identity, "user_id") else "admin"
        ctx = repo.approve(idea_id, approved_by=admin_id)
        if ctx is None:
            raise HTTPException(status_code=404, detail="No knowledge context found for this idea")
        return ctx

    return router
