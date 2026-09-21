"""Migration 002 – add scan_count to qr_codes.

Revision ID: 002
Revises: 001
Create Date: 2026-09-21
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "qr_codes",
        sa.Column(
            "scan_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    op.drop_column("qr_codes", "scan_count")

