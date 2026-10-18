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


# ---------------------------------------------------------------------------
# Map locations
# ---------------------------------------------------------------------------

class ScanLocation(BaseModel):
    """Scans aggregated at one city-level coordinate."""

    latitude: float
    longitude: float
    city: str | None
    region: str | None
    country: str | None   # ISO 3166-1 alpha-2
    count: int


class ScanLocationsResponse(BaseModel):
    """All scan locations for the map, plus how many scans had no coordinates."""

    locations: list[ScanLocation]
    unlocated: int


# ---------------------------------------------------------------------------
# GeoIP
# ---------------------------------------------------------------------------

class GeoIPInfo(BaseModel):
    """Which GeoIP database is loaded – drives the attribution shown in the UI."""

    provider: str | None        # "maxmind" | "dbip" | None (no database loaded)
    database_type: str | None
    build_date: str | None      # YYYY-MM-DD
