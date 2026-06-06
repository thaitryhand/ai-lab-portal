"""User profile extensions for Better Auth users."""

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy import Engine, insert, select, update

from backend.app.admin_boundary import (
    ADMIN_IDENTITY_HEADER,
    ADMIN_SIGNATURE_HEADER,
    USER_IDENTITY_HEADER,
    USER_SIGNATURE_HEADER,
    AdminIdentity,
    SignedIdentity,
    require_admin_identity_with_settings,
    require_user_identity_with_settings,
)
from backend.app.database import user_profiles
from backend.app.settings import Settings


class UserProfile(BaseModel):
    user_id: str
    display_name: str
    bio: str | None = None
    avatar_url: str | None = None
    cover_url: str | None = None
    website_url: str | None = None
    github_url: str | None = None
    linkedin_url: str | None = None
    created_at: datetime
    updated_at: datetime


class UserProfileUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    bio: str | None = Field(default=None, max_length=2000)
    avatar_url: str | None = Field(default=None, max_length=2048)
    cover_url: str | None = Field(default=None, max_length=2048)
    website_url: HttpUrl | None = None
    github_url: HttpUrl | None = None
    linkedin_url: HttpUrl | None = None


class UserProfileRepository(ABC):
    @abstractmethod
    def get_by_user_id(self, user_id: str) -> UserProfile | None: ...

    @abstractmethod
    def get_or_create(self, user_id: str, *, default_name: str | None = None) -> UserProfile: ...

    @abstractmethod
    def update(self, user_id: str, request: UserProfileUpdate) -> UserProfile | None: ...

    @abstractmethod
    def list_all(self) -> list[UserProfile]: ...


class InMemoryUserProfileRepository(UserProfileRepository):
    def __init__(self) -> None:
        self._profiles: dict[str, UserProfile] = {}

    def get_by_user_id(self, user_id: str) -> UserProfile | None:
        return self._profiles.get(user_id)

    def get_or_create(self, user_id: str, *, default_name: str | None = None) -> UserProfile:
        existing = self._profiles.get(user_id)
        if existing:
            return existing
        now = datetime.now(UTC)
        profile = UserProfile(
            user_id=user_id,
            display_name=default_name or "AI Lab User",
            created_at=now,
            updated_at=now,
        )
        self._profiles[user_id] = profile
        return profile

    def update(self, user_id: str, request: UserProfileUpdate) -> UserProfile | None:
        profile = self.get_or_create(user_id)
        data = {key: str(value) if value is not None and key.endswith("_url") else value for key, value in request.model_dump(exclude_unset=True).items()}
        updated = profile.model_copy(update={**data, "updated_at": datetime.now(UTC)})
        self._profiles[user_id] = updated
        return updated

    def list_all(self) -> list[UserProfile]:
        return sorted(self._profiles.values(), key=lambda row: row.updated_at, reverse=True)


class PostgresUserProfileRepository(UserProfileRepository):
    def __init__(self, engine: Engine) -> None:
        self.engine = engine

    def get_by_user_id(self, user_id: str) -> UserProfile | None:
        with self.engine.begin() as conn:
            row = conn.execute(select(user_profiles).where(user_profiles.c.user_id == user_id)).mappings().first()
        return UserProfile(**dict(row)) if row else None

    def get_or_create(self, user_id: str, *, default_name: str | None = None) -> UserProfile:
        existing = self.get_by_user_id(user_id)
        if existing:
            return existing
        now = datetime.now(UTC)
        profile = UserProfile(
            user_id=user_id,
            display_name=default_name or "AI Lab User",
            created_at=now,
            updated_at=now,
        )
        with self.engine.begin() as conn:
            conn.execute(insert(user_profiles).values(**profile.model_dump()))
        return profile

    def update(self, user_id: str, request: UserProfileUpdate) -> UserProfile | None:
        self.get_or_create(user_id)
        data = {
            key: str(value) if value is not None and key.endswith("_url") else value
            for key, value in request.model_dump(exclude_unset=True).items()
        }
        data["updated_at"] = datetime.now(UTC)
        with self.engine.begin() as conn:
            row = (
                conn.execute(update(user_profiles).where(user_profiles.c.user_id == user_id).values(**data).returning(*user_profiles.c))
                .mappings()
                .first()
            )
        return UserProfile(**dict(row)) if row else None

    def list_all(self) -> list[UserProfile]:
        with self.engine.begin() as conn:
            rows = conn.execute(select(user_profiles).order_by(user_profiles.c.updated_at.desc())).mappings()
        return [UserProfile(**dict(row)) for row in rows]


def default_name_from_identity(identity: SignedIdentity) -> str:
    return identity.email.split("@")[0] if identity.email else "AI Lab User"


def create_user_profile_routes(repo: UserProfileRepository, settings: Settings) -> APIRouter:
    def require_user(
        identity_payload: Annotated[str | None, Header(alias=USER_IDENTITY_HEADER)] = None,
        signature: Annotated[str | None, Header(alias=USER_SIGNATURE_HEADER)] = None,
    ) -> SignedIdentity:
        return require_user_identity_with_settings(settings, identity_payload, signature)

    router = APIRouter(prefix="/public")

    @router.get("/profile/me")
    async def get_my_profile(identity: SignedIdentity = Depends(require_user)) -> UserProfile:
        return repo.get_or_create(identity.user_id, default_name=default_name_from_identity(identity))

    @router.patch("/profile/me")
    async def update_my_profile(
        request: UserProfileUpdate,
        identity: SignedIdentity = Depends(require_user),
    ) -> UserProfile:
        profile = repo.update(identity.user_id, request)
        assert profile is not None
        return profile

    @router.get("/profiles/{user_id}")
    async def get_public_profile(user_id: str) -> UserProfile:
        profile = repo.get_by_user_id(user_id)
        if profile is None:
            raise HTTPException(status_code=404, detail="Profile not found")
        return profile

    return router


def create_user_profile_admin_routes(repo: UserProfileRepository, settings: Settings) -> APIRouter:
    def require_admin(
        identity_payload: Annotated[str | None, Header(alias=ADMIN_IDENTITY_HEADER)] = None,
        signature: Annotated[str | None, Header(alias=ADMIN_SIGNATURE_HEADER)] = None,
    ) -> AdminIdentity:
        return require_admin_identity_with_settings(settings, identity_payload, signature)

    router = APIRouter(prefix="/admin/user-profiles")

    @router.get("")
    async def admin_user_profiles(_identity: AdminIdentity = Depends(require_admin)) -> list[UserProfile]:
        return repo.list_all()

    return router
