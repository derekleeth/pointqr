"""JWT creation/verification and password hashing utilities."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings
from app.models.user import UserRole
from app.schemas.auth import TokenData

settings = get_settings()

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Hash a plaintext password with bcrypt."""
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against its bcrypt hash."""
    return _pwd_context.verify(plain, hashed)


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def _create_token(data: dict[str, Any], expires_delta: timedelta) -> str:
    """Create a signed JWT with an expiry."""
    payload = data.copy()
    payload["exp"] = datetime.now(UTC) + expires_delta
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_access_token(user_id: uuid.UUID, role: UserRole) -> str:
    """Create a short-lived access token."""
    return _create_token(
        {"sub": str(user_id), "role": role.value, "type": "access"},
        timedelta(minutes=settings.access_token_expire_minutes),
    )


def create_refresh_token(user_id: uuid.UUID, role: UserRole) -> str:
    """Create a long-lived refresh token."""
    return _create_token(
        {"sub": str(user_id), "role": role.value, "type": "refresh"},
        timedelta(days=settings.refresh_token_expire_days),
    )


def decode_access_token(token: str) -> TokenData:
    """Decode and validate an access token, returning its payload.

    Raises:
        ValueError: if the token is invalid, expired, or wrong type.
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc

    if payload.get("type") != "access":
        raise ValueError("Token is not an access token")

    sub = payload.get("sub")
    role_value = payload.get("role")
    if sub is None or role_value is None:
        raise ValueError("Token payload is missing required fields")

    return TokenData(sub=uuid.UUID(sub), role=UserRole(role_value))


def decode_refresh_token(token: str) -> TokenData:
    """Decode and validate a refresh token.

    Raises:
        ValueError: if the token is invalid, expired, or wrong type.
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc

    if payload.get("type") != "refresh":
        raise ValueError("Token is not a refresh token")

    sub = payload.get("sub")
    role_value = payload.get("role")
    if sub is None or role_value is None:
        raise ValueError("Token payload is missing required fields")

    return TokenData(sub=uuid.UUID(sub), role=UserRole(role_value))
