"""Add knowledge_contexts table for Knowledge Collector Agent.

Stores collected context per blog idea. Enables admin review/edit before
passing context to LLM prompts. One row per idea (1:1 with blog_ideas).

Revision ID: 20260608_0042
Revises: 89295a3e1dde
Create Date: 2026-06-08 14:30:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260608_0042"
down_revision: str | None = "89295a3e1dde"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "knowledge_contexts",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("blog_idea_id", sa.String(64), sa.ForeignKey("blog_ideas.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("project_name", sa.String(255), nullable=True),
        sa.Column("project_summary", sa.Text, nullable=True),
        sa.Column("project_content", sa.Text, nullable=True),
        sa.Column("related_blog_posts", sa.Text, nullable=True),
        sa.Column("related_showcases", sa.Text, nullable=True),
        sa.Column("recent_news", sa.Text, nullable=True),
        sa.Column("raw_collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by", sa.String(255), nullable=True),
        sa.Column("edited_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_knowledge_contexts_idea", "knowledge_contexts", ["blog_idea_id"])


def downgrade() -> None:
    op.drop_index("ix_knowledge_contexts_idea")
    op.drop_table("knowledge_contexts")
