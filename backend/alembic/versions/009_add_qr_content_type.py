"""Add content_type and content_data to qr_codes for structured payloads (vCard).

Revision ID: 009
Revises: 008
Create Date: 2026-11-01
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE qrcontenttype AS ENUM ('URL', 'TEXT', 'VCARD');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    # The server default backfills every existing row as URL.
    op.add_column(
        "qr_codes",
        sa.Column(
            "content_type",
            sa.Enum("URL", "TEXT", "VCARD", name="qrcontenttype", create_type=False),
            nullable=False,
            server_default="URL",
        ),
    )
    op.add_column("qr_codes", sa.Column("content_data", JSONB, nullable=True))


def downgrade() -> None:
    op.drop_column("qr_codes", "content_data")
    op.drop_column("qr_codes", "content_type")
    op.execute("DROP TYPE IF EXISTS qrcontenttype")
