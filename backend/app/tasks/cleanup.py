"""Celery Beat cleanup tasks for storage lifecycle management.

Four scheduled tasks run automatically via Celery Beat:

  purge_expired_exports   – daily @ 02:00 UTC
      Deletes export files + BatchJob rows older than EXPORT_RETENTION_DAYS.

  purge_orphaned_logos    – daily @ 03:00 UTC
      Removes logo files for QR codes that have been soft-deleted for more
      than LOGO_ORPHAN_GRACE_DAYS.

  purge_old_scan_events   – weekly Sunday @ 04:00 UTC
      Deletes ScanEvent rows beyond per-tier retention windows:
        free       → SCAN_EVENT_RETENTION_DAYS_FREE       (default 90 days)
        pro        → SCAN_EVENT_RETENTION_DAYS_PRO        (default 365 days)
        max → SCAN_EVENT_RETENTION_DAYS_MAX (default 730 days, -1 = keep forever)

  reap_stale_jobs         – every hour
      Marks BatchJob rows stuck in PENDING / PROCESSING for more than
      STALE_JOB_TIMEOUT_HOURS as FAILED.

All DB access uses the synchronous psycopg2 engine from app.tasks.db so
there is no asyncpg / event-loop interaction inside forked Celery workers.
"""

from __future__ import annotations

import logging
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import delete, select, update

from app.celery_app import celery_app
from app.config import get_settings
from app.models.batch_job import BatchJob, BatchJobStatus
from app.models.qrcode import QRCode
from app.models.scan_event import ScanEvent
from app.models.user import User, UserTier
from app.tasks.db import task_session

logger = logging.getLogger(__name__)
settings = get_settings()


# ---------------------------------------------------------------------------
# Task 1 – Purge expired export files + their BatchJob rows
# ---------------------------------------------------------------------------

@celery_app.task(
    bind=True,
    name="app.tasks.cleanup.purge_expired_exports",
    queue="default",
    max_retries=3,
    default_retry_delay=300,
)
def purge_expired_exports(self) -> dict:
    """Delete export files and BatchJob rows older than ``export_retention_days``.

    Targets BatchJob rows whose status is COMPLETED or FAILED and whose
    ``created_at`` is older than the configured retention window.

    Export files live at:
        ``{storage_path}/exports/{qr_code_id}/{job_id}.{format}``

    The result_url on the job (``/static/exports/...``) is converted to a
    filesystem path by swapping the ``/static/`` prefix with ``storage_path``.

    Returns:
        dict with keys ``deleted_jobs``, ``deleted_files``, ``errors``.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=settings.export_retention_days)
    deleted_jobs = 0
    deleted_files = 0
    errors = 0

    logger.info("purge_expired_exports: starting (cutoff=%s)", cutoff.isoformat())

    try:
        with task_session() as session:
            jobs = (
                session.execute(
                    select(BatchJob).where(
                        BatchJob.status.in_(
                            [BatchJobStatus.completed, BatchJobStatus.failed]
                        ),
                        BatchJob.created_at < cutoff,
                    )
                )
                .scalars()
                .all()
            )

            for job in jobs:
                # ----------------------------------------------------------
                # 1a. Delete the export file from disk (if result_url is set)
                # ----------------------------------------------------------
                if job.result_url:
                    # result_url is e.g. /static/exports/{qr_id}/{job_id}.png
                    # Map /static/ → {storage_path}/
                    rel = job.result_url.removeprefix("/static/")
                    file_path = Path(settings.storage_path) / rel
                    try:
                        if file_path.exists():
                            file_path.unlink()
                            deleted_files += 1
                            logger.debug("Deleted export file: %s", file_path)

                        # Prune the parent dir if it's now empty
                        parent = file_path.parent
                        if parent.exists() and not any(parent.iterdir()):
                            shutil.rmtree(parent, ignore_errors=True)
                            logger.debug("Pruned empty export dir: %s", parent)
                    except OSError as exc:
                        logger.warning(
                            "Failed to delete export file %s: %s", file_path, exc
                        )
                        errors += 1

                # ----------------------------------------------------------
                # 1b. Delete the BatchJob row
                # ----------------------------------------------------------
                session.delete(job)
                deleted_jobs += 1

        logger.info(
            "purge_expired_exports: done – deleted %d jobs, %d files, %d errors",
            deleted_jobs,
            deleted_files,
            errors,
        )
        return {"deleted_jobs": deleted_jobs, "deleted_files": deleted_files, "errors": errors}

    except Exception as exc:
        logger.error("purge_expired_exports failed: %s", exc, exc_info=True)
        raise self.retry(exc=exc)


# ---------------------------------------------------------------------------
# Task 2 – Purge logo files for soft-deleted QR codes
# ---------------------------------------------------------------------------

@celery_app.task(
    bind=True,
    name="app.tasks.cleanup.purge_orphaned_logos",
    queue="default",
    max_retries=3,
    default_retry_delay=300,
)
def purge_orphaned_logos(self) -> dict:
    """Remove logo files for QR codes that have been soft-deleted.

    A QR code is eligible for logo cleanup when:
    - ``is_active = False``
    - ``updated_at < now() - logo_orphan_grace_days``

    Logo files live at:
        ``{storage_path}/logos/{user_id}/{qr_id}/``

    The entire per-QR directory is removed, not individual files, so any
    extension variant (PNG / SVG / JPEG / WebP) is covered.

    Returns:
        dict with keys ``deleted_dirs``, ``errors``.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=settings.logo_orphan_grace_days)
    deleted_dirs = 0
    errors = 0

    logger.info("purge_orphaned_logos: starting (cutoff=%s)", cutoff.isoformat())

    try:
        with task_session() as session:
            rows = session.execute(
                select(QRCode.id, QRCode.user_id).where(
                    QRCode.is_active == False,  # noqa: E712
                    QRCode.updated_at < cutoff,
                )
            ).all()

        # File deletion happens outside the session to keep the transaction short
        for qr_id, user_id in rows:
            logo_dir = Path(settings.storage_path) / "logos" / str(user_id) / str(qr_id)
            if logo_dir.exists():
                try:
                    shutil.rmtree(logo_dir)
                    deleted_dirs += 1
                    logger.debug("Deleted logo dir: %s", logo_dir)

                    # Prune the user-level dir if it's now empty
                    user_dir = logo_dir.parent
                    if user_dir.exists() and not any(user_dir.iterdir()):
                        shutil.rmtree(user_dir, ignore_errors=True)
                        logger.debug("Pruned empty user logo dir: %s", user_dir)
                except OSError as exc:
                    logger.warning("Failed to delete logo dir %s: %s", logo_dir, exc)
                    errors += 1

        logger.info(
            "purge_orphaned_logos: done – deleted %d dirs, %d errors",
            deleted_dirs,
            errors,
        )
        return {"deleted_dirs": deleted_dirs, "errors": errors}

    except Exception as exc:
        logger.error("purge_orphaned_logos failed: %s", exc, exc_info=True)
        raise self.retry(exc=exc)


