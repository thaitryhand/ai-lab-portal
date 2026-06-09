"""Custom event tracking module.

Tracks user interactions (clicks, shares, comments, scroll) beyond page views.
Provides CSV export for page views and events.
"""

from __future__ import annotations

import csv
import io
from abc import ABC, abstractmethod
from collections import Counter
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, Header, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import insert, select
from sqlalchemy.engine import Engine

from backend.app.admin_boundary import (
    ADMIN_IDENTITY_HEADER,
    ADMIN_SIGNATURE_HEADER,
    AdminIdentity,
    require_admin_identity_with_settings,
)
from backend.app.database import events as events_table, page_views as page_views_table
from backend.app.page_views import PageViewRepository
from backend.app.settings import Settings


# ── Models ──


class TrackEventRequest(BaseModel):
    path: str = Field(..., min_length=1, max_length=2048)
    event_type: str = Field(..., pattern=r"^(click|share|comment|scroll)$")
    event_metadata: str | None = Field(default=None, max_length=4096)
    session_id: str = Field(..., min_length=1, max_length=64)


class Event(BaseModel):
    id: str
    path: str
    event_type: str
    event_metadata: str | None = None
    session_id: str
    created_at: datetime


# ── Repository ──


class EventRepository(ABC):
    @abstractmethod
    def create(self, event: Event) -> Event: ...

    @abstractmethod
    def count_by_type(self, event_type: str, since: datetime | None = None) -> int: ...

    @abstractmethod
    def count_total(self, since: datetime | None = None) -> int: ...

    @abstractmethod
    def get_all_since(self, since: datetime | None = None) -> list[Event]: ...


class InMemoryEventRepository(EventRepository):
    def __init__(self) -> None:
        self._store: list[Event] = []

    def create(self, event: Event) -> Event:
        self._store.append(event)
        return event

    def count_by_type(self, event_type: str, since: datetime | None = None) -> int:
        return sum(
            1 for e in self._store
            if e.event_type == event_type and (since is None or e.created_at >= since)
        )

    def count_total(self, since: datetime | None = None) -> int:
        if since is None:
            return len(self._store)
        return sum(1 for e in self._store if e.created_at >= since)

    def get_all_since(self, since: datetime | None = None) -> list[Event]:
        if since is None:
            return list(self._store)
        return [e for e in self._store if e.created_at >= since]


class PostgresEventRepository(EventRepository):
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def create(self, event: Event) -> Event:
        with self.engine.begin() as conn:
            conn.execute(insert(events_table).values(**event.model_dump()))
        return event

    def count_by_type(self, event_type: str, since: datetime | None = None) -> int:
        from sqlalchemy import func
        with self.engine.begin() as conn:
            query = select(func.count()).select_from(events_table).where(
                events_table.c.event_type == event_type
            )
            if since:
                query = query.where(events_table.c.created_at >= since)
            return conn.execute(query).scalar() or 0

    def count_total(self, since: datetime | None = None) -> int:
        from sqlalchemy import func
        with self.engine.begin() as conn:
            query = select(func.count()).select_from(events_table)
            if since:
                query = query.where(events_table.c.created_at >= since)
            return conn.execute(query).scalar() or 0

    def get_all_since(self, since: datetime | None = None) -> list[Event]:
        with self.engine.begin() as conn:
            query = select(events_table)
            if since:
                query = query.where(events_table.c.created_at >= since)
            query = query.order_by(events_table.c.created_at.desc())
            rows = conn.execute(query).mappings().fetchall()
            return [
                Event(
                    id=r["id"],
                    path=r["path"],
                    event_type=r["event_type"],
                    event_metadata=r.get("event_metadata"),
                    session_id=r["session_id"],
                    created_at=r["created_at"],
                )
                for r in rows
            ]


# ── CSV Export ──


def _export_page_views_csv(repo: PageViewRepository, since: datetime) -> str:
    """Generate CSV string of page views since given timestamp."""
    # Use the repo's internal data if available
    if hasattr(repo, "_store") and isinstance(repo._store, list):
        views = [v for v in repo._store if v.created_at >= since]
    else:
        views = []

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "path", "referrer", "session_id", "ip_hash", "viewport_width", "viewport_height", "created_at"])
    for v in views:
        writer.writerow([
            v.id, v.path, v.referrer or "", v.session_id,
            v.ip_hash or "", v.viewport_width or "", v.viewport_height or "",
            v.created_at.isoformat(),
        ])
    return output.getvalue()


def _export_events_csv(repo: EventRepository, since: datetime, event_type: str | None = None) -> str:
    """Generate CSV string of events since given timestamp."""
    events = repo.get_all_since(since)
    if event_type:
        events = [e for e in events if e.event_type == event_type]

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "path", "event_type", "event_metadata", "session_id", "created_at"])
    for e in events:
        writer.writerow([
            e.id, e.path, e.event_type, e.event_metadata or "",
            e.session_id, e.created_at.isoformat(),
        ])
    return output.getvalue()


# ── Router Factory ──


def create_event_routes(
    event_repo: EventRepository,
    page_view_repo: PageViewRepository,
    settings: Settings,
) -> APIRouter:
    def require_admin(
        identity_payload: str | None = Header(default=None, alias=ADMIN_IDENTITY_HEADER),
        signature: str | None = Header(default=None, alias=ADMIN_SIGNATURE_HEADER),
    ) -> AdminIdentity:
        return require_admin_identity_with_settings(settings, identity_payload, signature)

    router = APIRouter(tags=["events"])

    # ── Public track event endpoint ──

    @router.post("/api/track-event")
    async def track_event(
        payload: TrackEventRequest,
        background_tasks: BackgroundTasks,
    ) -> dict:
        """Record a custom event. Public endpoint, no auth required."""
        event = Event(
            id=str(uuid4()),
            path=payload.path,
            event_type=payload.event_type,
            event_metadata=payload.event_metadata,
            session_id=payload.session_id,
            created_at=datetime.now(UTC),
        )
        background_tasks.add_task(event_repo.create, event)
        return {"ok": True}

    # ── Admin CSV export endpoints ──

    @router.get("/admin/analytics/export/views")
    async def export_views_csv(
        from_days: int = Query(30, ge=1, le=365, alias="from"),
        _identity: AdminIdentity = Depends(require_admin),
    ) -> str:
        """Export page views as CSV for the last N days."""
        since = datetime.now(UTC) - timedelta(days=from_days)
        return _export_page_views_csv(page_view_repo, since)

    @router.get("/admin/analytics/export/events")
    async def export_events_csv(
        from_days: int = Query(30, ge=1, le=365, alias="from"),
        event_type: str | None = Query(None, pattern=r"^(click|share|comment|scroll)$"),
        _identity: AdminIdentity = Depends(require_admin),
    ) -> str:
        """Export events as CSV for the last N days, optionally filtered by type."""
        since = datetime.now(UTC) - timedelta(days=from_days)
        return _export_events_csv(event_repo, since, event_type=event_type)

    return router
