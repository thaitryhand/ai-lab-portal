"""Add user follows and blog author user ids.

Revision ID: 20260604_0028
Revises: 20260604_0027
Create Date: 2026-06-04 16:10:00
"""

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260604_0028"
down_revision: str | None = "20260604_0027"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("blog_posts", sa.Column("author_user_id", sa.String(255), nullable=True))
    op.create_table(
        "user_follows",
        sa.Column("follower_user_id", sa.String(255), nullable=False),
        sa.Column("followed_user_id", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("follower_user_id", "followed_user_id"),
        sa.CheckConstraint("follower_user_id <> followed_user_id", name="ck_user_follows_not_self"),
    )
    op.create_index("ix_user_follows_follower", "user_follows", ["follower_user_id"])
    op.create_index("ix_user_follows_followed", "user_follows", ["followed_user_id"])
    op.create_index("ix_blog_posts_author_user_id", "blog_posts", ["author_user_id"])


def downgrade() -> None:
    op.drop_index("ix_blog_posts_author_user_id", table_name="blog_posts")
    op.drop_index("ix_user_follows_followed", table_name="user_follows")
    op.drop_index("ix_user_follows_follower", table_name="user_follows")
    op.drop_table("user_follows")
    op.drop_column("blog_posts", "author_user_id")
