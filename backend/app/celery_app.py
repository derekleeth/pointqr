"""Celery application factory with RabbitMQ broker and PostgreSQL result backend."""

from __future__ import annotations

from celery import Celery

from app.config import get_settings

settings = get_settings()

# ---------------------------------------------------------------------------
# Queue definitions
# ---------------------------------------------------------------------------
# default       – lightweight tasks (emails, notifications)
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
        # "app.tasks.export",
        # "app.tasks.batch",
        # "app.tasks.analytics",
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
)

# Convenience alias used by the Celery CLI: `celery -A app.celery_app worker`
app = celery_app
