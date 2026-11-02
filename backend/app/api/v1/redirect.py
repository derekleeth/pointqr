"""Redirect service – resolves short codes to target URLs or contact pages and fires scan analytics."""

from __future__ import annotations

import hashlib
import logging
import re
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy import select

from app.config import get_settings
from app.database import AsyncSessionLocal
from app.models.qrcode import QRCode, QRContentType
from app.schemas.qrcode import ContactData
from app.services.vcard import build_vcard, display_name, vcf_content_disposition

logger = logging.getLogger(__name__)

router = APIRouter(tags=["redirect"])
settings = get_settings()
templates = Jinja2Templates(directory=Path(__file__).resolve().parents[2] / "templates")

# ---------------------------------------------------------------------------
# In-process TTL cache: short_code → _Resolved | None
#
# Structure: _redirect_cache[short_code] = (_Resolved | None, expire_at)
# TTL = 60 seconds.  Cache invalidation is TTL-based (natural expiry).
#
# Contact details are deliberately not cached: they are read fresh on every
# request, so deactivating or editing a contact code takes effect immediately.
# ---------------------------------------------------------------------------

class _Resolved(NamedTuple):
    target_url: str
    qr_id: uuid.UUID
    content_type: QRContentType


_CACHE_TTL_SECONDS: int = 60
_redirect_cache: dict[str, tuple[_Resolved | None, float]] = {}


def _cache_get(short_code: str) -> tuple[_Resolved | None, bool]:
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


def _cache_set(short_code: str, value: _Resolved | None) -> None:
    """Store value in the TTL cache."""
    _redirect_cache[short_code] = (value, time.monotonic() + _CACHE_TTL_SECONDS)


# ---------------------------------------------------------------------------
# Contact pages
# ---------------------------------------------------------------------------

# Contact details are personal data: keep them out of search engines and shared caches.
_CONTACT_HEADERS: dict[str, str] = {
    "X-Robots-Tag": "noindex, nofollow",
    "Cache-Control": "no-store",
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
}
_CONTACT_PAGE_HEADERS: dict[str, str] = {
    **_CONTACT_HEADERS,
    # No scripts, forms or embedding. Styles are inline in the template.
    "Content-Security-Policy": (
        "default-src 'none'; img-src 'self' https: data:; style-src 'unsafe-inline'; "
        "base-uri 'none'; form-action 'none'; frame-ancestors 'none'"
    ),
}

_DEFAULT_ACCENT = "#4f46e5"
_PHONE_LABELS = {"mobile": "Mobile", "work": "Work", "home": "Home", "fax": "Fax", "other": "Phone"}
_EMAIL_LABELS = {"work": "Work", "home": "Home", "other": "Other"}
_PHONE_EXTENSION = re.compile(r"\s*(?:x|ext\.?)\s*([0-9]+)$", re.IGNORECASE)


