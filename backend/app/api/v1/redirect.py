"""URL redirect service – resolves short codes to target URLs and fires scan analytics."""

from __future__ import annotations

import hashlib
import logging
import time
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.qrcode import QRCode

logger = logging.getLogger(__name__)

router = APIRouter(tags=["redirect"])

# ---------------------------------------------------------------------------
# In-process TTL cache: short_code → (target_url, qr_id) | None
#
# Structure: _redirect_cache[short_code] = ((target_url, qr_id) | None, expire_at)
# TTL = 60 seconds.  Cache invalidation is TTL-based (natural expiry).
# ---------------------------------------------------------------------------

_CACHE_TTL_SECONDS: int = 60
_redirect_cache: dict[str, tuple[tuple[str, uuid.UUID] | None, float]] = {}


def _cache_get(short_code: str) -> tuple[tuple[str, uuid.UUID] | None, bool]:
    """Return (cached_value, hit).  Expired entries are treated as misses."""
    entry = _redirect_cache.get(short_code)
    if entry is None:
        return None, False
    value, expire_at = entry
    if time.monotonic() > expire_at:
        # Entry expired – evict and signal miss
        _redirect_cache.pop(short_code, None)
        return None, False
    return value, True


def _cache_set(short_code: str, value: tuple[str, uuid.UUID] | None) -> None:
    """Store value in the TTL cache."""
    _redirect_cache[short_code] = (value, time.monotonic() + _CACHE_TTL_SECONDS)


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@router.get("/r/{short_code}", summary="Redirect a short code to its target URL")
async def redirect_short_code(short_code: str, request: Request) -> RedirectResponse:
    """Resolve *short_code* to its target URL and issue a 302 redirect.

    - Returns HTTP 404 if the code is unknown or the QR code is inactive.
    - Caches lookups for 60 s to minimise DB load on popular codes.
    - Fires a fire-and-forget Celery task to record the scan event.
    """
    # ------------------------------------------------------------------
    # 1. Cache lookup
    # ------------------------------------------------------------------
    cached, hit = _cache_get(short_code)
    if hit:
        if cached is None:
            # Previously resolved as not-found; return 404 fast
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="QR code not found")
        target_url, qr_id = cached
    else:
        # ------------------------------------------------------------------
        # 2. DB lookup
        # ------------------------------------------------------------------
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(QRCode).where(QRCode.short_code == short_code)
            )
            qr: QRCode | None = result.scalar_one_or_none()

        if qr is None or not qr.is_active:
            # Cache the negative result so repeated 404s skip the DB too
            _cache_set(short_code, None)
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="QR code not found")

        target_url = qr.target_url or ""
        qr_id = qr.id
        _cache_set(short_code, (target_url, qr_id))

    # ------------------------------------------------------------------
    # 3. Respond immediately with 302
    # ------------------------------------------------------------------
    response = RedirectResponse(url=target_url, status_code=302)

    # ------------------------------------------------------------------
    # 4. Fire-and-forget: publish scan event to Celery (non-blocking)
    # ------------------------------------------------------------------
    try:
        # Lazy import to avoid circular dependency at module load time
        from app.tasks.analytics import log_scan_event  # noqa: PLC0415

        # Extract client metadata
        forwarded_for = request.headers.get("X-Forwarded-For")
        raw_ip: str = (
            forwarded_for.split(",")[0].strip()
            if forwarded_for
            else (request.client.host if request.client else "unknown")
        )
        ip_hash = hashlib.sha256(raw_ip.encode()).hexdigest()
        user_agent: str | None = request.headers.get("User-Agent")
        referer: str | None = request.headers.get("Referer")
        timestamp: str = datetime.now(tz=timezone.utc).isoformat()

        log_scan_event.apply_async(
            args=[str(qr_id), ip_hash, user_agent, referer, timestamp],
            queue="scan_analytics",
        )
    except Exception:
        # Never let analytics dispatch failure break the redirect
        logger.exception("Failed to dispatch scan analytics task for short_code=%s", short_code)

    return response
