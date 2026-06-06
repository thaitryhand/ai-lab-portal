"""Helpers for passing rich project context into blog agent LLM stages."""

from __future__ import annotations

from backend.app.blog_ideas import BlogIdea


def build_project_context(idea: BlogIdea) -> str:
    """Assemble idea metadata plus stored source project fields for LLM prompts."""
    sections = [
        f"Title: {idea.title}",
        f"Angle: {idea.angle}",
        f"Target reader: {idea.target_reader}",
        f"Article goal: {idea.article_goal}",
    ]
    if idea.positioning_notes:
        sections.append(f"Positioning notes: {'; '.join(idea.positioning_notes)}")

    ctx = idea.source_project_context
    if ctx:
        sections.append("--- Source project (ground truth for examples) ---")
        for key, label in (
            ("project_name", "Project name"),
            ("project_summary", "Summary"),
            ("ai_capabilities", "AI capabilities"),
            ("technical_highlights", "Technical highlights"),
            ("business_value", "Business value"),
        ):
            value = ctx.get(key)
            if value:
                sections.append(f"{label}:\n{value}")

    return "\n\n".join(sections)
