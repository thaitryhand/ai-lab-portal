"""Celery tasks for the AI Lab Portal."""

from __future__ import annotations

import json

from backend.app.blog_ideas import (
    BlogIdeaCreate,
    OutlineSection,
)
from backend.app.celery_app import celery_app
from backend.app.llm.schemas import BlogDraft
from backend.app.llm.schemas import BlogIdea as BlogIdeaSchema
from backend.app.llm.schemas import BlogOutline
from backend.app.llm.schemas import MarketingMetadata
from backend.app.llm.schemas import TechnicalReview
from backend.app.news_crawl import run_crawl_due_rss_sources, run_rss_crawl
from backend.app.news_extraction import run_extract_pending_raw_items, run_extract_raw_item
from backend.app.news_scoring import run_score_extracted_article, run_score_pending_extractions
from backend.app.task_support import (
    article_extractor,
    extracted_article_repository,
    generation_job_repository,
    idea_repository,
    llm_service_for_idea,
    news_raw_item_repository,
    news_review_repository,
    news_source_repository,
    track_job_lifecycle,
)


def _finish_job(task, jobs, exc: Exception | None = None) -> None:
    if exc is None:
        jobs.mark_completed(task.request.id)
    else:
        jobs.mark_failed(task.request.id, str(exc))


@celery_app.task(name="foundation.smoke")
def foundation_smoke() -> dict[str, str]:
    return {"status": "ok", "task": "foundation.smoke"}


@celery_app.task(name="blog_ideas.generate", bind=True, max_retries=2)
def generate_blog_idea_task(
    self,
    project_name: str,
    project_summary: str,
    ai_capabilities: str = "",
    technical_highlights: str = "",
    business_value: str = "",
) -> dict:
    jobs = track_job_lifecycle(self)
    try:
        service = llm_service_for_idea(self.request.id)
        result = service.generate(
            "blog_idea",
            inputs={
                "project_name": project_name,
                "project_summary": project_summary,
                "ai_capabilities": ai_capabilities,
                "technical_highlights": technical_highlights,
                "business_value": business_value,
            },
            output_schema=BlogIdeaSchema,
        )
        repo = idea_repository()
        idea = repo.add_generated(
            BlogIdeaCreate(
                title=result.title,
                angle=result.angle,
                target_reader=result.target_reader,
                article_goal=result.article_goal,
                positioning_notes=result.positioning_notes,
            ),
            context={
                "project_name": project_name,
                "project_summary": project_summary,
            },
        )
        payload = idea.model_dump()
        _finish_job(self, jobs)
        return payload
    except Exception as exc:
        _finish_job(self, jobs, exc)
        raise self.retry(exc=exc)


@celery_app.task(name="blog_ideas.generate_outline", bind=True, max_retries=2)
def generate_blog_outline_task(self, idea_id: str) -> dict:
    jobs = track_job_lifecycle(self)
    repo = idea_repository()
    idea = repo.get_by_id(idea_id)
    if idea is None:
        _finish_job(self, jobs, ValueError(f"Blog idea {idea_id} not found"))
        raise ValueError(f"Blog idea {idea_id} not found")
    if idea.status != "approved":
        err = ValueError(f"Blog idea {idea_id} is not approved (status={idea.status})")
        _finish_job(self, jobs, err)
        raise err

    positioning_text = ", ".join(idea.positioning_notes) if idea.positioning_notes else ""
    try:
        service = llm_service_for_idea(idea_id)
        result = service.generate(
            "blog_outline",
            inputs={
                "title": idea.title,
                "angle": idea.angle,
                "target_reader": idea.target_reader,
                "article_goal": idea.article_goal,
                "positioning_notes": positioning_text,
            },
            output_schema=BlogOutline,
        )
        sections = [OutlineSection(section=s.section, points=s.points) for s in result.outline]
        updated = repo.set_outline(idea_id, sections, status="pending")
        if updated is None:
            raise RuntimeError(f"Failed to store outline for idea {idea_id}")
        _finish_job(self, jobs)
        return updated.model_dump()
    except Exception as exc:
        _finish_job(self, jobs, exc)
        raise self.retry(exc=exc)


@celery_app.task(name="blog_ideas.generate_draft", bind=True, max_retries=2)
def generate_blog_draft_task(self, idea_id: str) -> dict:
    jobs = track_job_lifecycle(self)
    repo = idea_repository()
    idea = repo.get_by_id(idea_id)
    if idea is None:
        _finish_job(self, jobs, ValueError(f"Blog idea {idea_id} not found"))
        raise ValueError(f"Blog idea {idea_id} not found")
    if idea.outline_status != "approved":
        err = ValueError(
            f"Blog idea {idea_id} outline is not approved (status={idea.outline_status})"
        )
        _finish_job(self, jobs, err)
        raise err

    context_parts = [
        f"Title: {idea.title}",
        f"Angle: {idea.angle}",
        f"Target reader: {idea.target_reader}",
        f"Article goal: {idea.article_goal}",
    ]
    if idea.positioning_notes:
        context_parts.append(f"Positioning notes: {', '.join(idea.positioning_notes)}")
    project_context = "\n".join(context_parts)
    outline_json = json.dumps(
        [{"section": s.section, "points": s.points} for s in idea.outline_sections],
        indent=2,
    )
    positioning = ", ".join(idea.positioning_notes) if idea.positioning_notes else "N/A"

    try:
        service = llm_service_for_idea(idea_id)
        result = service.generate(
            "draft_writer",
            inputs={
                "outline_json": outline_json,
                "project_context": project_context,
                "positioning_notes": positioning,
            },
            output_schema=BlogDraft,
        )
        updated = repo.set_draft(idea_id, result.markdown, status="pending")
        if updated is None:
            raise RuntimeError(f"Failed to store draft for idea {idea_id}")
        _finish_job(self, jobs)
        return updated.model_dump()
    except Exception as exc:
        _finish_job(self, jobs, exc)
        raise self.retry(exc=exc)


