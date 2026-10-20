"""Feedback submission ORM model."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class FeedbackType(str, enum.Enum):
    bug = "bug"
    feature_request = "feature_request"
    feedback = "feedback"
    question = "question"


class FeedbackStatus(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"


class FeedbackSubmission(Base):
    __tablename__ = "feedback_submissions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type: Mapped[FeedbackType] = mapped_column(
        Enum(
            FeedbackType,
            name="feedbacktype",
            values_callable=lambda objs: [e.value for e in objs],
        ),
        nullable=False,
    )
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[FeedbackStatus] = mapped_column(
        Enum(
            FeedbackStatus,
            name="feedbackstatus",
            values_callable=lambda objs: [e.value for e in objs],
        ),
        default=FeedbackStatus.open,
        nullable=False,
    )
    # GitHub integration — populated when an issue is created
    github_issue_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )
    github_issue_number: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    # Slack integration — set to True after message is sent
    slack_notified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    # Admin notes (internal)
    admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", lazy="selectin")

    def __repr__(self) -> str:
        return f"<FeedbackSubmission id={self.id} type={self.type} status={self.status}>"

