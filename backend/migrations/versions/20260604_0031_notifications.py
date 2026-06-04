"""Add notifications table.

Revision ID: 20260604_0031
Revises: 20260604_0030
Create Date: 2026-06-04 23:00:00
"""

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260604_0031"
down_revision: str | None = "20260604_0030"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(255), nullable=False),
        sa.Column("type", sa.String(32), nullable=False),
        sa.Column("actor_user_id", sa.String(255), nullable=False),
        sa.Column("actor_email", sa.String(320), nullable=True),
        sa.Column("actor_display_name", sa.String(160), nullable=True),
        sa.Column("resource_id", sa.String(64), nullable=False, server_default=""),
        sa.Column("resource_type", sa.String(32), nullable=False, server_default=""),
        sa.Column("read", sa.Boolean, nullable=False, server_default=sa.text("FALSE")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_notifications_user_read",
        "notifications",
        ["user_id", "read"],
    )
    op.create_index(
        "ix_notifications_user_created",
        "notifications",
        ["user_id", "created_at"],
    )
