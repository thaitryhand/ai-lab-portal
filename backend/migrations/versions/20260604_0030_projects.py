"""Add projects table.

Revision ID: 20260604_0030
Revises: 20260604_0029
Create Date: 2026-06-04 22:00:00
"""

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260604_0030"
down_revision: str | None = "20260604_0029"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("slug", sa.String(160), nullable=False, unique=True),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("content_markdown", sa.Text, nullable=False),
        sa.Column("image_url", sa.String(2048), nullable=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_projects_status_published_at",
        "projects",
        ["status", "published_at"],
    )
