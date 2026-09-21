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
    # ------------------------------------------------------------------
    userrole = postgresql.ENUM("admin", "user", name="userrole", create_type=True)
    usertier = postgresql.ENUM("free", "pro", "enterprise", name="usertier", create_type=True)
    qrcodetype = postgresql.ENUM("STATIC", "DYNAMIC", name="qrcodetype", create_type=True)
    batchjobstatus = postgresql.ENUM(
        "PENDING", "PROCESSING", "COMPLETED", "FAILED",
        name="batchjobstatus", create_type=True,
    )

    userrole.create(op.get_bind(), checkfirst=True)
    usertier.create(op.get_bind(), checkfirst=True)
    qrcodetype.create(op.get_bind(), checkfirst=True)
    batchjobstatus.create(op.get_bind(), checkfirst=True)

    # ------------------------------------------------------------------
    # users
    # ------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("is_verified", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column(
            "role",
            sa.Enum("admin", "user", name="userrole"),
            nullable=False,
            server_default="user",
        ),
        sa.Column(
            "tier",
            sa.Enum("free", "pro", "enterprise", name="usertier"),
            nullable=False,
            server_default="free",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # ------------------------------------------------------------------
    # qr_codes
    # ------------------------------------------------------------------
    op.create_table(
        "qr_codes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column(
            "type",
            sa.Enum("STATIC", "DYNAMIC", name="qrcodetype"),
            nullable=False,
            server_default="STATIC",
        ),
        sa.Column("short_code", sa.String(16), nullable=True),
        sa.Column("target_url", sa.Text, nullable=True),
        sa.Column("design_config", postgresql.JSONB, nullable=True, server_default="{}"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_qr_codes_user_id", "qr_codes", ["user_id"])
    op.create_index("ix_qr_codes_short_code", "qr_codes", ["short_code"], unique=True)

    # ------------------------------------------------------------------
    # scan_events
    # ------------------------------------------------------------------
    op.create_table(
        "scan_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "qr_code_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("qr_codes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("ip_hash", sa.String(64), nullable=True),
        sa.Column("country", sa.String(2), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("device_type", sa.String(20), nullable=True),
        sa.Column("os", sa.String(50), nullable=True),
        sa.Column("browser", sa.String(50), nullable=True),
        sa.Column("referer", sa.String(500), nullable=True),
    )
    op.create_index("ix_scan_events_qr_code_id", "scan_events", ["qr_code_id"])
    op.create_index("ix_scan_events_timestamp", "scan_events", ["timestamp"])

    # ------------------------------------------------------------------
    # batch_jobs
    # ------------------------------------------------------------------
    op.create_table(
        "batch_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("PENDING", "PROCESSING", "COMPLETED", "FAILED", name="batchjobstatus"),
            nullable=False,
            server_default="PENDING",
        ),
        sa.Column("total_items", sa.Integer, nullable=False, server_default="0"),
        sa.Column("processed_items", sa.Integer, nullable=False, server_default="0"),
        sa.Column("result_url", sa.String(500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_batch_jobs_user_id", "batch_jobs", ["user_id"])
    op.create_index("ix_batch_jobs_status", "batch_jobs", ["status"])


def downgrade() -> None:
    op.drop_table("batch_jobs")
    op.drop_table("scan_events")
    op.drop_table("qr_codes")
    op.drop_table("users")

    op.execute("DROP TYPE IF EXISTS batchjobstatus")
    op.execute("DROP TYPE IF EXISTS qrcodetype")
    op.execute("DROP TYPE IF EXISTS usertier")
    op.execute("DROP TYPE IF EXISTS userrole")
