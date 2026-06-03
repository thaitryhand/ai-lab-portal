"""add news_raw_items table for RSS crawl storage

Revision ID: 20260603_0014
Revises: 20260603_0013
Create Date: 2026-06-03
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260603_0014"
down_revision: str | None = "20260603_0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "news_raw_items",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("source_id", sa.String(length=64), nullable=False),
        sa.Column("external_id", sa.String(length=512), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("link_url", sa.String(length=1024), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("raw_payload", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["news_sources.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("source_id", "external_id", name="uq_news_raw_items_source_external"),
    )
    op.create_index("ix_news_raw_items_source", "news_raw_items", ["source_id"])
    op.create_index("ix_news_raw_items_fetched", "news_raw_items", ["fetched_at"])


def downgrade() -> None:
    op.drop_index("ix_news_raw_items_fetched", table_name="news_raw_items")
    op.drop_index("ix_news_raw_items_source", table_name="news_raw_items")
    op.drop_table("news_raw_items")
