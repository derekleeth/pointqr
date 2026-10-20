"""Pydantic schemas for feedback submissions."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.feedback import FeedbackStatus, FeedbackType


class FeedbackCreate(BaseModel):
    """Payload for submitting feedback."""

    type: FeedbackType
    subject: str = Field(min_length=3, max_length=255)
    message: str = Field(min_length=10, max_length=5000)


class FeedbackRead(BaseModel):
    """Public read schema for feedback submissions."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: str
    subject: str
    message: str
    status: str
    github_issue_url: str | None
    github_issue_number: int | None
    created_at: datetime


class FeedbackAdminRead(BaseModel):
    """Admin read schema – includes user info, Slack status, and admin notes."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    user_email: str  # populated from the relationship
    type: str
    subject: str
    message: str
    status: str
    github_issue_url: str | None
    github_issue_number: int | None
    slack_notified: bool
    admin_notes: str | None
    created_at: datetime
    updated_at: datetime


class FeedbackStatusUpdate(BaseModel):
    """Payload to update feedback status (admin only)."""

    status: FeedbackStatus
    admin_notes: str | None = None

