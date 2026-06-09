"""create events table for custom event tracking (clicks, shares, comments)

Revision ID: 20260608_0044
Revises: 20260608_0043
Create Date: 2026-06-08
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260608_0044"
down_revision: str | None = "20260608_0043"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "events",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("event_metadata", sa.Text(), nullable=True),
        sa.Column("session_id", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_events_type_created", "events", ["event_type", "created_at"])
    op.create_index("ix_events_path_created", "events", ["path", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_events_path_created", table_name="events")
    op.drop_index("ix_events_type_created", table_name="events")
    op.drop_table("events")
