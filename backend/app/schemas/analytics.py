"""Pydantic schemas for the analytics domain."""

from __future__ import annotations

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

class ScanSummary(BaseModel):
    """Aggregate snapshot for the current user's scan activity."""

    total_scans: int
    unique_ips: int
    total_qr_codes: int
    dynamic_count: int
    static_count: int


# ---------------------------------------------------------------------------
# Time-series
# ---------------------------------------------------------------------------

class TimeSeriesPoint(BaseModel):
    """Single data point in a scans-over-time series."""

    period: str   # ISO date string: "YYYY-MM-DD", "YYYY-MM-DD HH:00", or "YYYY-MM"
    count: int


class TimeSeriesResponse(BaseModel):
    """Full scans-over-time response."""

    granularity: str          # "day" | "hour" | "month"
    points: list[TimeSeriesPoint]


# ---------------------------------------------------------------------------
# Breakdowns
# ---------------------------------------------------------------------------

class BreakdownItem(BaseModel):
    """Single slice in a categorical breakdown (device, OS, browser, country)."""

    label: str    # Human-readable category value; "(unknown)" when NULL
    count: int


class BreakdownResponse(BaseModel):
    """Full categorical breakdown response."""

    items: list[BreakdownItem]
