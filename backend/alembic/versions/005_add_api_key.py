"""Add api_key and api_key_created_at to users table.

Revision ID: 005
Revises: 004
Create Date: 2026-10-14
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("api_key", sa.String(64), nullable=True))
    op.add_column("users", sa.Column("api_key_created_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_users_api_key", "users", ["api_key"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_api_key", table_name="users")
    op.drop_column("users", "api_key_created_at")
    op.drop_column("users", "api_key")
