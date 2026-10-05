"""Synchronous SQLAlchemy engine for use inside Celery tasks.

Celery uses fork-based multiprocessing (ForkPoolWorker).  The async engine
in app.database uses asyncpg, whose connections are bound to the event loop
that created them.  When a worker forks, it inherits those connections but
the parent's loop is closed in the child, causing:

    RuntimeError: Task … got Future … attached to a different loop

The solution is a *separate*, fully synchronous psycopg2 engine that is
created fresh inside each worker process after the fork.  It shares no state
with the async engine used by FastAPI.

Usage (inside a Celery task):
    from app.tasks.db import task_session

    with task_session() as session:
        job = session.get(BatchJob, uuid.UUID(job_id))
        job.status = BatchJobStatus.processing
        session.commit()
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings

settings = get_settings()


def _make_sync_url(async_url: str) -> str:
    """Convert an asyncpg DSN to a psycopg2 DSN.

    e.g. postgresql+asyncpg://... → postgresql+psycopg2://...
    """
    return async_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)


# Engine is module-level so it is created once per worker process (after the
# fork) and reused across tasks in that same worker.  pool_pre_ping guards
# against stale connections when a worker idles between tasks.
_sync_engine = create_engine(
    _make_sync_url(settings.database_url),
    pool_pre_ping=True,
    pool_size=2,        # small – each Celery worker runs one task at a time
    max_overflow=2,
    echo=settings.app_debug,
)

_SyncSession = sessionmaker(bind=_sync_engine, expire_on_commit=False, autoflush=False)


@contextmanager
def task_session() -> Generator[Session, None, None]:
    """Context manager that yields a synchronous SQLAlchemy session.

    Automatically commits on clean exit and rolls back on exceptions.

    Example::

        with task_session() as session:
            job = session.get(BatchJob, job_uuid)
            job.status = BatchJobStatus.processing
            session.commit()
    """
    session: Session = _SyncSession()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
