"""Analytics API endpoints – scan metrics for the authenticated user."""

from __future__ import annotations

import uuid
from typing import Literal

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.core.dependencies import CurrentUser, DBSession
from app.models.qrcode import QRCode, QRCodeType
from app.models.scan_event import ScanEvent
from app.schemas.analytics import (
    BreakdownItem,
    BreakdownResponse,
    ScanSummary,
    TimeSeriesPoint,
    TimeSeriesResponse,
)

router = APIRouter(prefix="/analytics", tags=["analytics"])


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _user_qr_ids(user_id: uuid.UUID, db: object) -> list[uuid.UUID]:
    """Return all active QR code IDs owned by the user."""
    result = await db.execute(
        select(QRCode.id).where(
            QRCode.user_id == user_id,
            QRCode.is_active == True,  # noqa: E712
        )
    )
    return list(result.scalars().all())


def _scan_base_query(qr_ids: list[uuid.UUID], qr_id_filter: uuid.UUID | None):
    """Return a base select on ScanEvent filtered to the user's QR codes.

    If *qr_id_filter* is given, further restrict to that single code.
    """
    ids = [qr_id_filter] if qr_id_filter else qr_ids
    return select(ScanEvent).where(ScanEvent.qr_code_id.in_(ids))


# ---------------------------------------------------------------------------
# GET /v1/analytics/summary
# ---------------------------------------------------------------------------

@router.get("/summary", response_model=ScanSummary, summary="Overall scan metrics summary")
async def get_summary(
    current_user: CurrentUser,
    db: DBSession,
    qr_id: uuid.UUID | None = Query(default=None, description="Filter to a single QR code"),
) -> ScanSummary:
    """Return aggregate scan statistics for the current user.

    - **total_scans**: Total number of scan events recorded.
    - **unique_ips**: Distinct hashed IP values (privacy-safe estimate of unique visitors).
    - **total_qr_codes**: Count of the user's active QR codes.
    - **dynamic_count** / **static_count**: Breakdown of active codes by type.
    """
    qr_ids = await _user_qr_ids(current_user.id, db)

    # Scan-level aggregates
    scan_ids = [qr_id] if qr_id else qr_ids

    total_scans_res = await db.execute(
        select(func.count()).select_from(ScanEvent).where(ScanEvent.qr_code_id.in_(scan_ids))
    )
    total_scans: int = total_scans_res.scalar_one()

    unique_ips_res = await db.execute(
        select(func.count(func.distinct(ScanEvent.ip_hash)))
        .where(ScanEvent.qr_code_id.in_(scan_ids), ScanEvent.ip_hash.isnot(None))
    )
    unique_ips: int = unique_ips_res.scalar_one()

    # QR code counts (always global per-user, ignoring qr_id filter for counts)
    total_qr_res = await db.execute(
        select(func.count())
        .select_from(QRCode)
        .where(QRCode.user_id == current_user.id, QRCode.is_active == True)  # noqa: E712
    )
    total_qr_codes: int = total_qr_res.scalar_one()

    dynamic_res = await db.execute(
        select(func.count())
        .select_from(QRCode)
        .where(
            QRCode.user_id == current_user.id,
            QRCode.is_active == True,  # noqa: E712
            QRCode.type == QRCodeType.dynamic,
        )
    )
    dynamic_count: int = dynamic_res.scalar_one()

    return ScanSummary(
        total_scans=total_scans,
        unique_ips=unique_ips,
        total_qr_codes=total_qr_codes,
        dynamic_count=dynamic_count,
        static_count=total_qr_codes - dynamic_count,
    )


# ---------------------------------------------------------------------------
# GET /v1/analytics/scans-over-time
# ---------------------------------------------------------------------------

@router.get(
    "/scans-over-time",
    response_model=TimeSeriesResponse,
    summary="Scans aggregated over time",
)
async def get_scans_over_time(
    current_user: CurrentUser,
    db: DBSession,
    granularity: Literal["day", "hour", "month"] = Query(
        default="day",
        description="Time bucket size: 'day', 'hour', or 'month'",
    ),
    days: int = Query(default=30, ge=1, le=365, description="Look-back window in days"),
    qr_id: uuid.UUID | None = Query(default=None, description="Filter to a single QR code"),
) -> TimeSeriesResponse:
    """Return scan counts bucketed by the selected time granularity.

    Uses PostgreSQL ``date_trunc`` for accurate timezone-naive UTC bucketing.
    The ``days`` parameter controls how far back the window extends from now.
    """
    from sqlalchemy import text

    qr_ids = await _user_qr_ids(current_user.id, db)
    scan_ids = [qr_id] if qr_id else qr_ids

    if not scan_ids:
        return TimeSeriesResponse(granularity=granularity, points=[])

    # Build the format string for the output label
    fmt_map = {"day": "YYYY-MM-DD", "hour": "YYYY-MM-DD HH24:00", "month": "YYYY-MM"}
    fmt = fmt_map[granularity]

    # Parameterised raw SQL keeps the query clean and prevents injection
    stmt = text("""
        SELECT
            to_char(date_trunc(:gran, timestamp), :fmt) AS period,
            COUNT(*)::int AS count
        FROM scan_events
        WHERE
            qr_code_id = ANY(:ids)
            AND timestamp >= NOW() - make_interval(days => :days)
        GROUP BY date_trunc(:gran, timestamp)
        ORDER BY date_trunc(:gran, timestamp)
    """)

    result = await db.execute(
        stmt,
        {
            "gran": granularity,
            "fmt": fmt,
            "ids": [str(i) for i in scan_ids],
            "days": days,
        },
    )
    rows = result.fetchall()

    return TimeSeriesResponse(
        granularity=granularity,
        points=[TimeSeriesPoint(period=row.period, count=row.count) for row in rows],
    )


