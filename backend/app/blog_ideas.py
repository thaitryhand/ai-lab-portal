"""Blog Idea management for the AI Blog Agent.

Exposes:
- Pydantic models for API request/response.
- An in-memory repository for tests and a Postgres-backed repository.
- FastAPI route handlers registered by ``create_blog_idea_routes()``.
- Celery tasks that call the LLM service for idea and outline generation.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Annotated, Any, Literal, cast
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import Engine, insert, select, update

from backend.app.admin_boundary import (
    ADMIN_IDENTITY_HEADER,
    ADMIN_SIGNATURE_HEADER,
    AdminIdentity,
    require_admin_identity_with_settings,
)
from backend.app.ai_runs import AiRun, AiRunRepository
from backend.app.blog import BlogRepositoryProtocol
from backend.app.blog_claims import (
    BlogClaim,
    BlogClaimsRepository,
    BlogClaimUpdate,
    claims_from_extraction,
    extract_claims_with_llm,
    heuristic_claims_from_draft,
)
from backend.app.database import blog_ideas as blog_ideas_table
from backend.app.generation_jobs import (
    GenerationJob,
    GenerationJobRepository,
    GenerationStage,
)
from backend.app.llm.schemas import MarketingMetadata
from backend.app.settings import Settings


def marketing_metadata_for_storage(result: MarketingMetadata) -> dict:
    """Normalize LLM marketing output to the admin UI / publish contract."""
    excerpt = (result.excerpt or result.meta_description or "").strip()
    return {
        "seo_title": result.seo_title,
        "meta_description": result.meta_description,
        "excerpt": excerpt,
        "canonical_url": "",
        "social_headline": result.linkedin_post,
        "social_description": result.x_post,
        "cta_text": result.cta,
        "tags": [],
    }


IdeaSource = Literal["manual", "ai_generated"]
IdeaStatus = Literal["pending", "approved", "rejected"]
OutlineStatus = Literal["pending", "approved", "rejected"] | None

# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class OutlineSection(BaseModel):
    """A single section in a blog post outline."""

    section: str
    points: list[str]


class BlogIdea(BaseModel):
    """A blog idea with structured metadata and review state."""

    id: str
    title: str
    angle: str
    target_reader: str
    article_goal: str
    positioning_notes: list[str] = Field(default_factory=list)
    source: IdeaSource = "manual"
    source_project_context: dict | None = None
    status: IdeaStatus = "pending"
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    feedback: str | None = None
    outline_sections: list[OutlineSection] = Field(default_factory=list)
    outline_status: str | None = None
    draft_markdown: str | None = None
    draft_status: str | None = None
    technical_review: dict | None = None
    technical_review_status: str | None = None
    marketing_metadata: dict | None = None
    marketing_status: str | None = None
    published_blog_post_id: str | None = None
    created_at: datetime
    updated_at: datetime


class BlogIdeaCreate(BaseModel):
    """Manual creation payload."""

    title: str = Field(min_length=1, max_length=240)
    angle: str = Field(max_length=160)
    target_reader: str = Field(max_length=160)
    article_goal: str = Field(min_length=1)
    positioning_notes: list[str] = Field(default_factory=list)


class BlogIdeaUpdate(BaseModel):
    """Review update payload."""

    status: IdeaStatus | None = None
    feedback: str | None = None
    outline_status: str | None = None
    draft_status: str | None = None
    technical_review_status: str | None = None
    marketing_status: str | None = None


class BlogIdeaGenerateRequest(BaseModel):
    """Trigger AI idea generation from project context."""

    project_name: str = Field(min_length=1)
    project_summary: str = Field(min_length=1)
    ai_capabilities: str = ""
    technical_highlights: str = ""
    business_value: str = ""


class BlogIdeaGenerateOutlineRequest(BaseModel):
    """Trigger AI outline generation for an approved idea."""

    positioning_notes: list[str] = Field(default_factory=list)


class PublishFromIdeaResponse(BaseModel):
    """Result of bridging an approved idea into a published blog post."""

    blog_post_id: str
    slug: str
    already_linked: bool = False


class BlogIdeaSummary(BaseModel):
    """Lightweight view for list display."""

    id: str
    title: str
    angle: str
    source: IdeaSource
    status: IdeaStatus
    outline_status: str | None = None
    draft_status: str | None = None
    technical_review_status: str | None = None
    marketing_status: str | None = None
    created_at: datetime


# ---------------------------------------------------------------------------
# Repository
# ---------------------------------------------------------------------------


class BlogIdeaRepository:
    """In-memory blog idea repository for tests."""

    def __init__(self, ideas: list[BlogIdea] | None = None) -> None:
        self._ideas: dict[str, BlogIdea] = {i.id: i for i in (ideas or [])}

    def list_all(self) -> list[BlogIdeaSummary]:
        ideas = sorted(self._ideas.values(), key=lambda i: i.created_at, reverse=True)
        return [
            BlogIdeaSummary(
                id=i.id,
                title=i.title,
                angle=i.angle,
                source=i.source,
                status=i.status,
                outline_status=i.outline_status,
                draft_status=i.draft_status,
                technical_review_status=i.technical_review_status,
                marketing_status=i.marketing_status,
                created_at=i.created_at,
            )
            for i in ideas
        ]

    def get_by_id(self, idea_id: str) -> BlogIdea | None:
        return self._ideas.get(idea_id)

    def create(self, payload: BlogIdeaCreate) -> BlogIdea:
        now = datetime.now(UTC)
        idea = BlogIdea(
            id=f"idea_{uuid4().hex}",
            title=payload.title,
            angle=payload.angle,
            target_reader=payload.target_reader,
            article_goal=payload.article_goal,
            positioning_notes=payload.positioning_notes,
            source="manual",
            created_at=now,
            updated_at=now,
        )
        self._ideas[idea.id] = idea
        return idea

    def add_generated(
        self, payload: BlogIdeaCreate, context: dict | None = None
    ) -> BlogIdea:
        now = datetime.now(UTC)
        idea = BlogIdea(
            id=f"idea_{uuid4().hex}",
            title=payload.title,
            angle=payload.angle,
            target_reader=payload.target_reader,
            article_goal=payload.article_goal,
            positioning_notes=payload.positioning_notes,
            source="ai_generated",
            source_project_context=context,
            created_at=now,
            updated_at=now,
        )
        self._ideas[idea.id] = idea
        return idea

    def update(self, idea_id: str, payload: BlogIdeaUpdate) -> BlogIdea | None:
        idea = self._ideas.get(idea_id)
        if idea is None:
            return None
        updated = idea.model_copy(deep=True)
        if payload.status is not None:
            updated.status = payload.status
            if payload.status in ("approved", "rejected"):
                updated.reviewed_at = datetime.now(UTC)
                updated.reviewed_by = "admin"
        if payload.feedback is not None:
            updated.feedback = payload.feedback
        if payload.outline_status is not None:
            updated.outline_status = payload.outline_status
        if payload.draft_status is not None:
            updated.draft_status = payload.draft_status
        if payload.technical_review_status is not None:
            updated.technical_review_status = payload.technical_review_status
        if payload.marketing_status is not None:
            updated.marketing_status = payload.marketing_status
        updated.updated_at = datetime.now(UTC)
        self._ideas[idea_id] = updated
        return updated

    def set_outline(
        self,
        idea_id: str,
        sections: list[OutlineSection],
        status: str = "pending",
    ) -> BlogIdea | None:
        idea = self._ideas.get(idea_id)
        if idea is None:
            return None
        updated = idea.model_copy(deep=True)
        updated.outline_sections = sections
        updated.outline_status = status
        updated.updated_at = datetime.now(UTC)
        self._ideas[idea_id] = updated
        return updated

    def set_draft(
        self,
        idea_id: str,
        markdown: str,
        status: str = "pending",
    ) -> BlogIdea | None:
        idea = self._ideas.get(idea_id)
        if idea is None:
            return None
        updated = idea.model_copy(deep=True)
        updated.draft_markdown = markdown
        updated.draft_status = status
        updated.updated_at = datetime.now(UTC)
        self._ideas[idea_id] = updated
        return updated

    def set_technical_review(
        self,
        idea_id: str,
        review: dict,
        status: str = "pending",
    ) -> BlogIdea | None:
        idea = self._ideas.get(idea_id)
        if idea is None:
            return None
        updated = idea.model_copy(deep=True)
        updated.technical_review = review
        updated.technical_review_status = status
        updated.updated_at = datetime.now(UTC)
        self._ideas[idea_id] = updated
        return updated

    def set_marketing_metadata(
        self,
        idea_id: str,
        metadata: dict,
        status: str = "pending",
    ) -> BlogIdea | None:
        idea = self._ideas.get(idea_id)
        if idea is None:
            return None
        updated = idea.model_copy(deep=True)
        updated.marketing_metadata = metadata
        updated.marketing_status = status
        updated.updated_at = datetime.now(UTC)
        self._ideas[idea_id] = updated
        return updated

    def link_published_post(self, idea_id: str, post_id: str) -> BlogIdea | None:
        idea = self._ideas.get(idea_id)
        if idea is None:
            return None
        updated = idea.model_copy(deep=True)
        updated.published_blog_post_id = post_id
        updated.updated_at = datetime.now(UTC)
        self._ideas[idea_id] = updated
        return updated


class PostgresBlogIdeaRepository(BlogIdeaRepository):
    """Postgres-backed repository."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def list_all(self) -> list[BlogIdeaSummary]:
        with self._engine.connect() as conn:
            rows = conn.execute(
                select(
                    blog_ideas_table.c.id,
                    blog_ideas_table.c.title,
                    blog_ideas_table.c.angle,
                    blog_ideas_table.c.source,
                    blog_ideas_table.c.status,
                    blog_ideas_table.c.outline_status,
                    blog_ideas_table.c.draft_status,
                    blog_ideas_table.c.technical_review_status,
                    blog_ideas_table.c.marketing_status,
                    blog_ideas_table.c.created_at,
                ).order_by(blog_ideas_table.c.created_at.desc())
            ).mappings()
            return [BlogIdeaSummary(**row) for row in rows]

    def get_by_id(self, idea_id: str) -> BlogIdea | None:
        with self._engine.connect() as conn:
            row = (
                conn.execute(
                    select(blog_ideas_table).where(blog_ideas_table.c.id == idea_id)
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                return None
            return _row_to_idea(dict(row))

    def create(self, payload: BlogIdeaCreate) -> BlogIdea:
        now = datetime.now(UTC)
        data: dict = {
            "id": f"idea_{uuid4().hex}",
            "title": payload.title,
            "angle": payload.angle,
            "target_reader": payload.target_reader,
            "article_goal": payload.article_goal,
            "positioning_notes": (
                json.dumps(payload.positioning_notes)
                if payload.positioning_notes
                else None
            ),
            "source": "manual",
            "status": "pending",
            "created_at": now,
            "updated_at": now,
        }
        with self._engine.begin() as conn:
            conn.execute(insert(blog_ideas_table).values(**data))
        return BlogIdea(**{**data, "positioning_notes": payload.positioning_notes})

    def add_generated(
        self, payload: BlogIdeaCreate, context: dict | None = None
    ) -> BlogIdea:
        now = datetime.now(UTC)
        data: dict = {
            "id": f"idea_{uuid4().hex}",
            "title": payload.title,
            "angle": payload.angle,
            "target_reader": payload.target_reader,
            "article_goal": payload.article_goal,
            "positioning_notes": (
                json.dumps(payload.positioning_notes)
                if payload.positioning_notes
                else None
            ),
            "source_project_context": json.dumps(context) if context else None,
            "source": "ai_generated",
            "status": "pending",
            "created_at": now,
            "updated_at": now,
        }
        with self._engine.begin() as conn:
            conn.execute(insert(blog_ideas_table).values(**data))
        return BlogIdea(
            **{
                **data,
                "positioning_notes": payload.positioning_notes,
                "source_project_context": context,
            }
        )

    def update(self, idea_id: str, payload: BlogIdeaUpdate) -> BlogIdea | None:
        existing = self.get_by_id(idea_id)
        if existing is None:
            return None

        values: dict = {"updated_at": datetime.now(UTC)}
        if payload.status is not None:
            values["status"] = payload.status
            if payload.status in ("approved", "rejected"):
                values["reviewed_at"] = datetime.now(UTC)
                values["reviewed_by"] = "admin"
        if payload.feedback is not None:
            values["feedback"] = payload.feedback
        if payload.outline_status is not None:
            values["outline_status"] = payload.outline_status
        if payload.draft_status is not None:
            values["draft_status"] = payload.draft_status
        if payload.technical_review_status is not None:
            values["technical_review_status"] = payload.technical_review_status
        if payload.marketing_status is not None:
            values["marketing_status"] = payload.marketing_status

        with self._engine.begin() as conn:
            conn.execute(
                update(blog_ideas_table)
                .where(blog_ideas_table.c.id == idea_id)
                .values(**values)
            )
        return self.get_by_id(idea_id)

    def set_outline(
        self,
        idea_id: str,
        sections: list[OutlineSection],
        status: str = "pending",
    ) -> BlogIdea | None:
        existing = self.get_by_id(idea_id)
        if existing is None:
            return None
        values: dict = {
            "outline_sections": json.dumps([s.model_dump() for s in sections]),
            "outline_status": status,
            "updated_at": datetime.now(UTC),
        }
        with self._engine.begin() as conn:
            conn.execute(
                update(blog_ideas_table)
                .where(blog_ideas_table.c.id == idea_id)
                .values(**values)
            )
        return self.get_by_id(idea_id)

    def set_draft(
        self,
        idea_id: str,
        markdown: str,
        status: str = "pending",
    ) -> BlogIdea | None:
        existing = self.get_by_id(idea_id)
        if existing is None:
            return None
        values: dict = {
            "draft_markdown": markdown,
            "draft_status": status,
            "updated_at": datetime.now(UTC),
        }
        with self._engine.begin() as conn:
            conn.execute(
                update(blog_ideas_table)
                .where(blog_ideas_table.c.id == idea_id)
                .values(**values)
            )
        return self.get_by_id(idea_id)

    def set_technical_review(
        self,
        idea_id: str,
        review: dict,
        status: str = "pending",
    ) -> BlogIdea | None:
        existing = self.get_by_id(idea_id)
        if existing is None:
            return None
        values: dict = {
            "technical_review": json.dumps(review),
            "technical_review_status": status,
            "updated_at": datetime.now(UTC),
        }
        with self._engine.begin() as conn:
            conn.execute(
                update(blog_ideas_table)
                .where(blog_ideas_table.c.id == idea_id)
                .values(**values)
            )
        return self.get_by_id(idea_id)

    def set_marketing_metadata(
        self,
        idea_id: str,
        metadata: dict,
        status: str = "pending",
    ) -> BlogIdea | None:
        existing = self.get_by_id(idea_id)
        if existing is None:
            return None
        values: dict = {
            "marketing_metadata": json.dumps(metadata),
            "marketing_status": status,
            "updated_at": datetime.now(UTC),
        }
        with self._engine.begin() as conn:
            conn.execute(
                update(blog_ideas_table)
                .where(blog_ideas_table.c.id == idea_id)
                .values(**values)
            )
        return self.get_by_id(idea_id)

    def link_published_post(self, idea_id: str, post_id: str) -> BlogIdea | None:
        existing = self.get_by_id(idea_id)
        if existing is None:
            return None
        values: dict = {
            "published_blog_post_id": post_id,
            "updated_at": datetime.now(UTC),
        }
        with self._engine.begin() as conn:
            conn.execute(
                update(blog_ideas_table)
                .where(blog_ideas_table.c.id == idea_id)
                .values(**values)
            )
        return self.get_by_id(idea_id)


def _row_to_idea(row: dict) -> BlogIdea:
    data = dict(row)
    raw_pos = data.pop("positioning_notes", None)
    raw_ctx = data.pop("source_project_context", None)
    raw_outline = data.pop("outline_sections", None)
    raw_review = data.pop("technical_review", None)
    raw_marketing = data.pop("marketing_metadata", None)
    idea = BlogIdea(**data)
    if raw_pos:
        try:
            idea.positioning_notes = json.loads(raw_pos)
        except (json.JSONDecodeError, TypeError):
            pass
    if raw_ctx:
        try:
            idea.source_project_context = json.loads(raw_ctx)
        except (json.JSONDecodeError, TypeError):
            pass
    if raw_outline:
        try:
            parsed = json.loads(raw_outline)
            idea.outline_sections = [OutlineSection(**s) for s in parsed]
        except (json.JSONDecodeError, TypeError, Exception):
            pass
    if raw_review:
        try:
            idea.technical_review = json.loads(raw_review)
        except (json.JSONDecodeError, TypeError):
            pass
    if raw_marketing:
        try:
            idea.marketing_metadata = json.loads(raw_marketing)
        except (json.JSONDecodeError, TypeError):
            pass
    return idea


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


def _dispatch_generation_task(
    *,
    stage: GenerationStage,
    idea_id: str,
    celery_task_id: str,
    message: str,
    jobs_repository: GenerationJobRepository | None,
    track_job: bool,
) -> None:
    if track_job and jobs_repository is not None:
        jobs_repository.create_queued(
            blog_idea_id=idea_id,
            stage=stage,
            celery_task_id=celery_task_id,
        )
    raise HTTPException(
        status_code=202,
        detail={"task_id": celery_task_id, "message": message},
    )


def _dispatch_or_run_generation(
    repository: BlogIdeaRepository,
    task: Any,
    *,
    stage: GenerationStage,
    idea_id: str,
    message: str,
    jobs_repository: GenerationJobRepository | None,
    kwargs: dict[str, Any],
    settings: Settings,
) -> Any:
    """Queue Celery work for Postgres, or run inline for in-memory repositories."""
    if not isinstance(repository, PostgresBlogIdeaRepository):
        return cast(Any, task)(**kwargs)

    celery_task_id = f"celery_{uuid4().hex}"
    job_idea_id = idea_id if not idea_id.startswith("pending:") else f"pending:{celery_task_id}"
    if jobs_repository is not None:
        jobs_repository.create_queued(
            blog_idea_id=job_idea_id,
            stage=stage,
            celery_task_id=celery_task_id,
        )

    result = task.apply_async(kwargs=kwargs, task_id=celery_task_id)
    if settings.llm_e2e_fake and result.ready():
        if result.successful():
            return result.get()
        raise HTTPException(status_code=500, detail=str(result.result))

    raise HTTPException(
        status_code=202,
        detail={"task_id": celery_task_id, "message": message},
    )


def create_blog_idea_routes(
    repository: BlogIdeaRepository,
    settings: Settings,
    blog_repository: BlogRepositoryProtocol | None = None,
    record_blog_audit: Callable[[AdminIdentity, str, str], None] | None = None,
    jobs_repository: GenerationJobRepository | None = None,
    claims_repository: BlogClaimsRepository | None = None,
    ai_runs_repository: AiRunRepository | None = None,
) -> APIRouter:
    """Create a router with blog idea endpoints."""

    def require_identity(
        identity_payload: Annotated[
            str | None, Header(alias=ADMIN_IDENTITY_HEADER)
        ] = None,
        signature: Annotated[str | None, Header(alias=ADMIN_SIGNATURE_HEADER)] = None,
    ) -> AdminIdentity:
        return require_admin_identity_with_settings(
            settings, identity_payload, signature
        )

    router = APIRouter(prefix="/admin/blog-ideas")

    @router.get("/generation-jobs/{task_id}")
    async def get_generation_job(
        task_id: str,
        _identity: AdminIdentity = Depends(require_identity),
    ) -> GenerationJob:
        if jobs_repository is None:
            raise HTTPException(status_code=404, detail="Generation job not found")
        job = jobs_repository.get_by_celery_task_id(task_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Generation job not found")
        return job

    @router.patch("/claims/{claim_id}")
    async def update_claim(
        claim_id: str,
        payload: BlogClaimUpdate,
        _identity: AdminIdentity = Depends(require_identity),
    ) -> BlogClaim:
        if claims_repository is None:
            raise HTTPException(
                status_code=500, detail="Claims repository not configured"
            )
        updated = claims_repository.update(claim_id, payload)
        if updated is None:
            raise HTTPException(status_code=404, detail="Claim not found")
        return updated

    @router.get("")
    async def list_ideas(
        _identity: AdminIdentity = Depends(require_identity),
    ) -> list[BlogIdeaSummary]:
        return repository.list_all()

    @router.get("/{idea_id}")
    async def get_idea(
        idea_id: str,
        _identity: AdminIdentity = Depends(require_identity),
    ) -> BlogIdea:
        idea = repository.get_by_id(idea_id)
        if idea is None:
            raise HTTPException(status_code=404, detail="Blog idea not found")
        return idea

    @router.post("")
    async def create_idea(
        payload: BlogIdeaCreate,
        _identity: AdminIdentity = Depends(require_identity),
    ) -> BlogIdea:
        return repository.create(payload)

    @router.patch("/{idea_id}")
    async def update_idea(
        idea_id: str,
        payload: BlogIdeaUpdate,
        _identity: AdminIdentity = Depends(require_identity),
    ) -> BlogIdea:
        idea = repository.update(idea_id, payload)
        if idea is None:
            raise HTTPException(status_code=404, detail="Blog idea not found")
        return idea

    @router.post("/generate")
    async def generate_ideas(
        payload: BlogIdeaGenerateRequest,
        _identity: AdminIdentity = Depends(require_identity),
    ) -> BlogIdea | dict:
        """Generate one blog idea from project context using the LLM.

        In test/dev (in-memory repo) runs inline.
        In production dispatches a Celery task.
        """
        from backend.app.tasks import generate_blog_idea_task

        return _dispatch_or_run_generation(
            repository,
            generate_blog_idea_task,
            stage="idea",
            idea_id="pending:",
            message="Idea generation started",
            jobs_repository=jobs_repository,
            kwargs={
                "project_name": payload.project_name,
                "project_summary": payload.project_summary,
                "ai_capabilities": payload.ai_capabilities,
                "technical_highlights": payload.technical_highlights,
                "business_value": payload.business_value,
            },
            settings=settings,
        )

    @router.post("/{idea_id}/generate-outline")
    async def generate_outline(
        idea_id: str,
        payload: BlogIdeaGenerateOutlineRequest,
        _identity: AdminIdentity = Depends(require_identity),
    ) -> BlogIdea | dict:
        """Generate an outline for an approved idea.

        In test/dev runs inline; in production dispatches a Celery task.
        """
        idea = repository.get_by_id(idea_id)
        if idea is None:
            raise HTTPException(status_code=404, detail="Blog idea not found")
        if idea.status != "approved":
            raise HTTPException(
                status_code=400,
                detail="Outline generation requires an approved idea",
            )

        from backend.app.tasks import generate_blog_outline_task

        return _dispatch_or_run_generation(
            repository,
            generate_blog_outline_task,
            stage="outline",
            idea_id=idea_id,
            message="Outline generation started",
            jobs_repository=jobs_repository,
            kwargs={"idea_id": idea_id},
            settings=settings,
        )

    @router.post("/{idea_id}/generate-draft")
    async def generate_draft(
        idea_id: str,
        _identity: AdminIdentity = Depends(require_identity),
    ) -> BlogIdea | dict:
        """Generate a full markdown draft from an approved outline.

        In test/dev runs inline; in production dispatches a Celery task.
        """
        idea = repository.get_by_id(idea_id)
        if idea is None:
            raise HTTPException(status_code=404, detail="Blog idea not found")
        if idea.outline_status != "approved":
            raise HTTPException(
                status_code=400,
                detail="Draft generation requires an approved outline",
            )

        from backend.app.tasks import generate_blog_draft_task

        return _dispatch_or_run_generation(
            repository,
            generate_blog_draft_task,
            stage="draft",
            idea_id=idea_id,
            message="Draft generation started",
            jobs_repository=jobs_repository,
            kwargs={"idea_id": idea_id},
            settings=settings,
        )

    @router.post("/{idea_id}/review-technical")
    async def review_technical(
        idea_id: str,
        _identity: AdminIdentity = Depends(require_identity),
    ) -> BlogIdea | dict:
        """Run AI technical review on an approved draft.

        Requires draft_status == approved.
        In test/dev runs inline; in production dispatches a Celery task.
        """
        idea = repository.get_by_id(idea_id)
        if idea is None:
            raise HTTPException(status_code=404, detail="Blog idea not found")
        if idea.draft_status != "approved":
            raise HTTPException(
                status_code=400,
                detail="Technical review requires an approved draft",
            )

        from backend.app.tasks import generate_technical_review_task

        return _dispatch_or_run_generation(
            repository,
            generate_technical_review_task,
            stage="technical_review",
            idea_id=idea_id,
            message="Technical review started",
            jobs_repository=jobs_repository,
            kwargs={"idea_id": idea_id},
            settings=settings,
        )

    @router.post("/{idea_id}/generate-marketing")
    async def generate_marketing(
        idea_id: str,
        _identity: AdminIdentity = Depends(require_identity),
    ) -> BlogIdea | dict:
        """Generate SEO metadata and social snippets from an approved draft.

        Requires draft_status == approved.
        In test/dev runs inline; in production dispatches a Celery task.
        """
        idea = repository.get_by_id(idea_id)
        if idea is None:
            raise HTTPException(status_code=404, detail="Blog idea not found")
        if idea.draft_status != "approved":
            raise HTTPException(
                status_code=400,
                detail="Marketing generation requires an approved draft",
            )

        from backend.app.tasks import generate_marketing_metadata_task

        return _dispatch_or_run_generation(
            repository,
            generate_marketing_metadata_task,
            stage="marketing",
            idea_id=idea_id,
            message="Marketing metadata generation started",
            jobs_repository=jobs_repository,
            kwargs={"idea_id": idea_id},
            settings=settings,
        )

    @router.post("/{idea_id}/publish-to-blog")
    async def publish_to_blog(
        idea_id: str,
        identity: AdminIdentity = Depends(require_identity),
    ) -> PublishFromIdeaResponse:
        """Create and publish a blog post from a fully approved idea."""
        if blog_repository is None:
            raise HTTPException(
                status_code=500,
                detail="Blog repository is not configured for publish bridge",
            )
        from backend.app.blog_publish import publish_idea_to_blog

        post_id, slug, already_linked = publish_idea_to_blog(
            idea_id,
            repository,
            blog_repository,
            claims_repository=claims_repository,
        )
        if not already_linked and record_blog_audit is not None:
            record_blog_audit(identity, "blog_post.created", post_id)
            record_blog_audit(identity, "blog_post.published", post_id)
            record_blog_audit(identity, "blog_idea.published_to_blog", idea_id)
        return PublishFromIdeaResponse(
            blog_post_id=post_id,
            slug=slug,
            already_linked=already_linked,
        )

    @router.get("/{idea_id}/ai-runs")
    async def list_ai_runs(
        idea_id: str,
        _identity: AdminIdentity = Depends(require_identity),
    ) -> list[AiRun]:
        if ai_runs_repository is None:
            return []
        return ai_runs_repository.list_for_entity("blog_idea", idea_id)

    @router.get("/{idea_id}/claims")
    async def list_claims(
        idea_id: str,
        _identity: AdminIdentity = Depends(require_identity),
    ) -> list[BlogClaim]:
        if claims_repository is None:
            return []
        return claims_repository.list_for_idea(idea_id)

    @router.post("/{idea_id}/extract-claims")
    async def extract_claims(
        idea_id: str,
        _identity: AdminIdentity = Depends(require_identity),
    ) -> list[BlogClaim]:
        if claims_repository is None:
            raise HTTPException(
                status_code=500, detail="Claims repository not configured"
            )
        idea = repository.get_by_id(idea_id)
        if idea is None:
            raise HTTPException(status_code=404, detail="Blog idea not found")
        if not idea.draft_markdown:
            raise HTTPException(status_code=400, detail="Draft markdown is required")
        from backend.app.task_support import llm_service_for_idea

        try:
            service = llm_service_for_idea(idea_id)
            extraction = extract_claims_with_llm(idea, service)
            claims = claims_from_extraction(idea_id, extraction)
        except Exception:
            claims = heuristic_claims_from_draft(idea_id, idea.draft_markdown)
        return claims_repository.replace_for_idea(idea_id, claims)

    return router
