"""Publish approved AI news review items to the public feed (US-041)."""

from __future__ import annotations

import re
from datetime import UTC, datetime

from pydantic import BaseModel

from backend.app.news_extraction import ExtractedArticleRepository
from backend.app.news_scoring import NewsReviewItem, NewsReviewRepository, ReviewStatus
from backend.app.news_sources import NewsSourceRepository


class PublicAiNewsSummary(BaseModel):
    slug: str
    title: str
    summary: str
    why_it_matters: str
    source_name: str
    topic: str
    published_at: datetime


class PublicAiNewsDetail(PublicAiNewsSummary):
    content_markdown: str
    source_url: str
    site_name: str | None = None
    author: str | None = None


class PublishResult(BaseModel):
    id: str
    slug: str
    review_status: ReviewStatus
    published_at: datetime


class UnpublishResult(BaseModel):
    id: str
    review_status: ReviewStatus


def slugify_title(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    slug = slug[:120].strip("-")
    return slug or "ai-news-item"


def ensure_unique_slug(review: NewsReviewRepository, base_slug: str) -> str:
    slug = base_slug
    suffix = 2
    while review.get_by_slug(slug) is not None:
        slug = f"{base_slug}-{suffix}"[:160]
        suffix += 1
    return slug


TOPIC_KEYWORDS: dict[str, tuple[str, ...]] = {
    "models": ("model", "gpt", "claude", "gemini", "llama", "frontier"),
    "agents": ("agent", "workflow", "automation", "tool use", "computer use"),
    "research": ("research", "paper", "benchmark", "eval", "dataset"),
    "policy": ("policy", "regulation", "safety", "governance", "law"),
    "infrastructure": ("chip", "gpu", "datacenter", "cloud", "infrastructure"),
    "product": ("launch", "release", "feature", "api", "app"),
}


def classify_public_topic(*, title: str, summary: str, why_it_matters: str, source_name: str) -> str:
    text = f"{title} {summary} {why_it_matters} {source_name}".lower()
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            return topic
    return "general"


def build_public_detail(
    *,
    review_item: NewsReviewItem,
    extracted: ExtractedArticleRepository,
    sources: NewsSourceRepository,
) -> PublicAiNewsDetail | None:
    if review_item.review_status != "published" or not review_item.slug or not review_item.published_at:
        return None

    article = extracted.get_by_id(review_item.extracted_article_id)
    if article is None:
        return None

    source = sources.get_by_id(review_item.source_id)
    source_name = source.name if source is not None else "Official source"
    article_url = article.canonical_url or article.final_url or article.source_url

    return PublicAiNewsDetail(
        slug=review_item.slug,
        title=review_item.title,
        summary=review_item.summary,
        why_it_matters=review_item.why_it_matters,
        source_name=source_name,
        topic=classify_public_topic(
            title=review_item.title,
            summary=review_item.summary,
            why_it_matters=review_item.why_it_matters,
            source_name=source_name,
        ),
        published_at=review_item.published_at,
        content_markdown=article.content_markdown,
        source_url=article_url,
        site_name=article.site_name,
        author=article.author,
    )


def list_public_ai_news(
    *,
    review: NewsReviewRepository,
    extracted: ExtractedArticleRepository,
    sources: NewsSourceRepository,
    limit: int = 100,
    topic: str | None = None,
) -> list[PublicAiNewsSummary]:
    items: list[PublicAiNewsSummary] = []
    for row in review.list_published(limit=limit):
        detail = build_public_detail(review_item=row, extracted=extracted, sources=sources)
        if detail is None:
            continue
        if topic and detail.topic != topic:
            continue
        items.append(
            PublicAiNewsSummary(
                slug=detail.slug,
                title=detail.title,
                summary=detail.summary,
                why_it_matters=detail.why_it_matters,
                source_name=detail.source_name,
                topic=detail.topic,
                published_at=detail.published_at,
            )
        )
    return items


def get_public_ai_news_by_slug(
    slug: str,
    *,
    review: NewsReviewRepository,
    extracted: ExtractedArticleRepository,
    sources: NewsSourceRepository,
) -> PublicAiNewsDetail | None:
    row = review.get_by_slug(slug)
    if row is None:
        return None
    return build_public_detail(review_item=row, extracted=extracted, sources=sources)


def run_publish_review_item(
    review_id: str,
    *,
    review: NewsReviewRepository,
    slug: str | None = None,
) -> PublishResult:
    row = review.get_by_id(review_id)
    if row is None:
        raise ValueError(f"Review item not found: {review_id}")
    if row.review_status != "approved":
        raise ValueError("Only approved review items can be published")

    base_slug = slugify_title(slug or row.title)
    unique_slug = ensure_unique_slug(review, base_slug)
    published = review.publish(review_id, slug=unique_slug)
    if published is None or published.published_at is None or not published.slug:
        raise ValueError(f"Failed to publish review item: {review_id}")

    return PublishResult(
        id=published.id,
        slug=published.slug,
        review_status=published.review_status,
        published_at=published.published_at,
    )


def run_unpublish_review_item(
    review_id: str,
    *,
    review: NewsReviewRepository,
) -> UnpublishResult:
    row = review.get_by_id(review_id)
    if row is None:
        raise ValueError(f"Review item not found: {review_id}")
    if row.review_status != "published":
        raise ValueError("Only published review items can be unpublished")

    unpublished = review.unpublish(review_id)
    if unpublished is None:
        raise ValueError(f"Failed to unpublish review item: {review_id}")

    return UnpublishResult(id=unpublished.id, review_status=unpublished.review_status)
