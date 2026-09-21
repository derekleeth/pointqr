"""QR code generation service using segno + Pillow.

Translates the shared design_config JSON schema (compatible with qr-code-styling)
into segno/Pillow calls for server-side high-resolution PNG, SVG, PDF, and EPS export.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Optional

import segno
from PIL import Image


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _error_level(design_config: dict) -> str:
    """Extract error correction level (lower-cased) from design_config."""
    return design_config.get("qrOptions", {}).get("errorCorrectionLevel", "H").lower()


def _dot_color(design_config: dict) -> str:
    return design_config.get("dotsOptions", {}).get("color", "#000000")


def _bg_color(design_config: dict) -> str:
    return design_config.get("backgroundOptions", {}).get("color", "#ffffff")


def _scale(qr: segno.QRCode, target_width: int) -> int:
    """Calculate the integer scale factor to reach approximately target_width pixels."""
    symbol_width = qr.symbol_size()[0]
    return max(1, target_width // symbol_width)


def _border(design_config: dict, scale: int) -> int:
    """Convert the design margin (pixels) to a segno border (modules)."""
    margin_px = design_config.get("margin", 10)
    return max(0, margin_px // max(scale, 1))


def _embed_logo(png_bytes: bytes, logo_path: Path, size_ratio: float = 0.25) -> bytes:
    """Paste a logo image into the center of a PNG QR code using Pillow.

    A white padded background is added behind the logo so it stays readable
    regardless of the dot/background colors.
    """
    qr_img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
    logo_img = Image.open(logo_path).convert("RGBA")

    logo_px = int(qr_img.width * size_ratio)
    logo_img = logo_img.resize((logo_px, logo_px), Image.Resampling.LANCZOS)

    # Add white padding around logo
    pad = max(4, logo_px // 12)
    padded = Image.new("RGBA", (logo_px + pad * 2, logo_px + pad * 2), (255, 255, 255, 255))
    padded.paste(logo_img, (pad, pad), logo_img)

    pos_x = (qr_img.width - padded.width) // 2
    pos_y = (qr_img.height - padded.height) // 2
    qr_img.paste(padded, (pos_x, pos_y), padded)

    buf = io.BytesIO()
    qr_img.save(buf, format="PNG")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Public generation functions
# ---------------------------------------------------------------------------

def generate_png(
    design_config: dict,
    logo_path: Optional[Path | str] = None,
) -> bytes:
    """Render a QR code as PNG bytes.

    If logo_path is provided and the file exists, the logo is composited
    into the center using Pillow (requires error correction level H).
    """
    content = design_config.get("content", "")
    target_width = design_config.get("width", 300)

    qr = segno.make(content, error=_error_level(design_config))
    scale = _scale(qr, target_width)
    border = _border(design_config, scale)

    buf = io.BytesIO()
    qr.save(
        buf,
        kind="png",
        scale=scale,
        dark=_dot_color(design_config),
        light=_bg_color(design_config),
        border=border,
    )
    png_bytes = buf.getvalue()

    # Embed logo if supplied
    if logo_path:
        lp = Path(logo_path)
        if lp.exists():
            size_ratio = design_config.get("imageOptions", {}).get("imageSize", 0.25)
            png_bytes = _embed_logo(png_bytes, lp, size_ratio)

    return png_bytes


def generate_svg(design_config: dict) -> str:
    """Render a QR code as an inline SVG string (no XML declaration)."""
    content = design_config.get("content", "")
    target_width = design_config.get("width", 300)

    qr = segno.make(content, error=_error_level(design_config))
    scale = _scale(qr, target_width)
    border = _border(design_config, scale)

    buf = io.BytesIO()
    qr.save(
        buf,
        kind="svg",
        scale=scale,
        dark=_dot_color(design_config),
        light=_bg_color(design_config),
        border=border,
        xmldecl=False,
        nl=False,
    )
    return buf.getvalue().decode("utf-8")


def generate_pdf(design_config: dict) -> bytes:
    """Render a QR code as PDF bytes."""
    content = design_config.get("content", "")
    target_width = design_config.get("width", 300)

    qr = segno.make(content, error=_error_level(design_config))
    scale = _scale(qr, target_width)
    border = _border(design_config, scale)

    buf = io.BytesIO()
    qr.save(
        buf,
        kind="pdf",
        scale=scale,
        dark=_dot_color(design_config),
        light=_bg_color(design_config),
        border=border,
    )
    return buf.getvalue()


def generate_eps(design_config: dict) -> bytes:
    """Render a QR code as EPS bytes (print-ready vector)."""
    content = design_config.get("content", "")
    target_width = design_config.get("width", 300)

    qr = segno.make(content, error=_error_level(design_config))
    scale = _scale(qr, target_width)
    border = _border(design_config, scale)

    buf = io.BytesIO()
    qr.save(
        buf,
        kind="eps",
        scale=scale,
        dark=_dot_color(design_config),
        light=_bg_color(design_config),
        border=border,
    )
    return buf.getvalue()

