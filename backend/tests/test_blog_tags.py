import json
from time import time

from fastapi.testclient import TestClient

from backend.app.admin_boundary import ADMIN_IDENTITY_HEADER, ADMIN_SIGNATURE_HEADER, sign_admin_identity
from backend.app.blog import BlogRepository
from backend.app.blog_tags import InMemoryBlogTagRepository
from backend.app.main import create_app
from backend.app.settings import Settings

TEST_SECRET = "test-admin-boundary-secret-at-least-32-chars"


def _admin_headers() -> dict[str, str]:
    payload = json.dumps(
        {
            "user_id": "user_123",
            "email": "admin@example.com",
            "role": "admin",
            "issued_at": int(time()),
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    return {
        ADMIN_IDENTITY_HEADER: payload,
        ADMIN_SIGNATURE_HEADER: sign_admin_identity(payload, TEST_SECRET),
    }


def _client() -> TestClient:
    return TestClient(
        create_app(
            Settings(environment="test", admin_boundary_secret=TEST_SECRET),
            blog_repository=BlogRepository(posts=[]),
            blog_tag_repository=InMemoryBlogTagRepository(),
        )
    )


def _post_payload(slug: str) -> dict[str, str]:
    return {
        "slug": slug,
        "title": f"Post {slug}",
        "excerpt": "A tagged post.",
        "author_name": "AI Lab Team",
        "content_markdown": "Tagged content.",
    }


def test_admin_can_create_tags_and_attach_to_post() -> None:
    client = _client()
    post = client.post("/admin/blog-posts", json=_post_payload("tagged-post"), headers=_admin_headers()).json()
    tag = client.post("/admin/blog-tags", json={"name": "Agents"}, headers=_admin_headers()).json()

    response = client.put(
        f"/admin/blog-posts/{post['id']}/tags",
        json={"tag_ids": [tag["id"]]},
        headers=_admin_headers(),
    )

    assert response.status_code == 200
    assert response.json()[0]["slug"] == "agents"


def test_public_tag_filter_only_returns_published_tagged_posts() -> None:
    client = _client()
    tagged = client.post("/admin/blog-posts", json=_post_payload("tagged-published"), headers=_admin_headers()).json()
    untagged = client.post("/admin/blog-posts", json=_post_payload("untagged-published"), headers=_admin_headers()).json()
    tag = client.post("/admin/blog-tags", json={"name": "LLM Ops"}, headers=_admin_headers()).json()
    client.put(f"/admin/blog-posts/{tagged['id']}/tags", json={"tag_ids": [tag["id"]]}, headers=_admin_headers())
    client.post(f"/admin/blog-posts/{tagged['id']}/publish", headers=_admin_headers())
    client.post(f"/admin/blog-posts/{untagged['id']}/publish", headers=_admin_headers())

    response = client.get("/public/blog-posts?tag=llm-ops")

    assert response.status_code == 200
    assert [item["slug"] for item in response.json()] == ["tagged-published"]


def test_public_blog_tags_counts_only_published_posts() -> None:
    client = _client()
    draft = client.post("/admin/blog-posts", json=_post_payload("tagged-draft"), headers=_admin_headers()).json()
    published = client.post("/admin/blog-posts", json=_post_payload("tagged-published"), headers=_admin_headers()).json()
    tag = client.post("/admin/blog-tags", json={"name": "AI Tools"}, headers=_admin_headers()).json()
    client.put(
        f"/admin/blog-posts/{draft['id']}/tags",
        json={"tag_ids": [tag["id"]]},
        headers=_admin_headers(),
    )
    client.put(
        f"/admin/blog-posts/{published['id']}/tags",
        json={"tag_ids": [tag["id"]]},
        headers=_admin_headers(),
    )
    client.post(f"/admin/blog-posts/{published['id']}/publish", headers=_admin_headers())

    response = client.get("/public/blog-tags")

    assert response.status_code == 200
    assert response.json() == [{"id": tag["id"], "slug": "ai-tools", "name": "AI Tools", "post_count": 1}]


def test_duplicate_tag_slug_returns_409() -> None:
    client = _client()
    assert client.post("/admin/blog-tags", json={"name": "Agents"}, headers=_admin_headers()).status_code == 200

    response = client.post("/admin/blog-tags", json={"name": "Agents"}, headers=_admin_headers())

    assert response.status_code == 409
