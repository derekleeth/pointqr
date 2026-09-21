"""QRCode ORM model."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class QRCodeType(str, enum.Enum):
    static = "STATIC"
    dynamic = "DYNAMIC"


class QRCode(Base):
    __tablename__ = "qr_codes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[QRCodeType] = mapped_column(
        Enum(QRCodeType, name="qrcodetype"), default=QRCodeType.static, nullable=False
    )
    # Unique short code for dynamic QR redirect URLs (e.g. /r/{short_code})
    short_code: Mapped[str | None] = mapped_column(
        String(16), unique=True, nullable=True, index=True
    )
    # Target URL for dynamic codes or the encoded content for static codes
    target_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    # QR design configuration stored as JSONB for flexibility
    design_config: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="qr_codes")
    scan_events: Mapped[list["ScanEvent"]] = relationship(
        "ScanEvent", back_populates="qr_code", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<QRCode id={self.id} title={self.title!r} type={self.type}>"
