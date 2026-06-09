"""create page_views table for general page view tracking

Revision ID: 20260608_0043
Revises: 20260608_0042
Create Date: 2026-06-08
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260608_0043"
down_revision: str | None = "20260608_0042"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "page_views",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column("referrer", sa.Text(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("ip_hash", sa.String(length=64), nullable=True),
        sa.Column("session_id", sa.String(length=64), nullable=False),
        sa.Column("viewport_width", sa.Integer(), nullable=True),
        sa.Column("viewport_height", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_page_views_created", "page_views", ["created_at"])
    op.create_index("ix_page_views_path_created", "page_views", ["path", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_page_views_path_created", table_name="page_views")
    op.drop_index("ix_page_views_created", table_name="page_views")
    op.drop_table("page_views")
