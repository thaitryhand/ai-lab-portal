import json
from time import time

from fastapi.testclient import TestClient

from backend.app.admin_boundary import ADMIN_IDENTITY_HEADER, ADMIN_SIGNATURE_HEADER, USER_IDENTITY_HEADER, USER_SIGNATURE_HEADER, sign_admin_identity
from backend.app.blog import BlogRepository
from backend.app.main import create_app
from backend.app.settings import Settings
from backend.app.user_follows import InMemoryUserFollowRepository

TEST_SECRET = "test-admin-boundary-secret-at-least-32-chars"


def _headers(*, role: str = "user", user_id: str = "user_123", email: str = "reader@example.com") -> dict[str, str]:
    payload = json.dumps({"user_id": user_id, "email": email, "role": role, "issued_at": int(time())}, separators=(",", ":"), sort_keys=True)
    if role == "admin":
        return {ADMIN_IDENTITY_HEADER: payload, ADMIN_SIGNATURE_HEADER: sign_admin_identity(payload, TEST_SECRET)}
    return {USER_IDENTITY_HEADER: payload, USER_SIGNATURE_HEADER: sign_admin_identity(payload, TEST_SECRET)}


def _client() -> TestClient:
    return TestClient(
        create_app(
            Settings(environment="test", admin_boundary_secret=TEST_SECRET),
            blog_repository=BlogRepository(posts=[]),
            user_follow_repository=InMemoryUserFollowRepository(),
        )
    )


def _create_published_post(client: TestClient, *, slug: str, author_user_id: str) -> dict:
    post = client.post(
        "/admin/blog-posts",
        headers=_headers(role="admin", email="admin@example.com"),
        json={
            "slug": slug,
            "title": slug.replace("-", " ").title(),
            "excerpt": "Excerpt",
            "author_name": "Author",
            "author_user_id": author_user_id,
            "content_markdown": "# Post",
        },
    ).json()
    client.post(f"/admin/blog-posts/{post['id']}/publish", headers=_headers(role="admin", email="admin@example.com"))
    return post


def test_follow_unfollow_and_self_follow_rejection() -> None:
    client = _client()

    self_follow = client.post("/public/profiles/reader/follow", headers=_headers(user_id="reader"))
    assert self_follow.status_code == 422

    followed = client.post("/public/profiles/author/follow", headers=_headers(user_id="reader"))
    assert followed.status_code == 200
    assert followed.json()["is_following"] is True
    assert followed.json()["follower_count"] == 1

    unfollowed = client.delete("/public/profiles/author/follow", headers=_headers(user_id="reader"))
    assert unfollowed.status_code == 200
    assert unfollowed.json()["is_following"] is False
    assert unfollowed.json()["follower_count"] == 0


def test_following_feed_filters_by_author_user_id() -> None:
    client = _client()
    _create_published_post(client, slug="author-one-post", author_user_id="author_one")
    _create_published_post(client, slug="author-two-post", author_user_id="author_two")

    latest = client.get("/public/blog-posts?feed=latest").json()
    assert {post["slug"] for post in latest} == {"author-one-post", "author-two-post"}

    client.post("/public/profiles/author_one/follow", headers=_headers(user_id="reader"))
    following = client.get("/public/blog-posts?feed=following", headers=_headers(user_id="reader")).json()

    assert [post["slug"] for post in following] == ["author-one-post"]
    assert following[0]["author_user_id"] == "author_one"


def test_following_feed_requires_login() -> None:
    client = _client()

    response = client.get("/public/blog-posts?feed=following")

    assert response.status_code == 401