@celery_app.task(name="blog_ideas.review_technical", bind=True, max_retries=2)
def generate_technical_review_task(self, idea_id: str) -> dict:
    jobs = track_job_lifecycle(self)
    repo = idea_repository()
    idea = repo.get_by_id(idea_id)
    if idea is None:
        _finish_job(self, jobs, ValueError(f"Blog idea {idea_id} not found"))
        raise ValueError(f"Blog idea {idea_id} not found")
    if idea.draft_status != "approved":
        err = ValueError(
            f"Blog idea {idea_id} draft is not approved (status={idea.draft_status})"
        )
        _finish_job(self, jobs, err)
        raise err

    project_context_parts = [
        f"Title: {idea.title}",
        f"Angle: {idea.angle}",
        f"Target reader: {idea.target_reader}",
        f"Article goal: {idea.article_goal}",
    ]
    if idea.positioning_notes:
        project_context_parts.append(
            f"Positioning notes: {', '.join(idea.positioning_notes)}"
        )
    project_context = "\n".join(project_context_parts)

    try:
        service = llm_service_for_idea(idea_id)
        result = service.generate(
            "technical_review",
            inputs={
                "draft_markdown": idea.draft_markdown or "",
                "project_context": project_context,
            },
            output_schema=TechnicalReview,
        )
        updated = repo.set_technical_review(idea_id, result.model_dump(), status="pending")
        if updated is None:
            raise RuntimeError(f"Failed to store technical review for idea {idea_id}")
        _finish_job(self, jobs)
        return updated.model_dump()
    except Exception as exc:
        _finish_job(self, jobs, exc)
        raise self.retry(exc=exc)


@celery_app.task(name="blog_ideas.generate_marketing", bind=True, max_retries=2)
def generate_marketing_metadata_task(self, idea_id: str) -> dict:
    jobs = track_job_lifecycle(self)
    repo = idea_repository()
    idea = repo.get_by_id(idea_id)
    if idea is None:
        _finish_job(self, jobs, ValueError(f"Blog idea {idea_id} not found"))
        raise ValueError(f"Blog idea {idea_id} not found")
    if idea.draft_status != "approved":
        err = ValueError(
            f"Blog idea {idea_id} draft is not approved (status={idea.draft_status})"
        )
        _finish_job(self, jobs, err)
        raise err

    try:
        service = llm_service_for_idea(idea_id)
        result = service.generate(
            "marketing_metadata",
            inputs={
                "draft_markdown": idea.draft_markdown or "",
                "title": idea.title,
                "angle": idea.angle,
                "target_reader": idea.target_reader,
            },
            output_schema=MarketingMetadata,
        )
        updated = repo.set_marketing_metadata(idea_id, result.model_dump(), status="pending")
        if updated is None:
            raise RuntimeError(
                f"Failed to store marketing metadata for idea {idea_id}"
            )
        _finish_job(self, jobs)
        return updated.model_dump()
    except Exception as exc:
        _finish_job(self, jobs, exc)
        raise self.retry(exc=exc)


@celery_app.task(name="news.crawl_rss_source")
def crawl_rss_source_task(source_id: str) -> dict:
    sources = news_source_repository()
    raw_items = news_raw_item_repository()
    result = run_rss_crawl(source_id, sources=sources, raw_items=raw_items)
    return result.model_dump()


@celery_app.task(name="news.crawl_due_sources")
def crawl_due_rss_sources_task() -> list[dict]:
    sources = news_source_repository()
    raw_items = news_raw_item_repository()
    results = run_crawl_due_rss_sources(sources=sources, raw_items=raw_items)
    return [r.model_dump() for r in results]


@celery_app.task(name="news.extract_raw_item")
def extract_raw_item_task(raw_item_id: str) -> dict:
    result = run_extract_raw_item(
        raw_item_id,
        raw_items=news_raw_item_repository(),
        extracted=extracted_article_repository(),
        extractor=article_extractor(),
        sources=news_source_repository(),
        review=news_review_repository(),
    )
    return result.model_dump()


@celery_app.task(name="news.extract_pending_raw_items")
def extract_pending_raw_items_task(source_id: str | None = None) -> list[dict]:
    results = run_extract_pending_raw_items(
        raw_items=news_raw_item_repository(),
        extracted=extracted_article_repository(),
        extractor=article_extractor(),
        source_id=source_id,
        sources=news_source_repository(),
        review=news_review_repository(),
    )
    return [r.model_dump() for r in results]


@celery_app.task(name="news.score_extracted_article")
def score_extracted_article_task(extracted_article_id: str) -> dict:
    result = run_score_extracted_article(
        extracted_article_id,
        extracted=extracted_article_repository(),
        raw_items=news_raw_item_repository(),
        sources=news_source_repository(),
        review=news_review_repository(),
    )
    return result.model_dump()


@celery_app.task(name="news.score_pending_extractions")
def score_pending_extractions_task(source_id: str | None = None) -> list[dict]:
    results = run_score_pending_extractions(
        extracted=extracted_article_repository(),
        raw_items=news_raw_item_repository(),
        sources=news_source_repository(),
        review=news_review_repository(),
        source_id=source_id,
    )
    return [r.model_dump() for r in results]
