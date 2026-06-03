"""Tests for heuristic news scoring and review queue (US-040)."""

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
from backend.app.news_scoring import (
    InMemoryNewsReviewRepository,
    compute_heuristic_scores,
    run_score_extracted_article,
)
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


def _seed_extracted() -> tuple[
    NewsSourceRepository,
    NewsRawItemRepository,
    ExtractedArticleRepository,
    InMemoryNewsReviewRepository,
    str,
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
    return sources, raw, extracted, review, source.id, article.id


def test_compute_heuristic_scores_uses_source_credibility() -> None:
    sources, _raw, extracted, _review, _source_id, article_id = _seed_extracted()
    article = extracted.get_by_id(article_id)
    assert article is not None
    source = sources.get_by_id(sources.list_all()[0].id)
    assert source is not None
    scores = compute_heuristic_scores(article=article, source=source)
    assert scores.source_credibility_score == source.credibility_base_score
    assert 0.0 <= scores.final_publish_score <= 1.0


def test_run_score_extracted_article_skips_duplicates() -> None:
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
    items = raw.list_for_source(source.id)
    extractor = FakeArticleExtractor()
    run_extract_raw_item(
        items[0].id,
        raw_items=raw,
        extracted=extracted,
        extractor=extractor,
        sources=sources,
        review=review,
    )
    run_extract_raw_item(
        items[1].id,
        raw_items=raw,
        extracted=extracted,
        extractor=extractor,
        sources=sources,
        review=review,
    )
    second = extracted.get_by_raw_item_id(items[1].id)
    assert second is not None
    if second.duplicate_status != "unique":
        result = run_score_extracted_article(
            second.id,
            extracted=extracted,
            raw_items=raw,
            sources=sources,
            review=review,
        )
        assert result.review_status == "skipped"


def test_run_score_marks_candidate_when_threshold_met() -> None:
    sources, raw, extracted, review, _source_id, article_id = _seed_extracted()
    result = run_score_extracted_article(
        article_id,
        extracted=extracted,
        raw_items=raw,
        sources=sources,
        review=review,
        threshold=0.0,
    )
    assert result.review_status == "candidate"
    assert review.list_items(status="candidate")


def test_admin_review_queue_list_approve_reject() -> None:
    sources, raw, extracted, review, _source_id, _article_id = _seed_extracted()
    client = TestClient(
        create_app(
            settings=_test_settings(),
            news_source_repository=sources,
            news_raw_item_repository=raw,
            extracted_article_repository=extracted,
            news_review_repository=review,
        )
    )
    listed = client.get("/admin/news/review-items", headers=_admin_headers())
    assert listed.status_code == 200
    body = listed.json()
    assert len(body) >= 1
    review_id = body[0]["id"]

    approved = client.post(
        f"/admin/news/review-items/{review_id}/approve",
        headers=_admin_headers(),
    )
    assert approved.status_code == 200
    assert approved.json()["review_status"] == "approved"

    rejected = client.post(
        f"/admin/news/review-items/{review_id}/reject",
        headers=_admin_headers(),
    )
    assert rejected.status_code == 200
    assert rejected.json()["review_status"] == "rejected"