# ---------------------------------------------------------------------------
# Generic breakdown helper
# ---------------------------------------------------------------------------

async def _breakdown(
    column_name: str,
    scan_ids: list[uuid.UUID],
    db: object,
) -> BreakdownResponse:
    """Group scan events by *column_name* and return sorted counts."""
    from sqlalchemy import text

    if not scan_ids:
        return BreakdownResponse(items=[])

    stmt = text(f"""
        SELECT
            COALESCE({column_name}, '(unknown)') AS label,
            COUNT(*)::int AS count
        FROM scan_events
        WHERE qr_code_id = ANY(:ids)
        GROUP BY {column_name}
        ORDER BY count DESC
    """)  # column_name is an internal constant — not user input, safe from injection

    result = await db.execute(stmt, {"ids": [str(i) for i in scan_ids]})
    rows = result.fetchall()
    return BreakdownResponse(
        items=[BreakdownItem(label=row.label, count=row.count) for row in rows]
    )


# ---------------------------------------------------------------------------
# GET /v1/analytics/by-device
# ---------------------------------------------------------------------------

@router.get("/by-device", response_model=BreakdownResponse, summary="Scans by device type")
async def get_by_device(
    current_user: CurrentUser,
    db: DBSession,
    qr_id: uuid.UUID | None = Query(default=None),
) -> BreakdownResponse:
    """Return scan counts grouped by ``device_type`` (mobile / tablet / desktop)."""
    qr_ids = await _user_qr_ids(current_user.id, db)
    scan_ids = [qr_id] if qr_id else qr_ids
    return await _breakdown("device_type", scan_ids, db)


# ---------------------------------------------------------------------------
# GET /v1/analytics/by-os
# ---------------------------------------------------------------------------

@router.get("/by-os", response_model=BreakdownResponse, summary="Scans by operating system")
async def get_by_os(
    current_user: CurrentUser,
    db: DBSession,
    qr_id: uuid.UUID | None = Query(default=None),
) -> BreakdownResponse:
    """Return scan counts grouped by ``os`` (Windows / macOS / Android / iOS / Linux)."""
    qr_ids = await _user_qr_ids(current_user.id, db)
    scan_ids = [qr_id] if qr_id else qr_ids
    return await _breakdown("os", scan_ids, db)


# ---------------------------------------------------------------------------
# GET /v1/analytics/by-browser
# ---------------------------------------------------------------------------

@router.get("/by-browser", response_model=BreakdownResponse, summary="Scans by browser")
async def get_by_browser(
    current_user: CurrentUser,
    db: DBSession,
    qr_id: uuid.UUID | None = Query(default=None),
) -> BreakdownResponse:
    """Return scan counts grouped by ``browser`` (Chrome / Firefox / Safari / Edge / …)."""
    qr_ids = await _user_qr_ids(current_user.id, db)
    scan_ids = [qr_id] if qr_id else qr_ids
    return await _breakdown("browser", scan_ids, db)


# ---------------------------------------------------------------------------
# GET /v1/analytics/by-country
# ---------------------------------------------------------------------------

@router.get("/by-country", response_model=BreakdownResponse, summary="Scans by country")
async def get_by_country(
    current_user: CurrentUser,
    db: DBSession,
    qr_id: uuid.UUID | None = Query(default=None),
) -> BreakdownResponse:
    """Return scan counts grouped by ISO 3166-1 alpha-2 ``country`` code.

    Note: this field is populated once GeoIP lookup is wired into the Celery
    analytics task (Phase 5). Until then most rows will appear as '(unknown)'.
    """
    qr_ids = await _user_qr_ids(current_user.id, db)
    scan_ids = [qr_id] if qr_id else qr_ids
    return await _breakdown("country", scan_ids, db)
