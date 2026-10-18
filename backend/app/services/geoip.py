"""Local GeoIP lookup backed by a MaxMind-format (.mmdb) city database.

The database file is downloaded and refreshed by the Celery Beat task
``app.tasks.geoip.update_geoip_database``, which atomically replaces the file
at ``GEOIP_DB_PATH``.  Each process keeps its own memory-mapped reader and
re-opens it when the file's mtime changes, so a refreshed database is picked
up without restarting uvicorn or the Celery workers.

Both DB-IP "City Lite" and MaxMind "GeoLite2-City" use the same record layout
(``country.iso_code``, ``subdivisions[].names``, ``city.names``, ``location``),
so lookups are provider-agnostic.
"""

from __future__ import annotations

import ipaddress
import logging
import os
import threading
import time
from typing import TypedDict

import maxminddb

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# How often (seconds) to stat() the database file for a newer version.
_RELOAD_CHECK_INTERVAL_S: float = 60.0


class GeoResult(TypedDict):
    country: str | None     # ISO 3166-1 alpha-2
    region: str | None      # First-level subdivision (state / province)
    city: str | None
    latitude: float | None
    longitude: float | None


_lock = threading.Lock()
_reader: maxminddb.Reader | None = None
_reader_mtime: float | None = None
_next_check_at: float = 0.0


def _get_reader() -> maxminddb.Reader | None:
    """Return the current reader, (re)opening it if the file changed on disk."""
    global _reader, _reader_mtime, _next_check_at

    now = time.monotonic()
    if now < _next_check_at:
        return _reader

    with _lock:
        if now < _next_check_at:
            return _reader
        _next_check_at = now + _RELOAD_CHECK_INTERVAL_S

        try:
            mtime = os.stat(settings.geoip_db_path).st_mtime
        except FileNotFoundError:
            if _reader_mtime is not None:
                logger.warning("GeoIP database disappeared from %s", settings.geoip_db_path)
            return _reader

        if mtime == _reader_mtime:
            return _reader

        try:
            new_reader = maxminddb.open_database(settings.geoip_db_path)
        except Exception:
            logger.exception("Failed to open GeoIP database at %s", settings.geoip_db_path)
            return _reader

        old_reader, _reader, _reader_mtime = _reader, new_reader, mtime
        logger.info(
            "Loaded GeoIP database %s (build %s)",
            new_reader.metadata().database_type,
            time.strftime("%Y-%m-%d", time.gmtime(new_reader.metadata().build_epoch)),
        )
        if old_reader is not None:
            old_reader.close()
        return _reader


def provider_for(database_type: str) -> str | None:
    """Map an mmdb ``database_type`` to a provider id ("maxmind" | "dbip")."""
    if database_type.startswith("GeoLite2") or database_type.startswith("GeoIP2"):
        return "maxmind"
    if database_type.startswith("DBIP"):
        return "dbip"
    return None


def database_info() -> dict | None:
    """Return ``{"provider", "database_type", "build_date"}`` for the loaded database."""
    reader = _get_reader()
    if reader is None:
        return None
    meta = reader.metadata()
    return {
        "provider": provider_for(meta.database_type),
        "database_type": meta.database_type,
        "build_date": time.strftime("%Y-%m-%d", time.gmtime(meta.build_epoch)),
    }


def _name(record: dict | None) -> str | None:
    if not record:
        return None
    return (record.get("names") or {}).get("en")


def lookup(ip: str) -> GeoResult | None:
    """Resolve *ip* to a coarse location, or ``None`` if unavailable.

    Private, loopback, and otherwise non-global addresses are skipped, as is
    everything when no database has been downloaded yet.  Never raises.
    """
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return None
    if not addr.is_global:
        return None

    reader = _get_reader()
    if reader is None:
        return None

    try:
        record = reader.get(addr)
    except Exception:
        logger.exception("GeoIP lookup failed")
        return None
    if not record:
        return None

    location = record.get("location") or {}
    subdivisions = record.get("subdivisions") or []
    return GeoResult(
        country=(record.get("country") or {}).get("iso_code"),
        region=_name(subdivisions[0]) if subdivisions else None,
        city=_name(record.get("city")),
        latitude=location.get("latitude"),
        longitude=location.get("longitude"),
    )
