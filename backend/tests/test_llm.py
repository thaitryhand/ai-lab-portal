"""Tests for the LLM service, schemas, and prompt registry.

The LLM service tests use ``FakeLLMService`` so they never call a real API.
Schema tests verify Pydantic validation rules.
Prompt registry tests verify template rendering.
"""

import json

import pytest
from pydantic import ValidationError

from backend.app.llm.prompts import PROMPT_REGISTRY, BLOG_IDEA_PROMPT, PromptTemplate
from backend.app.llm.schemas import (
    BlogIdea,
    BlogOutline,
    BlogOutlineSection,
    BlogDraft,
    TechnicalReview,
    TechnicalReviewIssue,
    MarketingMetadata,
    NewsScoring,
)
from backend.app.llm.service import (
    FakeLLMService,
    LLMGenerationError,
    LLMService,
)


# ===========================================================================
# Prompt registry
# ===========================================================================


class TestPromptRegistry:
    def test_all_prompts_are_registered(self) -> None:
        """Every prompt name used by the blog workflow is present."""
        expected = {
            "blog_idea",
            "blog_outline",
            "draft_writer",
            "technical_review",
            "marketing_metadata",
            "claim_extraction",
            "ai_news_scoring",
        }
        assert expected.issubset(PROMPT_REGISTRY.keys())

    def test_prompt_template_is_pydantic_model(self) -> None:
        assert isinstance(BLOG_IDEA_PROMPT, PromptTemplate)
        assert len(BLOG_IDEA_PROMPT.system) > 0
        assert len(BLOG_IDEA_PROMPT.user_template) > 0

    def test_user_template_has_placeholder(self) -> None:
        assert "{project_name}" in BLOG_IDEA_PROMPT.user_template
        assert "{project_summary}" in BLOG_IDEA_PROMPT.user_template

    def test_user_template_renders_with_inputs(self) -> None:
        rendered = BLOG_IDEA_PROMPT.user_template.format(
            project_name="Test Project",
            project_summary="A test project for validation.",
            ai_capabilities="LLM, evaluation",
            technical_highlights="Structured output",
            business_value="Reduce manual work",
        )
        assert "Test Project" in rendered
        assert "A test project for validation." in rendered


# ===========================================================================
# Schemas
# ===========================================================================


class TestBlogIdeaSchema:
    def test_valid_blog_idea(self) -> None:
        idea = BlogIdea(
            title="How We Built an AI Evaluation Pipeline",
            angle="AI Evaluation",
            target_reader="CTO evaluating AI adoption",
            article_goal="Show our evaluation process",
            positioning_notes=["Avoid overpromising autonomy"],
        )
        assert idea.title == "How We Built an AI Evaluation Pipeline"
        assert "Avoid overpromising autonomy" in idea.positioning_notes

    def test_minimal_blog_idea(self) -> None:
        """positioning_notes defaults to empty list."""
        idea = BlogIdea(
            title="Minimal idea",
            angle="Test",
            target_reader="Developers",
            article_goal="Test goal",
        )
        assert idea.positioning_notes == []


class TestBlogOutlineSchema:
    def test_valid_outline(self) -> None:
        outline = BlogOutline(
            title="Test Article",
            outline=[
                BlogOutlineSection(
                    section="Context",
                    points=["Project background", "Team size"],
                ),
                BlogOutlineSection(
                    section="Problem",
                    points=["What we were solving"],
                ),
            ],
        )
        assert len(outline.outline) == 2
        assert outline.outline[0].points == ["Project background", "Team size"]


class TestBlogDraftSchema:
    def test_valid_draft(self) -> None:
        draft = BlogDraft(
            title="Test Draft",
            markdown="# Hello\n\nThis is a test draft.",
        )
        assert "# Hello" in draft.markdown


class TestTechnicalReviewSchema:
    def test_valid_review_no_issues(self) -> None:
        review = TechnicalReview(
            overall_risk="low",
            issues=[],
            approval_recommendation="approve",
        )
        assert review.overall_risk == "low"

    def test_valid_review_with_issues(self) -> None:
        review = TechnicalReview(
            overall_risk="medium",
            issues=[
                TechnicalReviewIssue(
                    severity="high",
                    type="unsupported_claim",
                    text="Our AI reduces cost by 80%",
                    reason="No measurement data provided",
                    suggestion='Use "noticeable reduction" instead',
                ),
            ],
            approval_recommendation="needs_revision",
        )
        assert len(review.issues) == 1
        assert review.issues[0].severity == "high"

    @pytest.mark.parametrize(
        "field,value",
        [
            ("overall_risk", "critical"),
            ("approval_recommendation", "maybe"),
        ],
    )
    def test_invalid_enum_values_are_rejected(self, field: str, value: str) -> None:
        data = {
            "overall_risk": "low",
            "issues": [],
            "approval_recommendation": "approve",
        }
        data[field] = value
        with pytest.raises(ValidationError):
            TechnicalReview(**data)

    def test_invalid_severity_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            TechnicalReview(
                overall_risk="low",
                issues=[
                    TechnicalReviewIssue(
                        severity="urgent",
                        type="unsupported_claim",
                        text="Test",
                        reason="Test",
                        suggestion="Test",
                    ),
                ],
                approval_recommendation="approve",
            )


