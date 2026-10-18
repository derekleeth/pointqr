"""Celery application factory with RabbitMQ broker and PostgreSQL result backend."""

from __future__ import annotations

from celery import Celery
from celery.signals import beat_init
from celery.schedules import crontab

from app.config import get_settings

settings = get_settings()

# ---------------------------------------------------------------------------
# Queue definitions
# ---------------------------------------------------------------------------
# default       – lightweight tasks (emails, notifications, scheduled cleanup)
# qr_export     – high-priority single QR render/vector export
# qr_batch      – lower-priority bulk batch generation
# scan_analytics – high-throughput scan event ingestion
# ---------------------------------------------------------------------------

celery_app = Celery(
    "pointqr",
    broker=settings.celery_broker_url,
    # Store task results (state, return values) in RabbitMQ via RPC backend
    backend="rpc://",
    include=[
        # Phase 3+ – task modules will be added here:
        "app.tasks.analytics",
        "app.tasks.export",
        "app.tasks.cleanup",
        "app.tasks.geoip",
        # "app.tasks.batch",
        # "app.tasks.notifications",
    ],
)

celery_app.conf.update(
    # Task serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Reliability settings
    task_acks_late=True,                 # ACK only after successful completion
    task_reject_on_worker_lost=True,     # Re-queue if worker dies mid-task
    worker_prefetch_multiplier=1,        # One task at a time per worker slot
    # Queue routing
    task_default_queue="default",
    task_queues={
        "default": {
            "exchange": "default",
            "exchange_type": "direct",
            "routing_key": "default",
        },
        "qr_export": {
            "exchange": "qr_export",
            "exchange_type": "direct",
            "routing_key": "qr_export",
        },
        "qr_batch": {
            "exchange": "qr_batch",
            "exchange_type": "direct",
            "routing_key": "qr_batch",
        },
        "scan_analytics": {
            "exchange": "scan_analytics",
            "exchange_type": "direct",
            "routing_key": "scan_analytics",
        },
    },
    # Dead-letter exchange for failed messages (configure in RabbitMQ policy)
    task_annotations={
        "*": {"max_retries": 3, "default_retry_delay": 60},
    },
    # ---------------------------------------------------------------------------
    # Celery Beat – periodic cleanup schedules
    # ---------------------------------------------------------------------------
    beat_schedule={
        # Purge completed/failed export files + BatchJob rows older than
        # EXPORT_RETENTION_DAYS (default 7 days).  Runs daily at 02:00 UTC.
        "purge-expired-exports-daily": {
            "task": "app.tasks.cleanup.purge_expired_exports",
            "schedule": crontab(hour=2, minute=0),
        },
        # Remove logo files for QR codes soft-deleted more than
        # LOGO_ORPHAN_GRACE_DAYS ago (default 7 days).  Runs daily at 03:00 UTC.
        "purge-orphaned-logos-daily": {
            "task": "app.tasks.cleanup.purge_orphaned_logos",
            "schedule": crontab(hour=3, minute=0),
        },
        # Delete scan events beyond per-tier retention windows
        # (free=90d / pro=365d / enterprise=730d).  Runs weekly on Sunday 04:00 UTC.
        "purge-old-scan-events-weekly": {
            "task": "app.tasks.cleanup.purge_old_scan_events",
            "schedule": crontab(hour=4, minute=0, day_of_week=0),
        },
        # Mark PENDING/PROCESSING BatchJobs that haven't updated in
        # STALE_JOB_TIMEOUT_HOURS (default 2 h) as FAILED.  Runs every hour.
        "reap-stale-jobs-hourly": {
            "task": "app.tasks.cleanup.reap_stale_jobs",
            "schedule": crontab(minute=0),
        },
        # Refresh the local GeoIP city database if the provider has published
        # a newer build (HEAD check first – no download when unchanged).
        # Runs weekly on Wednesday 05:00 UTC.
        "update-geoip-database-weekly": {
            "task": "app.tasks.geoip.update_geoip_database",
            "schedule": crontab(hour=5, minute=0, day_of_week=3),
        },
    },
    # Beat schedule persistence – stored on disk in the beat service container
    beat_schedule_filename="/app/storage/celerybeat-schedule",
)



@beat_init.connect
def _bootstrap_geoip_database(sender=None, **kwargs) -> None:
    """Check the GeoIP database on every Beat start instead of waiting a week.

    Covers first install and provider switches (MaxMind keys added/removed).
    When nothing changed this is a single HEAD request.
    """
    celery_app.send_task("app.tasks.geoip.update_geoip_database", queue="default")


# Convenience alias used by the Celery CLI: `celery -A app.celery_app worker`
app = celery_app

