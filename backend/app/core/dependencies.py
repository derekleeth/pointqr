"""FastAPI dependency providers (authentication, role enforcement, DB session)."""

from __future__ import annotations

import hashlib
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.database import get_db
from app.models.user import User, UserRole

# OAuth2 scheme – points to the login endpoint
# auto_error=False so we can fall through to API key auth
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_current_user(
    request: Request,
    token: Annotated[Optional[str], Depends(oauth2_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Decode the JWT or API key and load the corresponding user from the database."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    user: User | None = None

    # --- Strategy 1: JWT Bearer token ---
    if token:
        try:
            token_data = decode_access_token(token)
        except ValueError:
            raise credentials_exception

        result = await db.execute(select(User).where(User.id == token_data.sub))
        user = result.scalar_one_or_none()

    # --- Strategy 2: X-API-Key header ---
    if user is None:
        api_key = request.headers.get("X-API-Key")
        if api_key:
            hashed = hashlib.sha256(api_key.encode("utf-8")).hexdigest()
            result = await db.execute(select(User).where(User.api_key == hashed))
            user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )
    return user


async def require_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Dependency that enforces admin role."""
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator privileges required",
        )
    return current_user


# Convenient type aliases for use in route signatures
CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(require_admin)]
DBSession = Annotated[AsyncSession, Depends(get_db)]
