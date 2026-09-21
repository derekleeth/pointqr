"""Pydantic schemas for authentication tokens."""

from __future__ import annotations

import uuid

from pydantic import BaseModel

from app.models.user import UserRole


class Token(BaseModel):
    """Response schema for successful login."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Payload extracted from a decoded JWT."""

    sub: uuid.UUID
    role: UserRole


class RefreshRequest(BaseModel):
    """Body for the /auth/refresh endpoint."""

    refresh_token: str
