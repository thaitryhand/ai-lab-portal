from fastapi.testclient import TestClient

from backend.app.main import create_app
from backend.app.settings import Settings


def test_public_blog_list_returns_only_published_posts() -> None:
    client = TestClient(create_app(Settings(environment="test")))

    response = client.get("/public/blog-posts")

    assert response.status_code == 200
    posts = response.json()
    assert len(posts) == 1
    assert posts[0]["slug"] == "building-an-ai-lab-with-human-review"
    assert "draft-provider-scorecards" not in {post["slug"] for post in posts}


def test_public_blog_list_supports_paginated_response() -> None:
    client = TestClient(create_app(Settings(environment="test")))

    response = client.get("/public/blog-posts?paginated=true&page=1&limit=1")

    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["limit"] == 1
    assert data["total"] == 1
    assert data["has_more"] is False
    assert data["items"][0]["slug"] == "building-an-ai-lab-with-human-review"


def test_public_blog_detail_returns_published_post() -> None:
    client = TestClient(create_app(Settings(environment="test")))

    response = client.get("/public/blog-posts/building-an-ai-lab-with-human-review")

    assert response.status_code == 200
    assert response.json()["title"] == "Building an AI Lab with Human Review at the Center"
    assert "human review" in response.json()["content_markdown"].lower()


def test_public_blog_detail_rejects_draft_or_missing_posts() -> None:
    client = TestClient(create_app(Settings(environment="test")))

    draft_response = client.get("/public/blog-posts/draft-provider-scorecards")
    missing_response = client.get("/public/blog-posts/not-found")

    assert draft_response.status_code == 404
    assert missing_response.status_code == 404
