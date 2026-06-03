"""add news_extracted_articles for URL content extraction

Revision ID: 20260603_0015
Revises: 20260603_0014
Create Date: 2026-06-03
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260603_0015"
down_revision: str | None = "20260603_0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "news_extracted_articles",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("raw_item_id", sa.String(length=64), nullable=False),
        sa.Column("source_url", sa.String(length=1024), nullable=False),
        sa.Column("final_url", sa.String(length=1024), nullable=True),
        sa.Column("canonical_url", sa.String(length=1024), nullable=True),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("author", sa.String(length=256), nullable=True),
        sa.Column("site_name", sa.String(length=256), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("content_markdown", sa.Text(), nullable=False),
        sa.Column("content_text", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("extraction_status", sa.String(length=32), nullable=False),
        sa.Column("extraction_error", sa.Text(), nullable=True),
        sa.Column("provider_latency_ms", sa.Integer(), nullable=True),
        sa.Column("provider_payload", sa.Text(), nullable=True),
        sa.Column("extracted_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["raw_item_id"], ["news_raw_items.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("raw_item_id", name="uq_news_extracted_articles_raw_item"),
    )
    op.create_index(
        "ix_news_extracted_articles_status",
        "news_extracted_articles",
        ["extraction_status"],
    )


def downgrade() -> None:
    op.drop_index("ix_news_extracted_articles_status", table_name="news_extracted_articles")
    op.drop_table("news_extracted_articles")
