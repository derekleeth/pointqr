"""SiteSetting ORM model – persists admin-configurable site settings."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SiteSetting(Base):
    """Key-value store for site-wide settings that admins can change at runtime.

    The *key* is a short snake_case identifier (e.g. ``registration_enabled``).
    The *value* is always stored as a UTF-8 string; callers are responsible for
    serialising/deserialising the actual type (bool → "true"/"false", etc.).
    """

    __tablename__ = "site_settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<SiteSetting key={self.key!r} value={self.value!r}>"