async def _get_active_contact(short_code: str) -> tuple[QRCode, ContactData]:
    """Load a contact code fresh from the DB, or raise 404 if it is unknown or inactive."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(QRCode).where(QRCode.short_code == short_code)
        )
        qr: QRCode | None = result.scalar_one_or_none()

    if (
        qr is None
        or not qr.is_active
        or qr.content_type != QRContentType.vcard
        or not qr.content_data
    ):
        raise HTTPException(status_code=404, detail="QR code not found")
    return qr, ContactData.model_validate(qr.content_data)


def _tel_href(number: str) -> str:
    """Build a tel: link. The display format is dropped, but an extension is kept."""
    extension = _PHONE_EXTENSION.search(number)
    base = _PHONE_EXTENSION.sub("", number)
    href = "tel:" + re.sub(r"[^0-9+]", "", base)
    return f"{href};ext={extension.group(1)}" if extension else href


def _readable_on(hex_color: str) -> str:
    """Return black or white, whichever is legible on *hex_color* (WCAG relative luminance)."""
    channels = [int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    r, g, b = (c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels)
    luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return "#000000" if luminance > 0.179 else "#ffffff"


def _contact_page_context(short_code: str, contact: ContactData) -> dict:
    """Prepare what the page shows. Jinja autoescaping handles every value."""
    name = display_name(contact)
    accent = contact.theme_color or _DEFAULT_ACCENT
    addr = contact.address
    return {
        "contact": contact,
        "name": name,
        "initials": "".join(word[0] for word in name.split()[:2]).upper(),
        "role": " · ".join(p for p in (contact.job_title, contact.organization) if p),
        "accent": accent,
        "on_accent": _readable_on(accent),
        "phones": [
            {"label": _PHONE_LABELS[p.type], "number": p.number, "href": _tel_href(p.number)}
            for p in contact.phones
        ],
        "emails": [
            {"label": _EMAIL_LABELS[e.type], "address": e.address, "href": "mailto:" + quote(e.address, safe="@")}
            for e in contact.emails
        ],
        "address": ", ".join(
            p for p in (addr.street, addr.city, addr.region, addr.postal_code, addr.country) if p
        ) if addr else "",
        "vcf_url": f"/r/{short_code}.vcf",
        "home_url": settings.frontend_url,
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

# Declared before /r/{short_code}, which would otherwise match "abc.vcf" too.
@router.get("/r/{short_code}.vcf", summary="Download a dynamic contact code as a vCard file")
async def download_contact_vcf(short_code: str) -> Response:
    """Serve the contact as a .vcf file. Doesn't record a scan; the page view already did."""
    _, contact = await _get_active_contact(short_code)
    return Response(
        content=build_vcard(contact),
        media_type="text/vcard; charset=utf-8",
        headers={**_CONTACT_HEADERS, "Content-Disposition": vcf_content_disposition(contact)},
    )


@router.get("/r/{short_code}", summary="Resolve a short code to its target URL or contact page")
async def redirect_short_code(short_code: str, request: Request) -> Response:
    """Resolve *short_code* and either issue a 302 redirect or show a hosted contact page.

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
            raise HTTPException(status_code=404, detail="QR code not found")
        resolved = cached
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
            raise HTTPException(status_code=404, detail="QR code not found")

        resolved = _Resolved(qr.target_url or "", qr.id, qr.content_type)
        _cache_set(short_code, resolved)

    # ------------------------------------------------------------------
    # 3. Respond immediately with a contact page or a 302
    # ------------------------------------------------------------------
    response: Response
    if resolved.content_type == QRContentType.vcard:
        _, contact = await _get_active_contact(short_code)
        response = templates.TemplateResponse(
            request,
            "contact.html",
            _contact_page_context(short_code, contact),
            headers=_CONTACT_PAGE_HEADERS,
        )
    else:
        response = RedirectResponse(url=resolved.target_url, status_code=302)

    # ------------------------------------------------------------------
    # 4. Fire-and-forget: publish scan event to Celery (non-blocking)
    # ------------------------------------------------------------------
    try:
        # Lazy import to avoid circular dependency at module load time
        from app.tasks.analytics import log_scan_event  # noqa: PLC0415

        # Extract client metadata
        from app.core.rate_limit import get_client_ip  # noqa: PLC0415

        from app.services.geoip import lookup as geoip_lookup  # noqa: PLC0415

        raw_ip: str = get_client_ip(request)
        ip_hash = hashlib.sha256(raw_ip.encode()).hexdigest()
        user_agent: str | None = request.headers.get("User-Agent")
        referer: str | None = request.headers.get("Referer")
        timestamp: str = datetime.now(tz=timezone.utc).isoformat()
        # Resolve location here (local mmdb, microseconds) so the raw IP never
        # leaves this process – only the hash and coarse location are queued.
        geo = geoip_lookup(raw_ip)

        log_scan_event.apply_async(
            args=[str(resolved.qr_id), ip_hash, user_agent, referer, timestamp],
            kwargs={"geo": geo},
            queue="scan_analytics",
        )
    except Exception:
        # Never let analytics dispatch failure break the redirect
        logger.exception("Failed to dispatch scan analytics task for short_code=%s", short_code)

    return response
