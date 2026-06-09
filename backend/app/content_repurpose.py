"""Content Repurposing Agent.

Transforms a published blog post into social media content:
- Twitter thread (5-10 tweets)
- LinkedIn article (headline + summary + key takeaways)
- Short summary snippet (2-3 sentences)

Uses the existing LLMService (respects AI_LAB_LLM_BACKEND setting).
Fake provider returns realistic mock content for testing.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


# ── Output Models ──


class Tweet(BaseModel):
    """A single tweet in a thread."""
    number: int = Field(..., ge=1, le=20)
    content: str = Field(..., min_length=1, max_length=280)


class TwitterThread(BaseModel):
    """Complete Twitter thread."""
    tweets: list[Tweet] = Field(..., min_length=1, max_length=20)


class LinkedInArticle(BaseModel):
    """LinkedIn article format."""
    headline: str = Field(..., min_length=1, max_length=200)
    summary: str = Field(..., min_length=1, max_length=500)
    key_takeaways: list[str] = Field(default_factory=list, max_length=5)


class RepurposedContent(BaseModel):
    """Complete output of the content repurposing agent."""
    id: str = ""
    blog_post_id: str = ""
    twitter_thread: TwitterThread | None = None
    linkedin_article: LinkedInArticle | None = None
    summary_snippet: str = Field(default="", max_length=500)
    created_at: str = ""


# ── Service Interface ──


class ContentRepurposeService(ABC):
    """Abstract service for content repurposing."""

    @abstractmethod
    def repurpose(self, blog_post_id: str, title: str, excerpt: str, content_markdown: str) -> RepurposedContent: ...


# ── Fake Provider ──


class FakeContentRepurposeService(ContentRepurposeService):
    """Returns fake but realistic repurposed content for testing."""

    def repurpose(self, blog_post_id: str, title: str, excerpt: str, content_markdown: str) -> RepurposedContent:
        now = datetime.now(UTC).isoformat()
        return RepurposedContent(
            id=str(uuid4()),
            blog_post_id=blog_post_id,
            twitter_thread=TwitterThread(tweets=[
                Tweet(number=1, content=f"🧵 {title}"),
                Tweet(number=2, content=excerpt[:260]),
                Tweet(number=3, content="Here are the key insights from this article..."),
                Tweet(number=4, content="What do you think? Share your thoughts below! 👇"),
            ]),
            linkedin_article=LinkedInArticle(
                headline=f"{title} — Key Insights",
                summary=f"I recently published an article about {title.lower()}. Here's what I learned.",
                key_takeaways=[
                    "The AI landscape is evolving rapidly",
                    "Practical implementation matters more than theory",
                    "Start small, iterate fast",
                ],
            ),
            summary_snippet=f"Check out our latest article: {title}. {excerpt[:200]}",
            created_at=now,
        )


# ── LLM-Powered Service ──


class LLMContentRepurposeService(ContentRepurposeService):
    """Uses LLMService to generate repurposed content."""

    def __init__(self, llm_service: Any) -> None:
        self._llm = llm_service

    def repurpose(self, blog_post_id: str, title: str, excerpt: str, content_markdown: str) -> RepurposedContent:
        """Generate repurposed content using the LLM service."""
        from backend.app.llm.prompts import PROMPT_REGISTRY

        # Generate Twitter thread
        twitter_thread = self._generate_twitter_thread(title, excerpt, content_markdown)

        # Generate LinkedIn article
        linkedin_article = self._generate_linkedin_article(title, excerpt, content_markdown)

        # Generate summary snippet
        summary_snippet = self._generate_summary(title, excerpt)

        return RepurposedContent(
            id=str(uuid4()),
            blog_post_id=blog_post_id,
            twitter_thread=twitter_thread,
            linkedin_article=linkedin_article,
            summary_snippet=summary_snippet,
            created_at=datetime.now(UTC).isoformat(),
        )

    def _generate_twitter_thread(self, title: str, excerpt: str, content_markdown: str) -> TwitterThread | None:
        try:
            from backend.app.llm.prompts import PROMPT_REGISTRY
            result = self._llm.generate(
                "repurpose_twitter",
                {"title": title, "excerpt": excerpt, "content": content_markdown[:3000]},
                TwitterThread,
            )
            return result if isinstance(result, TwitterThread) else None
        except Exception:
            return None

    def _generate_linkedin_article(self, title: str, excerpt: str, content_markdown: str) -> LinkedInArticle | None:
        try:
            result = self._llm.generate(
                "repurpose_linkedin",
                {"title": title, "excerpt": excerpt, "content": content_markdown[:3000]},
                LinkedInArticle,
            )
            return result if isinstance(result, LinkedInArticle) else None
        except Exception:
            return None

    def _generate_summary(self, title: str, excerpt: str) -> str:
        try:
            result = self._llm.generate(
                "repurpose_summary",
                {"title": title, "excerpt": excerpt},
                _SummaryOutput,
            )
            return result.text if hasattr(result, "text") else excerpt[:200]
        except Exception:
            return excerpt[:200]


class _SummaryOutput(BaseModel):
    text: str = Field(..., max_length=500)
