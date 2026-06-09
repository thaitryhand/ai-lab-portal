"""Tests for Auto-Scheduling Agent (US-108)."""

import pytest

from backend.app.scheduling_agent import (
    FakeSchedulingService,
    LLMSchedulingService,
    SchedulingService,
    SchedulingSuggestion,
)
from backend.app.llm.service import FakeLLMService


class TestFakeSchedulingService:
    """FakeSchedulingService returns plausible suggestions."""

    @pytest.fixture
    def service(self):
        return FakeSchedulingService()

    def test_returns_suggestion(self, service):
        result = service.suggest("post-1", "Test Post", "published")
        assert isinstance(result, SchedulingSuggestion)
        assert result.blog_post_id == "post-1"

    def test_has_valid_date_format(self, service):
        result = service.suggest("p1", "Title", "published")
        import re
        assert re.match(r"^\d{4}-\d{2}-\d{2}$", result.suggested_date)

    def test_has_valid_time_format(self, service):
        result = service.suggest("p1", "Title", "published")
        import re
        assert re.match(r"^\d{2}:\d{2}$", result.suggested_time)

    def test_has_rationale(self, service):
        result = service.suggest("p1", "Title", "published")
        assert len(result.rationale) > 10

    def test_confidence_in_range(self, service):
        result = service.suggest("p1", "Title", "published")
        assert 0.0 <= result.confidence <= 1.0

    def test_has_id_and_timestamp(self, service):
        result = service.suggest("p1", "Title", "published")
        assert len(result.id) > 0
        assert len(result.created_at) > 0

    def test_accepts_existing_scheduled(self, service):
        result = service.suggest("p1", "Title", "published",
                                 existing_scheduled=["2026-06-10", "2026-06-12"])
        assert result.suggested_date is not None


class TestSchedulingSuggestionModel:
    """Pydantic model validation."""

    def test_valid_suggestion(self):
        s = SchedulingSuggestion(
            id="s-1",
            blog_post_id="p-1",
            suggested_date="2026-06-15",
            suggested_time="10:00",
            rationale="Best time for engagement.",
            confidence=0.85,
            created_at="2026-06-08T00:00:00Z",
        )
        assert s.suggested_date == "2026-06-15"
        assert s.confidence == 0.85

    def test_invalid_date_format(self):
        with pytest.raises(ValueError, match="String should match pattern"):
            SchedulingSuggestion(
                id="s-1", blog_post_id="p-1",
                suggested_date="invalid", suggested_time="10:00",
                rationale="test", confidence=0.5, created_at="now",
            )

    def test_invalid_confidence_too_high(self):
        with pytest.raises(ValueError, match="Input should be less than or equal to 1"):
            SchedulingSuggestion(
                id="s-1", blog_post_id="p-1",
                suggested_date="2026-06-15", suggested_time="10:00",
                rationale="test", confidence=1.5, created_at="now",
            )


class TestLLMSchedulingService:
    """LLM-powered service with FakeLLMService fallback."""

    def test_fallback_to_fake(self):
        """With an empty FakeLLMService, should fallback to fake logic."""
        fake_llm = FakeLLMService({})
        service = LLMSchedulingService(fake_llm)
        result = service.suggest("p1", "Title", "published")
        assert isinstance(result, SchedulingSuggestion)
        assert result.blog_post_id == "p1"
        assert result.confidence > 0
