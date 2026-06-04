"""Prompt templates for the AI Blog Agent workflow.

This module acts as a code-level prompt registry for MVP. Each entry maps a
logical prompt name (`blog_idea`, `blog_outline`, etc.) to a pair of system
message and user template.

Future iterations may promote this to a database-backed registry so that
prompts can be versioned, A/B tested, and edited without deploys.
"""

from __future__ import annotations

from pydantic import BaseModel


class PromptTemplate(BaseModel):
    """A prompt composed of a system message and a user-side template.

    The user template uses Python ``str.format()`` syntax so that callers
    inject dynamic context before sending the request.

    Attributes:
        system: System-level instruction that defines the agent's role and
            behavioral constraints.
        user_template: Template string with ``{placeholder}`` markers that
            will be filled by the caller.
        version: Registry version recorded on each AI run.
    """

    system: str
    user_template: str
    version: str = "1"


# ---------------------------------------------------------------------------
# Blog idea generation
# ---------------------------------------------------------------------------

BLOG_IDEA_PROMPT = PromptTemplate(
    system=(
        "You are a blog strategist for an AI/LLM Lab company. "
        "Your job is to generate blog post ideas based on internal project "
        "information. Each idea must be practical, grounded in real engineering "
        "work, and appealing to a B2B technical audience.\n\n"
        "Guidelines:\n"
        "- Focus on real systems, real lessons, and real business value.\n"
        "- Avoid vague statements like 'AI will change everything.'\n"
        "- Avoid unsupported performance claims.\n"
        "- The target reader is CTOs, product managers, or founders evaluating "
        "AI adoption."
    ),
    user_template=(
        "Generate 1 blog idea for the following project:\n\n"
        "Project name: {project_name}\n"
        "Project summary: {project_summary}\n"
        "AI capabilities: {ai_capabilities}\n"
        "Technical highlights: {technical_highlights}\n"
        "Business value: {business_value}"
    ),
)


# ---------------------------------------------------------------------------
# Blog outline generation
# ---------------------------------------------------------------------------

BLOG_OUTLINE_PROMPT = PromptTemplate(
    system=(
        "You are a content strategist who creates clear, structured blog "
        "outlines for B2B technical articles. Each section should have "
        "specific, actionable bullet points that guide a writer."
    ),
    user_template=(
        "Create a detailed outline for a blog post with the following details:\n\n"
        "Title: {title}\n"
        "Angle: {angle}\n"
        "Target reader: {target_reader}\n"
        "Article goal: {article_goal}\n"
        "Positioning notes: {positioning_notes}\n\n"
        "Use the standard blog structure:\n"
        "1. Context — background on the project or problem\n"
        "2. Problem — what challenge was being solved\n"
        "3. AI/LLM approach — how AI was applied\n"
        "4. Architecture or workflow — technical design\n"
        "5. Evaluation and quality control — how quality was measured\n"
        "6. Lessons learned — what the team learned\n"
        "7. Business value — impact on the business\n"
        "8. What's next — future improvements"
    ),
)


# ---------------------------------------------------------------------------
# Draft writing
# ---------------------------------------------------------------------------

DRAFT_WRITER_PROMPT = PromptTemplate(
    system=(
        "You are a professional B2B technical writer. Write a complete, "
        "polished blog post in markdown format based on the provided outline "
        "and context.\n\n"
        "Tone: practical, clear, calm, experienced. "
        "Avoid hype, buzzwords, and unsupported claims. "
        "The reader is technical but may also be a business stakeholder."
    ),
    user_template=(
        "Write a complete blog post in markdown using this outline:\n\n"
        "{outline_json}\n\n"
        "Project context:\n{project_context}\n"
        "Positioning notes:\n{positioning_notes}"
    ),
)


# ---------------------------------------------------------------------------
# Technical review
# ---------------------------------------------------------------------------

TECHNICAL_REVIEW_PROMPT = PromptTemplate(
    system=(
        "You are a senior technical reviewer. Your job is to check a blog "
        "draft for technical accuracy, unsupported claims, vague statements, "
        "and risk.\n\n"
        "Check for:\n"
        "- Technical correctness\n"
        "- Unsupported performance claims\n"
        "- Misleading descriptions of AI capabilities\n"
        "- Missing limitations\n"
        "- Security or confidentiality risks\n"
        "- Overly broad claims\n"
        "- Whether examples are grounded in real project information"
    ),
    user_template=(
        "Review the following blog draft for technical accuracy and risk:\n\n"
        "{draft_markdown}\n\n"
        "Project context:\n{project_context}"
    ),
)


# ---------------------------------------------------------------------------
# Marketing metadata generation
# ---------------------------------------------------------------------------

MARKETING_META_PROMPT = PromptTemplate(
    system=(
        "You are a marketing editor for an AI/LLM Lab company. Generate "
        "SEO metadata, social media posts, and a call-to-action for the "
        "provided blog post. The tone should be professional, confident, "
        "and B2B-appropriate."
    ),
    user_template=(
        "Generate marketing metadata for the following blog post:\n\n"
        "Title: {title}\n"
        "Excerpt: {excerpt}\n\n"
        "Full draft:\n{draft_markdown}"
    ),
)


# ---------------------------------------------------------------------------
# AI News scoring
# ---------------------------------------------------------------------------

AI_NEWS_SCORING_PROMPT = PromptTemplate(
    system=(
        "You are an AI news editor scoring official-source articles for a technical B2B audience. "
        "Return calibrated scores from 0.0 to 1.0, a concise factual summary, and a why-it-matters note. "
        "Avoid hype and do not invent facts beyond the provided article text. Penalize spam, vague promotion, "
        "and weak AI relevance."
    ),
    user_template=(
        "Score this extracted AI news article.\n\n"
        "Source name: {source_name}\n"
        "Source credibility base score: {source_credibility_score}\n"
        "Title: {title}\n"
        "Published at: {published_at}\n\n"
        "Article text:\n{content_text}"
    ),
    version="1",
)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

CLAIM_EXTRACTION_PROMPT = PromptTemplate(
    system=(
        "You extract factual claims from a B2B blog draft. "
        "Flag quantified metrics, performance comparisons, and product capability claims "
        "that would need evidence before publishing."
    ),
    user_template=(
        "Extract notable claims from this draft. "
        "Mark requires_evidence=true for numbers, percentages, benchmarks, or outcomes.\n\n"
        "{draft_markdown}"
    ),
    version="1",
)


PROMPT_REGISTRY: dict[str, PromptTemplate] = {
    "blog_idea": BLOG_IDEA_PROMPT,
    "blog_outline": BLOG_OUTLINE_PROMPT,
    "draft_writer": DRAFT_WRITER_PROMPT,
    "technical_review": TECHNICAL_REVIEW_PROMPT,
    "marketing_metadata": MARKETING_META_PROMPT,
    "claim_extraction": CLAIM_EXTRACTION_PROMPT,
    "ai_news_scoring": AI_NEWS_SCORING_PROMPT,
}
