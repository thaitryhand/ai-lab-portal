"""add deduplication fields to news_extracted_articles

Revision ID: 20260603_0016
Revises: 20260603_0015
Create Date: 2026-06-03
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260603_0016"
down_revision: str | None = "20260603_0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "news_extracted_articles",
        sa.Column("canonical_url_normalized", sa.String(length=1024), nullable=False, server_default=""),
    )
    op.add_column(
        "news_extracted_articles",
        sa.Column("duplicate_status", sa.String(length=32), nullable=False, server_default="unique"),
    )
    op.add_column(
        "news_extracted_articles",
        sa.Column("duplicate_of_id", sa.String(length=64), nullable=True),
    )
    op.create_foreign_key(
        "fk_news_extracted_duplicate_of",
        "news_extracted_articles",
        "news_extracted_articles",
        ["duplicate_of_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_news_extracted_canonical_normalized",
        "news_extracted_articles",
        ["canonical_url_normalized"],
    )
    op.create_index(
        "ix_news_extracted_content_hash",
        "news_extracted_articles",
        ["content_hash"],
    )


def downgrade() -> None:
    op.drop_index("ix_news_extracted_content_hash", table_name="news_extracted_articles")
    op.drop_index("ix_news_extracted_canonical_normalized", table_name="news_extracted_articles")
    op.drop_constraint("fk_news_extracted_duplicate_of", "news_extracted_articles", type_="foreignkey")
    op.drop_column("news_extracted_articles", "duplicate_of_id")
    op.drop_column("news_extracted_articles", "duplicate_status")
    op.drop_column("news_extracted_articles", "canonical_url_normalized")
