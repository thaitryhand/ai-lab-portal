"""Tests for Content Repurposing Agent (US-107)."""

import pytest

from backend.app.content_repurpose import (
    FakeContentRepurposeService,
    LLMContentRepurposeService,
    RepurposedContent,
    TwitterThread,
    LinkedInArticle,
    Tweet,
)
from backend.app.llm.service import FakeLLMService


class TestFakeContentRepurposeService:
    """Fake service returns realistic mock content."""

    @pytest.fixture
    def service(self):
        return FakeContentRepurposeService()

    def test_returns_repurposed_content(self, service):
        result = service.repurpose(
            blog_post_id="post-1",
            title="Test Post",
            excerpt="A test excerpt",
            content_markdown="# Test\nContent here.",
        )
        assert isinstance(result, RepurposedContent)
        assert result.blog_post_id == "post-1"

    def test_twitter_thread_has_tweets(self, service):
        result = service.repurpose("p1", "Title", "Excerpt", "# Content")
        assert result.twitter_thread is not None
        assert len(result.twitter_thread.tweets) >= 3
        assert result.twitter_thread.tweets[0].number == 1
        assert all(len(t.content) <= 280 for t in result.twitter_thread.tweets)

    def test_linkedin_article_has_fields(self, service):
        result = service.repurpose("p1", "Title", "Excerpt", "# Content")
        assert result.linkedin_article is not None
        assert len(result.linkedin_article.headline) > 0
        assert len(result.linkedin_article.summary) > 0
        assert len(result.linkedin_article.key_takeaways) >= 1

    def test_summary_snippet_not_empty(self, service):
        result = service.repurpose("p1", "Title", "Excerpt", "# Content")
        assert len(result.summary_snippet) > 0

    def test_has_id_and_timestamp(self, service):
        result = service.repurpose("p1", "Title", "Excerpt", "# Content")
        assert len(result.id) > 0
        assert len(result.created_at) > 0


class TestRepurposedContentModels:
    """Pydantic model validation."""

    def test_tweet_valid(self):
        t = Tweet(number=1, content="Hello world")
        assert t.number == 1
        assert t.content == "Hello world"

    def test_tweet_content_max_length(self):
        with pytest.raises(ValueError, match="String should have at most 280 characters"):
            Tweet(number=1, content="x" * 281)

    def test_twitter_thread_valid(self):
        thread = TwitterThread(tweets=[Tweet(number=1, content="Hello"), Tweet(number=2, content="World")])
        assert len(thread.tweets) == 2

    def test_linkedin_article_valid(self):
        article = LinkedInArticle(
            headline="Test",
            summary="Summary text",
            key_takeaways=["Point 1", "Point 2"],
        )
        assert article.headline == "Test"
        assert len(article.key_takeaways) == 2

    def test_repurposed_content_with_all_fields(self):
        content = RepurposedContent(
            id="r-1",
            blog_post_id="p-1",
            twitter_thread=TwitterThread(tweets=[Tweet(number=1, content="Hi")]),
            linkedin_article=LinkedInArticle(headline="H", summary="S"),
            summary_snippet="Check this out!",
            created_at="2026-06-08T00:00:00Z",
        )
        assert content.id == "r-1"
        assert content.summary_snippet == "Check this out!"

    def test_repurposed_content_minimal(self):
        content = RepurposedContent(id="r-1", blog_post_id="p-1", created_at="now")
        assert content.twitter_thread is None
        assert content.linkedin_article is None


class TestLLMServiceBackedRepurpose:
    """Tests for LLM-powered service (uses FakeLLMService for testing)."""

    def test_with_fake_llm_service(self):
        """LLMContentRepurposeService should work with any LLMService."""
        fake_llm = FakeLLMService({})
        service = LLMContentRepurposeService(fake_llm)
        # Without proper prompts, this should gracefully handle errors
        result = service.repurpose("p1", "Title", "Excerpt", "# Content")
        assert isinstance(result, RepurposedContent)
        assert result.blog_post_id == "p1"
