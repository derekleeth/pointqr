"""QR code CRUD, export, and logo upload endpoints."""

from __future__ import annotations

import math
import secrets
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Query, Response, UploadFile, status
from sqlalchemy import func, select

from app.config import get_settings
from app.core.dependencies import CurrentUser, DBSession
from app.models.qrcode import QRCode, QRCodeType
from app.schemas.qrcode import (
    DesignConfig,
    QRCodeCreate,
    QRCodeListResponse,
    QRCodeRead,
    QRCodeUpdate,
)
from app.services.qr_generator import generate_eps, generate_pdf, generate_png, generate_svg

router = APIRouter(prefix="/qrcodes", tags=["qrcodes"])
settings = get_settings()

ALLOWED_LOGO_CONTENT_TYPES = {"image/png", "image/svg+xml", "image/jpeg", "image/webp"}
MAX_LOGO_BYTES = 500 * 1024  # 500 KB


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _make_short_code() -> str:
    """Return an 8-character URL-safe alphanumeric short code."""
    # token_urlsafe(6) → 6 raw bytes → 8 base64url characters
    return secrets.token_urlsafe(6)


async def _get_qr_or_404(qr_id: uuid.UUID, user: object, db: object) -> QRCode:
    """Fetch a QR code owned by the current user or raise HTTP 404."""
    result = await db.execute(
        select(QRCode).where(QRCode.id == qr_id, QRCode.user_id == user.id)
    )
    qr = result.scalar_one_or_none()
    if qr is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="QR code not found")
    return qr


def _resolve_logo_path(design_config: dict) -> Path | None:
    """Convert /static/... logo URL in design_config to a filesystem path."""
    src = (design_config.get("imageOptions") or {}).get("src")
    if src and src.startswith("/static/"):
        rel = src.removeprefix("/static/")
        candidate = Path(settings.storage_path) / rel
        return candidate if candidate.exists() else None
    return None


# ---------------------------------------------------------------------------
# CRUD endpoints
# ---------------------------------------------------------------------------

