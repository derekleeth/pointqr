"""Authentication endpoints: register, login, refresh, me."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.dependencies import CurrentUser, DBSession
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import RefreshRequest, Token
from app.schemas.user import UserCreate, UserRead
from app.services.site_settings import get_registration_enabled

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(payload: UserCreate, db: DBSession) -> User:
    """Create a new user account with a hashed password.

    Returns 409 if the email is already registered.
    Returns 403 if registration is disabled by the administrator.
    """
    reg_enabled = await get_registration_enabled(db, settings.registration_enabled)
    if not reg_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Registration is currently disabled. Please contact the administrator.",
        )

    result = await db.execute(select(User).where(User.email == payload.email))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


@router.post(
    "/login",
    response_model=Token,
    summary="Authenticate and receive JWT tokens",
)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DBSession,
) -> Token:
    """Authenticate with email + password (OAuth2 form).

    Returns access and refresh JWTs on success.
    """
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    return Token(
        access_token=create_access_token(user.id, user.role),
        refresh_token=create_refresh_token(user.id, user.role),
    )


@router.post(
    "/refresh",
    response_model=Token,
    summary="Refresh access token using a valid refresh token",
)
async def refresh(payload: RefreshRequest, db: DBSession) -> Token:
    """Exchange a valid refresh token for a new access + refresh token pair."""
    try:
        token_data = decode_refresh_token(payload.refresh_token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    result = await db.execute(select(User).where(User.id == token_data.sub))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return Token(
        access_token=create_access_token(user.id, user.role),
        refresh_token=create_refresh_token(user.id, user.role),
    )


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get the currently authenticated user",
)
async def me(current_user: CurrentUser) -> User:
    """Return the authenticated user's profile."""
    return current_user


@router.get(
    "/registration-status",
    summary="Check whether public registration is enabled",
)
async def registration_status(db: DBSession) -> dict:
    """Return whether self-registration is currently open.

    Reads the DB value first (set by the admin UI), falling back to the
    REGISTRATION_ENABLED env var if no DB override exists.
    """
    reg_enabled = await get_registration_enabled(db, settings.registration_enabled)
    return {"registration_enabled": reg_enabled}

