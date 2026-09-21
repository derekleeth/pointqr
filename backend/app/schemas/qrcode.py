"""Pydantic schemas for the QR Code domain."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.models.qrcode import QRCodeType


# ---------------------------------------------------------------------------
# Design sub-schemas – match qr-code-styling options 1:1
# ---------------------------------------------------------------------------

class QROptions(BaseModel):
    errorCorrectionLevel: Literal["L", "M", "Q", "H"] = "H"


class DotsOptions(BaseModel):
    color: str = "#000000"
    type: Literal["square", "dots", "rounded", "classy", "classy-rounded", "extra-rounded"] = "square"


class BackgroundOptions(BaseModel):
    color: str = "#ffffff"


class CornersSquareOptions(BaseModel):
    color: str = "#000000"
    type: Literal["square", "dot", "extra-rounded"] = "square"


class CornersDotOptions(BaseModel):
    color: str = "#000000"
    type: Literal["square", "dot"] = "square"


class ImageOptions(BaseModel):
    src: Optional[str] = None
    margin: int = Field(default=5, ge=0, le=50)
    imageSize: float = Field(default=0.4, ge=0.1, le=0.8)
    hideBackgroundDots: bool = True


class DesignConfig(BaseModel):
    """Full QR code design configuration.

    Shared schema between the qr-code-styling frontend library and
    the segno/Pillow backend renderer.
    """

    content: str = "https://example.com"
    width: int = Field(default=300, ge=100, le=4000)
    height: int = Field(default=300, ge=100, le=4000)
    margin: int = Field(default=10, ge=0, le=100)
    qrOptions: QROptions = Field(default_factory=QROptions)
    dotsOptions: DotsOptions = Field(default_factory=DotsOptions)
    backgroundOptions: BackgroundOptions = Field(default_factory=BackgroundOptions)
    cornersSquareOptions: CornersSquareOptions = Field(default_factory=CornersSquareOptions)
    cornersDotOptions: CornersDotOptions = Field(default_factory=CornersDotOptions)
    imageOptions: ImageOptions = Field(default_factory=ImageOptions)


# ---------------------------------------------------------------------------
# QR Code CRUD schemas
# ---------------------------------------------------------------------------

class QRCodeCreate(BaseModel):
    """Payload for creating a new QR code."""

    title: str = Field(min_length=1, max_length=255)
    type: QRCodeType = QRCodeType.static
    target_url: Optional[str] = Field(default=None, max_length=2048)
    design_config: DesignConfig = Field(default_factory=DesignConfig)


class QRCodeUpdate(BaseModel):
    """Partial update payload – all fields are optional."""

    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    target_url: Optional[str] = Field(default=None, max_length=2048)
    design_config: Optional[DesignConfig] = None
    is_active: Optional[bool] = None


class QRCodeRead(BaseModel):
    """Full QR code response – safe to return to the client."""

    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    type: QRCodeType
    short_code: Optional[str]
    target_url: Optional[str]
    design_config: Optional[dict]
    is_active: bool
    scan_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class QRCodeListResponse(BaseModel):
    """Paginated list of QR codes."""

    items: list[QRCodeRead]
    total: int
    page: int
    per_page: int
    pages: int
