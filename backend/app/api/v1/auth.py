"""Authentication endpoints: register, login, refresh, me, email verification, password reset."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.dependencies import CurrentUser, DBSession
from app.core.rate_limit import limiter
from app.core.security import (
    create_access_token,
    create_email_verification_token,
    create_password_reset_token,
    create_refresh_token,
    decode_email_verification_token,
    decode_password_reset_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import RefreshRequest, Token
from app.schemas.user import UserCreate, UserRead
from app.services.email import send_password_reset_email, send_verification_email
from app.services.site_settings import get_email_verification_required, get_registration_enabled

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class RegisterResponse(BaseModel):
    """Response schema for the /register endpoint.

    When *email_verification_required* is ``True`` the ``user`` field is
    ``None`` and *message* explains what the user should do next.
    When verification is not required, *user* contains the new account data.
    """

    email_verification_required: bool
    user: UserRead | None = None
    message: str = ""


class EmailRequest(BaseModel):
    """Generic payload carrying a single email address."""

    email: str


class PasswordResetRequest(BaseModel):
    """Payload for completing a password reset."""

    token: str
    new_password: str


class ChangePasswordRequest(BaseModel):
    """Payload for changing password while authenticated."""

    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


# ---------------------------------------------------------------------------
# POST /auth/register
# ---------------------------------------------------------------------------

@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
@limiter.limit("5/minute")
async def register(
    request: Request,
    payload: UserCreate,
    db: DBSession,
    background_tasks: BackgroundTasks,
) -> RegisterResponse:
    """Create a new user account with a hashed password.

    Returns 409 if the email is already registered.
    Returns 403 if registration is disabled by the administrator.

    When ``email_verification_required`` is enabled in site settings the new
    account is left unverified and a verification email is dispatched in the
    background; the response body signals this with
    ``email_verification_required=True``.  Otherwise the account is
    immediately marked verified and the new ``UserRead`` is returned.
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

    verification_required = await get_email_verification_required(
        db, settings.email_verification_required
    )

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        is_verified=not verification_required,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    if verification_required:
        token = create_email_verification_token(user.id)
        background_tasks.add_task(
            send_verification_email,
            to=user.email,
            token=token,
            frontend_url=settings.frontend_url,
        )
        return RegisterResponse(
            email_verification_required=True,
            message="Verification email sent. Please check your inbox to activate your account.",
        )

    return RegisterResponse(
        email_verification_required=False,
        user=UserRead.model_validate(user),
    )


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------

@router.post(
    "/login",
    response_model=Token,
    summary="Authenticate and receive JWT tokens",
)
@limiter.limit("10/minute")
async def login(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DBSession,
) -> Token:
    """Authenticate with email + password (OAuth2 form).

    Returns access and refresh JWTs on success.
    Returns 403 if the account email has not been verified yet.
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

    email_verification_required = await get_email_verification_required(
        db, settings.email_verification_required
    )
    if email_verification_required and not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "message": "Email not verified",
                "code": "EMAIL_NOT_VERIFIED",
                "email": user.email,
            },
        )

    return Token(
        access_token=create_access_token(user.id, user.role),
        refresh_token=create_refresh_token(user.id, user.role),
    )


# ---------------------------------------------------------------------------
# POST /auth/refresh
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# GET /auth/me
# ---------------------------------------------------------------------------

@router.get(
    "/me",
    response_model=UserRead,
    summary="Get the currently authenticated user",
)
async def me(current_user: CurrentUser) -> User:
    """Return the authenticated user's profile."""
    return current_user


# ---------------------------------------------------------------------------
# GET /auth/registration-status
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# POST /auth/verify-email
# ---------------------------------------------------------------------------

@router.post(
    "/verify-email",
    summary="Verify a user's email address",
)
@limiter.limit("10/minute")
async def verify_email(request: Request, token: str, db: DBSession) -> dict:
    """Mark a user's email address as verified using a signed JWT.

    The token is produced by :func:`~app.core.security.create_email_verification_token`
    and embedded in the link sent by :func:`~app.services.email.send_verification_email`.

    Returns 400 if the token is invalid or expired.
    """
    try:
        user_id = decode_email_verification_token(token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token",
        )

    user.is_verified = True
    await db.flush()

    return {"message": "Email verified successfully"}


# ---------------------------------------------------------------------------
# POST /auth/resend-verification
# ---------------------------------------------------------------------------

@router.post(
    "/resend-verification",
    summary="Resend email verification link",
)
@limiter.limit("3/10minutes")
async def resend_verification(
    request: Request,
    payload: EmailRequest,
    db: DBSession,
    background_tasks: BackgroundTasks,
) -> dict:
    """Resend the email address verification link.

    Always returns 200 to prevent user enumeration – the caller cannot tell
    whether the address is registered or already verified.
    """
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if user is not None and not user.is_verified:
        token = create_email_verification_token(user.id)
        background_tasks.add_task(
            send_verification_email,
            to=user.email,
            token=token,
            frontend_url=settings.frontend_url,
        )

    return {
        "message": (
            "If that email is registered and unverified, "
            "a new verification link has been sent."
        )
    }


# ---------------------------------------------------------------------------
# POST /auth/forgot-password
# ---------------------------------------------------------------------------

@router.post(
    "/forgot-password",
    summary="Request a password reset link",
)
@limiter.limit("5/minute")
async def forgot_password(
    request: Request,
    payload: EmailRequest,
    db: DBSession,
    background_tasks: BackgroundTasks,
) -> dict:
    """Dispatch a password-reset email if the address is registered.

    Always returns 200 to prevent user enumeration.
    """
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    if user is not None and user.is_active:
        token = create_password_reset_token(user.id)
        background_tasks.add_task(
            send_password_reset_email,
            to=user.email,
            token=token,
            frontend_url=settings.frontend_url,
        )

    return {
        "message": (
            "If that email exists in our system, a password reset link has been sent."
        )
    }


# ---------------------------------------------------------------------------
# POST /auth/reset-password
# ---------------------------------------------------------------------------

@router.post(
    "/reset-password",
    summary="Complete a password reset",
)
async def reset_password(payload: PasswordResetRequest, db: DBSession) -> dict:
    """Set a new password using a valid password-reset JWT.

    Returns 400 if the token is invalid or expired.
    """
    try:
        user_id = decode_password_reset_token(payload.token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token",
        )

    user.hashed_password = hash_password(payload.new_password)
    await db.flush()

    return {"message": "Password reset successful. You can now log in with your new password."}


# ---------------------------------------------------------------------------
# PUT /auth/change-password
# ---------------------------------------------------------------------------

@router.put(
    "/change-password",
    summary="Change password for the currently authenticated user",
)
@limiter.limit("5/minute")
async def change_password(
    request: Request,
    payload: ChangePasswordRequest,
    current_user: CurrentUser,
    db: DBSession,
) -> dict:
    """Change the authenticated user's password.

    Requires the current password for verification before accepting
    the new password.

    Returns 400 if the current password is incorrect.
    Returns 422 if the new password fails validation (too short/long).
    """
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    if payload.current_password == payload.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password",
        )

    current_user.hashed_password = hash_password(payload.new_password)
    await db.flush()

    return {"message": "Password changed successfully"}
