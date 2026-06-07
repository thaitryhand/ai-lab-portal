"""Multi-agent news review: bias detection and quality assessment.

Uses the Agents SDK ``Agent.as_tool()`` pattern where a main
``NewsQualityReviewer`` agent calls a ``NewsClaimExtractor``
sub-agent as a tool during article review.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# ── Output schema ──────────────────────────────────────────────


class BiasIndicator(BaseModel):
    """A single potential bias or quality concern found in the article."""

    category: str = Field(
        description="Category: 'bias', 'factual_claim', 'source_credibility', 'missing_context'"
    )
    excerpt: str = Field(description="The relevant text excerpt from the article")
    concern: str = Field(description="Why this is a concern")
    severity: str = Field(description="'low', 'medium', or 'high'")


class NewsQualityReport(BaseModel):
    """Quality assessment report for a news article."""

    overall_assessment: str = Field(
        description="One sentence overall quality assessment"
    )
    credibility_score: float = Field(
        ge=0.0, le=1.0, description="Adjusted credibility score (0.0-1.0)"
    )
    concerns: list[BiasIndicator] = Field(
        description="List of bias/quality concerns found"
    )
    positive_notes: list[str] = Field(
        description="Positive aspects of the article"
    )
    recommendation: str = Field(
        description="'approve', 'review', or 'reject'"
    )


# ── Agent builders ──────────────────────────────────────────────


def build_news_claim_extractor(output_type: type[BaseModel] | None = None) -> Any:
    """Build a ClaimExtractor sub-agent for news articles.

    Args:
        output_type: Optional Pydantic model for the extraction output.
            Defaults to ``NewsQualityReport``.

    Returns:
        An ``Agent`` instance configured for claim extraction.
    """
    from agents import Agent

    resolved_type = output_type or NewsQualityReport

    return Agent(
        name="NewsClaimExtractor",
        instructions=(
            "You are a news quality analyst. Read the article text and extract:\n"
            "1. Factual claims that need verification.\n"
            "2. Potential biases (political, commercial, sensationalism).\n"
            "3. Missing context that would help readers evaluate the claims.\n"
            "4. Source credibility indicators.\n\n"
            "Be specific — quote exact excerpts. Rate each concern's severity.\n"
            "Provide a balanced overall assessment with positive notes too."
        ),
        output_type=resolved_type,
    )


def build_news_quality_reviewer(
    mcp_servers: list[Any] | None = None,
) -> Any:
    """Build the main NewsQualityReviewer agent.

    Uses ``Agent.as_tool()`` to incorporate the claim extractor
    sub-agent during review.

    Args:
        mcp_servers: Optional list of MCP server instances.

    Returns:
        An ``Agent`` instance configured for quality review.
    """
    from agents import Agent

    claim_extractor = build_news_claim_extractor()
    tools = [claim_extractor.as_tool(
        tool_name="extract_claims",
        tool_description=(
            "Extract factual claims, biases, and quality concerns "
            "from the article text. Call this first."
        ),
    )]

    return Agent(
        name="NewsQualityReviewer",
        instructions=(
            "You are a senior news editor performing a quality review.\n\n"
            "1. First, call 'extract_claims' to analyze the article.\n"
            "2. Review the extraction results and produce a final quality report.\n"
            "3. Assign a credibility score considering source reliability and content quality.\n"
            "4. Recommend 'approve' for high-quality articles, 'review' for articles with "
            "medium concerns, and 'reject' for articles with severe issues.\n\n"
            "Be fair and constructive — identify both strengths and concerns."
        ),
        output_type=NewsQualityReport,
        tools=tools,
        mcp_servers=mcp_servers or [],
    )


def news_quality_prompt() -> str:
    """Return the formatted prompt for the quality review."""
    return (
        "Review this news article for quality, bias, and credibility.\n\n"
        "Title: {title}\n"
        "Source: {source_name}\n"
        "Source credibility base score: {score}\n\n"
        "Article text:\n{content_text}"
    )
