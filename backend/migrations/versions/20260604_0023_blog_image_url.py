"""add image_url column to blog_posts for featured images

Revision ID: 20260604_0023
Revises: 20260604_0022
Create Date: 2026-06-04
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260604_0023"
down_revision: str | None = "20260604_0022"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "blog_posts",
        sa.Column("image_url", sa.String(length=2048), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("blog_posts", "image_url")
