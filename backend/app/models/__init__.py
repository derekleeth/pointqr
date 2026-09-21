"""ORM models – import all here so Alembic can discover them."""

from app.models.batch_job import BatchJob  # noqa: F401
from app.models.qrcode import QRCode  # noqa: F401
from app.models.scan_event import ScanEvent  # noqa: F401
from app.models.user import User  # noqa: F401

__all__ = ["User", "QRCode", "ScanEvent", "BatchJob"]