@router.get("", response_model=QRCodeListResponse, summary="List QR codes for the current user")
async def list_qrcodes(
    current_user: CurrentUser,
    db: DBSession,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
) -> QRCodeListResponse:
    """Return a paginated list of the authenticated user's active QR codes."""
    offset = (page - 1) * per_page

    total_result = await db.execute(
        select(func.count())
        .select_from(QRCode)
        .where(QRCode.user_id == current_user.id, QRCode.is_active == True)  # noqa: E712
    )
    total = total_result.scalar_one()

    items_result = await db.execute(
        select(QRCode)
        .where(QRCode.user_id == current_user.id, QRCode.is_active == True)  # noqa: E712
        .order_by(QRCode.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    items = list(items_result.scalars().all())

    return QRCodeListResponse(
        items=[QRCodeRead.model_validate(item) for item in items],
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if total > 0 else 0,
    )


@router.post(
    "",
    response_model=QRCodeRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new QR code",
)
async def create_qrcode(
    payload: QRCodeCreate,
    current_user: CurrentUser,
    db: DBSession,
) -> QRCode:
    """Persist a new QR code for the authenticated user.

    Dynamic codes receive an auto-generated 8-character short code.
    """
    short_code: str | None = None
    if payload.type == QRCodeType.dynamic:
        # Retry up to 10 times to guarantee uniqueness
        for _ in range(10):
            candidate = _make_short_code()
            result = await db.execute(select(QRCode).where(QRCode.short_code == candidate))
            if result.scalar_one_or_none() is None:
                short_code = candidate
                break
        if short_code is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate a unique short code – please try again",
            )

    # For dynamic codes the encoded content is the future redirect URL
    # For static codes target_url equals the encoded content
    design = payload.design_config.model_dump()
    if payload.type == QRCodeType.dynamic and payload.target_url:
        # Static short URL will be filled in Phase 3
        design["content"] = payload.target_url

    qr = QRCode(
        user_id=current_user.id,
        title=payload.title,
        type=payload.type,
        short_code=short_code,
        target_url=payload.target_url,
        design_config=design,
    )
    db.add(qr)
    await db.flush()
    await db.refresh(qr)
    return qr


@router.get("/{qr_id}", response_model=QRCodeRead, summary="Get a single QR code")
async def get_qrcode(
    qr_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> QRCode:
    return await _get_qr_or_404(qr_id, current_user, db)


@router.patch("/{qr_id}", response_model=QRCodeRead, summary="Update a QR code")
async def update_qrcode(
    qr_id: uuid.UUID,
    payload: QRCodeUpdate,
    current_user: CurrentUser,
    db: DBSession,
) -> QRCode:
    """Partially update title, target URL, design config, or active state."""
    qr = await _get_qr_or_404(qr_id, current_user, db)

    if payload.title is not None:
        qr.title = payload.title
    if payload.target_url is not None:
        qr.target_url = payload.target_url
    if payload.design_config is not None:
        # Merge with existing config so logo src is preserved unless explicitly overwritten
        existing = dict(qr.design_config or {})
        updated = payload.design_config.model_dump()
        existing.update(updated)
        qr.design_config = existing
    if payload.is_active is not None:
        qr.is_active = payload.is_active

    await db.flush()
    await db.refresh(qr)
    return qr


@router.delete(
    "/{qr_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a QR code",
)
async def delete_qrcode(
    qr_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
) -> None:
    """Mark a QR code as inactive (soft delete). Scan history is preserved."""
    qr = await _get_qr_or_404(qr_id, current_user, db)
    qr.is_active = False
    await db.flush()


# ---------------------------------------------------------------------------
# Export endpoint
# ---------------------------------------------------------------------------

@router.post("/{qr_id}/export", summary="Export QR code as a downloadable file")
async def export_qrcode(
    qr_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
    format: str = Query(default="png", pattern="^(png|svg|pdf|eps)$"),
) -> Response:
    """Render and stream the QR code in the requested format.

    Uses the segno/Pillow backend renderer (not the client-side library),
    so the output is always high-resolution and print-quality.
    """
    qr = await _get_qr_or_404(qr_id, current_user, db)
    design = qr.design_config or DesignConfig().model_dump()
    logo_path = _resolve_logo_path(design)
    safe_name = qr.title.replace(" ", "_")

    match format:
        case "png":
            data = generate_png(design, logo_path)
            media_type = "image/png"
        case "svg":
            data = generate_svg(design).encode("utf-8")
            media_type = "image/svg+xml"
        case "pdf":
            data = generate_pdf(design)
            media_type = "application/pdf"
        case "eps":
            data = generate_eps(design)
            media_type = "application/postscript"
        case _:
            raise HTTPException(status_code=400, detail="Unsupported format")

    return Response(
        content=data,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{safe_name}.{format}"'},
    )


# ---------------------------------------------------------------------------
# Logo upload endpoint
# ---------------------------------------------------------------------------

@router.post(
    "/{qr_id}/logo",
    response_model=QRCodeRead,
    summary="Upload a center logo for the QR code",
)
async def upload_logo(
    qr_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
    file: UploadFile = File(...),
) -> QRCode:
    """Upload a PNG/SVG/JPEG logo to embed in the center of the QR code.

    The file is saved to the shared storage volume and served at /static/logos/...
    The design_config.imageOptions.src is updated with the static URL.
    """
    qr = await _get_qr_or_404(qr_id, current_user, db)

    if file.content_type not in ALLOWED_LOGO_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported file type '{file.content_type}'. Allowed: PNG, SVG, JPEG, WebP.",
        )

    raw = await file.read()
    if len(raw) > MAX_LOGO_BYTES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Logo file exceeds the 500 KB limit.",
        )

    # Persist to storage volume
    ext = Path(file.filename or "logo.png").suffix or ".png"
    logo_dir = Path(settings.storage_path) / "logos" / str(current_user.id) / str(qr_id)
    logo_dir.mkdir(parents=True, exist_ok=True)
    logo_file = logo_dir / f"logo{ext}"
    logo_file.write_bytes(raw)

    # Store the static URL in design_config
    static_url = f"/static/logos/{current_user.id}/{qr_id}/logo{ext}"
    design = dict(qr.design_config or {})
    img_opts = dict(design.get("imageOptions") or {})
    img_opts["src"] = static_url
    design["imageOptions"] = img_opts
    qr.design_config = design

    await db.flush()
    await db.refresh(qr)
    return qr