# ---------------------------------------------------------------------------
# Task 3 – Purge old scan events beyond per-tier retention windows
# ---------------------------------------------------------------------------

@celery_app.task(
    bind=True,
    name="app.tasks.cleanup.purge_old_scan_events",
    queue="default",
    max_retries=3,
    default_retry_delay=600,
)
def purge_old_scan_events(self) -> dict:
    """Delete ScanEvent rows beyond each tier's configured retention window.

    Retention windows (all configurable via env / Settings):
        - free       → ``scan_event_retention_days_free``       (default  90 days)
        - pro        → ``scan_event_retention_days_pro``        (default 365 days)
        - max → ``scan_event_retention_days_max`` (default 730 days)
          Set to ``-1`` to keep max-tier events forever.

    The delete is tier-aware: scan_events are joined through qr_codes → users
    to identify which tier governs each event.

    Returns:
        dict with keys ``deleted_by_tier`` (per-tier counts) and ``total_deleted``.
    """
    now = datetime.now(timezone.utc)
    total_deleted = 0
    deleted_by_tier: dict[str, int] = {}

    tier_config = [
        (UserTier.free, settings.scan_event_retention_days_free),
        (UserTier.pro, settings.scan_event_retention_days_pro),
        (UserTier.max, settings.scan_event_retention_days_max),
    ]

    logger.info("purge_old_scan_events: starting")

    try:
        for tier, retention_days in tier_config:
            if retention_days == -1:
                logger.info(
                    "purge_old_scan_events [%s]: unlimited retention – skipping",
                    tier.value,
                )
                deleted_by_tier[tier.value] = 0
                continue

            cutoff = now - timedelta(days=retention_days)

            with task_session() as session:
                # Subquery: IDs of QR codes owned by users of this tier
                qr_ids_for_tier = select(QRCode.id).where(
                    QRCode.user_id.in_(
                        select(User.id).where(User.tier == tier)
                    )
                )

                result = session.execute(
                    delete(ScanEvent).where(
                        ScanEvent.timestamp < cutoff,
                        ScanEvent.qr_code_id.in_(qr_ids_for_tier),
                    )
                )
                deleted = result.rowcount

            deleted_by_tier[tier.value] = deleted
            total_deleted += deleted
            logger.info(
                "purge_old_scan_events [%s]: deleted %d rows (cutoff=%s)",
                tier.value,
                deleted,
                cutoff.isoformat(),
            )

        logger.info(
            "purge_old_scan_events: done – total %d rows deleted (%s)",
            total_deleted,
            deleted_by_tier,
        )
        return {"deleted_by_tier": deleted_by_tier, "total_deleted": total_deleted}

    except Exception as exc:
        logger.error("purge_old_scan_events failed: %s", exc, exc_info=True)
        raise self.retry(exc=exc)


# ---------------------------------------------------------------------------
# Task 4 – Reap stale PENDING / PROCESSING jobs
# ---------------------------------------------------------------------------

@celery_app.task(
    bind=True,
    name="app.tasks.cleanup.reap_stale_jobs",
    queue="default",
    max_retries=2,
    default_retry_delay=60,
)
def reap_stale_jobs(self) -> dict:
    """Mark BatchJobs stuck in PENDING or PROCESSING as FAILED.

    A job is considered stale when it has been in PENDING or PROCESSING status
    for longer than ``stale_job_timeout_hours``.  This guards against tasks
    that crashed before they could update their own status row (e.g. worker OOM
    kill, unhandled exception bypassing the retry handler).

    Returns:
        dict with key ``reaped`` (count of jobs marked FAILED).
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=settings.stale_job_timeout_hours)

    try:
        with task_session() as session:
            result = session.execute(
                update(BatchJob)
                .where(
                    BatchJob.status.in_(
                        [BatchJobStatus.pending, BatchJobStatus.processing]
                    ),
                    BatchJob.created_at < cutoff,
                )
                .values(status=BatchJobStatus.failed)
            )
            reaped = result.rowcount

        if reaped:
            logger.warning(
                "reap_stale_jobs: marked %d stale job(s) as FAILED (cutoff=%s)",
                reaped,
                cutoff.isoformat(),
            )
        else:
            logger.debug("reap_stale_jobs: no stale jobs found")

        return {"reaped": reaped}

    except Exception as exc:
        logger.error("reap_stale_jobs failed: %s", exc, exc_info=True)
        raise self.retry(exc=exc)

