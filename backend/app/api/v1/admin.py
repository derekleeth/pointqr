"""Admin-only endpoints: user management, usage stats, site settings."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, select

from app.config import get_settings
from app.core.dependencies import AdminUser, DBSession
from app.core.security import hash_password
from app.models.qrcode import QRCode
from app.models.user import User, UserRole, UserTier
from app.schemas.user import UserRead
from app.services.site_settings import (
    get_registration_enabled,
    set_registration_enabled,
)

router = APIRouter(prefix="/admin", tags=["admin"])
settings = get_settings()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class UserRoleUpdate(BaseModel):
    """Payload to update a user's role."""
    role: UserRole


class UserTierUpdate(BaseModel):
    """Payload to update a user's tier."""
    tier: UserTier


class UserStatusUpdate(BaseModel):
    """Payload to activate or deactivate a user."""
    is_active: bool


class SiteSettings(BaseModel):
    """Current site-level settings returned to the admin UI."""
    registration_enabled: bool


class RegistrationUpdate(BaseModel):
    """Payload to toggle public registration."""
    registration_enabled: bool


class AdminCreateUser(BaseModel):
    """Admin can create a user with an explicit role."""
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.user
    tier: UserTier = UserTier.free


# ---------------------------------------------------------------------------
# GET /admin/users – list all users with usage stats
# ---------------------------------------------------------------------------

@router.get(
    "/users",
    summary="List all users with usage statistics",
)
async def list_users(
    _admin: AdminUser,
    db: DBSession,
) -> list[dict]:
    """Return every registered user together with their QR code and scan counts."""
    users_result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = list(users_result.scalars().all())

    # Batch-load QR code counts per user
    qr_counts_result = await db.execute(
        select(QRCode.user_id, func.count().label("cnt"))
        .where(QRCode.is_active == True)  # noqa: E712
        .group_by(QRCode.user_id)
    )
    qr_counts: dict[uuid.UUID, int] = {row.user_id: row.cnt for row in qr_counts_result}

    # Batch-load total scan counts per user via the denormalised scan_count column
    scan_counts_result = await db.execute(
        select(QRCode.user_id, func.sum(QRCode.scan_count).label("total"))
        .group_by(QRCode.user_id)
    )
    scan_counts: dict[uuid.UUID, int] = {
        row.user_id: (row.total or 0) for row in scan_counts_result
    }

    return [
        {
            "id": str(u.id),
            "email": u.email,
            "is_active": u.is_active,
            "is_verified": u.is_verified,
            "role": u.role.value,
            "tier": u.tier.value,
            "created_at": u.created_at.isoformat(),
            "qr_code_count": qr_counts.get(u.id, 0),
            "total_scans": scan_counts.get(u.id, 0),
        }
        for u in users
    ]


# ---------------------------------------------------------------------------
# POST /admin/users – create a user as admin
# ---------------------------------------------------------------------------

@router.post(
    "/users",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user (admin only)",
)
async def admin_create_user(
    payload: AdminCreateUser,
    _admin: AdminUser,
    db: DBSession,
) -> User:
    """Create a user account with an explicit role without going through the
    public registration flow (works even when registration is disabled).
    """
    result = await db.execute(select(User).where(User.email == payload.email))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        tier=payload.tier,
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# PATCH /admin/users/{user_id}/role
# ---------------------------------------------------------------------------

@router.patch(
    "/users/{user_id}/role",
    response_model=UserRead,
    summary="Change a user's role",
)
async def update_user_role(
    user_id: uuid.UUID,
    payload: UserRoleUpdate,
    admin: AdminUser,
    db: DBSession,
) -> User:
    """Promote or demote a user's role (admin <-> user).

    Raises 400 if an admin tries to demote themselves to prevent lockout.
    """
    if user_id == admin.id and payload.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot remove your own admin role.",
        )
    user = await _get_user_or_404(user_id, db)
    user.role = payload.role
    await db.flush()
    await db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# PATCH /admin/users/{user_id}/tier
# ---------------------------------------------------------------------------

@router.patch(
    "/users/{user_id}/tier",
    response_model=UserRead,
    summary="Change a user's subscription tier",
)
async def update_user_tier(
    user_id: uuid.UUID,
    payload: UserTierUpdate,
    _admin: AdminUser,
    db: DBSession,
) -> User:
    """Update a user's tier (free / pro / enterprise)."""
    user = await _get_user_or_404(user_id, db)
    user.tier = payload.tier
    await db.flush()
    await db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# PATCH /admin/users/{user_id}/status
# ---------------------------------------------------------------------------

@router.patch(
    "/users/{user_id}/status",
    response_model=UserRead,
    summary="Enable or disable a user account",
)
async def update_user_status(
    user_id: uuid.UUID,
    payload: UserStatusUpdate,
    admin: AdminUser,
    db: DBSession,
) -> User:
    """Activate or deactivate a user account.

    Raises 400 if an admin tries to deactivate themselves.
    """
    if user_id == admin.id and not payload.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot deactivate your own account.",
        )
    user = await _get_user_or_404(user_id, db)
    user.is_active = payload.is_active
    await db.flush()
    await db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# DELETE /admin/users/{user_id}
# ---------------------------------------------------------------------------

@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user account permanently",
)
async def delete_user(
    user_id: uuid.UUID,
    admin: AdminUser,
    db: DBSession,
) -> None:
    """Permanently delete a user and all associated data (cascade)."""
    if user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account.",
        )
    user = await _get_user_or_404(user_id, db)
    await db.delete(user)
    await db.flush()


# ---------------------------------------------------------------------------
# GET /admin/settings
# ---------------------------------------------------------------------------

@router.get(
    "/settings",
    response_model=SiteSettings,
    summary="Get current site settings",
)
async def get_site_settings(_admin: AdminUser, db: DBSession) -> SiteSettings:
    """Return the current site-level configuration.

    The DB value takes priority over the .env default.
    """
    reg_enabled = await get_registration_enabled(db, settings.registration_enabled)
    return SiteSettings(registration_enabled=reg_enabled)


# ---------------------------------------------------------------------------
# PATCH /admin/settings
# ---------------------------------------------------------------------------

@router.patch(
    "/settings",
    response_model=SiteSettings,
    summary="Update site settings",
)
async def update_site_settings(
    payload: RegistrationUpdate,
    _admin: AdminUser,
    db: DBSession,
) -> SiteSettings:
    """Persist updated site settings to the database.

    The DB value overrides whatever is set in the .env file without requiring
    a container restart.
    """
    await set_registration_enabled(payload.registration_enabled, db=db)
    return SiteSettings(registration_enabled=payload.registration_enabled)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _get_user_or_404(user_id: uuid.UUID, db: object) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user
