"""Shared helpers for Celery tasks (LLM recording, generation job status)."""

from __future__ import annotations

from backend.app.ai_runs import AiRunRepository, PostgresAiRunRepository
from backend.app.blog_ideas import BlogIdeaRepository, PostgresBlogIdeaRepository
from backend.app.database import create_database_engine
from backend.app.generation_jobs import (
    GenerationJobRepository,
    PostgresGenerationJobRepository,
)
from backend.app.llm.recording import RecordingLLMService
from backend.app.llm.service import LLMService, OpenAILLMService
from backend.app.news_crawl import NewsRawItemRepository, PostgresNewsRawItemRepository
from backend.app.news_extraction import (
    ExtractedArticleRepository,
    PostgresExtractedArticleRepository,
    extractor_for_settings,
)
from backend.app.news_sources import NewsSourceRepository, PostgresNewsSourceRepository
from backend.app.news_scoring import (
    InMemoryNewsReviewRepository,
    PostgresNewsReviewRepository,
    NewsReviewRepository,
)
from backend.app.settings import Settings


def news_source_repository(settings: Settings | None = None) -> NewsSourceRepository:
    resolved = settings or Settings()
    if resolved.environment == "test":
        return NewsSourceRepository()
    return PostgresNewsSourceRepository(create_database_engine(resolved))


def news_raw_item_repository(settings: Settings | None = None) -> NewsRawItemRepository:
    resolved = settings or Settings()
    if resolved.environment == "test":
        return NewsRawItemRepository()
    return PostgresNewsRawItemRepository(create_database_engine(resolved))


def extracted_article_repository(
    settings: Settings | None = None,
) -> ExtractedArticleRepository:
    resolved = settings or Settings()
    if resolved.environment == "test":
        return ExtractedArticleRepository()
    return PostgresExtractedArticleRepository(create_database_engine(resolved))


def article_extractor(settings: Settings | None = None):
    return extractor_for_settings(settings or Settings())


def news_review_repository(settings: Settings | None = None) -> NewsReviewRepository:
    resolved = settings or Settings()
    if resolved.environment == "test":
        return InMemoryNewsReviewRepository()
    return PostgresNewsReviewRepository(create_database_engine(resolved))


def idea_repository(settings: Settings | None = None) -> BlogIdeaRepository:
    resolved = settings or Settings()
    if resolved.environment == "test":
        return BlogIdeaRepository()
    return PostgresBlogIdeaRepository(create_database_engine(resolved))


def ai_run_repository(settings: Settings | None = None) -> AiRunRepository | None:
    resolved = settings or Settings()
    if resolved.environment == "test":
        return AiRunRepository()
    return PostgresAiRunRepository(create_database_engine(resolved))


def generation_job_repository(
    settings: Settings | None = None,
) -> GenerationJobRepository:
    resolved = settings or Settings()
    if resolved.environment == "test":
        return GenerationJobRepository()
    return PostgresGenerationJobRepository(create_database_engine(resolved))


def llm_service_for_idea(
    idea_id: str,
    settings: Settings | None = None,
) -> LLMService:
    resolved = settings or Settings()
    api_key = resolved.llm_openai_api_key.get_secret_value()
    if not api_key:
        raise RuntimeError(
            "AI_LAB_LLM_OPENAI_API_KEY is not set. "
            "Add it to .env or the process environment."
        )
    inner = OpenAILLMService(api_key=api_key, model=resolved.llm_model)
    recorder = ai_run_repository(resolved)
    if recorder is None:
        return inner
    return RecordingLLMService(
        inner,
        recorder,
        entity_type="blog_idea",
        entity_id=idea_id,
        provider="openai",
        model=resolved.llm_model,
    )


def track_job_lifecycle(task) -> GenerationJobRepository:
    """Mark a Celery task running; caller should complete/fail on exit."""
    jobs = generation_job_repository()
    jobs.mark_running(task.request.id)
    return jobs
