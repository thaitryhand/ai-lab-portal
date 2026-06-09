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
from backend.app.blog import BlogRepository
from backend.app.blog_social import InMemoryBlogSocialRepository
from backend.app.main import create_app
from backend.app.settings import Settings
from backend.app.user_profiles import InMemoryUserProfileRepository

TEST_SECRET = "test-admin-boundary-secret-at-least-32-chars"


def _headers(*, role: str, user_id: str = "user_123", email: str = "reader@example.com") -> dict[str, str]:
    payload = json.dumps(
        {"user_id": user_id, "email": email, "role": role, "issued_at": int(time())},
        separators=(",", ":"),
        sort_keys=True,
    )
    if role == "admin":
        return {ADMIN_IDENTITY_HEADER: payload, ADMIN_SIGNATURE_HEADER: sign_admin_identity(payload, TEST_SECRET)}
    return {USER_IDENTITY_HEADER: payload, USER_SIGNATURE_HEADER: sign_admin_identity(payload, TEST_SECRET)}


def _client() -> TestClient:
    return TestClient(
        create_app(
            Settings(environment="test", admin_boundary_secret=TEST_SECRET),
            blog_repository=BlogRepository(),
            blog_social_repository=InMemoryBlogSocialRepository(),
            user_profile_repository=InMemoryUserProfileRepository(),
        )
    )


def test_approved_comments_are_public_and_profile_enriched() -> None:
    client = _client()
    client.patch(
        "/public/profile/me",
        headers=_headers(role="user", user_id="u1", email="ada@example.com"),
        json={"display_name": "Ada", "avatar_url": "https://example.com/avatar.png"},
    )
    created = client.post(
        "/public/blog-posts/building-an-ai-lab-with-human-review/comments",
        headers=_headers(role="user", user_id="u1", email="ada@example.com"),
        json={"content": "Great writeup."},
    ).json()
    client.post(f"/admin/blog-comments/{created['id']}/approve", headers=_headers(role="admin", email="admin@example.com"))

    response = client.get("/public/blog-posts/building-an-ai-lab-with-human-review/comments")

    assert response.status_code == 200
    assert response.json()[0]["user_id"] == "u1"
    assert response.json()[0]["user_name"] == "Ada"
    assert response.json()[0]["avatar_url"] == "https://example.com/avatar.png"


def test_reply_parent_must_belong_to_same_post() -> None:
    client = _client()
    response = client.post(
        "/public/blog-posts/building-an-ai-lab-with-human-review/comments",
        headers=_headers(role="user"),
        json={"content": "reply", "parent_id": "missing"},
    )

    assert response.status_code == 422
