"""Site-settings service – read/write DB-persisted admin settings.

DB values take priority over .env defaults.  All values are stored as
plain strings; this module handles the bool <-> string conversion.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.site_setting import SiteSetting

# Keys used across the codebase
KEY_REGISTRATION_ENABLED = "registration_enabled"


async def get_setting(key: str, default: str, db: AsyncSession) -> str:
    """Return the DB-persisted value for *key*, or *default* if not set."""
    result = await db.execute(select(SiteSetting).where(SiteSetting.key == key))
    row = result.scalar_one_or_none()
    return row.value if row is not None else default


async def set_setting(key: str, value: str, db: AsyncSession) -> SiteSetting:
    """Upsert a setting row and return the updated object."""
    result = await db.execute(select(SiteSetting).where(SiteSetting.key == key))
    row = result.scalar_one_or_none()
    if row is None:
        row = SiteSetting(key=key, value=value)
        db.add(row)
    else:
        row.value = value
    await db.flush()
    await db.refresh(row)
    return row


# ---------------------------------------------------------------------------
# Typed helpers for registration_enabled
# ---------------------------------------------------------------------------

async def get_registration_enabled(db: AsyncSession, env_default: bool) -> bool:
    """Return whether registration is enabled, preferring the DB value."""
    raw = await get_setting(
        KEY_REGISTRATION_ENABLED,
        default="true" if env_default else "false",
        db=db,
    )
    return raw.lower() in ("true", "1", "yes")


async def set_registration_enabled(enabled: bool, db: AsyncSession) -> None:
    """Persist the registration_enabled setting to the database."""
    await set_setting(KEY_REGISTRATION_ENABLED, "true" if enabled else "false", db=db)
