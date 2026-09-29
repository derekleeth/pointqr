"""Initial schema – users, qr_codes, scan_events, batch_jobs.

Revision ID: 001
Revises:
Create Date: 2026-09-21
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Enums
    # Using DO $$ blocks because PostgreSQL has no CREATE TYPE IF NOT EXISTS,
    # and SQLAlchemy's checkfirst=True is unreliable over async connection wrappers.
    # ------------------------------------------------------------------
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE userrole AS ENUM ('admin', 'user');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE usertier AS ENUM ('free', 'pro', 'enterprise');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE qrcodetype AS ENUM ('STATIC', 'DYNAMIC');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE batchjobstatus AS ENUM ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # ------------------------------------------------------------------
    # users
    # ------------------------------------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          UUID PRIMARY KEY,
            email       VARCHAR(255) NOT NULL,
            hashed_password VARCHAR(255) NOT NULL,
            is_active   BOOLEAN NOT NULL DEFAULT TRUE,
            is_verified BOOLEAN NOT NULL DEFAULT FALSE,
            role        userrole NOT NULL DEFAULT 'user',
            tier        usertier NOT NULL DEFAULT 'free',
            created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email)
    """)

    # ------------------------------------------------------------------
    # qr_codes
    # ------------------------------------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS qr_codes (
            id            UUID PRIMARY KEY,
            user_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title         VARCHAR(255) NOT NULL,
            type          qrcodetype NOT NULL DEFAULT 'STATIC',
            short_code    VARCHAR(16),
            target_url    TEXT,
            design_config JSONB DEFAULT '{}',
            is_active     BOOLEAN NOT NULL DEFAULT TRUE,
            created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_qr_codes_user_id ON qr_codes (user_id)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_qr_codes_short_code ON qr_codes (short_code)")

    # ------------------------------------------------------------------
    # scan_events
    # ------------------------------------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS scan_events (
            id          UUID PRIMARY KEY,
            qr_code_id  UUID NOT NULL REFERENCES qr_codes(id) ON DELETE CASCADE,
            timestamp   TIMESTAMPTZ NOT NULL DEFAULT now(),
            ip_hash     VARCHAR(64),
            country     VARCHAR(2),
            city        VARCHAR(100),
            device_type VARCHAR(20),
            os          VARCHAR(50),
            browser     VARCHAR(50),
            referer     VARCHAR(500)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_scan_events_qr_code_id ON scan_events (qr_code_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_scan_events_timestamp ON scan_events (timestamp)")

    # ------------------------------------------------------------------
    # batch_jobs
    # ------------------------------------------------------------------
    op.execute("""
        CREATE TABLE IF NOT EXISTS batch_jobs (
            id               UUID PRIMARY KEY,
            user_id          UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            status           batchjobstatus NOT NULL DEFAULT 'PENDING',
            total_items      INTEGER NOT NULL DEFAULT 0,
            processed_items  INTEGER NOT NULL DEFAULT 0,
            result_url       VARCHAR(500),
            created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_batch_jobs_user_id ON batch_jobs (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_batch_jobs_status ON batch_jobs (status)")


def downgrade() -> None:
    op.drop_table("batch_jobs")
    op.drop_table("scan_events")
    op.drop_table("qr_codes")
    op.drop_table("users")

    op.execute("DROP TYPE IF EXISTS batchjobstatus")
    op.execute("DROP TYPE IF EXISTS qrcodetype")
    op.execute("DROP TYPE IF EXISTS usertier")
    op.execute("DROP TYPE IF EXISTS userrole")
