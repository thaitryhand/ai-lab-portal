"""add news_review_items for scoring and review queue

Revision ID: 20260603_0017
Revises: 20260603_0016
Create Date: 2026-06-03
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260603_0017"
down_revision: str | None = "20260603_0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "news_review_items",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("extracted_article_id", sa.String(length=64), nullable=False),
        sa.Column("raw_item_id", sa.String(length=64), nullable=False),
        sa.Column("source_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("source_credibility_score", sa.Float(), nullable=False),
        sa.Column("engagement_score", sa.Float(), nullable=False),
        sa.Column("relevance_score", sa.Float(), nullable=False),
        sa.Column("novelty_score", sa.Float(), nullable=False),
        sa.Column("technical_depth_score", sa.Float(), nullable=False),
        sa.Column("business_value_score", sa.Float(), nullable=False),
        sa.Column("spam_risk_score", sa.Float(), nullable=False),
        sa.Column("final_publish_score", sa.Float(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("why_it_matters", sa.Text(), nullable=False),
        sa.Column("scorer_version", sa.String(length=32), nullable=False),
        sa.Column("review_status", sa.String(length=32), nullable=False),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("scored_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["extracted_article_id"],
            ["news_extracted_articles.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["raw_item_id"], ["news_raw_items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_id"], ["news_sources.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("extracted_article_id", name="uq_news_review_items_extracted"),
    )
    op.create_index("ix_news_review_items_status", "news_review_items", ["review_status"])
    op.create_index(
        "ix_news_review_items_final_score",
        "news_review_items",
        ["final_publish_score"],
    )


def downgrade() -> None:
    op.drop_index("ix_news_review_items_final_score", table_name="news_review_items")
    op.drop_index("ix_news_review_items_status", table_name="news_review_items")
    op.drop_table("news_review_items")
