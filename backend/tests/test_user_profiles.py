import json
from time import time

from fastapi.testclient import TestClient

from backend.app.admin_boundary import (
    ADMIN_IDENTITY_HEADER,
    ADMIN_SIGNATURE_HEADER,
    USER_IDENTITY_HEADER,
    USER_SIGNATURE_HEADER,
    sign_admin_identity,
)
from backend.app.main import create_app
from backend.app.settings import Settings
from backend.app.user_profiles import InMemoryUserProfileRepository

TEST_SECRET = "test-admin-boundary-secret-at-least-32-chars"


def _client() -> TestClient:
    return TestClient(
        create_app(
            Settings(environment="test", admin_boundary_secret=TEST_SECRET),
            user_profile_repository=InMemoryUserProfileRepository(),
        )
    )


def _signed_headers(*, role: str, user_id: str = "user_123", email: str = "reader@example.com") -> dict[str, str]:
    payload = json.dumps(
        {"user_id": user_id, "email": email, "role": role, "issued_at": int(time())},
        separators=(",", ":"),
        sort_keys=True,
    )
    if role == "admin":
        return {ADMIN_IDENTITY_HEADER: payload, ADMIN_SIGNATURE_HEADER: sign_admin_identity(payload, TEST_SECRET)}
    return {USER_IDENTITY_HEADER: payload, USER_SIGNATURE_HEADER: sign_admin_identity(payload, TEST_SECRET)}


def test_user_profile_get_or_create_uses_identity_default_name() -> None:
    response = _client().get("/public/profile/me", headers=_signed_headers(role="user", email="reader@example.com"))

    assert response.status_code == 200
    assert response.json()["user_id"] == "user_123"
    assert response.json()["display_name"] == "reader"


def test_user_can_update_own_profile() -> None:
    client = _client()
    response = client.patch(
        "/public/profile/me",
        json={
            "display_name": "Ada Reader",
            "bio": "I build agent workflows.",
            "avatar_url": "https://example.com/avatar.png",
            "cover_url": "https://example.com/cover.png",
            "website_url": "https://example.com",
            "github_url": "https://github.com/example",
            "linkedin_url": "https://linkedin.com/in/example",
        },
        headers=_signed_headers(role="user"),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["display_name"] == "Ada Reader"
    assert body["bio"] == "I build agent workflows."
    assert body["avatar_url"] == "https://example.com/avatar.png/" or body["avatar_url"] == "https://example.com/avatar.png"
    assert body["cover_url"] == "https://example.com/cover.png/" or body["cover_url"] == "https://example.com/cover.png"


def test_user_can_save_uploaded_image_paths() -> None:
    client = _client()
    response = client.patch(
        "/public/profile/me",
        json={
            "avatar_url": "/uploads/avatar.webp",
            "cover_url": "/uploads/cover.webp",
        },
        headers=_signed_headers(role="user"),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["avatar_url"] == "/uploads/avatar.webp"
    assert body["cover_url"] == "/uploads/cover.webp"


def test_public_profile_omits_email_and_requires_existing_profile() -> None:
    client = _client()
    client.get("/public/profile/me", headers=_signed_headers(role="user", user_id="u_public", email="public@example.com"))

    response = client.get("/public/profiles/u_public")

    assert response.status_code == 200
    assert "email" not in response.json()
    assert response.json()["display_name"] == "public"


def test_admin_can_list_profiles() -> None:
    client = _client()
    client.get("/public/profile/me", headers=_signed_headers(role="user", user_id="u1", email="one@example.com"))

    response = client.get("/admin/user-profiles", headers=_signed_headers(role="admin", email="admin@example.com"))

    assert response.status_code == 200
    assert response.json()[0]["user_id"] == "u1"