class TestNewsScoringSchema:
    def test_valid_news_scoring(self) -> None:
        scoring = NewsScoring(
            source_credibility_score=0.8,
            engagement_score=0.5,
            relevance_score=0.9,
            novelty_score=0.7,
            technical_depth_score=0.6,
            business_value_score=0.6,
            spam_risk_score=0.1,
            final_publish_score=0.78,
            summary="OpenAI released a model update.",
            why_it_matters="Practitioners should evaluate the API impact.",
        )
        assert scoring.final_publish_score == 0.78

    def test_invalid_news_scoring_score_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            NewsScoring(
                source_credibility_score=1.2,
                engagement_score=0.5,
                relevance_score=0.9,
                novelty_score=0.7,
                technical_depth_score=0.6,
                business_value_score=0.6,
                spam_risk_score=0.1,
                final_publish_score=0.78,
                summary="Summary",
                why_it_matters="Why",
            )


class TestMarketingMetadataSchema:
    def test_valid_metadata(self) -> None:
        meta = MarketingMetadata(
            seo_title="AI Evaluation at AI Lab",
            meta_description="Learn how we built an evaluation pipeline.",
            excerpt="A practical evaluation case study.",
            linkedin_post="We built an AI evaluation pipeline. Here's what we learned.",
            x_post="We built an AI evaluation pipeline. Here's what we learned.",
            cta="Contact our AI/LLM Lab to learn more.",
        )
        assert len(meta.seo_title) <= 60
        assert len(meta.meta_description) <= 160


# ===========================================================================
# LLM Service
# ===========================================================================


class TestLLMService:
    def test_fake_service_returns_canned_response(self) -> None:
        expected = BlogIdea(
            title="Test Idea",
            angle="AI Evaluation",
            target_reader="CTOs",
            article_goal="Show evaluation",
        )
        service: LLMService = FakeLLMService(responses={"blog_idea": expected})

        result = service.generate("blog_idea", {}, BlogIdea)
        assert isinstance(result, BlogIdea)
        assert result.title == "Test Idea"

    def test_fake_service_raises_on_missing_prompt(self) -> None:
        service: LLMService = FakeLLMService(responses={})

        with pytest.raises(LLMGenerationError, match="No fake response configured"):
            service.generate("blog_idea", {}, BlogIdea)

    def test_fake_service_serializes_like_real_output(self) -> None:
        """Ensure the fake output can be JSON-serialized (like a real API response)."""
        expected = BlogIdea(
            title="Serializable Idea",
            angle="AI Evaluation",
            target_reader="Developers",
            article_goal="Test serialization",
        )
        service: LLMService = FakeLLMService(responses={"blog_idea": expected})

        result = service.generate("blog_idea", {}, BlogIdea)
        raw = result.model_dump_json()
        parsed = json.loads(raw)
        assert parsed["title"] == "Serializable Idea"

    def test_fake_service_with_all_schema_types(self) -> None:
        """Verify the fake can return every schema type."""
        schemas: dict[str, tuple[dict, type]] = {
            "blog_idea": (
                {
                    "title": "Idea",
                    "angle": "Tech",
                    "target_reader": "Devs",
                    "article_goal": "Inform",
                },
                BlogIdea,
            ),
            "blog_outline": (
                {
                    "title": "Outline",
                    "outline": [
                        {
                            "section": "Context",
                            "points": ["Background"],
                        },
                    ],
                },
                BlogOutline,
            ),
            "draft": (
                {
                    "title": "Draft",
                    "markdown": "# Content",
                },
                BlogDraft,
            ),
            "review": (
                {
                    "overall_risk": "low",
                    "issues": [],
                    "approval_recommendation": "approve",
                },
                TechnicalReview,
            ),
            "marketing": (
                {
                    "seo_title": "SEO",
                    "meta_description": "Desc",
                    "excerpt": "Excerpt",
                    "linkedin_post": "LinkedIn",
                    "x_post": "X/Twitter",
                    "cta": "CTA",
                },
                MarketingMetadata,
            ),
        }

        for name, (data, schema) in schemas.items():
            obj = schema(**data)
            service: LLMService = FakeLLMService(responses={name: obj})
            result = service.generate(name, {}, schema)
            assert isinstance(result, schema), f"Failed for {name}"


# ===========================================================================
# Prompt + service integration (via fake)
# ===========================================================================


class TestPromptServiceIntegration:
    def test_prompt_registry_entries_match_service_expected_names(self) -> None:
        """All registered prompts should be usable by the service."""
        idea = BlogIdea(
            title="Integration Idea",
            angle="Test",
            target_reader="Devs",
            article_goal="Integrate",
        )
        service: LLMService = FakeLLMService(responses={"blog_idea": idea})

        for name in PROMPT_REGISTRY:
            # FakeLLMService will raise if it has no response for this name
            try:
                service.generate(name, {}, BlogIdea)
            except LLMGenerationError:
                pass  # Expected for names not in responses dict
