"""Add user_profiles.cover_url column

Revision ID: 0033
Revises: 0032
Create Date: 2026-06-06 12:00:00.000000

"""

from typing import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "20260606_0033"
down_revision: str | None = "20260604_0032"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("user_profiles", sa.Column("cover_url", sa.String(2048), nullable=True))


def downgrade() -> None:
    op.drop_column("user_profiles", "cover_url")
