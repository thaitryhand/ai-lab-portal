"""User follow graph and feed helpers."""

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from collections.abc import Callable
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import Engine, delete, func, insert, select
from sqlalchemy.exc import IntegrityError

from backend.app.admin_boundary import (
    USER_IDENTITY_HEADER,
    USER_SIGNATURE_HEADER,
    SignedIdentity,
    require_user_identity_with_settings,
)
from backend.app.database import user_follows
from backend.app.settings import Settings


class FollowState(BaseModel):
    user_id: str
    follower_count: int
    following_count: int
    is_following: bool = False


class UserFollowRepository(ABC):
    @abstractmethod
    def follow(self, follower_user_id: str, followed_user_id: str) -> None: ...

    @abstractmethod
    def unfollow(self, follower_user_id: str, followed_user_id: str) -> None: ...

    @abstractmethod
    def is_following(self, follower_user_id: str, followed_user_id: str) -> bool: ...

    @abstractmethod
    def followed_user_ids(self, follower_user_id: str) -> set[str]: ...

    @abstractmethod
    def state_for(self, user_id: str, *, viewer_user_id: str | None = None) -> FollowState: ...


class InMemoryUserFollowRepository(UserFollowRepository):
    def __init__(self) -> None:
        self._follows: set[tuple[str, str]] = set()

    def follow(self, follower_user_id: str, followed_user_id: str) -> None:
        if follower_user_id == followed_user_id:
            raise ValueError("Users cannot follow themselves")
        self._follows.add((follower_user_id, followed_user_id))

    def unfollow(self, follower_user_id: str, followed_user_id: str) -> None:
        self._follows.discard((follower_user_id, followed_user_id))

    def is_following(self, follower_user_id: str, followed_user_id: str) -> bool:
        return (follower_user_id, followed_user_id) in self._follows

    def followed_user_ids(self, follower_user_id: str) -> set[str]:
        return {followed for follower, followed in self._follows if follower == follower_user_id}

    def state_for(self, user_id: str, *, viewer_user_id: str | None = None) -> FollowState:
        return FollowState(
            user_id=user_id,
            follower_count=sum(1 for _, followed in self._follows if followed == user_id),
            following_count=sum(1 for follower, _ in self._follows if follower == user_id),
            is_following=bool(viewer_user_id and self.is_following(viewer_user_id, user_id)),
        )


class PostgresUserFollowRepository(UserFollowRepository):
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def follow(self, follower_user_id: str, followed_user_id: str) -> None:
        if follower_user_id == followed_user_id:
            raise ValueError("Users cannot follow themselves")
        try:
            with self.engine.begin() as conn:
                conn.execute(
                    insert(user_follows).values(
                        follower_user_id=follower_user_id,
                        followed_user_id=followed_user_id,
                        created_at=datetime.now(UTC),
                    )
                )
        except IntegrityError:
            return

    def unfollow(self, follower_user_id: str, followed_user_id: str) -> None:
        with self.engine.begin() as conn:
            conn.execute(
                delete(user_follows).where(
                    user_follows.c.follower_user_id == follower_user_id,
                    user_follows.c.followed_user_id == followed_user_id,
                )
            )

    def is_following(self, follower_user_id: str, followed_user_id: str) -> bool:
        with self.engine.begin() as conn:
            row = conn.execute(
                select(user_follows.c.follower_user_id).where(
                    user_follows.c.follower_user_id == follower_user_id,
                    user_follows.c.followed_user_id == followed_user_id,
                )
            ).first()
        return row is not None

    def followed_user_ids(self, follower_user_id: str) -> set[str]:
        with self.engine.begin() as conn:
            rows = conn.execute(select(user_follows.c.followed_user_id).where(user_follows.c.follower_user_id == follower_user_id))
        return {row.followed_user_id for row in rows}

    def state_for(self, user_id: str, *, viewer_user_id: str | None = None) -> FollowState:
        with self.engine.begin() as conn:
            follower_count = conn.execute(
                select(func.count()).select_from(user_follows).where(user_follows.c.followed_user_id == user_id)
            ).scalar_one()
            following_count = conn.execute(
                select(func.count()).select_from(user_follows).where(user_follows.c.follower_user_id == user_id)
            ).scalar_one()
        return FollowState(
            user_id=user_id,
            follower_count=follower_count,
            following_count=following_count,
            is_following=bool(viewer_user_id and self.is_following(viewer_user_id, user_id)),
        )


def create_user_follow_routes(
    repo: UserFollowRepository,
    settings: Settings,
    on_follow: Callable[[str, str, str | None], None] | None = None,
) -> APIRouter:
    def require_user(
        identity_payload: Annotated[str | None, Header(alias=USER_IDENTITY_HEADER)] = None,
        signature: Annotated[str | None, Header(alias=USER_SIGNATURE_HEADER)] = None,
    ) -> SignedIdentity:
        return require_user_identity_with_settings(settings, identity_payload, signature)

    router = APIRouter(prefix="/public/profiles")

    @router.get("/{user_id}/follow-state")
    async def get_follow_state(user_id: str, identity: SignedIdentity = Depends(require_user)) -> FollowState:
        return repo.state_for(user_id, viewer_user_id=identity.user_id)

    @router.post("/{user_id}/follow")
    async def follow_user(user_id: str, identity: SignedIdentity = Depends(require_user)) -> FollowState:
        try:
            repo.follow(identity.user_id, user_id)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        if on_follow is not None:
            on_follow(user_id, identity.user_id, identity.email)
        return repo.state_for(user_id, viewer_user_id=identity.user_id)

    @router.delete("/{user_id}/follow")
    async def unfollow_user(user_id: str, identity: SignedIdentity = Depends(require_user)) -> FollowState:
        repo.unfollow(identity.user_id, user_id)
        return repo.state_for(user_id, viewer_user_id=identity.user_id)

    return router
