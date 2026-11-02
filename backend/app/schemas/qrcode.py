"""Pydantic schemas for the QR Code domain."""

from __future__ import annotations

import re
import uuid
from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.models.qrcode import QRCodeType, QRContentType


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


class TextLabelOptions(BaseModel):
    """Text label rendered above or below the QR barcode."""

    enabled: bool = False
    text: str = ""
    fontFamily: str = "sans-serif"
    fontSize: int = Field(default=14, ge=6, le=96)
    fontWeight: Literal["normal", "bold"] = "normal"
    fontStyle: Literal["normal", "italic"] = "normal"
    color: str = "#000000"
    align: Literal["left", "center", "right"] = "center"
    letterSpacing: float = 0.0
    padding: int = Field(default=8, ge=0, le=64)


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
    labelTop: TextLabelOptions = Field(default_factory=TextLabelOptions)
    labelBottom: TextLabelOptions = Field(default_factory=TextLabelOptions)


# ---------------------------------------------------------------------------
# Contact (vCard) sub-schemas – stored in QRCode.content_data for VCARD codes
# ---------------------------------------------------------------------------

_PHONE_PATTERN = re.compile(r"^\+?[0-9 ()./-]+(?:\s*(?:x|ext\.?)\s*[0-9]+)?$", re.IGNORECASE)
_HTTP_URL_PATTERN = re.compile(r"^https?://[^\s/$.?#][^\s]*$", re.IGNORECASE)
_HEX_COLOR_PATTERN = re.compile(r"^#[0-9a-fA-F]{6}$")


def _http_url_or_none(value: object) -> object:
    """Allow only absolute http(s) URLs – blocks javascript:, data:, etc."""
    if not isinstance(value, str):
        return value
    value = value.strip()
    if not value:
        return None
    if not _HTTP_URL_PATTERN.match(value):
        raise ValueError("must be an http:// or https:// URL")
    return value


class ContactPhone(BaseModel):
    type: Literal["mobile", "work", "home", "fax", "other"] = "mobile"
    number: str = Field(min_length=1, max_length=32)

    @field_validator("number")
    @classmethod
    def _check_number(cls, v: str) -> str:
        v = v.strip()
        if not _PHONE_PATTERN.match(v) or sum(c.isdigit() for c in v) < 3:
            raise ValueError("must be a phone number (digits, spaces, + ( ) . - and an optional extension)")
        return v


class ContactEmail(BaseModel):
    type: Literal["work", "home", "other"] = "work"
    address: EmailStr


class ContactAddress(BaseModel):
    type: Literal["work", "home"] = "work"
    street: Optional[str] = Field(default=None, max_length=255)
    city: Optional[str] = Field(default=None, max_length=100)
    region: Optional[str] = Field(default=None, max_length=100)
    postal_code: Optional[str] = Field(default=None, max_length=20)
    country: Optional[str] = Field(default=None, max_length=100)

    def is_empty(self) -> bool:
        return not any((self.street, self.city, self.region, self.postal_code, self.country))


class ContactSocialLink(BaseModel):
    label: str = Field(min_length=1, max_length=50)
    url: str = Field(max_length=2048)

    @field_validator("url")
    @classmethod
    def _check_url(cls, v: str) -> str:
        checked = _http_url_or_none(v)
        if checked is None:
            raise ValueError("must be an http:// or https:// URL")
        return checked


class ContactData(BaseModel):
    """Structured contact details, encoded as a vCard 3.0 (or MECARD) payload."""

    model_config = {"extra": "forbid"}

    # Name
    prefix: Optional[str] = Field(default=None, max_length=50)
    first_name: Optional[str] = Field(default=None, max_length=100)
    last_name: Optional[str] = Field(default=None, max_length=100)
    suffix: Optional[str] = Field(default=None, max_length=50)
    display_name: Optional[str] = Field(default=None, max_length=255)
    # Work
    organization: Optional[str] = Field(default=None, max_length=255)
    job_title: Optional[str] = Field(default=None, max_length=255)
    # Reach
    phones: list[ContactPhone] = Field(default_factory=list, max_length=5)
    emails: list[ContactEmail] = Field(default_factory=list, max_length=3)
    website: Optional[str] = Field(default=None, max_length=2048)
    address: Optional[ContactAddress] = None
    # Other
    note: Optional[str] = Field(default=None, max_length=500)
    birthday: Optional[date] = None
    # Static codes: "mecard" drops some fields in exchange for a less dense code
    encoding: Literal["vcard", "mecard"] = "vcard"
    # Dynamic codes only – shown on the hosted contact page
    social_links: list[ContactSocialLink] = Field(default_factory=list, max_length=10)
    photo_url: Optional[str] = Field(default=None, max_length=2048)
    theme_color: Optional[str] = None

    @field_validator(
        "prefix", "first_name", "last_name", "suffix", "display_name",
        "organization", "job_title", "note",
        mode="before",
    )
    @classmethod
    def _blank_to_none(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip() or None
        return v

    @field_validator("website", mode="before")
    @classmethod
    def _check_website(cls, v: object) -> object:
        return _http_url_or_none(v)

    @field_validator("photo_url", mode="before")
    @classmethod
    def _check_photo_url(cls, v: object) -> object:
        # Uploaded photos are served from our own storage under /static/
        if isinstance(v, str) and v.strip().startswith("/static/"):
            return v.strip()
        return _http_url_or_none(v)

    @field_validator("theme_color")
    @classmethod
    def _check_theme_color(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not _HEX_COLOR_PATTERN.match(v):
            raise ValueError("must be a hex color like #1a2b3c")
        return v

    @field_validator("address")
    @classmethod
    def _drop_empty_address(cls, v: Optional[ContactAddress]) -> Optional[ContactAddress]:
        return None if v is not None and v.is_empty() else v

    @model_validator(mode="after")
    def _require_name(self) -> "ContactData":
        if not (self.first_name or self.last_name or self.organization):
            raise ValueError("at least one of first_name, last_name or organization is required")
        return self

    def dynamic_only_fields(self) -> list[str]:
        """Populated fields that only apply to a hosted (dynamic) contact page."""
        return [
            name
            for name in ("social_links", "photo_url", "theme_color")
            if getattr(self, name)
        ]


# ---------------------------------------------------------------------------
# QR Code CRUD schemas
# ---------------------------------------------------------------------------

class QRCodeCreate(BaseModel):
    """Payload for creating a new QR code."""

    title: str = Field(min_length=1, max_length=255)
    type: QRCodeType = QRCodeType.static
    target_url: Optional[str] = Field(default=None, max_length=2048)
    content_type: QRContentType = QRContentType.url
    content_data: Optional[ContactData] = None
    design_config: DesignConfig = Field(default_factory=DesignConfig)

    @model_validator(mode="after")
    def _check_content(self) -> "QRCodeCreate":
        if self.content_type == QRContentType.vcard and self.content_data is None:
            raise ValueError("content_data is required when content_type is VCARD")
        if self.content_type != QRContentType.vcard and self.content_data is not None:
            raise ValueError("content_data is only supported when content_type is VCARD")
        return self


class QRCodeUpdate(BaseModel):
    """Partial update payload – all fields are optional."""

    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    target_url: Optional[str] = Field(default=None, max_length=2048)
    content_type: Optional[QRContentType] = None
    content_data: Optional[ContactData] = None
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
    content_type: QRContentType
    content_data: Optional[dict]
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

