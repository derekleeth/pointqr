"""Pydantic schemas for User domain."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole, UserTier


class UserCreate(BaseModel):
    """Schema for creating a new user (registration)."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserRead(BaseModel):
    """Schema returned to the client – never exposes hashed_password."""

    id: uuid.UUID
    email: EmailStr
    is_active: bool
    is_verified: bool
    role: UserRole
    tier: UserTier
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    """Schema for partial user profile updates."""

    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)
