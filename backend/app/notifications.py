"""Notifications module — auto-generated from follows and comment replies."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Annotated, Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import Engine, delete, insert, select, update

from backend.app.admin_boundary import (
    USER_IDENTITY_HEADER,
    USER_SIGNATURE_HEADER,
    SignedIdentity,
    require_user_identity_with_settings,
)
from backend.app.database import notifications as notifications_table
from backend.app.settings import Settings, get_settings

NotificationType = Literal["follow", "comment_reply", "mention"]


class Notification(BaseModel):
    id: str
    user_id: str
    type: NotificationType
    actor_user_id: str
    actor_email: str | None = None
    actor_display_name: str | None = None
    resource_id: str = ""
    resource_type: str = ""
    read: bool = False
    created_at: datetime


class NotificationSummary(BaseModel):
    id: str
    type: NotificationType
    actor_user_id: str
    actor_email: str | None = None
    actor_display_name: str | None = None
    resource_id: str = ""
    resource_type: str = ""
    read: bool
    created_at: datetime


# ─── Repository ────────────────────────────────────────────────────────────────


def _now() -> datetime:
    return datetime.now(UTC)


class InMemoryNotificationRepository:
    def __init__(self) -> None:
        self.items: list[Notification] = []

    def create(
        self,
        user_id: str,
        type: NotificationType,
        actor_user_id: str,
        actor_email: str | None = None,
        actor_display_name: str | None = None,
        resource_id: str = "",
        resource_type: str = "",
    ) -> Notification:
        notification = Notification(
            id=f"notif_{uuid4().hex}",
            user_id=user_id,
            type=type,
            actor_user_id=actor_user_id,
            actor_email=actor_email,
            actor_display_name=actor_display_name,
            resource_id=resource_id,
            resource_type=resource_type,
            read=False,
            created_at=_now(),
        )
        self.items.append(notification)
        return notification

    def list_for_user(self, user_id: str, limit: int = 20) -> list[NotificationSummary]:
        user_notifs = [n for n in self.items if n.user_id == user_id]
        user_notifs.sort(key=lambda n: n.created_at, reverse=True)
        return [_to_summary(n) for n in user_notifs[:limit]]

    def unread_count(self, user_id: str) -> int:
        return sum(1 for n in self.items if n.user_id == user_id and not n.read)

    def mark_read(self, notification_id: str, user_id: str) -> Notification | None:
        for n in self.items:
            if n.id == notification_id and n.user_id == user_id:
                n.read = True
                return n
        return None

    def mark_all_read(self, user_id: str) -> int:
        count = 0
        for n in self.items:
            if n.user_id == user_id and not n.read:
                n.read = True
                count += 1
        return count


class PostgresNotificationRepository:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def create(
        self,
        user_id: str,
        type: NotificationType,
        actor_user_id: str,
        actor_email: str | None = None,
        actor_display_name: str | None = None,
        resource_id: str = "",
        resource_type: str = "",
    ) -> Notification:
        notification = Notification(
            id=f"notif_{uuid4().hex}",
            user_id=user_id,
            type=type,
            actor_user_id=actor_user_id,
            actor_email=actor_email,
            actor_display_name=actor_display_name,
            resource_id=resource_id,
            resource_type=resource_type,
            read=False,
            created_at=_now(),
        )
        with self.engine.begin() as connection:
            connection.execute(insert(notifications_table).values(**notification.model_dump()))
        return notification

    def list_for_user(self, user_id: str, limit: int = 20) -> list[NotificationSummary]:
        with self.engine.begin() as connection:
            rows = (
                connection.execute(
                    select(notifications_table)
                    .where(notifications_table.c.user_id == user_id)
                    .order_by(notifications_table.c.created_at.desc())
                    .limit(limit)
                )
                .mappings()
                .all()
            )
            return [NotificationSummary.model_validate(dict(row)) for row in rows]

    def unread_count(self, user_id: str) -> int:
        with self.engine.begin() as connection:
            rows = connection.execute(
                select(notifications_table.c.id).where(
                    notifications_table.c.user_id == user_id,
                    notifications_table.c.read == False,  # noqa: E712
                )
            ).fetchall()
            return len(rows)

    def mark_read(self, notification_id: str, user_id: str) -> Notification | None:
        with self.engine.begin() as connection:
            result = connection.execute(
                update(notifications_table)
                .where(
                    notifications_table.c.id == notification_id,
                    notifications_table.c.user_id == user_id,
                )
                .values(read=True)
            )
            if result.rowcount == 0:
                return None
            row = (
                connection.execute(
                    select(notifications_table).where(notifications_table.c.id == notification_id)
                )
                .mappings()
                .one()
            )
            return Notification.model_validate(dict(row))

    def mark_all_read(self, user_id: str) -> int:
        with self.engine.begin() as connection:
            result = connection.execute(
                update(notifications_table)
                .where(
                    notifications_table.c.user_id == user_id,
                    notifications_table.c.read == False,  # noqa: E712
                )
                .values(read=True)
            )
            return result.rowcount


def _to_summary(n: Notification) -> NotificationSummary:
    return NotificationSummary(
        id=n.id,
        type=n.type,
        actor_user_id=n.actor_user_id,
        actor_email=n.actor_email,
        actor_display_name=n.actor_display_name,
        resource_id=n.resource_id,
        resource_type=n.resource_type,
        read=n.read,
        created_at=n.created_at,
    )


# ─── Route factory ────────────────────────────────────────────────────────────

OnNotificationCallback = Callable[
    [str, NotificationType, str, str | None, str | None, str, str],
    None,
]


def create_notification_routes(
    repo: InMemoryNotificationRepository | PostgresNotificationRepository,
    settings: Settings,
) -> APIRouter:
    def require_user(
        identity_payload: Annotated[str | None, Header(alias=USER_IDENTITY_HEADER)] = None,
        signature: Annotated[str | None, Header(alias=USER_SIGNATURE_HEADER)] = None,
    ) -> SignedIdentity:
        return require_user_identity_with_settings(settings, identity_payload, signature)

    router = APIRouter(prefix="/public/notifications")

    @router.get("")
    async def list_notifications(
        identity: SignedIdentity = Depends(require_user),
    ) -> list[NotificationSummary]:
        return repo.list_for_user(identity.user_id)

    @router.get("/unread-count")
    async def unread_count(
        identity: SignedIdentity = Depends(require_user),
    ) -> dict[str, int]:
        return {"count": repo.unread_count(identity.user_id)}

    @router.post("/{notification_id}/read")
    async def mark_read(
        notification_id: str,
        identity: SignedIdentity = Depends(require_user),
    ) -> dict[str, str]:
        notification = repo.mark_read(notification_id, identity.user_id)
        if notification is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
        return {"status": "read"}

    @router.post("/read-all")
    async def mark_all_read(
        identity: SignedIdentity = Depends(require_user),
    ) -> dict[str, object]:
        count = repo.mark_all_read(identity.user_id)
        return {"status": "all_read", "count": count}

    return router
