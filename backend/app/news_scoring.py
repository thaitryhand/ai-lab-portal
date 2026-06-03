"""Heuristic news scoring and admin review queue (US-040)."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Annotated, Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import Engine, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from backend.app.admin_boundary import (
    ADMIN_IDENTITY_HEADER,
    ADMIN_SIGNATURE_HEADER,
    AdminIdentity,
    require_admin_identity_with_settings,
)
from backend.app.database import news_review_items as review_table
from backend.app.news_crawl import NewsRawItemRepository
from backend.app.news_extraction import ExtractedArticle, ExtractedArticleRepository
from backend.app.news_sources import NewsSource, NewsSourceRepository
from backend.app.settings import Settings

ReviewStatus = Literal["candidate", "approved", "rejected", "low_score", "skipped"]
SCORER_VERSION = "heuristic_v1"
DEFAULT_REVIEW_THRESHOLD = 0.55

_AI_KEYWORDS = (
    "ai",
    "llm",
    "machine learning",
    "gpt",
    "agent",
    "model",
    "neural",
    "openai",
    "anthropic",
    "gemini",
    "embedding",
)
_TECH_KEYWORDS = (
    "benchmark",
    "api",
    "architecture",
    "inference",
    "training",
    "gpu",
    "transformer",
    "fine-tun",
    "rag",
    "evaluation",
)
_BUSINESS_KEYWORDS = (
    "enterprise",
    "productivity",
    "workflow",
    "customer",
    "business",
    "roi",
    "team",
    "adoption",
)
_SPAM_PATTERNS = ("click here", "free money", "casino", "buy now", "limited offer")


class ScoreDimensions(BaseModel):
    source_credibility_score: float = Field(ge=0.0, le=1.0)
    engagement_score: float = Field(ge=0.0, le=1.0)
    relevance_score: float = Field(ge=0.0, le=1.0)
    novelty_score: float = Field(ge=0.0, le=1.0)
    technical_depth_score: float = Field(ge=0.0, le=1.0)
    business_value_score: float = Field(ge=0.0, le=1.0)
    spam_risk_score: float = Field(ge=0.0, le=1.0)
    final_publish_score: float = Field(ge=0.0, le=1.0)


class NewsReviewItem(BaseModel):
    id: str
    extracted_article_id: str
    raw_item_id: str
    source_id: str
    title: str
    source_credibility_score: float
    engagement_score: float
    relevance_score: float
    novelty_score: float
    technical_depth_score: float
    business_value_score: float
    spam_risk_score: float
    final_publish_score: float
    summary: str
    why_it_matters: str
    scorer_version: str
    review_status: ReviewStatus
    review_notes: str | None = None
    scored_at: datetime
    reviewed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ScoringResult(BaseModel):
    extracted_article_id: str
    review_item_id: str | None = None
    review_status: ReviewStatus
    final_publish_score: float
    skipped_reason: str | None = None


class ReviewDecision(BaseModel):
    id: str
    review_status: ReviewStatus
    reviewed_at: datetime


class ScoreQueuedResponse(BaseModel):
    status: str = "queued"
    task_id: str


def _keyword_density(text: str, keywords: tuple[str, ...]) -> float:
    lower = text.lower()
    hits = sum(1 for keyword in keywords if keyword in lower)
    return min(1.0, hits / 3.0)


def _spam_risk(text: str) -> float:
    lower = text.lower()
    hits = sum(1 for pattern in _SPAM_PATTERNS if pattern in lower)
    promo_links = len(re.findall(r"https?://", lower))
    score = min(1.0, hits * 0.35 + max(0, promo_links - 3) * 0.1)
    return score


def _novelty_score(published_at: datetime | None, *, now: datetime) -> float:
    if published_at is None:
        return 0.55
    age = now - published_at
    if age <= timedelta(days=3):
        return 0.92
    if age <= timedelta(days=14):
        return 0.75
    return 0.5


def compute_heuristic_scores(
    *,
    article: ExtractedArticle,
    source: NewsSource,
    now: datetime | None = None,
) -> ScoreDimensions:
    moment = now or datetime.now(UTC)
    corpus = f"{article.title}\n{article.content_text}"
    relevance = _keyword_density(corpus, _AI_KEYWORDS)
    technical = _keyword_density(corpus, _TECH_KEYWORDS)
    business = _keyword_density(corpus, _BUSINESS_KEYWORDS)
    spam = _spam_risk(corpus)
    engagement = 0.5
    credibility = max(0.0, min(1.0, source.credibility_base_score))
    novelty = _novelty_score(article.published_at, now=moment)

    final = (
        credibility * 0.15
        + engagement * 0.10
        + relevance * 0.25
        + novelty * 0.10
        + technical * 0.15
        + business * 0.15
        + (1.0 - spam) * 0.10
    )
    final = max(0.0, min(1.0, final))

    return ScoreDimensions(
        source_credibility_score=credibility,
        engagement_score=engagement,
        relevance_score=relevance,
        novelty_score=novelty,
        technical_depth_score=technical,
        business_value_score=business,
        spam_risk_score=spam,
        final_publish_score=final,
    )


def _build_summary(article: ExtractedArticle, scores: ScoreDimensions) -> str:
    excerpt = article.content_text.strip().split("\n", 1)[0][:280]
    return excerpt or article.title


def _build_why_it_matters(scores: ScoreDimensions) -> str:
    if scores.relevance_score >= 0.66 and scores.technical_depth_score >= 0.33:
        return "Strong AI relevance and technical depth for practitioner readers."
    if scores.business_value_score >= 0.33:
        return "Potential business impact for teams evaluating AI adoption."
    if scores.relevance_score >= 0.33:
        return "Topical AI coverage worth a quick editorial review."
    return "Moderate signal; human review recommended before publishing."


class NewsReviewRepository(ABC):
    @abstractmethod
    def get_by_id(self, review_id: str) -> NewsReviewItem | None:
        ...

    @abstractmethod
    def get_by_extracted_article_id(self, extracted_article_id: str) -> NewsReviewItem | None:
        ...

    @abstractmethod
    def list_items(
        self, *, status: ReviewStatus | None = None, limit: int = 100
    ) -> list[NewsReviewItem]:
        ...

    @abstractmethod
    def upsert_scored(
        self,
        *,
        article: ExtractedArticle,
        source: NewsSource,
        scores: ScoreDimensions,
        review_status: ReviewStatus,
        summary: str,
        why_it_matters: str,
    ) -> NewsReviewItem:
        ...

    @abstractmethod
    def set_review_status(
        self,
        review_id: str,
        *,
        review_status: ReviewStatus,
        review_notes: str | None = None,
    ) -> NewsReviewItem | None:
        ...


class InMemoryNewsReviewRepository(NewsReviewRepository):
    def __init__(self) -> None:
        self._rows: dict[str, NewsReviewItem] = {}

    def get_by_id(self, review_id: str) -> NewsReviewItem | None:
        return self._rows.get(review_id)

    def get_by_extracted_article_id(self, extracted_article_id: str) -> NewsReviewItem | None:
        for row in self._rows.values():
            if row.extracted_article_id == extracted_article_id:
                return row
        return None

    def list_items(
        self, *, status: ReviewStatus | None = None, limit: int = 100
    ) -> list[NewsReviewItem]:
        rows = list(self._rows.values())
        if status is not None:
            rows = [row for row in rows if row.review_status == status]
        rows.sort(key=lambda row: row.final_publish_score, reverse=True)
        return rows[:limit]

    def upsert_scored(
        self,
        *,
        article: ExtractedArticle,
        source: NewsSource,
        scores: ScoreDimensions,
        review_status: ReviewStatus,
        summary: str,
        why_it_matters: str,
    ) -> NewsReviewItem:
        now = datetime.now(UTC)
        existing = self.get_by_extracted_article_id(article.id)
        values = {
            "extracted_article_id": article.id,
            "raw_item_id": article.raw_item_id,
            "source_id": source.id,
            "title": article.title[:512],
            "source_credibility_score": scores.source_credibility_score,
            "engagement_score": scores.engagement_score,
            "relevance_score": scores.relevance_score,
            "novelty_score": scores.novelty_score,
            "technical_depth_score": scores.technical_depth_score,
            "business_value_score": scores.business_value_score,
            "spam_risk_score": scores.spam_risk_score,
            "final_publish_score": scores.final_publish_score,
            "summary": summary,
            "why_it_matters": why_it_matters,
            "scorer_version": SCORER_VERSION,
            "review_status": review_status,
            "review_notes": None,
            "scored_at": now,
            "reviewed_at": None,
            "created_at": existing.created_at if existing else now,
            "updated_at": now,
        }
        if existing is not None:
            row = existing.model_copy(update=values)
        else:
            row = NewsReviewItem(id=f"newsrev_{uuid4().hex}", **values)
        self._rows[row.id] = row
        return row

    def set_review_status(
        self,
        review_id: str,
        *,
        review_status: ReviewStatus,
        review_notes: str | None = None,
    ) -> NewsReviewItem | None:
        row = self._rows.get(review_id)
        if row is None:
            return None
        now = datetime.now(UTC)
        updated = row.model_copy(
            update={
                "review_status": review_status,
                "review_notes": review_notes,
                "reviewed_at": now,
                "updated_at": now,
            }
        )
        self._rows[review_id] = updated
        return updated


class PostgresNewsReviewRepository(NewsReviewRepository):
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def get_by_id(self, review_id: str) -> NewsReviewItem | None:
        with self._engine.connect() as conn:
            row = (
                conn.execute(select(review_table).where(review_table.c.id == review_id))
                .mappings()
                .one_or_none()
            )
            if row is None:
                return None
            return NewsReviewItem(**dict(row))

    def get_by_extracted_article_id(self, extracted_article_id: str) -> NewsReviewItem | None:
        with self._engine.connect() as conn:
            row = (
                conn.execute(
                    select(review_table).where(
                        review_table.c.extracted_article_id == extracted_article_id
                    )
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                return None
            return NewsReviewItem(**dict(row))

    def list_items(
        self, *, status: ReviewStatus | None = None, limit: int = 100
    ) -> list[NewsReviewItem]:
        stmt = select(review_table).order_by(review_table.c.final_publish_score.desc()).limit(limit)
        if status is not None:
            stmt = stmt.where(review_table.c.review_status == status)
        with self._engine.connect() as conn:
            rows = conn.execute(stmt).mappings().all()
            return [NewsReviewItem(**dict(row)) for row in rows]

    def upsert_scored(
        self,
        *,
        article: ExtractedArticle,
        source: NewsSource,
        scores: ScoreDimensions,
        review_status: ReviewStatus,
        summary: str,
        why_it_matters: str,
    ) -> NewsReviewItem:
        now = datetime.now(UTC)
        existing = self.get_by_extracted_article_id(article.id)
        values = {
            "id": existing.id if existing else f"newsrev_{uuid4().hex}",
            "extracted_article_id": article.id,
            "raw_item_id": article.raw_item_id,
            "source_id": source.id,
            "title": article.title[:512],
            "source_credibility_score": scores.source_credibility_score,
            "engagement_score": scores.engagement_score,
            "relevance_score": scores.relevance_score,
            "novelty_score": scores.novelty_score,
            "technical_depth_score": scores.technical_depth_score,
            "business_value_score": scores.business_value_score,
            "spam_risk_score": scores.spam_risk_score,
            "final_publish_score": scores.final_publish_score,
            "summary": summary,
            "why_it_matters": why_it_matters,
            "scorer_version": SCORER_VERSION,
            "review_status": review_status,
            "review_notes": None,
            "scored_at": now,
            "reviewed_at": None,
            "created_at": existing.created_at if existing else now,
            "updated_at": now,
        }
        stmt = pg_insert(review_table).values(**values)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_news_review_items_extracted",
            set_={k: values[k] for k in values if k not in {"id", "created_at"}},
        )
        with self._engine.begin() as conn:
            conn.execute(stmt)
        row = self.get_by_extracted_article_id(article.id)
        assert row is not None
        return row

    def set_review_status(
        self,
        review_id: str,
        *,
        review_status: ReviewStatus,
        review_notes: str | None = None,
    ) -> NewsReviewItem | None:
        now = datetime.now(UTC)
        with self._engine.begin() as conn:
            conn.execute(
                update(review_table)
                .where(review_table.c.id == review_id)
                .values(
                    review_status=review_status,
                    review_notes=review_notes,
                    reviewed_at=now,
                    updated_at=now,
                )
            )
        return self.get_by_id(review_id)


def run_score_extracted_article(
    extracted_article_id: str,
    *,
    extracted: ExtractedArticleRepository,
    raw_items: NewsRawItemRepository,
    sources: NewsSourceRepository,
    review: NewsReviewRepository,
    threshold: float = DEFAULT_REVIEW_THRESHOLD,
) -> ScoringResult:
    article = extracted.get_by_id(extracted_article_id)
    if article is None:
        raise ValueError(f"Extraction not found: {extracted_article_id}")

    if article.extraction_status != "success":
        return ScoringResult(
            extracted_article_id=extracted_article_id,
            review_status="skipped",
            final_publish_score=0.0,
            skipped_reason="extraction_not_success",
        )

    if article.duplicate_status != "unique":
        return ScoringResult(
            extracted_article_id=extracted_article_id,
            review_status="skipped",
            final_publish_score=0.0,
            skipped_reason=f"duplicate_{article.duplicate_status}",
        )

    raw_item = raw_items.get_by_id(article.raw_item_id)
    if raw_item is None:
        raise ValueError(f"Raw item not found: {article.raw_item_id}")

    source = sources.get_by_id(raw_item.source_id)
    if source is None:
        raise ValueError(f"News source not found: {raw_item.source_id}")

    scores = compute_heuristic_scores(article=article, source=source)
    summary = _build_summary(article, scores)
    why = _build_why_it_matters(scores)
    review_status: ReviewStatus = (
        "candidate" if scores.final_publish_score >= threshold else "low_score"
    )

    row = review.upsert_scored(
        article=article,
        source=source,
        scores=scores,
        review_status=review_status,
        summary=summary,
        why_it_matters=why,
    )
    return ScoringResult(
        extracted_article_id=extracted_article_id,
        review_item_id=row.id,
        review_status=review_status,
        final_publish_score=scores.final_publish_score,
    )


def run_score_pending_extractions(
    *,
    extracted: ExtractedArticleRepository,
    raw_items: NewsRawItemRepository,
    sources: NewsSourceRepository,
    review: NewsReviewRepository,
    source_id: str | None = None,
    threshold: float = DEFAULT_REVIEW_THRESHOLD,
) -> list[ScoringResult]:
    source_ids = [source_id] if source_id is not None else [row.id for row in sources.list_all()]
    results: list[ScoringResult] = []
    seen: set[str] = set()

    for sid in source_ids:
        for raw in raw_items.list_for_source(sid):
            article = extracted.get_by_raw_item_id(raw.id)
            if article is None or article.id in seen:
                continue
            seen.add(article.id)
            if review.get_by_extracted_article_id(article.id) is not None:
                continue
            if article.extraction_status != "success" or article.duplicate_status != "unique":
                continue
            results.append(
                run_score_extracted_article(
                    article.id,
                    extracted=extracted,
                    raw_items=raw_items,
                    sources=sources,
                    review=review,
                    threshold=threshold,
                )
            )
    return results


def create_news_review_routes(
    review_repository: NewsReviewRepository,
    settings: Settings,
    *,
    extracted_repository: ExtractedArticleRepository | None = None,
    raw_items_repository: NewsRawItemRepository | None = None,
    sources_repository: NewsSourceRepository | None = None,
    enqueue_rescore: Callable[[str], str] | None = None,
) -> APIRouter:
    def require_identity(
        identity_payload: Annotated[str | None, Header(alias=ADMIN_IDENTITY_HEADER)] = None,
        signature: Annotated[str | None, Header(alias=ADMIN_SIGNATURE_HEADER)] = None,
    ) -> AdminIdentity:
        return require_admin_identity_with_settings(settings, identity_payload, signature)

    router = APIRouter(prefix="/admin/news/review-items")

    @router.get("")
    async def list_review_items(
        status: ReviewStatus | None = None,
        limit: int = 100,
        _identity: AdminIdentity = Depends(require_identity),
    ) -> list[NewsReviewItem]:
        return review_repository.list_items(status=status, limit=limit)

    @router.get("/{review_id}")
    async def get_review_item(
        review_id: str,
        _identity: AdminIdentity = Depends(require_identity),
    ) -> NewsReviewItem:
        row = review_repository.get_by_id(review_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Review item not found")
        return row

    @router.post("/{review_id}/approve")
    async def approve_review_item(
        review_id: str,
        _identity: AdminIdentity = Depends(require_identity),
    ) -> ReviewDecision:
        row = review_repository.set_review_status(review_id, review_status="approved")
        if row is None:
            raise HTTPException(status_code=404, detail="Review item not found")
        assert row.reviewed_at is not None
        return ReviewDecision(id=row.id, review_status=row.review_status, reviewed_at=row.reviewed_at)

    @router.post("/{review_id}/reject")
    async def reject_review_item(
        review_id: str,
        _identity: AdminIdentity = Depends(require_identity),
    ) -> ReviewDecision:
        row = review_repository.set_review_status(review_id, review_status="rejected")
        if row is None:
            raise HTTPException(status_code=404, detail="Review item not found")
        assert row.reviewed_at is not None
        return ReviewDecision(id=row.id, review_status=row.review_status, reviewed_at=row.reviewed_at)

    @router.post("/{review_id}/rescore")
    async def rescore_review_item(
        review_id: str,
        _identity: AdminIdentity = Depends(require_identity),
    ):
        from backend.app.task_support import (
            extracted_article_repository,
            news_raw_item_repository,
            news_review_repository,
            news_source_repository,
        )

        row = review_repository.get_by_id(review_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Review item not found")

        if enqueue_rescore is not None:
            return ScoreQueuedResponse(task_id=enqueue_rescore(row.extracted_article_id))

        return run_score_extracted_article(
            row.extracted_article_id,
            extracted=extracted_repository or extracted_article_repository(settings),
            raw_items=raw_items_repository or news_raw_item_repository(settings),
            sources=sources_repository or news_source_repository(settings),
            review=review_repository,
        )

    return router
