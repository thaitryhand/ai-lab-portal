"""Celery tasks for the AI Lab Portal."""

from __future__ import annotations

import json
from typing import cast

from backend.app.blog_agent_context import build_project_context
from backend.app.blog_ideas import (
    BlogIdeaCreate,
    OutlineSection,
    marketing_metadata_for_storage,
)
from backend.app.celery_app import celery_app
from backend.app.llm.schemas import (
    BlogDraft,
    BlogDraftSection,
    BlogOutline,
    MarketingMetadata,
    TechnicalReview,
)
from backend.app.llm.schemas import BlogIdea as BlogIdeaSchema
from backend.app.news_crawl import run_crawl_due_rss_sources, run_rss_crawl
from backend.app.news_extraction import (
    run_extract_pending_raw_items,
    run_extract_raw_item,
)
from backend.app.news_scoring import (
    run_score_extracted_article,
    run_score_pending_extractions,
)
from backend.app.news_submitted_links import run_process_submitted_link
from backend.app.task_support import (
    article_extractor,
    extracted_article_repository,
    idea_repository,
    llm_service_for_idea,
    llm_service_for_news_item,
    news_raw_item_repository,
    news_review_repository,
    news_source_repository,
    submitted_link_repository,
    track_job_lifecycle,
)


def _finish_job(task, jobs, exc: Exception | None = None) -> None:
    if exc is None:
        jobs.mark_completed(task.request.id)
    else:
        jobs.mark_failed(task.request.id, str(exc))


