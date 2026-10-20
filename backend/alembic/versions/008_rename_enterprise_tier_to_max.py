"""Rename the 'enterprise' user tier to 'max'.

Revision ID: 008
Revises: 007
Create Date: 2026-10-20
"""

from __future__ import annotations

from alembic import op

revision: str = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Renames in place, so existing users on this tier carry over automatically.
    op.execute("ALTER TYPE usertier RENAME VALUE 'enterprise' TO 'max'")


def downgrade() -> None:
    op.execute("ALTER TYPE usertier RENAME VALUE 'max' TO 'enterprise'")
