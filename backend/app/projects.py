"""Projects CRUD — follows Showcases pattern."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field
from sqlalchemy import Engine, insert, select, update

from backend.app.database import audit_events, projects

ProjectStatus = Literal["draft", "published"]


class Project(BaseModel):
    id: str
    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    title: str
    description: str
    content_markdown: str
    image_url: str | None = None
    status: ProjectStatus
    published_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ProjectCreate(BaseModel):
    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    title: str = Field(min_length=1, max_length=240)
    description: str = Field(min_length=1)
    content_markdown: str = Field(min_length=1)
    image_url: str | None = Field(default=None, max_length=2048)


class ProjectUpdate(BaseModel):
    slug: str | None = Field(default=None, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    title: str | None = Field(default=None, min_length=1, max_length=240)
    description: str | None = Field(default=None, min_length=1)
    content_markdown: str | None = Field(default=None, min_length=1)
    image_url: str | None = Field(default=None, max_length=2048)


class ProjectSummary(BaseModel):
    slug: str
    title: str
    description: str
    image_url: str | None = None
    published_at: datetime


class ProjectDetail(ProjectSummary):
    id: str
    content_markdown: str


class AdminProjectSummary(BaseModel):
    id: str
    slug: str
    title: str
    status: ProjectStatus
    published_at: datetime | None = None
    image_url: str | None = None


class AdminProjectDetail(AdminProjectSummary):
    description: str
    content_markdown: str


class ProjectAuditEvent(BaseModel):
    id: str
    actor_user_id: str
    actor_email: str
    action: str
    entity_type: str
    entity_id: str
    created_at: datetime


def _slugify(title: str) -> str:
    return title.lower().replace(" ", "-").replace("_", "-")


def _now() -> datetime:
    return datetime.now(UTC)


class InMemoryProjectRepository:
    def __init__(self) -> None:
        self.items: dict[str, Project] = {}

    def get_by_id(self, project_id: str) -> AdminProjectDetail | None:
        item = self.items.get(project_id)
        if item is None:
            return None
        return _to_admin_detail(item)

    def list_all(self) -> list[AdminProjectSummary]:
        items = sorted(
            self.items.values(),
            key=lambda item: item.published_at or datetime.min.replace(tzinfo=UTC),
            reverse=True,
        )
        return [_to_admin_summary(item) for item in items]

    def list_published(self) -> list[ProjectSummary]:
        items = [
            item for item in self.items.values()
            if item.status == "published" and item.published_at
        ]
        items.sort(
            key=lambda item: item.published_at or datetime.min.replace(tzinfo=UTC),
            reverse=True,
        )
        return [_to_public_summary(item) for item in items if item.published_at is not None]

    def get_published_by_slug(self, slug: str) -> ProjectDetail | None:
        for item in self.items.values():
            if item.slug == slug and item.status == "published" and item.published_at is not None:
                return _to_public_detail(item)
        return None

    def slug_exists(self, slug: str, exclude_id: str | None = None) -> bool:
        for item in self.items.values():
            if item.slug == slug and (exclude_id is None or item.id != exclude_id):
                return True
        return False

    def create(self, request: ProjectCreate) -> Project:
        now = _now()
        item = Project(
            id=f"project_{uuid4().hex}",
            slug=request.slug,
            title=request.title,
            description=request.description,
            content_markdown=request.content_markdown,
            image_url=request.image_url,
            status="draft",
            published_at=None,
            created_at=now,
            updated_at=now,
        )
        self.items[item.id] = item
        return item

    def update(self, project_id: str, request: ProjectUpdate) -> Project | None:
        item = self.items.get(project_id)
        if item is None:
            return None
        update_data = request.model_dump(exclude_unset=True)
        update_data["updated_at"] = _now()
        updated = item.model_copy(update=update_data)
        self.items[project_id] = updated
        return updated

    def publish(self, project_id: str) -> Project | None:
        item = self.items.get(project_id)
        if item is None:
            return None
        published = item.model_copy(update={"status": "published", "published_at": _now(), "updated_at": _now()})
        self.items[project_id] = published
        return published

    def unpublish(self, project_id: str) -> Project | None:
        item = self.items.get(project_id)
        if item is None:
            return None
        draft = item.model_copy(update={"status": "draft", "published_at": None, "updated_at": _now()})
        self.items[project_id] = draft
        return draft

    def record_audit(self, actor_user_id: str, actor_email: str, action: str, entity_id: str) -> ProjectAuditEvent:
        event = ProjectAuditEvent(
            id=f"audit_{uuid4().hex}",
            actor_user_id=actor_user_id,
            actor_email=actor_email,
            action=action,
            entity_type="project",
            entity_id=entity_id,
            created_at=_now(),
        )
        return event


class PostgresProjectRepository:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def get_by_id(self, project_id: str) -> AdminProjectDetail | None:
        with self.engine.begin() as connection:
            row = (
                connection.execute(select(projects).where(projects.c.id == project_id))
                .mappings()
                .first()
            )
            if row is None:
                return None
            return AdminProjectDetail.model_validate(dict(row))

    def list_all(self) -> list[AdminProjectSummary]:
        with self.engine.begin() as connection:
            rows = connection.execute(
                select(projects).order_by(projects.c.published_at.desc().nullslast())
            ).mappings()
            return [AdminProjectSummary.model_validate(dict(row)) for row in rows]

    def list_published(self) -> list[ProjectSummary]:
        with self.engine.begin() as connection:
            rows = connection.execute(
                select(projects)
                .where(projects.c.status == "published", projects.c.published_at.is_not(None))
                .order_by(projects.c.published_at.desc())
            ).mappings()
            return [ProjectSummary.model_validate(dict(row)) for row in rows]

    def get_published_by_slug(self, slug: str) -> ProjectDetail | None:
        with self.engine.begin() as connection:
            row = (
                connection.execute(
                    select(projects).where(
                        projects.c.slug == slug,
                        projects.c.status == "published",
                        projects.c.published_at.is_not(None),
                    )
                )
                .mappings()
                .first()
            )
            if row is None:
                return None
            return ProjectDetail.model_validate(dict(row))

    def slug_exists(self, slug: str, exclude_id: str | None = None) -> bool:
        with self.engine.begin() as connection:
            query = select(projects.c.id).where(projects.c.slug == slug)
            if exclude_id:
                query = query.where(projects.c.id != exclude_id)
            row = connection.execute(query).first()
            return row is not None

    def create(self, request: ProjectCreate) -> Project:
        now = _now()
        item = Project(
            id=f"project_{uuid4().hex}",
            **request.model_dump(),
            status="draft",
            published_at=None,
            created_at=now,
            updated_at=now,
        )
        with self.engine.begin() as connection:
            connection.execute(insert(projects).values(**item.model_dump()))
        return item

    def update(self, project_id: str, request: ProjectUpdate) -> Project | None:
        update_data = request.model_dump(exclude_unset=True)
        update_data["updated_at"] = _now()
        with self.engine.begin() as connection:
            existing = (
                connection.execute(select(projects).where(projects.c.id == project_id))
                .mappings()
                .first()
            )
            if existing is None:
                return None
            if update_data:
                connection.execute(update(projects).where(projects.c.id == project_id).values(**update_data))
            row = connection.execute(select(projects).where(projects.c.id == project_id)).mappings().one()
        return Project.model_validate(dict(row))

    def publish(self, project_id: str) -> Project | None:
        now = _now()
        with self.engine.begin() as connection:
            result = connection.execute(
                update(projects)
                .where(projects.c.id == project_id)
                .values(status="published", published_at=now, updated_at=now)
            )
            if result.rowcount == 0:
                return None
            row = connection.execute(select(projects).where(projects.c.id == project_id)).mappings().one()
        return Project.model_validate(dict(row))

    def unpublish(self, project_id: str) -> Project | None:
        now = _now()
        with self.engine.begin() as connection:
            result = connection.execute(
                update(projects)
                .where(projects.c.id == project_id)
                .values(status="draft", published_at=None, updated_at=now)
            )
            if result.rowcount == 0:
                return None
            row = connection.execute(select(projects).where(projects.c.id == project_id)).mappings().one()
        return Project.model_validate(dict(row))

    def record_audit(self, actor_user_id: str, actor_email: str, action: str, entity_id: str) -> ProjectAuditEvent:
        event = ProjectAuditEvent(
            id=f"audit_{uuid4().hex}",
            actor_user_id=actor_user_id,
            actor_email=actor_email,
            action=action,
            entity_type="project",
            entity_id=entity_id,
            created_at=_now(),
        )
        with self.engine.begin() as connection:
            connection.execute(insert(audit_events).values(**event.model_dump()))
        return event


def _to_admin_summary(item: Project) -> AdminProjectSummary:
    return AdminProjectSummary(
        id=item.id,
        slug=item.slug,
        title=item.title,
        status=item.status,
        published_at=item.published_at,
    )


def _to_admin_detail(item: Project) -> AdminProjectDetail:
    return AdminProjectDetail(
        id=item.id,
        slug=item.slug,
        title=item.title,
        status=item.status,
        published_at=item.published_at,
        description=item.description,
        content_markdown=item.content_markdown,
    )


def _to_public_summary(item: Project) -> ProjectSummary:
    assert item.published_at is not None
    return ProjectSummary(
        slug=item.slug,
        title=item.title,
        description=item.description,
        image_url=item.image_url,
        published_at=item.published_at,
    )


def _to_public_detail(item: Project) -> ProjectDetail:
    return ProjectDetail(
        **_to_public_summary(item).model_dump(),
        id=item.id,
        content_markdown=item.content_markdown,
    )
