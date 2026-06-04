"""Add blog tags tables.

Revision ID: 20260604_0026
Revises: 20260604_0025
Create Date: 2026-06-04 14:10:00
"""

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260604_0026"
down_revision: str | None = "20260604_0025"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "blog_tags",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("slug", sa.String(80), nullable=False, unique=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_blog_tags_slug", "blog_tags", ["slug"])

    op.create_table(
        "blog_post_tags",
        sa.Column("post_id", sa.String(64), sa.ForeignKey("blog_posts.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tag_id", sa.String(64), sa.ForeignKey("blog_tags.id", ondelete="CASCADE"), primary_key=True),
    )
    op.create_index("ix_blog_post_tags_post_id", "blog_post_tags", ["post_id"])
    op.create_index("ix_blog_post_tags_tag_id", "blog_post_tags", ["tag_id"])


def downgrade() -> None:
    op.drop_index("ix_blog_post_tags_tag_id", table_name="blog_post_tags")
    op.drop_index("ix_blog_post_tags_post_id", table_name="blog_post_tags")
    op.drop_table("blog_post_tags")
    op.drop_index("ix_blog_tags_slug", table_name="blog_tags")
    op.drop_table("blog_tags")
