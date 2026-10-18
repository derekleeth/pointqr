"""Celery Beat task that keeps the local GeoIP city database up to date.

  update_geoip_database   – weekly Wednesday @ 05:00 UTC (and once when Beat
                            starts if no database exists yet)

Provider selection:
  * MaxMind GeoLite2-City  – when MAXMIND_ACCOUNT_ID and MAXMIND_LICENSE_KEY
                             are set (free account; updated twice weekly).
  * DB-IP City Lite        – otherwise.  No account needed; updated monthly.
                             Licensed CC BY 4.0, so the UI must credit DB-IP.

The task first issues a HEAD request and only downloads when the remote file
is newer than the local copy, or when the installed file came from the other
provider (e.g. MaxMind keys were just added to .env) (MaxMind does not count HEAD requests against the
daily download limit).  The download is decompressed into a temp file next to
the target, validated by opening it with maxminddb, then swapped into place
with an atomic ``os.replace``.  Readers in uvicorn / Celery processes notice
the new mtime and re-open it (see app.services.geoip).
"""

from __future__ import annotations

import gzip
import logging
import os
import shutil
import tarfile
import tempfile
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

import httpx
import maxminddb

from app.celery_app import celery_app
from app.config import get_settings
from app.services.geoip import provider_for

logger = logging.getLogger(__name__)
settings = get_settings()

_MAXMIND_URL = "https://download.maxmind.com/geoip/databases/GeoLite2-City/download?suffix=tar.gz"
_DBIP_URL = "https://download.db-ip.com/free/dbip-city-lite-{month}.mmdb.gz"
_HTTP_TIMEOUT = httpx.Timeout(30.0, read=300.0)


def _use_maxmind() -> bool:
    return bool(settings.maxmind_account_id and settings.maxmind_license_key)


def _resolve_source(client: httpx.Client) -> tuple[str, datetime | None]:
    """Return ``(url, last_modified)`` for the newest available database."""
    if _use_maxmind():
        resp = client.head(_MAXMIND_URL)
        resp.raise_for_status()
        return str(resp.url), _parse_last_modified(resp)

    # DB-IP publishes on the 1st of each month; early on the 1st the new file
    # may not exist yet, so fall back to the previous month.
    today = datetime.now(timezone.utc).date()
    prev_month = today.replace(day=1) - timedelta(days=1)
    for month in (today.strftime("%Y-%m"), prev_month.strftime("%Y-%m")):
        url = _DBIP_URL.format(month=month)
        resp = client.head(url)
        if resp.status_code == 404:
            continue
        resp.raise_for_status()
        return url, _parse_last_modified(resp)
    raise RuntimeError("No DB-IP City Lite database found for this or last month")


def _parse_last_modified(resp: httpx.Response) -> datetime | None:
    header = resp.headers.get("Last-Modified")
    if not header:
        return None
    try:
        return parsedate_to_datetime(header)
    except (TypeError, ValueError):
        return None


def _installed_provider(path: Path) -> str | None:
    """Return the provider of the database at *path*, or None if unreadable."""
    try:
        with maxminddb.open_database(str(path)) as reader:
            return provider_for(reader.metadata().database_type)
    except Exception:
        return None


def _extract_mmdb(archive: Path, dest: Path) -> None:
    """Write the .mmdb contained in *archive* (tar.gz or .gz) to *dest*."""
    if _use_maxmind():
        with tarfile.open(archive, "r:gz") as tar:
            member = next(
                (m for m in tar.getmembers() if m.isfile() and m.name.endswith(".mmdb")),
                None,
            )
            if member is None:
                raise RuntimeError("MaxMind archive did not contain an .mmdb file")
            src = tar.extractfile(member)
            assert src is not None
            with src, dest.open("wb") as out:
                shutil.copyfileobj(src, out)
    else:
        with gzip.open(archive, "rb") as src, dest.open("wb") as out:
            shutil.copyfileobj(src, out)


@celery_app.task(
    bind=True,
    name="app.tasks.geoip.update_geoip_database",
    queue="default",
    max_retries=3,
    default_retry_delay=1800,
)
def update_geoip_database(self, force: bool = False) -> dict:
    """Download a newer GeoIP city database if one is available.

    Args:
        force: Download even if the local file is already up to date.

    Returns:
        dict with keys ``status`` ("updated" | "up_to_date"), ``source``,
        and ``build_date`` when updated.
    """
    target = Path(settings.geoip_db_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    provider = "maxmind" if _use_maxmind() else "dbip"
    auth = (settings.maxmind_account_id, settings.maxmind_license_key) if _use_maxmind() else None

    try:
        with httpx.Client(timeout=_HTTP_TIMEOUT, follow_redirects=True, auth=auth) as client:
            url, remote_modified = _resolve_source(client)

            if (
                not force
                and target.exists()
                and remote_modified is not None
                and _installed_provider(target) == provider
            ):
                local_modified = datetime.fromtimestamp(target.stat().st_mtime, tz=timezone.utc)
                if local_modified >= remote_modified:
                    logger.info(
                        "update_geoip_database: %s is up to date (remote %s)",
                        target, remote_modified.isoformat(),
                    )
                    return {"status": "up_to_date", "source": provider}

            logger.info("update_geoip_database: downloading %s database", provider)
            with tempfile.TemporaryDirectory(dir=target.parent) as tmp:
                archive = Path(tmp) / "download"
                with client.stream("GET", url) as resp, archive.open("wb") as fh:
                    resp.raise_for_status()
                    for chunk in resp.iter_bytes(1024 * 1024):
                        fh.write(chunk)

                staged = Path(tmp) / target.name
                _extract_mmdb(archive, staged)

                # Validate before swapping in: a corrupt file would break lookups.
                with maxminddb.open_database(str(staged)) as reader:
                    meta = reader.metadata()
                    if "City" not in meta.database_type:
                        raise RuntimeError(f"Unexpected database type {meta.database_type!r}")
                    build_date = datetime.fromtimestamp(meta.build_epoch, tz=timezone.utc)

                # Stamp the file with the remote Last-Modified so the next
                # run's freshness check compares like with like.
                if remote_modified is not None:
                    ts = remote_modified.timestamp()
                    os.utime(staged, (ts, ts))
                os.replace(staged, target)

    except Exception as exc:
        logger.exception("update_geoip_database failed – retrying: %s", exc)
        raise self.retry(exc=exc)

    logger.info(
        "update_geoip_database: installed %s (%s, built %s)",
        target, meta.database_type, build_date.date().isoformat(),
    )
    return {"status": "updated", "source": provider, "build_date": build_date.date().isoformat()}
