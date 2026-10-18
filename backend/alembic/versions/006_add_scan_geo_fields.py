"""Add region, latitude and longitude to scan_events for GeoIP enrichment.

Revision ID: 006
Revises: 005
Create Date: 2026-10-18
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("scan_events", sa.Column("region", sa.String(100), nullable=True))
    op.add_column("scan_events", sa.Column("latitude", sa.Float(), nullable=True))
    op.add_column("scan_events", sa.Column("longitude", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("scan_events", "longitude")
    op.drop_column("scan_events", "latitude")
    op.drop_column("scan_events", "region")
