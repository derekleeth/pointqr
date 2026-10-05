"""Celery tasks for high-resolution QR code export (PNG, SVG, PDF, EPS).

All database access uses the synchronous psycopg2 engine from app.tasks.db so
that there is no asyncpg / event-loop interaction inside forked Celery workers.
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path

from sqlalchemy import select

from app.celery_app import celery_app
from app.config import get_settings
from app.models.batch_job import BatchJob, BatchJobStatus
from app.models.qrcode import QRCode
from app.tasks.db import task_session

logger = logging.getLogger(__name__)
settings = get_settings()


# ---------------------------------------------------------------------------
# Internal sync helpers
# ---------------------------------------------------------------------------

def _mark_job_processing(job_id: str) -> None:
    """Set BatchJob status to PROCESSING."""
    with task_session() as session:
        job = session.execute(
            select(BatchJob).where(BatchJob.id == uuid.UUID(job_id))
        ).scalar_one_or_none()
        if job is None:
            raise ValueError(f"BatchJob {job_id} not found")
        job.status = BatchJobStatus.processing
        session.commit()


def _fetch_qr_design(qr_code_id: str) -> dict:
    """Fetch design_config for the given QRCode id."""
    with task_session() as session:
        qr = session.execute(
            select(QRCode).where(QRCode.id == uuid.UUID(qr_code_id))
        ).scalar_one_or_none()
        if qr is None:
            raise ValueError(f"QRCode {qr_code_id} not found")
        return dict(qr.design_config or {})


def _mark_job_completed(job_id: str, result_url: str) -> None:
    """Set BatchJob status to COMPLETED and store result_url."""
    with task_session() as session:
        job = session.execute(
            select(BatchJob).where(BatchJob.id == uuid.UUID(job_id))
        ).scalar_one_or_none()
        if job is None:
            raise ValueError(f"BatchJob {job_id} not found")
        job.status = BatchJobStatus.completed
        job.processed_items = job.total_items
        job.result_url = result_url
        session.commit()


def _mark_job_failed(job_id: str) -> None:
    """Set BatchJob status to FAILED."""
    with task_session() as session:
        job = session.execute(
            select(BatchJob).where(BatchJob.id == uuid.UUID(job_id))
        ).scalar_one_or_none()
        if job is None:
            logger.warning("BatchJob %s not found when attempting to mark FAILED", job_id)
            return
        job.status = BatchJobStatus.failed
        session.commit()


# ---------------------------------------------------------------------------
# Celery task
# ---------------------------------------------------------------------------

@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    queue="qr_export",
)
def export_qr_code(self, qr_code_id: str, format: str, job_id: str) -> str:  # noqa: A002
    """Export a QR code to a file on disk and record the result in the BatchJob.

    Args:
        qr_code_id: UUID string of the QRCode to export.
        format: One of ``png``, ``svg``, ``pdf``, ``eps``.
        job_id: UUID string of the BatchJob tracking this task.

    Returns:
        The relative static URL of the exported file.
    """
    from app.services.qr_generator import generate_eps, generate_pdf, generate_png, generate_svg

    try:
        # Step 1 – Mark job as PROCESSING
        _mark_job_processing(job_id)

        # Step 2 – Fetch QR code design config
        design = _fetch_qr_design(qr_code_id)

        # Step 3 – Generate the file bytes using the appropriate renderer
        match format:
            case "png":
                data: bytes = generate_png(design)
            case "svg":
                data = generate_svg(design).encode("utf-8")
            case "pdf":
                data = generate_pdf(design)
            case "eps":
                data = generate_eps(design)
            case _:
                raise ValueError(f"Unsupported export format: {format!r}")

        # Step 4 – Write file to storage
        out_dir = Path(settings.storage_path) / "exports" / qr_code_id
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f"{job_id}.{format}"
        out_file.write_bytes(data)
        logger.info("Exported QR %s to %s", qr_code_id, out_file)

        # Step 5 – Mark job as COMPLETED
        result_url = f"/static/exports/{qr_code_id}/{job_id}.{format}"
        _mark_job_completed(job_id, result_url)

        return result_url

    except Exception as exc:
        logger.exception(
            "export_qr_code failed for qr=%s format=%s job=%s: %s",
            qr_code_id,
            format,
            job_id,
            exc,
        )
        # Mark job FAILED before retrying so the client sees the intermediate
        # failure; it will be flipped back to PROCESSING on retry.
        try:
            _mark_job_failed(job_id)
        except Exception:
            logger.exception("Failed to mark BatchJob %s as FAILED", job_id)

        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
