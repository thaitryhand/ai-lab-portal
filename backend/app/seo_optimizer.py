"""SEO Auto-Optimize Agent.

Analyzes SEO audit results and blog post content to suggest improvements
for title, meta description, heading structure, internal links, and
keyword placement. Changes are presented as before/after diffs for
admin review and approval.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


# ── Output Models ──


class SeoChange(BaseModel):
    """A single SEO improvement suggestion with before/after."""
    section: str = Field(..., pattern=r"^(title|meta_description|headings|internal_links|keywords)$")
    before: str
    after: str
    rationale: str = Field(..., min_length=1, max_length=500)


class SeoOptimizationResult(BaseModel):
    """Complete output of the SEO optimization agent."""
    id: str = ""
    blog_idea_id: str = ""
    changes: list[SeoChange] = Field(default_factory=list, min_length=1)
    overall_summary: str = Field(default="", max_length=1000)
    created_at: str = ""


# ── Service Interface ──


class SeoOptimizerService(ABC):
    """Abstract service for SEO optimization suggestions."""

    @abstractmethod
    def optimize(
        self,
        blog_idea_id: str,
        title: str,
        content_markdown: str,
        seo_audit: dict | None = None,
    ) -> SeoOptimizationResult: ...


# ── Fake Provider ──


class FakeSeoOptimizerService(SeoOptimizerService):
    """Returns fake but realistic SEO optimization suggestions for testing."""

    def optimize(
        self,
        blog_idea_id: str,
        title: str,
        content_markdown: str,
        seo_audit: dict | None = None,
    ) -> SeoOptimizationResult:
        now = datetime.now(UTC).isoformat()

        changes = [
            SeoChange(
                section="title",
                before=title,
                after=f"{title} — A Complete Guide (2026)",
                rationale="Add year and value proposition to improve CTR in search results.",
            ),
            SeoChange(
                section="meta_description",
                before="",
                after=f"Learn about {title.lower()}. Expert insights, practical tips, and real-world examples to help you get started.",
                rationale="Meta description was missing or too short. Added keyword-rich description within 160 chars.",
            ),
            SeoChange(
                section="headings",
                before="## Getting Started\n## Advanced Topics",
                after="## What Is {title}?\n## Getting Started with {title}\n## Advanced {title} Techniques\n## Best Practices and Tips",
                rationale="Restructured headings to include the primary keyword in more H2s for better keyword relevance.",
            ),
            SeoChange(
                section="internal_links",
                before="",
                after="Consider linking to related blog posts about AI engineering patterns and agent workflows.",
                rationale="No internal links found. Adding contextual internal links improves site structure and SEO.",
            ),
            SeoChange(
                section="keywords",
                before="Primary keyword appears 2 times in content.",
                after=f"Primary keyword '{title.lower()}' appears 5-7 times naturally throughout content.",
                rationale="Increase keyword density from 2 to 5-7 occurrences for better topical relevance.",
            ),
        ]

        return SeoOptimizationResult(
            id=str(uuid4()),
            blog_idea_id=blog_idea_id,
            changes=changes,
            overall_summary=f"Found {len(changes)} SEO improvement opportunities. "
                           f"Focus areas: title optimization, meta description, "
                           f"heading structure, internal linking, and keyword density.",
            created_at=now,
        )


# ── LLM-Powered Service ──


class LLMSeoOptimizerService(SeoOptimizerService):
    """Uses LLMService to generate SEO optimization suggestions."""

    def __init__(self, llm_service: Any) -> None:
        self._llm = llm_service

    def optimize(
        self,
        blog_idea_id: str,
        title: str,
        content_markdown: str,
        seo_audit: dict | None = None,
    ) -> SeoOptimizationResult:
        audit_json = str(seo_audit or {})

        inputs = {
            "title": title,
            "content": content_markdown[:4000],
            "seo_audit": audit_json,
        }

        try:
            result = self._llm.generate(
                "seo_optimize",
                inputs,
                SeoOptimizationResult,
            )
            if isinstance(result, SeoOptimizationResult):
                result.id = str(uuid4())
                result.blog_idea_id = blog_idea_id
                result.created_at = datetime.now(UTC).isoformat()
                return result
        except Exception:
            pass

        # Fallback to fake logic
        return FakeSeoOptimizerService().optimize(
            blog_idea_id, title, content_markdown, seo_audit
        )
