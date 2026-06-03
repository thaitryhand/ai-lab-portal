"""News source configuration for AI News Intelligence (MVP 3)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from collections.abc import Callable
from typing import TYPE_CHECKING, Annotated, Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import Engine, insert, select, update

from backend.app.admin_boundary import (
    ADMIN_IDENTITY_HEADER,
    ADMIN_SIGNATURE_HEADER,
    AdminIdentity,
    require_admin_identity_with_settings,
)
from backend.app.database import news_sources as news_sources_table
from backend.app.news_crawl import NewsRawItemRepository
from backend.app.settings import Settings

if TYPE_CHECKING:
    from backend.app.news_extraction import ExtractedArticleRepository
    from backend.app.news_scoring import NewsReviewRepository

NewsSourceType = Literal["rss", "github", "website"]
NewsPriority = Literal["high", "medium", "low"]


class NewsSource(BaseModel):
    id: str
    name: str
    source_type: NewsSourceType
    url_or_identifier: str
    description: str | None = None
    priority: NewsPriority = "medium"
    crawl_frequency_minutes: int = Field(default=360, ge=15, le=10080)
    is_enabled: bool = True
    credibility_base_score: float = Field(default=0.7, ge=0.0, le=1.0)
    last_crawled_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class NewsSourceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    source_type: NewsSourceType
    url_or_identifier: str = Field(min_length=1, max_length=512)
    description: str | None = None
    priority: NewsPriority = "medium"
    crawl_frequency_minutes: int = Field(default=360, ge=15, le=10080)
    is_enabled: bool = True
    credibility_base_score: float = Field(default=0.7, ge=0.0, le=1.0)


class NewsSourceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    source_type: NewsSourceType | None = None
    url_or_identifier: str | None = Field(default=None, min_length=1, max_length=512)
    description: str | None = None
    priority: NewsPriority | None = None
    crawl_frequency_minutes: int | None = Field(default=None, ge=15, le=10080)
    is_enabled: bool | None = None
    credibility_base_score: float | None = Field(default=None, ge=0.0, le=1.0)


class NewsSourceSummary(BaseModel):
    id: str
    name: str
    source_type: NewsSourceType
    url_or_identifier: str
    priority: NewsPriority
    is_enabled: bool
    last_crawled_at: datetime | None = None


class NewsSourceRepository:
    def __init__(self, sources: list[NewsSource] | None = None) -> None:
        seeded = _default_sources() if sources is None else sources
        self._sources: dict[str, NewsSource] = {s.id: s for s in seeded}

    def list_all(self) -> list[NewsSourceSummary]:
        items = sorted(self._sources.values(), key=lambda s: s.name.lower())
        return [_to_summary(s) for s in items]

    def get_by_id(self, source_id: str) -> NewsSource | None:
        return self._sources.get(source_id)

    def create(self, payload: NewsSourceCreate) -> NewsSource:
        now = datetime.now(UTC)
        source = NewsSource(id=f"newssrc_{uuid4().hex}", created_at=now, updated_at=now, **payload.model_dump())
        self._sources[source.id] = source
        return source

    def update(self, source_id: str, payload: NewsSourceUpdate) -> NewsSource | None:
        existing = self._sources.get(source_id)
        if existing is None:
            return None
        updated = existing.model_copy(
            update={**payload.model_dump(exclude_unset=True), "updated_at": datetime.now(UTC)}
        )
        self._sources[source_id] = updated
        return updated

    def list_due_rss(self, *, now: datetime | None = None) -> list[NewsSource]:
        moment = now or datetime.now(UTC)
        due: list[NewsSource] = []
        for source in self._sources.values():
            if not source.is_enabled or source.source_type != "rss":
                continue
            if source.last_crawled_at is None:
                due.append(source)
                continue
            if source.last_crawled_at + timedelta(minutes=source.crawl_frequency_minutes) <= moment:
                due.append(source)
        return due

    def touch_last_crawled(self, source_id: str, crawled_at: datetime) -> None:
        existing = self._sources.get(source_id)
        if existing is None:
            return
        self._sources[source_id] = existing.model_copy(
            update={"last_crawled_at": crawled_at, "updated_at": crawled_at}
        )


class PostgresNewsSourceRepository(NewsSourceRepository):
    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        self._seeded = False

    def _ensure_seed(self) -> None:
        if self._seeded:
            return
        with self._engine.begin() as conn:
            count = conn.execute(select(news_sources_table.c.id).limit(1)).first()
            if count is None:
                for source in _default_sources():
                    conn.execute(insert(news_sources_table).values(**_source_row(source)))
        self._seeded = True

    def list_all(self) -> list[NewsSourceSummary]:
        self._ensure_seed()
        with self._engine.connect() as conn:
            rows = conn.execute(
                select(news_sources_table).order_by(news_sources_table.c.name.asc())
            ).mappings()
            return [_to_summary(NewsSource(**dict(row))) for row in rows]

    def get_by_id(self, source_id: str) -> NewsSource | None:
        self._ensure_seed()
        with self._engine.connect() as conn:
            row = (
                conn.execute(
                    select(news_sources_table).where(news_sources_table.c.id == source_id)
                )
                .mappings()
                .one_or_none()
            )
            if row is None:
                return None
            return NewsSource(**dict(row))

    def create(self, payload: NewsSourceCreate) -> NewsSource:
        now = datetime.now(UTC)
        data = {
            "id": f"newssrc_{uuid4().hex}",
            "created_at": now,
            "updated_at": now,
            **payload.model_dump(),
        }
        with self._engine.begin() as conn:
            conn.execute(insert(news_sources_table).values(**data))
        return NewsSource(**data)

    def update(self, source_id: str, payload: NewsSourceUpdate) -> NewsSource | None:
        existing = self.get_by_id(source_id)
        if existing is None:
            return None
        values = payload.model_dump(exclude_unset=True)
        values["updated_at"] = datetime.now(UTC)
        with self._engine.begin() as conn:
            conn.execute(
                update(news_sources_table)
                .where(news_sources_table.c.id == source_id)
                .values(**values)
            )
        return self.get_by_id(source_id)

    def list_due_rss(self, *, now: datetime | None = None) -> list[NewsSource]:
        self._ensure_seed()
        moment = now or datetime.now(UTC)
        with self._engine.connect() as conn:
            rows = conn.execute(
                select(news_sources_table).where(
                    news_sources_table.c.is_enabled.is_(True),
                    news_sources_table.c.source_type == "rss",
                )
            ).mappings()
            due: list[NewsSource] = []
            for row in rows:
                source = NewsSource(**dict(row))
                if source.last_crawled_at is None:
                    due.append(source)
                    continue
                if source.last_crawled_at + timedelta(
                    minutes=source.crawl_frequency_minutes
                ) <= moment:
                    due.append(source)
            return due

    def touch_last_crawled(self, source_id: str, crawled_at: datetime) -> None:
        with self._engine.begin() as conn:
            conn.execute(
                update(news_sources_table)
                .where(news_sources_table.c.id == source_id)
                .values(last_crawled_at=crawled_at, updated_at=crawled_at)
            )


def _to_summary(source: NewsSource) -> NewsSourceSummary:
    return NewsSourceSummary(
        id=source.id,
        name=source.name,
        source_type=source.source_type,
        url_or_identifier=source.url_or_identifier,
        priority=source.priority,
        is_enabled=source.is_enabled,
        last_crawled_at=source.last_crawled_at,
    )


def _source_row(source: NewsSource) -> dict:
    return source.model_dump()


def _default_sources() -> list[NewsSource]:
    now = datetime.now(UTC)
    return [
        NewsSource(
            id="newssrc_openai_blog",
            name="OpenAI Blog RSS",
            source_type="rss",
            url_or_identifier="https://openai.com/blog/rss.xml",
            description="Official OpenAI product and research announcements.",
            priority="high",
            crawl_frequency_minutes=360,
            is_enabled=True,
            credibility_base_score=0.95,
            created_at=now,
            updated_at=now,
        ),
        NewsSource(
            id="newssrc_anthropic_news",
            name="Anthropic News",
            source_type="website",
            url_or_identifier="https://www.anthropic.com/news",
            description="Official Anthropic news page (extraction TBD).",
            priority="high",
            crawl_frequency_minutes=720,
            is_enabled=False,
            credibility_base_score=0.9,
            created_at=now,
            updated_at=now,
        ),
    ]


def create_news_source_routes(
    repository: NewsSourceRepository,
    settings: Settings,
    *,
    enqueue_rss_crawl: Callable[[str], str] | None = None,
    enqueue_extract_raw_item: Callable[[str], str] | None = None,
    raw_items_repository: NewsRawItemRepository | None = None,
    extracted_repository: ExtractedArticleRepository | None = None,
    review_repository: NewsReviewRepository | None = None,
) -> APIRouter:
    def _review_repo(resolved_settings: Settings) -> NewsReviewRepository:
        from backend.app.task_support import news_review_repository

        return review_repository or news_review_repository(resolved_settings)
    def require_identity(
        identity_payload: Annotated[str | None, Header(alias=ADMIN_IDENTITY_HEADER)] = None,
        signature: Annotated[str | None, Header(alias=ADMIN_SIGNATURE_HEADER)] = None,
    ) -> AdminIdentity:
        return require_admin_identity_with_settings(settings, identity_payload, signature)

    router = APIRouter(prefix="/admin/news-sources")

    @router.get("")
    async def list_sources(
        _identity: AdminIdentity = Depends(require_identity),
    ) -> list[NewsSourceSummary]:
        return repository.list_all()

    @router.get("/raw-items/{raw_item_id}/extraction")
    async def get_raw_item_extraction(
        raw_item_id: str,
        _identity: AdminIdentity = Depends(require_identity),
    ):
        from backend.app.task_support import extracted_article_repository, news_raw_item_repository

        raw_repo = raw_items_repository or news_raw_item_repository(settings)
        extracted_repo = extracted_repository or extracted_article_repository(settings)
        if raw_repo.get_by_id(raw_item_id) is None:
            raise HTTPException(status_code=404, detail="Raw item not found")
        row = extracted_repo.get_by_raw_item_id(raw_item_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Extraction not found for raw item")
        return row

    @router.post("/raw-items/{raw_item_id}/extract")
    async def trigger_extract(
        raw_item_id: str,
        _identity: AdminIdentity = Depends(require_identity),
    ):
        from backend.app.news_extraction import ExtractionQueuedResponse, run_extract_raw_item
        from backend.app.task_support import (
            article_extractor,
            extracted_article_repository,
            news_raw_item_repository,
        )

        raw_repo = raw_items_repository or news_raw_item_repository(settings)
        extracted_repo = extracted_repository or extracted_article_repository(settings)
        if raw_repo.get_by_id(raw_item_id) is None:
            raise HTTPException(status_code=404, detail="Raw item not found")

        if enqueue_extract_raw_item is not None:
            return ExtractionQueuedResponse(task_id=enqueue_extract_raw_item(raw_item_id))

        return run_extract_raw_item(
            raw_item_id,
            raw_items=raw_repo,
            extracted=extracted_repo,
            extractor=article_extractor(settings),
            sources=repository,
            review=review_repository or _review_repo(settings),
        )

    @router.get("/{source_id}/raw-items")
    async def list_raw_items(
        source_id: str,
        _identity: AdminIdentity = Depends(require_identity),
    ):
        from backend.app.task_support import news_raw_item_repository

        if repository.get_by_id(source_id) is None:
            raise HTTPException(status_code=404, detail="News source not found")
        raw_repo = raw_items_repository or news_raw_item_repository(settings)
        return raw_repo.list_for_source(source_id)

    @router.get("/{source_id}")
    async def get_source(
        source_id: str,
        _identity: AdminIdentity = Depends(require_identity),
    ) -> NewsSource:
        source = repository.get_by_id(source_id)
        if source is None:
            raise HTTPException(status_code=404, detail="News source not found")
        return source

    @router.post("")
    async def create_source(
        payload: NewsSourceCreate,
        _identity: AdminIdentity = Depends(require_identity),
    ) -> NewsSource:
        return repository.create(payload)

    @router.patch("/{source_id}")
    async def update_source(
        source_id: str,
        payload: NewsSourceUpdate,
        _identity: AdminIdentity = Depends(require_identity),
    ) -> NewsSource:
        source = repository.update(source_id, payload)
        if source is None:
            raise HTTPException(status_code=404, detail="News source not found")
        return source

    @router.post("/{source_id}/crawl")
    async def trigger_crawl(
        source_id: str,
        _identity: AdminIdentity = Depends(require_identity),
    ):
        from backend.app.news_crawl import (
            CrawlQueuedResponse,
            CrawlResult,
            RssFetchError,
            run_rss_crawl,
        )

        source = repository.get_by_id(source_id)
        if source is None:
            raise HTTPException(status_code=404, detail="News source not found")
        if source.source_type != "rss":
            raise HTTPException(
                status_code=400,
                detail="Only RSS sources can be crawled in this story",
            )
        if not source.is_enabled:
            raise HTTPException(status_code=400, detail="News source is disabled")

        if enqueue_rss_crawl is not None:
            task_id = enqueue_rss_crawl(source_id)
            return CrawlQueuedResponse(task_id=task_id)

        from backend.app.task_support import news_raw_item_repository

        try:
            return run_rss_crawl(
                source_id,
                sources=repository,
                raw_items=news_raw_item_repository(settings),
            )
        except RssFetchError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return router
