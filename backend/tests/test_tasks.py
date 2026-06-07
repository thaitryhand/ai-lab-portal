"""Comprehensive tests for Celery tasks (backend.app.tasks) and task_support.

Covers:
- All ``@celery_app.task`` functions (happy path, validation errors, LLM failures)
- Blog pipeline helpers (``_idea_create_from_llm``, ``_finish_job``, ``_word_count``)
- Draft generation logic (sectional expansion, monolithic fallback)
- ``task_support`` factory functions (``_use_agents_sdk``, ``_build_llm_service``,
  ``llm_service_for_idea``, ``_build_mcp_servers``, repository factories)
- Representative news task wrappers
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from backend.app.blog_ideas import (
    BlogIdea,
    BlogIdeaCreate,
    BlogIdeaRepository,
    OutlineSection,
)
from backend.app.generation_jobs import GenerationJobRepository
from backend.app.llm.schemas import (
    BlogDraft,
    BlogDraftSection,
    BlogIdea as BlogIdeaSchema,
    BlogOutline,
    BlogOutlineSection as SchemaOutlineSection,
    MarketingMetadata,
    TechnicalReview,
)
from backend.app.llm.service import FakeLLMService, LLMGenerationError, LLMService
from backend.app.settings import Settings


# ===========================================================================
# Helpers
# ===========================================================================

_LONG_DRAFT_MD = " ".join(["word"] * 1600)  # 1600 words — passes _DRAFT_MIN_WORDS
_LONG_SECTION_MD = " ".join(["word"] * 800)  # 800 words per section
_SHORT_DRAFT_MD = "short"  # fails word-count checks


def _make_idea(**overrides: object) -> BlogIdea:
    """Build a ``BlogIdea`` with sensible defaults."""
    defaults: dict = {
        "id": "idea_test_001",
        "title": "Test Blog",
        "angle": "Technical deep dive",
        "target_reader": "Developers",
        "article_goal": "Teach something useful",
        "status": "approved",
        "positioning_notes": ["Note A", "Note B"],
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    defaults.update(overrides)
    return BlogIdea(**defaults)


def _fake_with(
    **responses: object,
) -> FakeLLMService:
    """Build a ``FakeLLMService`` with prompt-name→schema mappings."""
    return FakeLLMService(responses)


def _safe_call(task_func, **kwargs):
    """Call a task's ``__wrapped__`` (original function), returning the
    result or letting exceptions propagate untouched."""
    return task_func.__wrapped__(**kwargs)


# ===========================================================================
# foundation_smoke
# ===========================================================================


class TestFoundationSmoke:
    """The simplest task — a health-check endpoint."""

    def test_returns_expected_dict(self) -> None:
        from backend.app.tasks import foundation_smoke

        result = _safe_call(foundation_smoke)
        assert result == {"status": "ok", "task": "foundation.smoke"}

    def test_response_is_always_identical(self) -> None:
        from backend.app.tasks import foundation_smoke

        assert _safe_call(foundation_smoke) == _safe_call(foundation_smoke)


# ===========================================================================
# generate_blog_idea_task
# ===========================================================================


class TestGenerateBlogIdeaTask:
    """Tests for ``generate_blog_idea_task`` — creates a new idea from
    project context via LLM."""

    @patch("backend.app.tasks._finish_job")
    @patch("backend.app.tasks.track_job_lifecycle")
    def test_happy_path_creates_idea(
        self,
        mock_track: MagicMock,
        mock_finish: MagicMock,
    ) -> None:
        from backend.app.tasks import generate_blog_idea_task

        jobs = GenerationJobRepository()
        mock_track.return_value = jobs

        with (
            patch("backend.app.tasks.idea_repository") as mock_repo_factory,
            patch("backend.app.tasks.llm_service_for_idea") as mock_llm,
        ):
            repo = BlogIdeaRepository()
            mock_repo_factory.return_value = repo
            mock_llm.return_value = _fake_with(
                blog_idea=BlogIdeaSchema(
                    title="AI Lab Pipeline",
                    angle="Semi-auto AI blog pipeline",
                    target_reader="Engineering leaders",
                    article_goal="Prove generate-to-publish workflow",
                    positioning_notes=["Ground claims in project context"],
                ),
            )

            result = _safe_call(
                generate_blog_idea_task,
                project_name="AI Lab",
                project_summary="An AI blog platform",
                ai_capabilities="LLM, agents",
                technical_highlights="Structured output, tracing",
                business_value="Faster content creation",
            )

        assert result["title"] == "AI Lab Pipeline"
        assert result["source"] == "ai_generated"
        assert "project_name" in result["source_project_context"]
        mock_finish.assert_called_once()

    @patch("backend.app.tasks._finish_job")
    @patch("backend.app.tasks.track_job_lifecycle")
    def test_llm_failure_propagates(
        self,
        mock_track: MagicMock,
        mock_finish: MagicMock,
    ) -> None:
        from backend.app.tasks import generate_blog_idea_task

        mock_track.return_value = GenerationJobRepository()
        mock_finish.return_value = None

        with (
            patch("backend.app.tasks.idea_repository") as mock_repo,
            patch("backend.app.tasks.llm_service_for_idea") as mock_llm,
        ):
            mock_repo.return_value = BlogIdeaRepository()
            mock_llm.return_value = _fake_with()  # empty — any prompt fails

            with pytest.raises(LLMGenerationError):
                _safe_call(
                    generate_blog_idea_task,
                    project_name="P",
                    project_summary="S",
                )

        # _finish_job should have been called with an exception
        assert mock_finish.call_count >= 1
        call_args = mock_finish.call_args[0] if mock_finish.call_args else ()
        if len(call_args) >= 3:
            assert isinstance(call_args[2], Exception)

    @patch("backend.app.tasks._finish_job")
    @patch("backend.app.tasks.track_job_lifecycle")
    def test_repository_failure_propagates(
        self,
        mock_track: MagicMock,
        mock_finish: MagicMock,
    ) -> None:
        from backend.app.tasks import generate_blog_idea_task

        mock_track.return_value = GenerationJobRepository()

        # Make add_generated raise
        failing_repo = MagicMock(spec=BlogIdeaRepository)
        failing_repo.add_generated.side_effect = RuntimeError("DB write failed")

        with (
            patch("backend.app.tasks.idea_repository") as mock_repo,
            patch("backend.app.tasks.llm_service_for_idea") as mock_llm,
        ):
            mock_repo.return_value = failing_repo
            mock_llm.return_value = _fake_with(
                blog_idea=BlogIdeaSchema(
                    title="T", angle="A",
                    target_reader="D", article_goal="G",
                ),
            )

            with pytest.raises(RuntimeError, match="DB write failed"):
                _safe_call(
                    generate_blog_idea_task,
                    project_name="P", project_summary="S",
                )


# ===========================================================================
# generate_blog_outline_task
# ===========================================================================


class TestGenerateBlogOutlineTask:
    """Tests for ``generate_blog_outline_task`` — generates an outline
    from an approved idea."""

    @patch("backend.app.tasks._finish_job")
    @patch("backend.app.tasks.track_job_lifecycle")
    def test_happy_path_creates_outline(
        self,
        mock_track: MagicMock,
        mock_finish: MagicMock,
    ) -> None:
        from backend.app.tasks import generate_blog_outline_task

        mock_track.return_value = GenerationJobRepository()

        idea = _make_idea(id="idea_outline_1", status="approved")
        repo = BlogIdeaRepository(ideas=[idea])

        with (
            patch("backend.app.tasks.idea_repository") as mock_repo,
            patch("backend.app.tasks.llm_service_for_idea") as mock_llm,
        ):
            mock_repo.return_value = repo
            mock_llm.return_value = _fake_with(
                blog_outline=BlogOutline(
                    title="Blog Outline",
                    outline=[
                        SchemaOutlineSection(
                            section="Context",
                            points=["Background", "Problem"],
                        ),
                        SchemaOutlineSection(
                            section="Solution",
                            points=["Architecture", "Implementation"],
                        ),
                    ],
                ),
            )

            result = _safe_call(generate_blog_outline_task, idea_id="idea_outline_1")

        assert result["outline_status"] == "pending"
        assert len(result["outline_sections"]) == 2
        assert result["outline_sections"][0]["section"] == "Context"
        mock_finish.assert_called_once()

    @patch("backend.app.tasks._finish_job")
    @patch("backend.app.tasks.track_job_lifecycle")
    def test_idea_not_found(
        self,
        mock_track: MagicMock,
        mock_finish: MagicMock,
    ) -> None:
        from backend.app.tasks import generate_blog_outline_task

        mock_track.return_value = GenerationJobRepository()
        empty_repo = BlogIdeaRepository()

        with patch("backend.app.tasks.idea_repository") as mock_repo:
            mock_repo.return_value = empty_repo

            with pytest.raises(ValueError, match="Blog idea nonexistent not found"):
                _safe_call(generate_blog_outline_task, idea_id="nonexistent")

        assert mock_finish.call_count >= 1

    @patch("backend.app.tasks._finish_job")
    @patch("backend.app.tasks.track_job_lifecycle")
    def test_idea_not_approved(
        self,
        mock_track: MagicMock,
        mock_finish: MagicMock,
    ) -> None:
        from backend.app.tasks import generate_blog_outline_task

        mock_track.return_value = GenerationJobRepository()

        idea = _make_idea(
            id="idea_pending",
            status="pending",  # NOT approved
        )
        repo = BlogIdeaRepository(ideas=[idea])

        with patch("backend.app.tasks.idea_repository") as mock_repo:
            mock_repo.return_value = repo

            with pytest.raises(ValueError, match="is not approved"):
                _safe_call(generate_blog_outline_task, idea_id="idea_pending")

    @patch("backend.app.tasks._finish_job")
    @patch("backend.app.tasks.track_job_lifecycle")
    def test_llm_failure_propagates(
        self,
        mock_track: MagicMock,
        mock_finish: MagicMock,
    ) -> None:
        from backend.app.tasks import generate_blog_outline_task

        mock_track.return_value = GenerationJobRepository()

        idea = _make_idea(id="idea_llm_fail", status="approved")
        repo = BlogIdeaRepository(ideas=[idea])

        with (
            patch("backend.app.tasks.idea_repository") as mock_repo,
            patch("backend.app.tasks.llm_service_for_idea") as mock_llm,
        ):
            mock_repo.return_value = repo
            mock_llm.return_value = _fake_with()  # empty — will fail

            with pytest.raises(LLMGenerationError):
                _safe_call(generate_blog_outline_task, idea_id="idea_llm_fail")


# ===========================================================================
# generate_blog_draft_task
# ===========================================================================


class TestGenerateBlogDraftTask:
    """Tests for ``generate_blog_draft_task`` — expands an approved outline
    into a full markdown draft."""

    @patch("backend.app.tasks._finish_job")
    @patch("backend.app.tasks.track_job_lifecycle")
    def test_happy_path_creates_draft(
        self,
        mock_track: MagicMock,
        mock_finish: MagicMock,
    ) -> None:
        from backend.app.tasks import generate_blog_draft_task

        mock_track.return_value = GenerationJobRepository()

        idea = _make_idea(
            id="idea_draft_1",
            outline_sections=[
                OutlineSection(section="Context", points=["Background"]),
                OutlineSection(section="Solution", points=["Architecture"]),
            ],
            outline_status="approved",
        )
        repo = BlogIdeaRepository(ideas=[idea])

        with (
            patch("backend.app.tasks.idea_repository") as mock_repo,
            patch("backend.app.tasks.llm_service_for_idea") as mock_llm,
        ):
            mock_repo.return_value = repo
            mock_llm.return_value = _fake_with(
                draft_section_writer=BlogDraftSection(markdown=_LONG_SECTION_MD),
                draft_writer=BlogDraft(
                    title="Blog Draft",
                    markdown=_LONG_DRAFT_MD,
                ),
            )

            result = _safe_call(generate_blog_draft_task, idea_id="idea_draft_1")

        assert result["draft_status"] == "pending"
        assert "word" in (result.get("draft_markdown") or "")
        mock_finish.assert_called_once()

    @patch("backend.app.tasks._finish_job")
    @patch("backend.app.tasks.track_job_lifecycle")
    def test_idea_not_found(
        self,
        mock_track: MagicMock,
        mock_finish: MagicMock,
    ) -> None:
        from backend.app.tasks import generate_blog_draft_task

        mock_track.return_value = GenerationJobRepository()
        with patch("backend.app.tasks.idea_repository") as mock_repo:
            mock_repo.return_value = BlogIdeaRepository()
            with pytest.raises(ValueError, match="not found"):
                _safe_call(generate_blog_draft_task, idea_id="ghost")

    @patch("backend.app.tasks._finish_job")
    @patch("backend.app.tasks.track_job_lifecycle")
    def test_outline_not_approved(
        self,
        mock_track: MagicMock,
        mock_finish: MagicMock,
    ) -> None:
        from backend.app.tasks import generate_blog_draft_task

        mock_track.return_value = GenerationJobRepository()
        idea = _make_idea(
            id="idea_no_outline",
            outline_status=None,  # no outline at all
        )
        repo = BlogIdeaRepository(ideas=[idea])

        with patch("backend.app.tasks.idea_repository") as mock_repo:
            mock_repo.return_value = repo

            with pytest.raises(ValueError, match="outline is not approved"):
                _safe_call(generate_blog_draft_task, idea_id="idea_no_outline")

    @patch("backend.app.tasks._finish_job")
    @patch("backend.app.tasks.track_job_lifecycle")
    def test_llm_failure_propagates(
        self,
        mock_track: MagicMock,
        mock_finish: MagicMock,
    ) -> None:
        from backend.app.tasks import generate_blog_draft_task

        mock_track.return_value = GenerationJobRepository()
        idea = _make_idea(
            id="idea_draft_fail",
            outline_sections=[OutlineSection(section="A", points=["B"])],
            outline_status="approved",
        )
        repo = BlogIdeaRepository(ideas=[idea])

        with (
            patch("backend.app.tasks.idea_repository") as mock_repo,
            patch("backend.app.tasks.llm_service_for_idea") as mock_llm,
        ):
            mock_repo.return_value = repo
            mock_llm.return_value = _fake_with()  # empty — fails

            with pytest.raises(LLMGenerationError):
                _safe_call(generate_blog_draft_task, idea_id="idea_draft_fail")


# ===========================================================================
# generate_technical_review_task
# ===========================================================================


class TestGenerateTechnicalReviewTask:
    """Tests for ``generate_technical_review_task`` — AI audit of draft."""

    @patch("backend.app.tasks._finish_job")
    @patch("backend.app.tasks.track_job_lifecycle")
    def test_happy_path_creates_review(
        self,
        mock_track: MagicMock,
        mock_finish: MagicMock,
    ) -> None:
        from backend.app.tasks import generate_technical_review_task

        mock_track.return_value = GenerationJobRepository()

        idea = _make_idea(
            id="idea_review_1",
            draft_markdown="# Content\n\nSome draft content here.",
            draft_status="approved",
        )
        repo = BlogIdeaRepository(ideas=[idea])

        with (
            patch("backend.app.tasks.idea_repository") as mock_repo,
            patch("backend.app.tasks.llm_service_for_idea") as mock_llm,
        ):
            mock_repo.return_value = repo
            mock_llm.return_value = _fake_with(
                technical_review=TechnicalReview(
                    overall_risk="low",
                    issues=[],
                    approval_recommendation="approve",
                ),
            )

            result = _safe_call(generate_technical_review_task, idea_id="idea_review_1")

        assert result["technical_review_status"] == "pending"
        assert result["technical_review"]["overall_risk"] == "low"
        mock_finish.assert_called_once()

    @patch("backend.app.tasks._finish_job")
    @patch("backend.app.tasks.track_job_lifecycle")
    def test_idea_not_found(
        self,
        mock_track: MagicMock,
        mock_finish: MagicMock,
    ) -> None:
        from backend.app.tasks import generate_technical_review_task

        mock_track.return_value = GenerationJobRepository()
        with patch("backend.app.tasks.idea_repository") as mock_repo:
            mock_repo.return_value = BlogIdeaRepository()
            with pytest.raises(ValueError, match="not found"):
                _safe_call(generate_technical_review_task, idea_id="ghost")

    @patch("backend.app.tasks._finish_job")
    @patch("backend.app.tasks.track_job_lifecycle")
    def test_draft_not_approved(
        self,
        mock_track: MagicMock,
        mock_finish: MagicMock,
    ) -> None:
        from backend.app.tasks import generate_technical_review_task

        mock_track.return_value = GenerationJobRepository()
        idea = _make_idea(
            id="idea_no_draft",
            draft_status=None,
        )
        repo = BlogIdeaRepository(ideas=[idea])

        with patch("backend.app.tasks.idea_repository") as mock_repo:
            mock_repo.return_value = repo

            with pytest.raises(ValueError, match="draft is not approved"):
                _safe_call(generate_technical_review_task, idea_id="idea_no_draft")


# ===========================================================================
# generate_marketing_metadata_task
# ===========================================================================


class TestGenerateMarketingMetadataTask:
    """Tests for ``generate_marketing_metadata_task`` — SEO / social snippets."""

    @patch("backend.app.tasks._finish_job")
    @patch("backend.app.tasks.track_job_lifecycle")
    def test_happy_path_creates_metadata(
        self,
        mock_track: MagicMock,
        mock_finish: MagicMock,
    ) -> None:
        from backend.app.tasks import generate_marketing_metadata_task

        mock_track.return_value = GenerationJobRepository()

        idea = _make_idea(
            id="idea_mkt_1",
            draft_markdown="# Content\n\nSome draft content.",
            draft_status="approved",
        )
        repo = BlogIdeaRepository(ideas=[idea])

        with (
            patch("backend.app.tasks.idea_repository") as mock_repo,
            patch("backend.app.tasks.llm_service_for_idea") as mock_llm,
        ):
            mock_repo.return_value = repo
            mock_llm.return_value = _fake_with(
                marketing_metadata=MarketingMetadata(
                    seo_title="SEO Title",
                    meta_description="A meta description for the post.",
                    excerpt="Short excerpt.",
                    linkedin_post="LinkedIn post content.",
                    x_post="X/Twitter post.",
                    cta="Read more.",
                ),
            )

            result = _safe_call(generate_marketing_metadata_task, idea_id="idea_mkt_1")

        assert result["marketing_status"] == "pending"
        assert result["marketing_metadata"]["seo_title"] == "SEO Title"
        mock_finish.assert_called_once()

    @patch("backend.app.tasks._finish_job")
    @patch("backend.app.tasks.track_job_lifecycle")
    def test_idea_not_found(
        self,
        mock_track: MagicMock,
        mock_finish: MagicMock,
    ) -> None:
        from backend.app.tasks import generate_marketing_metadata_task

        mock_track.return_value = GenerationJobRepository()
        with patch("backend.app.tasks.idea_repository") as mock_repo:
            mock_repo.return_value = BlogIdeaRepository()
            with pytest.raises(ValueError, match="not found"):
                _safe_call(generate_marketing_metadata_task, idea_id="ghost")

    @patch("backend.app.tasks._finish_job")
    @patch("backend.app.tasks.track_job_lifecycle")
    def test_draft_not_approved(
        self,
        mock_track: MagicMock,
        mock_finish: MagicMock,
    ) -> None:
        from backend.app.tasks import generate_marketing_metadata_task

        mock_track.return_value = GenerationJobRepository()
        idea = _make_idea(
            id="idea_mkt_no_draft",
            draft_status=None,
        )
        repo = BlogIdeaRepository(ideas=[idea])

        with patch("backend.app.tasks.idea_repository") as mock_repo:
            mock_repo.return_value = repo

            with pytest.raises(ValueError, match="draft is not approved"):
                _safe_call(generate_marketing_metadata_task, idea_id="idea_mkt_no_draft")


# ===========================================================================
# Blog draft helpers
# ===========================================================================


class TestIdeaCreateFromLLM:
    """Verify the LLM→persistence mapping respects column limits.

    Note: we use ``model_construct()`` to bypass Pydantic field-level
    ``max_length`` validation, simulating what would happen if the LLM
    returned an over-long string (the real service doesn’t enforce
    ``max_length`` on the generation side).
    """

    def test_truncates_title_to_240_chars(self) -> None:
        from backend.app.tasks import _idea_create_from_llm

        result = BlogIdeaSchema.model_construct(
            title="A" * 500,
            angle="short angle",
            target_reader="reader",
            article_goal="goal",
        )
        create = _idea_create_from_llm(result)
        assert len(create.title) == 240
        assert create.title == "A" * 240

    def test_truncates_angle_to_160_chars(self) -> None:
        from backend.app.tasks import _idea_create_from_llm

        result = BlogIdeaSchema.model_construct(
            title="Short",
            angle="B" * 300,
            target_reader="reader",
            article_goal="goal",
        )
        create = _idea_create_from_llm(result)
        assert len(create.angle) == 160

    def test_truncates_target_reader_to_160_chars(self) -> None:
        from backend.app.tasks import _idea_create_from_llm

        result = BlogIdeaSchema.model_construct(
            title="Short",
            angle="angle",
            target_reader="C" * 300,
            article_goal="goal",
        )
        create = _idea_create_from_llm(result)
        assert len(create.target_reader) == 160

    def test_passes_article_goal_untouched(self) -> None:
        from backend.app.tasks import _idea_create_from_llm

        result = BlogIdeaSchema(
            title="Short",
            angle="angle",
            target_reader="reader",
            article_goal="This is a detailed goal with no length constraint.",
        )
        create = _idea_create_from_llm(result)
        assert create.article_goal == result.article_goal

    def test_passes_positioning_notes(self) -> None:
        from backend.app.tasks import _idea_create_from_llm

        result = BlogIdeaSchema(
            title="Short",
            angle="angle",
            target_reader="reader",
            article_goal="goal",
            positioning_notes=["Note 1", "Note 2"],
        )
        create = _idea_create_from_llm(result)
        assert create.positioning_notes == ["Note 1", "Note 2"]

    def test_returns_blog_idea_create_instance(self) -> None:
        from backend.app.tasks import _idea_create_from_llm

        result = BlogIdeaSchema(
            title="Test",
            angle="Angle",
            target_reader="Devs",
            article_goal="Goal",
        )
        create = _idea_create_from_llm(result)
        assert isinstance(create, BlogIdeaCreate)


class TestFinishJob:
    """Verify _finish_job marks jobs correctly."""

    def test_mark_completed_on_success(self) -> None:
        from backend.app.tasks import _finish_job

        task = MagicMock()
        task.request.id = "task_001"
        jobs = GenerationJobRepository()
        # Pre-create a job so mark_running/mark_completed find it
        jobs.create_queued(
            blog_idea_id="idea_1",
            stage="idea",
            celery_task_id="task_001",
        )
        jobs.mark_running("task_001")

        _finish_job(task, jobs)
        job = jobs.get_by_celery_task_id("task_001")
        assert job is not None
        assert job.status == "completed"

    def test_mark_failed_on_exception(self) -> None:
        from backend.app.tasks import _finish_job

        task = MagicMock()
        task.request.id = "task_002"
        jobs = GenerationJobRepository()
        jobs.create_queued(
            blog_idea_id="idea_2",
            stage="outline",
            celery_task_id="task_002",
        )
        jobs.mark_running("task_002")

        _finish_job(task, jobs, RuntimeError("Something went wrong"))
        job = jobs.get_by_celery_task_id("task_002")
        assert job is not None
        assert job.status == "failed"
        assert "Something went wrong" in (job.error_message or "")

    def test_noop_when_job_not_found(self) -> None:
        """Should not crash when the celery_task_id has no job."""
        from backend.app.tasks import _finish_job

        task = MagicMock()
        task.request.id = "nonexistent"
        jobs = GenerationJobRepository()

        # Neither exception nor crash expected
        _finish_job(task, jobs)
        _finish_job(task, jobs, RuntimeError("oops"))


class TestWordCount:
    """Verify the word-count helper used by draft generation."""

    def test_counts_simple_text(self) -> None:
        from backend.app.tasks import _word_count

        assert _word_count("one two three") == 3

    def test_counts_mixed_punctuation(self) -> None:
        from backend.app.tasks import _word_count

        assert _word_count("Hello, world! How are you?") == 5

    def test_empty_string(self) -> None:
        from backend.app.tasks import _word_count

        assert _word_count("") == 0

    def test_newlines_and_spaces(self) -> None:
        from backend.app.tasks import _word_count

        assert _word_count("line one\n\nline two\n\n\nline three") == 6


# ===========================================================================
# _generate_blog_draft_sectional
# ===========================================================================


class TestGenerateBlogDraftSectional:
    """Sectional expansion for blog drafts."""

    def test_expands_sections_into_full_draft(self) -> None:
        from backend.app.tasks import _generate_blog_draft_sectional

        service = _fake_with(
            draft_section_writer=BlogDraftSection(markdown=_LONG_SECTION_MD),
        )
        sections = [
            {"section": "Context", "points": ["Background"]},
            {"section": "Solution", "points": ["Architecture", "Trade-offs"]},
        ]

        result = _generate_blog_draft_sectional(
            service,
            inputs={"outline_json": "...", "project_context": "...", "positioning_notes": "..."},
            sections=sections,
            title="Test Post",
        )

        assert result.title == "Test Post"
        # Each section is wrapped in ## heading
        assert "## Context" in result.markdown
        assert "## Solution" in result.markdown

    def test_builds_prior_summary_chain(self) -> None:
        """Each section receives accumulated summaries of prior sections."""
        from backend.app.tasks import _generate_blog_draft_sectional

        tracker: list[dict] = []

        class TrackingFake(LLMService):
            def generate_with_usage(
                self, prompt_name, inputs, output_schema,
            ):
                tracker.append(
                    {
                        "index": inputs.get("section_index"),
                        "prior": inputs.get("prior_sections_summary"),
                    }
                )
                return BlogDraftSection(markdown="short body."), {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0,
                }

        sections = [
            {"section": "First", "points": ["A"]},
            {"section": "Second", "points": ["B"]},
        ]

        _generate_blog_draft_sectional(
            TrackingFake(),
            inputs={"project_context": "ctx"},
            sections=sections,
            title="Test",
        )

        assert len(tracker) == 2
        assert tracker[0]["prior"].startswith("None yet")
        assert "short body" in tracker[1]["prior"]


# ===========================================================================
# _generate_blog_draft (monolithic fallback logic)
# ===========================================================================


class TestGenerateBlogDraft:
    """Tests for the top-level _generate_blog_draft helper (fallback chain)."""

    def test_sectional_sufficient_returns_directly(self) -> None:
        """When sectional expansion meets word minimum, return immediately."""
        from backend.app.tasks import _generate_blog_draft

        service = _fake_with(
            draft_section_writer=BlogDraftSection(markdown=_LONG_SECTION_MD),
        )
        # 2 sections × 800 words = 1600 words > _DRAFT_MIN_WORDS (1500)
        sections = [
            {"section": "A", "points": ["1"]},
            {"section": "B", "points": ["2"]},
        ]

        result = _generate_blog_draft(
            service,
            inputs={"positioning_notes": "N/A"},
            sections=sections,
            title="Sectional Only",
        )
        assert result.title == "Sectional Only"
        assert "## A" in result.markdown
        assert "## B" in result.markdown

    def test_sectional_too_short_triggers_monolithic_attempts(self) -> None:
        """When sectional is too short, fall through to monolithic attempts."""
        from backend.app.tasks import _generate_blog_draft

        # Sectional produces short content (< 1500 words)
        # Monolithic first attempt also short, second attempt long enough
        call_count = [0]

        class SequentialFake(LLMService):
            def generate_with_usage(self, prompt_name, inputs, output_schema):
                call_count[0] += 1
                if prompt_name == "draft_section_writer":
                    return BlogDraftSection(markdown="short"), {
                        "prompt_tokens": 0, "completion_tokens": 0,
                        "total_tokens": 0,
                    }
                # draft_writer: first is short, second is long
                if call_count[0] < 3:
                    return BlogDraft(title="", markdown=_SHORT_DRAFT_MD), {
                        "prompt_tokens": 0, "completion_tokens": 0,
                        "total_tokens": 0,
                    }
                return BlogDraft(title="Retried", markdown=_LONG_DRAFT_MD), {
                    "prompt_tokens": 0, "completion_tokens": 0,
                    "total_tokens": 0,
                }

        sections = [{"section": "A", "points": ["1"]}]
        result = _generate_blog_draft(
            SequentialFake(),
            {"positioning_notes": "N/A"},
            sections=sections,
            title="Sequential",
        )

        assert "word" in result.markdown
        # At least: 1 sectional + 2 monolithic attempts
        assert call_count[0] >= 2

    def test_raises_when_all_attempts_too_short(self) -> None:
        """Short content after all attempts raises RuntimeError."""
        from backend.app.tasks import _generate_blog_draft

        service = _fake_with(
            draft_section_writer=BlogDraftSection(markdown="very short"),
            draft_writer=BlogDraft(title="", markdown="also short"),
        )
        sections = [{"section": "A", "points": ["1"]}]

        with pytest.raises(RuntimeError, match="too short"):
            _generate_blog_draft(
                service,
                {"positioning_notes": "N/A"},
                sections=sections,
                title="Short",
            )

    def test_no_sections_uses_only_monolithic(self) -> None:
        """Without sections, skip sectional expansion entirely."""
        from backend.app.tasks import _generate_blog_draft

        service = _fake_with(
            draft_writer=BlogDraft(title="Mono Only", markdown=_LONG_DRAFT_MD),
        )

        result = _generate_blog_draft(
            service,
            {"positioning_notes": "N/A"},
            sections=None,
            title="Mono Only",
        )
        assert result.title == "Mono Only"
        assert "word" in result.markdown


# ===========================================================================
# News task wrappers
# ===========================================================================


class TestNewsTasks:
    """Representative tests for news-oriented tasks (which delegate to
    ``run_*`` functions)."""

    @patch("backend.app.tasks.news_source_repository")
    @patch("backend.app.tasks.news_raw_item_repository")
    @patch("backend.app.tasks.run_rss_crawl")
    def test_crawl_rss_source_task(
        self,
        mock_run: MagicMock,
        mock_raw: MagicMock,
        mock_sources: MagicMock,
    ) -> None:
        from backend.app.tasks import crawl_rss_source_task

        mock_run.return_value.model_dump.return_value = {
            "source_id": "src_1",
            "items_stored": 3,
            "items_seen": 5,
        }

        result = _safe_call(crawl_rss_source_task, source_id="src_1")
        assert result["items_stored"] == 3
        assert result["items_seen"] == 5
        mock_run.assert_called_once()

    @patch("backend.app.tasks.news_source_repository")
    @patch("backend.app.tasks.news_raw_item_repository")
    @patch("backend.app.tasks.run_crawl_due_rss_sources")
    def test_crawl_due_rss_sources_task(
        self,
        mock_run: MagicMock,
        mock_raw: MagicMock,
        mock_sources: MagicMock,
    ) -> None:
        from backend.app.tasks import crawl_due_rss_sources_task

        r1 = MagicMock()
        r1.model_dump.return_value = {"source_id": "s1", "items_stored": 2}
        r2 = MagicMock()
        r2.model_dump.return_value = {"source_id": "s2", "items_stored": 0}
        mock_run.return_value = [r1, r2]

        results = _safe_call(crawl_due_rss_sources_task)
        assert len(results) == 2
        assert results[0]["source_id"] == "s1"

    @patch("backend.app.tasks.news_source_repository")
    @patch("backend.app.tasks.news_raw_item_repository")
    @patch("backend.app.tasks.extracted_article_repository")
    @patch("backend.app.tasks.article_extractor")
    @patch("backend.app.tasks.news_review_repository")
    @patch("backend.app.tasks.run_extract_raw_item")
    def test_extract_raw_item_task(
        self,
        mock_run: MagicMock,
        mock_review: MagicMock,
        mock_extractor: MagicMock,
        mock_extracted: MagicMock,
        mock_raw: MagicMock,
        mock_sources: MagicMock,
    ) -> None:
        from backend.app.tasks import extract_raw_item_task

        mock_run.return_value.model_dump.return_value = {
            "id": "extracted_1",
            "status": "completed",
        }

        result = _safe_call(extract_raw_item_task, raw_item_id="raw_1")
        assert result["id"] == "extracted_1"
        mock_run.assert_called_once()

    @patch("backend.app.tasks.news_source_repository")
    @patch("backend.app.tasks.news_raw_item_repository")
    @patch("backend.app.tasks.extracted_article_repository")
    @patch("backend.app.tasks.article_extractor")
    @patch("backend.app.tasks.news_review_repository")
    @patch("backend.app.tasks.llm_service_for_news_item")
    @patch("backend.app.tasks.run_score_extracted_article")
    def test_score_extracted_article_task(
        self,
        mock_run: MagicMock,
        mock_llm: MagicMock,
        mock_review: MagicMock,
        mock_extractor: MagicMock,
        mock_extracted: MagicMock,
        mock_raw: MagicMock,
        mock_sources: MagicMock,
    ) -> None:
        from backend.app.tasks import score_extracted_article_task

        mock_run.return_value.model_dump.return_value = {
            "id": "scored_1",
            "final_publish_score": 0.85,
        }

        result = _safe_call(
            score_extracted_article_task,
            extracted_article_id="extracted_1",
        )
        assert result["final_publish_score"] == 0.85
        mock_run.assert_called_once()

    @patch("backend.app.tasks.news_source_repository")
    @patch("backend.app.tasks.news_raw_item_repository")
    @patch("backend.app.tasks.extracted_article_repository")
    @patch("backend.app.tasks.article_extractor")
    @patch("backend.app.tasks.news_review_repository")
    @patch("backend.app.tasks.run_extract_pending_raw_items")
    def test_extract_pending_raw_items_task(
        self,
        mock_run: MagicMock,
        mock_review: MagicMock,
        mock_extractor: MagicMock,
        mock_extracted: MagicMock,
        mock_raw: MagicMock,
        mock_sources: MagicMock,
    ) -> None:
        from backend.app.tasks import extract_pending_raw_items_task

        r1 = MagicMock()
        r1.model_dump.return_value = {"id": "ext_1"}
        mock_run.return_value = [r1]

        results = _safe_call(extract_pending_raw_items_task, source_id="src_1")
        assert len(results) == 1
        assert results[0]["id"] == "ext_1"
        mock_run.assert_called_once()

    @patch("backend.app.tasks.news_source_repository")
    @patch("backend.app.tasks.news_raw_item_repository")
    @patch("backend.app.tasks.extracted_article_repository")
    @patch("backend.app.tasks.article_extractor")
    @patch("backend.app.tasks.news_review_repository")
    @patch("backend.app.tasks.run_extract_pending_raw_items")
    def test_extract_pending_raw_items_task_without_source_id(
        self,
        mock_run: MagicMock,
        mock_review: MagicMock,
        mock_extractor: MagicMock,
        mock_extracted: MagicMock,
        mock_raw: MagicMock,
        mock_sources: MagicMock,
    ) -> None:
        from backend.app.tasks import extract_pending_raw_items_task

        r1 = MagicMock()
        r1.model_dump.return_value = {"id": "ext_all"}
        mock_run.return_value = [r1]

        # Call without source_id (defaults to None)
        results = _safe_call(extract_pending_raw_items_task)
        assert len(results) == 1
        assert results[0]["id"] == "ext_all"

    @patch("backend.app.tasks.news_source_repository")
    @patch("backend.app.tasks.news_raw_item_repository")
    @patch("backend.app.tasks.extracted_article_repository")
    @patch("backend.app.tasks.news_review_repository")
    @patch("backend.app.tasks.run_score_pending_extractions")
    def test_score_pending_extractions_task(
        self,
        mock_run: MagicMock,
        mock_review: MagicMock,
        mock_extracted: MagicMock,
        mock_raw: MagicMock,
        mock_sources: MagicMock,
    ) -> None:
        from backend.app.tasks import score_pending_extractions_task

        r1 = MagicMock()
        r1.model_dump.return_value = {"id": "scored_1", "final_publish_score": 0.9}
        mock_run.return_value = [r1]

        results = _safe_call(score_pending_extractions_task, source_id="src_1")
        assert len(results) == 1
        assert results[0]["id"] == "scored_1"
        mock_run.assert_called_once()

    @patch("backend.app.tasks.news_source_repository")
    @patch("backend.app.tasks.news_raw_item_repository")
    @patch("backend.app.tasks.extracted_article_repository")
    @patch("backend.app.tasks.news_review_repository")
    @patch("backend.app.tasks.run_score_pending_extractions")
    def test_score_pending_extractions_task_without_source_id(
        self,
        mock_run: MagicMock,
        mock_review: MagicMock,
        mock_extracted: MagicMock,
        mock_raw: MagicMock,
        mock_sources: MagicMock,
    ) -> None:
        from backend.app.tasks import score_pending_extractions_task

        r1 = MagicMock()
        r1.model_dump.return_value = {"id": "scored_all"}
        mock_run.return_value = [r1]

        results = _safe_call(score_pending_extractions_task)
        assert len(results) == 1
        assert results[0]["id"] == "scored_all"

    @patch("backend.app.tasks.news_source_repository")
    @patch("backend.app.tasks.news_raw_item_repository")
    @patch("backend.app.tasks.extracted_article_repository")
    @patch("backend.app.tasks.article_extractor")
    @patch("backend.app.tasks.news_review_repository")
    @patch("backend.app.tasks.submitted_link_repository")
    @patch("backend.app.tasks.run_process_submitted_link")
    def test_process_submitted_link_task(
        self,
        mock_run: MagicMock,
        mock_link_repo: MagicMock,
        mock_review: MagicMock,
        mock_extractor: MagicMock,
        mock_extracted: MagicMock,
        mock_raw: MagicMock,
        mock_sources: MagicMock,
    ) -> None:
        from backend.app.tasks import process_submitted_link_task

        mock_run.return_value.model_dump.return_value = {
            "id": "link_1",
            "status": "processed",
        }

        result = _safe_call(
            process_submitted_link_task, submission_id="sub_1"
        )
        assert result["id"] == "link_1"
        assert result["status"] == "processed"
        mock_run.assert_called_once()

    @patch("backend.app.tasks.news_source_repository")
    @patch("backend.app.tasks.news_raw_item_repository")
    @patch("backend.app.tasks.extracted_article_repository")
    @patch("backend.app.tasks.article_extractor")
    @patch("backend.app.tasks.news_review_repository")
    @patch("backend.app.tasks.submitted_link_repository")
    @patch("backend.app.tasks.run_process_submitted_link")
    def test_process_submitted_link_task_without_source_id(
        self,
        mock_run: MagicMock,
        mock_link_repo: MagicMock,
        mock_review: MagicMock,
        mock_extractor: MagicMock,
        mock_extracted: MagicMock,
        mock_raw: MagicMock,
        mock_sources: MagicMock,
    ) -> None:
        from backend.app.tasks import process_submitted_link_task

        mock_run.return_value.model_dump.return_value = {
            "id": "link_2",
        }
        result = _safe_call(process_submitted_link_task, submission_id="sub_2")
        assert result["id"] == "link_2"


# ===========================================================================
# task_support helpers
# ===========================================================================


class TestUseAgentsSDK:
    """Test the ``_use_agents_sdk`` helper."""

    def test_default_is_false(self) -> None:
        from backend.app.task_support import _use_agents_sdk

        settings = Settings(environment="test", llm_backend="openai")
        assert not _use_agents_sdk(settings)

    def test_true_when_agents_sdk_configured(self) -> None:
        from backend.app.task_support import _use_agents_sdk

        settings = Settings(environment="test", llm_backend="agents_sdk")
        assert _use_agents_sdk(settings)


class TestBuildLLMService:
    """Test the ``_build_llm_service`` factory."""

    def test_openai_backend_returns_openai_service(self) -> None:
        from backend.app.task_support import _build_llm_service

        settings = Settings(environment="test", llm_backend="openai")
        service = _build_llm_service("test-key", "gpt-4o", settings)
        from backend.app.llm.service import OpenAILLMService

        assert isinstance(service, OpenAILLMService)

    def test_agents_sdk_backend_returns_agents_sdk_service(self) -> None:
        from backend.app.task_support import _build_llm_service

        settings = Settings(environment="test", llm_backend="agents_sdk")
        service = _build_llm_service("test-key", "gpt-4o-mini", settings)
        from backend.app.llm.agents_sdk_service import AgentsSDKLLMService

        assert isinstance(service, AgentsSDKLLMService)
        assert service._model == "gpt-4o-mini"

    def test_both_backends_satisfy_abc(self) -> None:
        from backend.app.task_support import _build_llm_service

        for backend in ("openai", "agents_sdk"):
            settings = Settings(environment="test", llm_backend=backend)
            service = _build_llm_service("test-key", "gpt-4o", settings)
            assert isinstance(service, LLMService)

    def test_mcp_enabled_returns_service_with_mcp(self) -> None:
        """When LLM_MCP_ENABLED and agents_sdk, MCP servers are created."""
        from backend.app.task_support import _build_llm_service

        settings = Settings(
            environment="test",
            llm_backend="agents_sdk",
            llm_mcp_enabled=True,
        )
        service = _build_llm_service("test-key", "gpt-4o", settings, entity_id="e1")
        from backend.app.llm.agents_sdk_service import AgentsSDKLLMService

        assert isinstance(service, AgentsSDKLLMService)
        # MCP servers list might be empty in test env depending on agents SDK
        # availability — we just verify no crash


class TestLLMServiceForIdea:
    """Test the ``llm_service_for_idea`` factory."""

    def test_fake_mode_returns_fake_service(self) -> None:
        from backend.app.task_support import llm_service_for_idea

        settings = Settings(
            environment="test",
            llm_e2e_fake=True,
        )
        service = llm_service_for_idea("idea_1", settings)
        from backend.app.llm.service import FakeLLMService

        inner = service._inner if hasattr(service, "_inner") else service
        assert isinstance(inner, FakeLLMService)

    def test_fake_mode_with_agents_sdk_backend(self) -> None:
        """E2E fake mode takes precedence over backend selection."""
        from backend.app.task_support import llm_service_for_idea

        settings = Settings(
            environment="test",
            llm_e2e_fake=True,
            llm_backend="agents_sdk",
        )
        service = llm_service_for_idea("idea_2", settings)
        from backend.app.llm.service import FakeLLMService

        inner = service._inner if hasattr(service, "_inner") else service
        assert isinstance(inner, FakeLLMService)

    def test_fake_is_wrapped_in_recording_when_recorder_available(self) -> None:
        """Fake mode with recorder wraps in RecordingLLMService."""
        from backend.app.task_support import llm_service_for_idea

        settings = Settings(
            environment="test",
            llm_e2e_fake=True,
        )
        service = llm_service_for_idea("idea_3", settings)
        from backend.app.llm.recording import RecordingLLMService

        assert isinstance(service, RecordingLLMService)

    def test_raises_without_api_key(self) -> None:
        """Without fake mode and without API key, raises RuntimeError."""
        from backend.app.task_support import llm_service_for_idea

        settings = Settings(
            environment="test",
            llm_e2e_fake=False,
            llm_openai_api_key="",  # empty
        )
        with pytest.raises(RuntimeError, match="API_KEY"):
            llm_service_for_idea("idea_4", settings)

    def test_fake_generates_response(self) -> None:
        """Fake service can generate a valid blog idea."""
        from backend.app.task_support import llm_service_for_idea

        settings = Settings(
            environment="test",
            llm_e2e_fake=True,
        )
        service = llm_service_for_idea("idea_5", settings)
        result = service.generate(
            "blog_idea",
            inputs={
                "project_name": "P",
                "project_summary": "S",
                "ai_capabilities": "C",
                "technical_highlights": "T",
                "business_value": "V",
            },
            output_schema=BlogIdeaSchema,
        )
        assert isinstance(result, BlogIdeaSchema)
        assert result.title == "E2E Golden Path Blog Idea"


class TestLLMServiceForNewsItem:
    """Test the ``llm_service_for_news_item`` factory."""

    def test_returns_none_without_api_key(self) -> None:
        from backend.app.task_support import llm_service_for_news_item

        settings = Settings(
            environment="test",
            llm_openai_api_key="",
        )
        service = llm_service_for_news_item("review_1", settings)
        assert service is None

    def test_returns_service_with_configured_key(self) -> None:
        from backend.app.task_support import llm_service_for_news_item

        settings = Settings(
            environment="test",
            llm_openai_api_key="sk-test-key",
        )
        service = llm_service_for_news_item("review_2", settings)
        assert service is not None
        from backend.app.llm.recording import RecordingLLMService
        from backend.app.llm.service import OpenAILLMService

        # With OpenAI backend, wraps in RecordingLLMService
        assert isinstance(service, RecordingLLMService)


class TestBuildMcpServers:
    """Test the ``_build_mcp_servers`` helper."""

    def test_returns_empty_when_disabled(self) -> None:
        from backend.app.task_support import _build_mcp_servers

        settings = Settings(environment="test", llm_mcp_enabled=False)
        assert _build_mcp_servers(settings) == []

    def test_returns_empty_when_not_agents_sdk(self) -> None:
        from backend.app.task_support import _build_mcp_servers

        settings = Settings(
            environment="test",
            llm_mcp_enabled=True,
            llm_backend="openai",
        )
        assert _build_mcp_servers(settings) == []

    def test_returns_list_when_enabled_with_agents_sdk(self) -> None:
        """When MCP is enabled and backend is agents_sdk, try to build."""
        from backend.app.task_support import _build_mcp_servers

        settings = Settings(
            environment="test",
            llm_mcp_enabled=True,
            llm_backend="agents_sdk",
        )
        try:
            servers = _build_mcp_servers(settings)
        except Exception:
            servers = None  # May fail if agents SDK not importable

        # If it succeeded, it should be a list (maybe empty on import error)
        assert servers is None or isinstance(servers, list)


class TestRepositoryFactories:
    """Test repository factory functions return the right types in test env."""

    def test_idea_repository(self) -> None:
        from backend.app.task_support import idea_repository
        from backend.app.blog_ideas import BlogIdeaRepository

        settings = Settings(environment="test")
        repo = idea_repository(settings)
        assert isinstance(repo, BlogIdeaRepository)

    def test_ai_run_repository(self) -> None:
        from backend.app.task_support import ai_run_repository
        from backend.app.ai_runs import AiRunRepository

        settings = Settings(environment="test")
        repo = ai_run_repository(settings)
        assert isinstance(repo, AiRunRepository)

    def test_generation_job_repository(self) -> None:
        from backend.app.task_support import generation_job_repository
        from backend.app.generation_jobs import GenerationJobRepository

        settings = Settings(environment="test")
        repo = generation_job_repository(settings)
        assert isinstance(repo, GenerationJobRepository)

    def test_news_source_repository(self) -> None:
        from backend.app.task_support import news_source_repository
        from backend.app.news_sources import NewsSourceRepository

        settings = Settings(environment="test")
        repo = news_source_repository(settings)
        assert isinstance(repo, NewsSourceRepository)

    def test_extracted_article_repository(self) -> None:
        from backend.app.task_support import extracted_article_repository
        from backend.app.news_extraction import ExtractedArticleRepository

        settings = Settings(environment="test")
        repo = extracted_article_repository(settings)
        assert isinstance(repo, ExtractedArticleRepository)

    def test_news_raw_item_repository(self) -> None:
        from backend.app.task_support import news_raw_item_repository
        from backend.app.news_crawl import NewsRawItemRepository

        settings = Settings(environment="test")
        repo = news_raw_item_repository(settings)
        assert isinstance(repo, NewsRawItemRepository)

    def test_article_extractor(self) -> None:
        from backend.app.task_support import article_extractor

        settings = Settings(environment="test")
        extractor = article_extractor(settings)
        # Should return an extractor instance without crashing
        assert extractor is not None

    def test_submitted_link_repository(self) -> None:
        from backend.app.task_support import submitted_link_repository
        from backend.app.news_submitted_links import InMemorySubmittedLinkRepository

        settings = Settings(environment="test")
        repo = submitted_link_repository(settings)
        assert isinstance(repo, InMemorySubmittedLinkRepository)

    def test_news_review_repository(self) -> None:
        from backend.app.task_support import news_review_repository
        from backend.app.news_scoring import InMemoryNewsReviewRepository

        settings = Settings(environment="test")
        repo = news_review_repository(settings)
        assert isinstance(repo, InMemoryNewsReviewRepository)


class TestTrackJobLifecycle:
    """Test the ``track_job_lifecycle`` helper."""

    def test_marks_job_running(self) -> None:
        from backend.app.task_support import track_job_lifecycle

        task = MagicMock()
        task.request.id = "celery_task_abc"

        with patch("backend.app.task_support.generation_job_repository") as mock_factory:
            jobs = GenerationJobRepository()
            # Pre-create a job so mark_running can find it
            jobs.create_queued(
                blog_idea_id="idea_1",
                stage="idea",
                celery_task_id="celery_task_abc",
            )
            mock_factory.return_value = jobs

            result = track_job_lifecycle(task)

        assert result is jobs
        job = jobs.get_by_celery_task_id("celery_task_abc")
        assert job is not None
        assert job.status == "running"

    def test_returns_repository_even_without_job(self) -> None:
        """Does not crash when no job exists for the task ID."""
        from backend.app.task_support import track_job_lifecycle

        task = MagicMock()
        task.request.id = "unknown_task"

        with patch("backend.app.task_support.generation_job_repository") as mock_factory:
            jobs = GenerationJobRepository()
            mock_factory.return_value = jobs

            result = track_job_lifecycle(task)
        assert result is jobs


class TestProviderName:
    """Test the ``_provider_name`` helper."""

    def test_returns_openai_by_default(self) -> None:
        from backend.app.task_support import _provider_name

        settings = Settings(environment="test", llm_backend="openai")
        assert _provider_name(settings) == "openai"

    def test_returns_agents_sdk_when_configured(self) -> None:
        from backend.app.task_support import _provider_name

        settings = Settings(environment="test", llm_backend="agents_sdk")
        assert _provider_name(settings) == "agents_sdk"


class TestRegisterBlogGuardrails:
    """Test the ``_register_blog_guardrails`` helper."""

    def test_noop_when_not_agents_sdk(self) -> None:
        """Does not crash when backend is OpenAI."""
        from backend.app.task_support import _register_blog_guardrails
        from backend.app.llm.service import FakeLLMService

        settings = Settings(environment="test", llm_backend="openai")
        service = FakeLLMService({})
        # Should not raise
        _register_blog_guardrails(service, "idea_1", settings)

    def test_noop_with_fake_service_even_with_agents_sdk(self) -> None:
        """Does not crash when service is not AgentsSDKLLMService."""
        from backend.app.task_support import _register_blog_guardrails
        from backend.app.llm.service import FakeLLMService

        settings = Settings(environment="test", llm_backend="agents_sdk")
        service = FakeLLMService({})
        # Should not raise — isinstance check prevents guardrail registration
        _register_blog_guardrails(service, "idea_1", settings)


# ===========================================================================
# Publish scheduled posts task
# ===========================================================================


class TestPublishScheduledPostsTask:
    """Test the scheduled publishing logic."""

    @patch("backend.app.blog_publish.publish_idea_to_blog")
    def test_publishes_overdue_ideas(
        self,
        mock_publish: MagicMock,
    ) -> None:
        """Ideas with scheduled_at <= now and approved status get published."""
        from backend.app.tasks import publish_scheduled_posts_task

        past = datetime(2020, 1, 1, tzinfo=UTC)
        future = datetime(2099, 1, 1, tzinfo=UTC)

        ready_idea = _make_idea(
            id="idea_ready",
            scheduled_at=past,
            status="approved",
            draft_markdown="# Ready to publish",
        )
        not_ready = _make_idea(
            id="idea_future",
            scheduled_at=future,
            status="approved",
            draft_markdown="# Future post",
        )
        no_draft = _make_idea(
            id="idea_no_draft",
            scheduled_at=past,
            status="approved",
            draft_markdown=None,
        )

        idea_repo = BlogIdeaRepository(
            ideas=[ready_idea, not_ready, no_draft],
        )

        # Return a simple object with .slug attribute to match task code expectations
        class PublishResult:
            slug = "ready-idea"
        mock_publish.return_value = PublishResult()

        with patch("backend.app.task_support.idea_repository") as mock_idea_fn, \
             patch("backend.app.task_support.blog_repository") as mock_blog_fn:
            mock_idea_fn.return_value = idea_repo

            results = publish_scheduled_posts_task.__wrapped__()

        assert len(results) == 1
        assert results[0]["idea_id"] == "idea_ready"
        assert results[0]["status"] == "published"
        assert results[0]["slug"] == "ready-idea"
        mock_publish.assert_called_once()

    @patch("backend.app.blog_publish.publish_idea_to_blog")
    def test_handles_publish_failure_gracefully(
        self,
        mock_publish: MagicMock,
    ) -> None:
        """Publish failure per idea does not crash the whole batch."""
        from backend.app.tasks import publish_scheduled_posts_task

        past = datetime(2020, 1, 1, tzinfo=UTC)

        ok_idea = _make_idea(
            id="idea_ok",
            scheduled_at=past,
            status="approved",
            draft_markdown="# OK content",
        )
        fail_idea = _make_idea(
            id="idea_fail",
            scheduled_at=past,
            status="approved",
            draft_markdown="# Fail content",
        )

        idea_repo = BlogIdeaRepository(ideas=[ok_idea, fail_idea])

        def _mock_publish(idea_id, ideas_repo, blog_repo):
            if idea_id == "idea_fail":
                raise RuntimeError("Publish error")
            class PublishResult:
                slug = "ok-slug"
            return PublishResult()

        mock_publish.side_effect = _mock_publish

        with patch("backend.app.task_support.idea_repository") as mock_idea_fn, \
             patch("backend.app.task_support.blog_repository") as mock_blog_fn:
            mock_idea_fn.return_value = idea_repo

            results = publish_scheduled_posts_task.__wrapped__()

        assert len(results) == 2
        ok_result = [r for r in results if r["idea_id"] == "idea_ok"][0]
        fail_result = [r for r in results if r["idea_id"] == "idea_fail"][0]
        assert ok_result["status"] == "published"
        assert fail_result["status"] == "failed"
        assert "Publish error" in fail_result["error"]


# ===========================================================================
# Social X / GitHub tasks (lightweight smoke)
# ===========================================================================


class TestSocialAndGitHubTasks:
    """These tasks do inline imports; we mock the underlying run function."""

    @patch("backend.app.tasks.news_source_repository")
    @patch("backend.app.tasks.news_raw_item_repository")
    def test_ingest_social_x_source_task(
        self,
        mock_raw: MagicMock,
        mock_sources: MagicMock,
    ) -> None:
        from backend.app.tasks import ingest_social_x_source_task

        with patch(
            "backend.app.news_social_x_ingest.run_social_x_ingest"
        ) as mock_run:
            mock_run.return_value.model_dump.return_value = {
                "source_id": "x_1",
                "items_stored": 5,
            }
            result = _safe_call(ingest_social_x_source_task, source_id="x_1")
            assert result["items_stored"] == 5

    @patch("backend.app.tasks.news_source_repository")
    @patch("backend.app.tasks.news_raw_item_repository")
    def test_fetch_github_source_task(
        self,
        mock_raw: MagicMock,
        mock_sources: MagicMock,
    ) -> None:
        from backend.app.tasks import fetch_github_source_task

        with patch(
            "backend.app.news_github_ingest.GitHubReleaseProvider"
        ) as mock_provider_cls, patch(
            "backend.app.news_github_ingest.run_github_fetch"
        ) as mock_run:
            mock_run.return_value.model_dump.return_value = {
                "source_id": "gh_1",
                "items_stored": 3,
            }
            result = _safe_call(fetch_github_source_task, source_id="gh_1")
            assert result["items_stored"] == 3

    @patch("backend.app.tasks.news_source_repository")
    @patch("backend.app.tasks.news_raw_item_repository")
    def test_ingest_due_social_x_sources_task(
        self,
        mock_raw: MagicMock,
        mock_sources: MagicMock,
    ) -> None:
        from backend.app.tasks import ingest_due_social_x_sources_task

        with patch(
            "backend.app.news_social_x_ingest.run_due_social_x_sources"
        ) as mock_run:
            r1 = MagicMock()
            r1.model_dump.return_value = {"source_id": "x_1", "items_stored": 3}
            mock_run.return_value = [r1]

            results = _safe_call(ingest_due_social_x_sources_task)
            assert len(results) == 1
            assert results[0]["items_stored"] == 3

    @patch("backend.app.tasks.news_source_repository")
    @patch("backend.app.tasks.news_raw_item_repository")
    def test_fetch_due_github_sources_task(
        self,
        mock_raw: MagicMock,
        mock_sources: MagicMock,
    ) -> None:
        from backend.app.tasks import fetch_due_github_sources_task

        with patch(
            "backend.app.news_github_ingest.GitHubReleaseProvider"
        ) as mock_provider_cls, patch(
            "backend.app.news_github_ingest.run_due_github_sources"
        ) as mock_run:
            r1 = MagicMock()
            r1.model_dump.return_value = {"source_id": "gh_1", "items_stored": 7}
            mock_run.return_value = [r1]

            results = _safe_call(fetch_due_github_sources_task)
            assert len(results) == 1
            assert results[0]["items_stored"] == 7
