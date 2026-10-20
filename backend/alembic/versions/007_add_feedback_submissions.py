"""Add feedback_submissions table.

Revision ID: 007
Revises: 006
Create Date: 2026-10-20
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types first, then reference them by name in the table.
    op.execute("CREATE TYPE feedbacktype AS ENUM ('bug', 'feature_request', 'feedback', 'question')")
    op.execute("CREATE TYPE feedbackstatus AS ENUM ('open', 'in_progress', 'resolved', 'closed')")

    op.create_table(
        "feedback_submissions",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "user_id",
            sa.UUID(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "type",
            sa.Enum("bug", "feature_request", "feedback", "question",
                    name="feedbacktype", create_type=False),
            nullable=False,
        ),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("open", "in_progress", "resolved", "closed",
                    name="feedbackstatus", create_type=False),
            nullable=False,
            server_default="open",
        ),
        sa.Column("github_issue_url", sa.String(500), nullable=True),
        sa.Column("github_issue_number", sa.Integer(), nullable=True),
        sa.Column(
            "slack_notified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("admin_notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_feedback_submissions_user_id",
        "feedback_submissions",
        ["user_id"],
    )
    op.create_index(
        "ix_feedback_submissions_type",
        "feedback_submissions",
        ["type"],
    )
    op.create_index(
        "ix_feedback_submissions_status",
        "feedback_submissions",
        ["status"],
    )


def downgrade() -> None:
    op.drop_table("feedback_submissions")
    op.execute("DROP TYPE IF EXISTS feedbackstatus")
    op.execute("DROP TYPE IF EXISTS feedbacktype")

