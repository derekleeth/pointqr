"""Add Phase 3 performance indexes for redirect service and analytics.

Revision ID: 003
Revises: 002
Create Date: 2026-09-29

Indexes added:
- scan_events(qr_code_id, timestamp DESC) – composite index for analytics queries
  that filter by QR code and order/range by time.
- qr_codes(short_code) – NOTE: already created by migration 001 as
  ix_qr_codes_short_code (UNIQUE). Skipped here to avoid duplication.
- qr_codes(short_code) WHERE is_active = true – partial index covering only
  active QR codes; significantly speeds up the redirect hot path since
  inactive codes are never redirected.
"""
from __future__ import annotations

from alembic import op

revision: str = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Composite index on scan_events(qr_code_id, timestamp DESC)
    # Speeds up analytics queries that filter by QR code and sort/range
    # on timestamp (e.g. "last N scans for code X", time-bucketed charts).
    # ------------------------------------------------------------------
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_scan_events_qr_code_id_timestamp
        ON scan_events (qr_code_id, timestamp DESC)
        """
    )

    # ------------------------------------------------------------------
    # qr_codes(short_code) plain index
    # NOTE: Migration 001 already creates a UNIQUE index named
    # ix_qr_codes_short_code on qr_codes(short_code) via:
    #   CREATE UNIQUE INDEX IF NOT EXISTS ix_qr_codes_short_code ON qr_codes (short_code)
    # A unique index also serves as a plain lookup index, so no additional
    # non-partial index is needed here.
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Partial index on qr_codes(short_code) WHERE is_active = true
    # Only active codes are eligible for redirect; this index is smaller
    # and faster for the hot-path lookup: SELECT ... WHERE short_code = $1
    # AND is_active = true.
    # ------------------------------------------------------------------
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_qr_codes_short_code_active
        ON qr_codes (short_code)
        WHERE is_active = true
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_qr_codes_short_code_active")
    op.execute("DROP INDEX IF EXISTS ix_scan_events_qr_code_id_timestamp")
