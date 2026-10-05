"""Celery tasks for scan event ingestion and analytics enrichment.

All database access uses the synchronous psycopg2 engine from app.tasks.db so
that there is no asyncpg / event-loop interaction inside forked Celery workers.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import text

from app.celery_app import celery_app
from app.models.scan_event import ScanEvent
from app.tasks.db import task_session

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# User-Agent parsing helpers (basic string matching – user_agents lib not installed)
# ---------------------------------------------------------------------------

def _parse_device_type(ua: str | None) -> str | None:
    """Classify device type from User-Agent string."""
    if not ua:
        return None
    if "Mobile" in ua or "Android" in ua and "Mobile" in ua:
        return "mobile"
    if "iPad" in ua or "Tablet" in ua:
        return "tablet"
    return "desktop"


def _parse_os(ua: str | None) -> str | None:
    """Extract operating system name from User-Agent string."""
    if not ua:
        return None
    if "Windows" in ua:
        return "Windows"
    if "Mac OS X" in ua or "Macintosh" in ua:
        return "macOS"
    if "Android" in ua:
        return "Android"
    if "iPhone" in ua or "iPad" in ua or "iOS" in ua:
        return "iOS"
    if "Linux" in ua:
        return "Linux"
    return None


def _parse_browser(ua: str | None) -> str | None:
    """Extract browser name from User-Agent string."""
    if not ua:
        return None
    # Order matters: Edg must come before Chrome; OPR before Chrome
    if "Edg/" in ua or "EdgA/" in ua:
        return "Edge"
    if "OPR/" in ua or "Opera" in ua:
        return "Opera"
    if "SamsungBrowser" in ua:
        return "Samsung Internet"
    if "Chrome/" in ua:
        return "Chrome"
    if "Firefox/" in ua:
        return "Firefox"
    if "Safari/" in ua and "Chrome/" not in ua:
        return "Safari"
    return None


# ---------------------------------------------------------------------------
# Celery task
# ---------------------------------------------------------------------------

@celery_app.task(
    bind=True,
    name="app.tasks.analytics.log_scan_event",
    queue="scan_analytics",
    max_retries=3,
    default_retry_delay=30,
)
def log_scan_event(
    self,
    qr_code_id: str,
    ip_hash: str,
    user_agent: str | None,
    referer: str | None,
    timestamp: str,
) -> None:
    """Record a QR code scan event and increment the scan counter.

    Args:
        qr_code_id: UUID string of the scanned QR code.
        ip_hash:    SHA-256 hex digest of the scanner's IP address.
        user_agent: Raw User-Agent header value (may be None).
        referer:    Referer header value (may be None).
        timestamp:  ISO-8601 datetime string of when the scan occurred.
    """
    try:
        # TODO: Add GeoIP lookup (country/city) once geoip2 is added to dependencies
        country: str | None = None
        city: str | None = None

        device_type = _parse_device_type(user_agent)
        os_name = _parse_os(user_agent)
        browser = _parse_browser(user_agent)

        try:
            ts = datetime.fromisoformat(timestamp)
        except ValueError:
            ts = datetime.now(tz=timezone.utc)

        qr_uuid = uuid.UUID(qr_code_id)

        with task_session() as session:
            # Insert ScanEvent row
            event = ScanEvent(
                qr_code_id=qr_uuid,
                timestamp=ts,
                ip_hash=ip_hash,
                country=country,
                city=city,
                device_type=device_type,
                os=os_name,
                browser=browser,
                referer=referer,
            )
            session.add(event)

            # Atomically increment the denormalized scan counter
            session.execute(
                text("UPDATE qr_codes SET scan_count = scan_count + 1 WHERE id = :id"),
                {"id": qr_uuid},
            )

            session.commit()
            logger.info(
                "scan_event logged",
                extra={"qr_code_id": qr_code_id, "device": device_type, "browser": browser},
            )

    except Exception as exc:
        logger.exception("log_scan_event failed – retrying: %s", exc)
        raise self.retry(exc=exc)
