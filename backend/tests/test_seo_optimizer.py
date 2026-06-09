"""Tests for SEO Auto-Optimize Agent (US-109)."""

import pytest

from backend.app.seo_optimizer import (
    FakeSeoOptimizerService,
    LLMSeoOptimizerService,
    SeoChange,
    SeoOptimizationResult,
)
from backend.app.llm.service import FakeLLMService


class TestFakeSeoOptimizerService:
    """FakeSeoOptimizerService returns realistic optimization suggestions."""

    @pytest.fixture
    def service(self):
        return FakeSeoOptimizerService()

    def test_returns_result(self, service):
        result = service.optimize("idea-1", "Test Title", "# Content", {})
        assert isinstance(result, SeoOptimizationResult)
        assert result.blog_idea_id == "idea-1"

    def test_has_changes(self, service):
        result = service.optimize("i1", "Title", "# Content", {})
        assert len(result.changes) >= 1
        assert all(isinstance(c, SeoChange) for c in result.changes)

    def test_has_all_sections(self, service):
        result = service.optimize("i1", "Title", "# Content", {})
        sections = {c.section for c in result.changes}
        assert "title" in sections
        assert "meta_description" in sections
        assert "headings" in sections
        assert "internal_links" in sections
        assert "keywords" in sections

    def test_each_change_has_before_after(self, service):
        result = service.optimize("i1", "Title", "# Content", {})
        for change in result.changes:
            # before can be empty for fields that don't exist yet (e.g. meta_description)
            assert change.after is not None
            assert len(change.rationale) > 0

    def test_has_overall_summary(self, service):
        result = service.optimize("i1", "Title", "# Content", {})
        assert len(result.overall_summary) > 0

    def test_has_id_and_timestamp(self, service):
        result = service.optimize("i1", "Title", "# Content", {})
        assert len(result.id) > 0
        assert len(result.created_at) > 0


class TestSeoChangeModel:
    """Pydantic model validation."""

    def test_valid_change(self):
        c = SeoChange(
            section="title",
            before="Old Title",
            after="New Title",
            rationale="Better for SEO",
        )
        assert c.section == "title"
        assert c.before == "Old Title"

    def test_invalid_section(self):
        with pytest.raises(ValueError, match="String should match pattern"):
            SeoChange(
                section="invalid",
                before="b", after="a", rationale="test",
            )

    def test_minimal_rationale(self):
        with pytest.raises(ValueError, match="String should have at least 1 character"):
            SeoChange(
                section="title",
                before="b", after="a", rationale="",
            )


class TestSeoOptimizationResultModel:
    """SeoOptimizationResult model validation."""

    def test_valid_result(self):
        r = SeoOptimizationResult(
            id="r-1",
            blog_idea_id="i-1",
            changes=[
                SeoChange(section="title", before="Old", after="New", rationale="Better title"),
            ],
            overall_summary="One improvement found.",
            created_at="now",
        )
        assert r.id == "r-1"
        assert len(r.changes) == 1

    def test_requires_at_least_one_change(self):
        with pytest.raises(ValueError, match="List should have at least 1 item"):
            SeoOptimizationResult(
                id="r-1", blog_idea_id="i-1",
                changes=[], overall_summary="", created_at="now",
            )


class TestLLMSeoOptimizerService:
    """LLM-powered service with FakeLLMService fallback."""

    def test_fallback_to_fake(self):
        fake_llm = FakeLLMService({})
        service = LLMSeoOptimizerService(fake_llm)
        result = service.optimize("i1", "Title", "# Content")
        assert isinstance(result, SeoOptimizationResult)
        assert result.blog_idea_id == "i1"
        assert len(result.changes) >= 1