def _idea_create_from_llm(result: BlogIdeaSchema) -> BlogIdeaCreate:
    """Map LLM output to persisted idea fields (DB column limits)."""
    return BlogIdeaCreate(
        title=result.title[:240],
        angle=result.angle[:160],
        target_reader=result.target_reader[:160],
        article_goal=result.article_goal,
        positioning_notes=result.positioning_notes,
    )


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
        result = cast(
            BlogIdeaSchema,
            service.generate(
                "blog_idea",
                inputs={
                    "project_name": project_name,
                    "project_summary": project_summary,
                    "ai_capabilities": ai_capabilities,
                    "technical_highlights": technical_highlights,
                    "business_value": business_value,
                },
                output_schema=BlogIdeaSchema,
            ),
        )
        repo = idea_repository()
        idea = repo.add_generated(
            _idea_create_from_llm(result),
            context={
                "project_name": project_name,
                "project_summary": project_summary,
                "ai_capabilities": ai_capabilities,
                "technical_highlights": technical_highlights,
                "business_value": business_value,
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

    positioning_text = (
        ", ".join(idea.positioning_notes) if idea.positioning_notes else ""
    )
    project_context = build_project_context(idea)
    try:
        service = llm_service_for_idea(idea_id)
        result = cast(
            BlogOutline,
            service.generate(
                "blog_outline",
                inputs={
                    "title": idea.title,
                    "angle": idea.angle,
                    "target_reader": idea.target_reader,
                    "article_goal": idea.article_goal,
                    "positioning_notes": positioning_text,
                    "project_context": project_context,
                },
                output_schema=BlogOutline,
            ),
        )
        sections = [
            OutlineSection(section=s.section, points=s.points) for s in result.outline
        ]
        updated = repo.set_outline(idea_id, sections, status="pending")
        if updated is None:
            raise RuntimeError(f"Failed to store outline for idea {idea_id}")
        _finish_job(self, jobs)
        return updated.model_dump()
    except Exception as exc:
        _finish_job(self, jobs, exc)
        raise self.retry(exc=exc)


def _word_count(text: str) -> int:
    import re

    return len(re.findall(r"\b\w+\b", text))


_DRAFT_MIN_WORDS = 1500
_DRAFT_TARGET_WORDS = 1800
_DRAFT_MAX_ATTEMPTS = 3


def _generate_blog_draft_sectional(
    service,
    inputs: dict[str, str],
    sections: list[dict[str, object]],
    title: str,
) -> BlogDraft:
    """Expand each outline section separately to avoid structured-output truncation."""
    parts: list[str] = []
    prior_summary = "None yet — this is the opening section."
    total = len(sections)

    for index, section in enumerate(sections, start=1):
        heading = str(section.get("section", f"Section {index}"))
        points = section.get("points") or []
        result = cast(
            BlogDraftSection,
            service.generate(
                "draft_section_writer",
                inputs={
                    **inputs,
                    "section_heading": heading,
                    "section_points": json.dumps(points, indent=2),
                    "section_index": str(index),
                    "section_total": str(total),
                    "prior_sections_summary": prior_summary,
                },
                output_schema=BlogDraftSection,
            ),
        )
        body = result.markdown.strip()
        parts.append(f"## {heading}\n\n{body}")
        prior_summary = (
            f"{prior_summary}\n- {heading}: {body[:280].replace(chr(10), ' ')}..."
        )

    return BlogDraft(title=title, markdown="\n\n".join(parts))


def _generate_blog_draft(
    service,
    inputs: dict[str, str],
    *,
    sections: list[dict[str, object]] | None = None,
    title: str = "Blog post",
) -> BlogDraft:
    """Generate draft via sectional expansion, with monolithic fallback retries."""
    if sections:
        sectional = _generate_blog_draft_sectional(service, inputs, sections, title)
        if _word_count(sectional.markdown) >= _DRAFT_MIN_WORDS:
            return sectional

    attempt_inputs = dict(inputs)
    best: BlogDraft | None = None
    best_words = 0

    for attempt in range(1, _DRAFT_MAX_ATTEMPTS + 1):
        result = cast(
            BlogDraft,
            service.generate(
                "draft_writer",
                inputs=attempt_inputs,
                output_schema=BlogDraft,
            ),
        )
        words = _word_count(result.markdown)
        if words > best_words:
            best = result
            best_words = words
        if words >= _DRAFT_MIN_WORDS:
            return result

        attempt_inputs = {
            **inputs,
            "positioning_notes": (
                f"{inputs['positioning_notes']}\n\n"
                f"REVISION REQUIRED (attempt {attempt}/{_DRAFT_MAX_ATTEMPTS}): "
                f"the previous draft was only {words} words. Write at least "
                f"{_DRAFT_TARGET_WORDS} words of natural English prose. Expand "
                "every outline section to 2–4 paragraphs with concrete examples "
                "from the project context (stack, workflow, gates, trade-offs). "
                "Do not shorten or summarize sections."
            ),
        }

    if sections:
        sectional = _generate_blog_draft_sectional(service, inputs, sections, title)
        if _word_count(sectional.markdown) >= 900:
            return sectional

    if best is None:
        raise RuntimeError("Draft generation returned no content")
    if best_words < 900:
        raise RuntimeError(
            f"Draft too short after {_DRAFT_MAX_ATTEMPTS} attempts ({best_words} words)"
        )
    return best


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

    project_context = build_project_context(idea)
    outline_json = json.dumps(
        [{"section": s.section, "points": s.points} for s in idea.outline_sections],
        indent=2,
    )
    outline_sections = [
        {"section": s.section, "points": s.points} for s in idea.outline_sections
    ]
    positioning = ", ".join(idea.positioning_notes) if idea.positioning_notes else "N/A"

    try:
        service = llm_service_for_idea(idea_id)
        result = _generate_blog_draft(
            service,
            {
                "outline_json": outline_json,
                "project_context": project_context,
                "positioning_notes": positioning,
            },
            sections=outline_sections,
            title=idea.title,
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

    project_context = build_project_context(idea)

    try:
        service = llm_service_for_idea(idea_id)
        result = cast(
            TechnicalReview,
            service.generate(
                "technical_review",
                inputs={
                    "draft_markdown": idea.draft_markdown or "",
                    "project_context": project_context,
                },
                output_schema=TechnicalReview,
            ),
        )
        updated = repo.set_technical_review(
            idea_id, result.model_dump(), status="pending"
        )
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
        result = cast(
            MarketingMetadata,
            service.generate(
                "marketing_metadata",
                inputs={
                    "draft_markdown": idea.draft_markdown or "",
                    "title": idea.title,
                    "angle": idea.angle,
                    "target_reader": idea.target_reader,
                },
                output_schema=MarketingMetadata,
            ),
        )
        updated = repo.set_marketing_metadata(
            idea_id, marketing_metadata_for_storage(result), status="pending"
        )
        if updated is None:
            raise RuntimeError(f"Failed to store marketing metadata for idea {idea_id}")
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
        llm=llm_service_for_news_item(extracted_article_id),
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


@celery_app.task(name="news.process_submitted_link")
def process_submitted_link_task(submission_id: str) -> dict:
    row = run_process_submitted_link(
        submission_id,
        repository=submitted_link_repository(),
        extracted=extracted_article_repository(),
        raw_items=news_raw_item_repository(),
        sources=news_source_repository(),
        review=news_review_repository(),
        extractor=article_extractor(),
    )
    return row.model_dump()


# --- US-055: X/Twitter social ingestion spike ---


@celery_app.task(name="news.ingest_social_x_source")
def ingest_social_x_source_task(source_id: str) -> dict:
    from backend.app.news_social_x_ingest import run_social_x_ingest

    result = run_social_x_ingest(
        source_id,
        sources=news_source_repository(),
        raw_items=news_raw_item_repository(),
    )
    return result.model_dump()


@celery_app.task(name="news.ingest_due_social_x_sources")
def ingest_due_social_x_sources_task() -> list[dict]:
    from backend.app.news_social_x_ingest import run_due_social_x_sources

    results = run_due_social_x_sources(
        sources=news_source_repository(),
        raw_items=news_raw_item_repository(),
    )
    return [r.model_dump() for r in results]
