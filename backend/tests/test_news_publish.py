"""Tests for publishing AI news to the public feed (US-041)."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from backend.app.admin_boundary import (
    ADMIN_IDENTITY_HEADER,
    ADMIN_SIGNATURE_HEADER,
    sign_admin_identity,
)
from backend.app.main import create_app
from backend.app.news_crawl import NewsRawItemRepository, run_rss_crawl
from backend.app.news_extraction import (
    ExtractedArticleRepository,
    FakeArticleExtractor,
    run_extract_raw_item,
)
from backend.app.news_publish import classify_public_topic, slugify_title
from backend.app.news_scoring import InMemoryNewsReviewRepository, run_score_extracted_article
from backend.app.news_sources import NewsSourceRepository
from backend.app.settings import Settings
from backend.tests.test_news_crawl import FIXTURE_RSS, _rss_source

TEST_SECRET = "test-admin-boundary-secret-at-least-32-chars"


def _test_settings() -> Settings:
    return Settings(environment="test", admin_boundary_secret=TEST_SECRET)


def _admin_headers() -> dict[str, str]:
    payload = json.dumps(
        {
            "user_id": "user_123",
            "email": "admin@example.com",
            "role": "admin",
            "issued_at": int(datetime.now(UTC).timestamp()),
        }
    )
    return {
        ADMIN_IDENTITY_HEADER: payload,
        ADMIN_SIGNATURE_HEADER: sign_admin_identity(payload, TEST_SECRET),
    }


def _seed_approved_review() -> tuple[
    NewsSourceRepository,
    NewsRawItemRepository,
    ExtractedArticleRepository,
    InMemoryNewsReviewRepository,
    str,
]:
    sources = NewsSourceRepository(sources=[])
    raw = NewsRawItemRepository()
    extracted = ExtractedArticleRepository()
    review = InMemoryNewsReviewRepository()
    source = _rss_source(sources)
    run_rss_crawl(
        source.id,
        sources=sources,
        raw_items=raw,
        fetcher=lambda _url: FIXTURE_RSS.read_bytes(),
    )
    raw_item = raw.list_for_source(source.id)[0]
    run_extract_raw_item(
        raw_item.id,
        raw_items=raw,
        extracted=extracted,
        extractor=FakeArticleExtractor(),
        sources=sources,
        review=review,
    )
    article = extracted.get_by_raw_item_id(raw_item.id)
    assert article is not None
    run_score_extracted_article(
        article.id,
        extracted=extracted,
        raw_items=raw,
        sources=sources,
        review=review,
        threshold=0.0,
    )
    review_row = review.get_by_extracted_article_id(article.id)
    assert review_row is not None
    approved = review.set_review_status(review_row.id, review_status="approved")
    assert approved is not None
    return sources, raw, extracted, review, approved.id


def test_slugify_title() -> None:
    assert slugify_title("OpenAI Ships New GPT Agent!") == "openai-ships-new-gpt-agent"


def test_classify_public_topic() -> None:
    assert (
        classify_public_topic(
            title="New GPT model benchmark",
            summary="A frontier model improves eval scores",
            why_it_matters="Teams can compare model quality",
            source_name="OpenAI",
        )
        == "models"
    )
    assert (
        classify_public_topic(
            title="Quarterly note",
            summary="Company update",
            why_it_matters="Useful context",
            source_name="Official source",
        )
        == "general"
    )


def test_publish_and_public_feed() -> None:
    sources, raw, extracted, review, review_id = _seed_approved_review()
    client = TestClient(
        create_app(
            settings=_test_settings(),
            news_source_repository=sources,
            news_raw_item_repository=raw,
            extracted_article_repository=extracted,
            news_review_repository=review,
        )
    )

    published = client.post(
        f"/admin/news/review-items/{review_id}/publish",
        headers=_admin_headers(),
    )
    assert published.status_code == 200
    slug = published.json()["slug"]
    assert slug

    listed = client.get("/public/ai-news")
    assert listed.status_code == 200
    listed_body = listed.json()
    assert any(item["slug"] == slug for item in listed_body)
    assert listed_body[0]["topic"] == "general"

    filtered = client.get("/public/ai-news?topic=general")
    assert filtered.status_code == 200
    assert any(item["slug"] == slug for item in filtered.json())

    filtered_empty = client.get("/public/ai-news?topic=models")
    assert filtered_empty.status_code == 200
    assert filtered_empty.json() == []

    detail = client.get(f"/public/ai-news/{slug}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["title"]
    assert body["topic"] == "general"
    assert "Stub article body" in body["content_markdown"]

    unpublished = client.post(
        f"/admin/news/review-items/{review_id}/unpublish",
        headers=_admin_headers(),
    )
    assert unpublished.status_code == 200
    assert client.get("/public/ai-news").json() == []


def test_publish_requires_approved_status() -> None:
    sources, raw, extracted, review, review_id = _seed_approved_review()
    review.set_review_status(review_id, review_status="rejected")
    client = TestClient(
        create_app(
            settings=_test_settings(),
            news_source_repository=sources,
            news_raw_item_repository=raw,
            extracted_article_repository=extracted,
            news_review_repository=review,
        )
    )
    response = client.post(
        f"/admin/news/review-items/{review_id}/publish",
        headers=_admin_headers(),
    )
    assert response.status_code == 400
