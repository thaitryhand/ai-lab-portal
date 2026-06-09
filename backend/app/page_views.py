"""Page view tracking module.

Provides:
- PageViewCreate / PageView models
- PageViewRepository ABC (InMemory + Postgres)
- FastAPI router for POST /api/page-view (public, no auth)
"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Request
from pydantic import BaseModel, Field
from sqlalchemy import insert, select
from sqlalchemy.engine import Engine

from backend.app.database import page_views as page_views_table


# ── Models ──


class PageViewCreate(BaseModel):
    """Payload for recording a page view."""

    path: str = Field(..., min_length=1, max_length=2048)
    referrer: str | None = None
    session_id: str = Field(..., min_length=1, max_length=64)
    viewport_width: int | None = None
    viewport_height: int | None = None


class PageView(PageViewCreate):
    """Full page view record as stored."""

    id: str
    ip_hash: str | None = None
    user_agent: str | None = None
    created_at: datetime


# ── In-memory store for rate limiting ──

_recent_views: dict[str, datetime] = {}  # session_id:path -> last_viewed_at


def _check_throttle(session_id: str, path: str, window_seconds: int = 30) -> bool:
    """Return True if this view should be allowed (not throttled)."""
    key = f"{session_id}:{path}"
    now = datetime.now(UTC)
    last = _recent_views.get(key)
    if last and (now - last) < timedelta(seconds=window_seconds):
        return False
    _recent_views[key] = now
    # Cleanup old entries every 100 requests
    if len(_recent_views) > 1000:
        cutoff = now - timedelta(seconds=window_seconds)
        _recent_views.clear()
    return True


# ── Repository ──


class PageViewRepository(ABC):
    @abstractmethod
    def create(self, view: PageView) -> PageView: ...

    @abstractmethod
    def count_by_path(self, path: str, since: datetime | None = None) -> int: ...

    @abstractmethod
    def count_total(self, since: datetime | None = None) -> int: ...

    @abstractmethod
    def distinct_sessions(self, since: datetime | None = None) -> int: ...

    @abstractmethod
    def top_paths(self, since: datetime | None = None, limit: int = 10) -> list[dict]:
        """Return top paths sorted by view count descending.
        Each dict: {"path": str, "views": int}
        """
        ...

    @abstractmethod
    def daily_counts(self, since: datetime | None = None, days: int = 30) -> list[dict]:
        """Return view counts grouped by day.
        Each dict: {"date": "YYYY-MM-DD", "views": int}
        """
        ...

    @abstractmethod
    def top_referrers(self, since: datetime | None = None, limit: int = 10) -> list[dict]:
        """Return top referrers sorted by view count descending.
        Each dict: {"referrer": str, "views": int}
        """
        ...


class InMemoryPageViewRepository(PageViewRepository):
    def __init__(self) -> None:
        self._store: list[PageView] = []

    def create(self, view: PageView) -> PageView:
        self._store.append(view)
        return view

    def count_by_path(self, path: str, since: datetime | None = None) -> int:
        return sum(
            1 for v in self._store
            if v.path == path and (since is None or v.created_at >= since)
        )

    def count_total(self, since: datetime | None = None) -> int:
        if since is None:
            return len(self._store)
        return sum(1 for v in self._store if v.created_at >= since)

    def distinct_sessions(self, since: datetime | None = None) -> int:
        sessions = {
            v.session_id for v in self._store
            if since is None or v.created_at >= since
        }
        return len(sessions)

    def top_paths(self, since: datetime | None = None, limit: int = 10) -> list[dict]:
        counts: dict[str, int] = {}
        for v in self._store:
            if since is None or v.created_at >= since:
                counts[v.path] = counts.get(v.path, 0) + 1
        sorted_items = sorted(counts.items(), key=lambda x: -x[1])
        return [{"path": p, "views": c} for p, c in sorted_items[:limit]]

    def daily_counts(self, since: datetime | None = None, days: int = 30) -> list[dict]:
        counts: dict[str, int] = {}
        for v in self._store:
            if since is None or v.created_at >= since:
                date_key = v.created_at.strftime("%Y-%m-%d")
                counts[date_key] = counts.get(date_key, 0) + 1
        # Fill in all days, even those with zero views
        now = datetime.now(UTC)
        result = []
        for i in range(days):
            d = (now - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d")
            result.append({"date": d, "views": counts.get(d, 0)})
        return result

    def top_referrers(self, since: datetime | None = None, limit: int = 10) -> list[dict]:
        counts: dict[str, int] = {}
        for v in self._store:
            if since is None or v.created_at >= since:
                ref = v.referrer or "(direct)"
                counts[ref] = counts.get(ref, 0) + 1
        sorted_items = sorted(counts.items(), key=lambda x: -x[1])
        return [{"referrer": r, "views": c} for r, c in sorted_items[:limit]]


class PostgresPageViewRepository(PageViewRepository):
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def create(self, view: PageView) -> PageView:
        with self.engine.begin() as conn:
            conn.execute(
                insert(page_views_table).values(**view.model_dump())
            )
        return view

    def count_by_path(self, path: str, since: datetime | None = None) -> int:
        with self.engine.begin() as conn:
            from sqlalchemy import func
            query = select(func.count()).select_from(page_views_table).where(
                page_views_table.c.path == path
            )
            if since:
                query = query.where(page_views_table.c.created_at >= since)
            return conn.execute(query).scalar() or 0

    def count_total(self, since: datetime | None = None) -> int:
        with self.engine.begin() as conn:
            from sqlalchemy import func
            query = select(func.count()).select_from(page_views_table)
            if since:
                query = query.where(page_views_table.c.created_at >= since)
            return conn.execute(query).scalar() or 0

    def distinct_sessions(self, since: datetime | None = None) -> int:
        with self.engine.begin() as conn:
            from sqlalchemy import func
            query = select(func.count(func.distinct(page_views_table.c.session_id)))
            if since:
                query = query.where(page_views_table.c.created_at >= since)
            return conn.execute(query).scalar() or 0

    def top_paths(self, since: datetime | None = None, limit: int = 10) -> list[dict]:
        with self.engine.begin() as conn:
            from sqlalchemy import func
            query = (
                select(page_views_table.c.path, func.count().label("views"))
                .group_by(page_views_table.c.path)
                .order_by(func.count().desc())
                .limit(limit)
            )
            if since:
                query = query.where(page_views_table.c.created_at >= since)
            rows = conn.execute(query).mappings().fetchall()
            return [{"path": r["path"], "views": r["views"]} for r in rows]

    def daily_counts(self, since: datetime | None = None, days: int = 30) -> list[dict]:
        with self.engine.begin() as conn:
            from sqlalchemy import func, cast, Date
            query = (
                select(
                    cast(page_views_table.c.created_at, Date).label("date"),
                    func.count().label("views"),
                )
                .group_by(cast(page_views_table.c.created_at, Date))
                .order_by(cast(page_views_table.c.created_at, Date))
            )
            if since:
                query = query.where(page_views_table.c.created_at >= since)
            rows = conn.execute(query).mappings().fetchall()
            row_map = {r["date"].isoformat() if hasattr(r["date"], "isoformat") else str(r["date"]): r["views"] for r in rows}
            # Fill in all days
            now = datetime.now(UTC)
            result = []
            for i in range(days):
                d = (now - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d")
                result.append({"date": d, "views": row_map.get(d, 0)})
            return result

    def top_referrers(self, since: datetime | None = None, limit: int = 10) -> list[dict]:
        with self.engine.begin() as conn:
            from sqlalchemy import func, case
            # Treat NULL referrer as "(direct)"
            ref_col = func.coalesce(page_views_table.c.referrer, "(direct)")
            query = (
                select(ref_col.label("referrer"), func.count().label("views"))
                .group_by(ref_col)
                .order_by(func.count().desc())
                .limit(limit)
            )
            if since:
                query = query.where(page_views_table.c.created_at >= since)
            rows = conn.execute(query).mappings().fetchall()
            return [{"referrer": r["referrer"], "views": r["views"]} for r in rows]


# ── Router ──

_repo: PageViewRepository | None = None


def _get_repo() -> PageViewRepository:
    """Lazy-init with a module-level default (InMemory for convenience)."""
    global _repo
    if _repo is None:
        _repo = InMemoryPageViewRepository()
    return _repo


def set_repository(repo: PageViewRepository) -> None:
    """Override the default repository (used by main.py to inject DB-backed repo)."""
    global _repo
    _repo = repo


def _hash_ip(ip: str) -> str:
    """SHA-256 hash an IP address for privacy-safe storage."""
    return hashlib.sha256(ip.encode()).hexdigest()


router = APIRouter(prefix="/api", tags=["page-views"])


@router.post("/page-view")
async def record_page_view(
    payload: PageViewCreate,
    request: Request,
    background_tasks: BackgroundTasks,
) -> dict:
    """Record a page view. Public endpoint, no auth required."""
    # Client-side throttle is primary; server-side as safety net
    if not _check_throttle(payload.session_id, payload.path):
        return {"ok": True, "throttled": True}

    ip_hash = _hash_ip(request.client.host) if request.client else None
    user_agent = request.headers.get("user-agent")

    view = PageView(
        id=str(uuid4()),
        path=payload.path,
        referrer=payload.referrer,
        session_id=payload.session_id,
        viewport_width=payload.viewport_width,
        viewport_height=payload.viewport_height,
        ip_hash=ip_hash,
        user_agent=user_agent,
        created_at=datetime.now(UTC),
    )

    repo = _get_repo()
    background_tasks.add_task(repo.create, view)

    return {"ok": True, "throttled": False}
