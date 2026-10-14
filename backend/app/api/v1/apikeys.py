"""API key management endpoints."""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.core.dependencies import CurrentUser, DBSession

router = APIRouter(prefix="/apikeys", tags=["apikeys"])


def _hash_api_key(key: str) -> str:
    """Return the SHA-256 hex digest of an API key."""
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


class APIKeyInfo(BaseModel):
    has_key: bool
    key_hint: str | None = None
    created_at: datetime | None = None


class APIKeyCreated(BaseModel):
    api_key: str
    key_hint: str
    created_at: datetime
    message: str = "Store this key securely — it will not be shown again."


@router.get("", response_model=APIKeyInfo, summary="Get API key status")
async def get_api_key_info(current_user: CurrentUser) -> APIKeyInfo:
    """Return whether the user has an active API key and when it was created."""
    if current_user.api_key is None:
        return APIKeyInfo(has_key=False)
    return APIKeyInfo(
        has_key=True,
        key_hint=f"pqr_{'•' * 12}",
        created_at=current_user.api_key_created_at,
    )


@router.post(
    "",
    response_model=APIKeyCreated,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a new API key",
)
async def create_api_key(current_user: CurrentUser, db: DBSession) -> APIKeyCreated:
    """Generate a new API key for the authenticated user.

    If the user already has a key, it is replaced. The plaintext key is returned
    only once — subsequent GET requests show a masked hint.
    """
    plaintext = f"pqr_{secrets.token_hex(32)}"
    hashed = _hash_api_key(plaintext)
    now = datetime.now(UTC)

    current_user.api_key = hashed
    current_user.api_key_created_at = now
    await db.flush()

    return APIKeyCreated(
        api_key=plaintext,
        key_hint=plaintext[:8] + "•" * 12,
        created_at=now,
    )


@router.delete("", status_code=status.HTTP_204_NO_CONTENT, summary="Revoke API key")
async def revoke_api_key(current_user: CurrentUser, db: DBSession) -> None:
    """Permanently revoke the user's API key."""
    if current_user.api_key is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No API key to revoke",
        )
    current_user.api_key = None
    current_user.api_key_created_at = None
    await db.flush()
