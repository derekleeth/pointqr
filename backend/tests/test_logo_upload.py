"""Tests for logo upload safety: uploads are served publicly from the app's own origin."""

from __future__ import annotations

import io
import uuid
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from PIL import Image

from app.config import get_settings
from app.main import UPLOAD_HEADERS, app

PASSWORD = "securepassword123"
CLEAN_SVG = (
    b'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 10 10">'
    b'<defs><rect id="r" width="10" height="10"/></defs><use xlink:href="#r" fill="red"/></svg>'
)
HTML = b"<html><body><script>document.title='xss'</script></body></html>"


# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------

@pytest.fixture
async def client() -> AsyncClient:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict:
    email = f"logo-{uuid.uuid4().hex}@pointqr.dev"
    await client.post("/v1/auth/register", json={"email": email, "password": PASSWORD})
    resp = await client.post("/v1/auth/login", data={"username": email, "password": PASSWORD})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
async def qr_id(client: AsyncClient, auth_headers: dict) -> str:
    response = await client.post(
        "/v1/qrcodes", json={"title": "Logo", "type": "STATIC"}, headers=auth_headers
    )
    return response.json()["id"]


async def _upload(
    client: AsyncClient,
    headers: dict,
    qr_id: str,
    data: bytes,
    content_type: str = "image/png",
    filename: str = "logo.png",
):
    return await client.post(
        f"/v1/qrcodes/{qr_id}/logo",
        files={"file": (filename, data, content_type)},
        headers=headers,
    )


def _image(fmt: str = "PNG", size: tuple[int, int] = (64, 64), mode: str = "RGB", **save: object) -> bytes:
    out = io.BytesIO()
    Image.new(mode, size).save(out, format=fmt, **save)
    return out.getvalue()


def _logo_src(response) -> str:
    return response.json()["design_config"]["imageOptions"]["src"]


def _stored_file(url: str) -> Path:
    return Path(get_settings().storage_path) / url.removeprefix("/static/")


# ---------------------------------------------------------------------------
# Disguised files
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("filename", ["logo.html", "logo.svg", "../../evil.html", "logo.png.html"])
async def test_stored_name_never_comes_from_the_upload(
    client: AsyncClient, auth_headers: dict, qr_id: str, filename: str
) -> None:
    response = await _upload(client, auth_headers, qr_id, _image(), filename=filename)
    assert response.status_code == 200
    src = _logo_src(response)
    assert src.endswith(f"/{qr_id}/logo.png")
    assert _stored_file(src).exists()


@pytest.mark.parametrize("content_type", ["image/png", "image/jpeg", "image/webp"])
async def test_html_disguised_as_an_image_is_rejected(
    client: AsyncClient, auth_headers: dict, qr_id: str, content_type: str
) -> None:
    response = await _upload(client, auth_headers, qr_id, HTML, content_type, "logo.html")
    assert response.status_code == 422


async def test_unlisted_content_types_are_rejected(
    client: AsyncClient, auth_headers: dict, qr_id: str
) -> None:
    response = await _upload(client, auth_headers, qr_id, HTML, "text/html", "logo.html")
    assert response.status_code == 422


async def test_polyglot_image_loses_its_payload(
    client: AsyncClient, auth_headers: dict, qr_id: str
) -> None:
    # A real image with a script after its end marker still opens as an image
    response = await _upload(client, auth_headers, qr_id, _image() + HTML)
    assert response.status_code == 200
    assert b"<script>" not in _stored_file(_logo_src(response)).read_bytes()


# ---------------------------------------------------------------------------
# Real images
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(("fmt", "content_type"), [("PNG", "image/png"), ("JPEG", "image/jpeg"), ("WEBP", "image/webp")])
async def test_images_are_stored_as_png(
    client: AsyncClient, auth_headers: dict, qr_id: str, fmt: str, content_type: str
) -> None:
    response = await _upload(client, auth_headers, qr_id, _image(fmt), content_type)
    assert response.status_code == 200
    with Image.open(_stored_file(_logo_src(response))) as img:
        assert img.format == "PNG"


async def test_exif_is_removed(client: AsyncClient, auth_headers: dict, qr_id: str) -> None:
    exif = Image.Exif()
    exif[0x010F] = "SecretCameraMaker"
    upload = _image("JPEG", exif=exif)
    assert b"SecretCameraMaker" in upload
    response = await _upload(client, auth_headers, qr_id, upload, "image/jpeg")
    assert b"SecretCameraMaker" not in _stored_file(_logo_src(response)).read_bytes()


@pytest.mark.parametrize("mode", ["RGBA", "LA", "P"])
async def test_transparency_is_kept(
    client: AsyncClient, auth_headers: dict, qr_id: str, mode: str
) -> None:
    save = {"transparency": 0} if mode == "P" else {}
    response = await _upload(client, auth_headers, qr_id, _image(mode=mode, **save))
    with Image.open(_stored_file(_logo_src(response))) as img:
        assert img.mode == "RGBA"
        assert img.getpixel((0, 0))[3] == 0


async def test_large_logos_are_shrunk(client: AsyncClient, auth_headers: dict, qr_id: str) -> None:
    response = await _upload(client, auth_headers, qr_id, _image(size=(4000, 1000)))
    with Image.open(_stored_file(_logo_src(response))) as img:
        assert max(img.size) == 2048


async def test_replacing_a_logo_removes_the_old_format(
    client: AsyncClient, auth_headers: dict, qr_id: str
) -> None:
    svg = await _upload(client, auth_headers, qr_id, CLEAN_SVG, "image/svg+xml", "logo.svg")
    svg_file = _stored_file(_logo_src(svg))
    png = await _upload(client, auth_headers, qr_id, _image())
    assert not svg_file.exists()
    assert _stored_file(_logo_src(png)).exists()


async def test_oversized_logos_are_rejected(
    client: AsyncClient, auth_headers: dict, qr_id: str
) -> None:
    response = await _upload(client, auth_headers, qr_id, b"x" * (500 * 1024 + 1))
    assert response.status_code == 422
    assert "500 KB" in response.json()["detail"]


# ---------------------------------------------------------------------------
# SVG
# ---------------------------------------------------------------------------

async def test_clean_svg_is_accepted(client: AsyncClient, auth_headers: dict, qr_id: str) -> None:
    response = await _upload(client, auth_headers, qr_id, CLEAN_SVG, "image/svg+xml", "logo.html")
    assert response.status_code == 200
    src = _logo_src(response)
    assert src.endswith("/logo.svg")
    assert _stored_file(src).read_bytes() == CLEAN_SVG


@pytest.mark.parametrize(
    "svg",
    [
        '<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>',
        '<svg xmlns="http://www.w3.org/2000/svg"><SCRIPT>alert(1)</SCRIPT></svg>',
        '<svg xmlns="http://www.w3.org/2000/svg" onload="alert(1)"/>',
        '<svg xmlns="http://www.w3.org/2000/svg"><rect ONCLICK="alert(1)"/></svg>',
        '<svg xmlns="http://www.w3.org/2000/svg"><foreignObject><body xmlns="http://www.w3.org/1999/xhtml"/></foreignObject></svg>',
        '<svg xmlns="http://www.w3.org/2000/svg"><a href="javascript:alert(1)"><text>x</text></a></svg>',
        '<svg xmlns="http://www.w3.org/2000/svg" xmlns:x="http://www.w3.org/1999/xlink"><use x:href="https://evil.example/a.svg#x"/></svg>',
        '<svg xmlns="http://www.w3.org/2000/svg"><image href=" JavaScript:alert(1)"/></svg>',
        '<svg xmlns="http://www.w3.org/2000/svg"><image href="data:image/svg+xml;base64,PHN2Zz4="/></svg>',
        '<svg xmlns="http://www.w3.org/2000/svg"><set attributeName="href" to="javascript:alert(1)"/></svg>',
        '<svg xmlns="http://www.w3.org/2000/svg"><animate attributeName="href" values="javascript:alert(1)"/></svg>',
        '<!DOCTYPE svg [<!ENTITY a "aaaa"><!ENTITY b "&a;&a;">]><svg xmlns="http://www.w3.org/2000/svg"><text>&b;</text></svg>',
        '<html xmlns="http://www.w3.org/1999/xhtml"><script>alert(1)</script></html>',
        "not xml at all",
    ],
)
async def test_unsafe_svg_is_rejected(
    client: AsyncClient, auth_headers: dict, qr_id: str, svg: str
) -> None:
    response = await _upload(client, auth_headers, qr_id, svg.encode(), "image/svg+xml", "logo.svg")
    assert response.status_code == 422


async def test_svg_in_another_encoding_is_rejected(
    client: AsyncClient, auth_headers: dict, qr_id: str
) -> None:
    upload = '<!DOCTYPE svg [<!ENTITY a "a">]><svg xmlns="http://www.w3.org/2000/svg"/>'.encode("utf-16")
    response = await _upload(client, auth_headers, qr_id, upload, "image/svg+xml", "logo.svg")
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Serving, including files uploaded before validation existed
# ---------------------------------------------------------------------------

async def test_files_already_in_storage_cannot_run_scripts(client: AsyncClient) -> None:
    folder = Path(get_settings().storage_path) / "logos" / f"legacy-{uuid.uuid4().hex}"
    folder.mkdir(parents=True)
    legacy = folder / "logo.html"
    legacy.write_bytes(HTML)
    try:
        # The backend mount sits under the app's root_path. nginx serves /static/ itself.
        response = await client.get(f"/api/static/logos/{folder.name}/logo.html")
        assert response.status_code == 200
        assert response.headers["content-security-policy"] == UPLOAD_HEADERS["Content-Security-Policy"]
        assert "sandbox" in response.headers["content-security-policy"]
        assert response.headers["x-content-type-options"] == "nosniff"
    finally:
        legacy.unlink()
        folder.rmdir()


async def test_uploaded_logos_are_served_with_the_safe_headers(
    client: AsyncClient, auth_headers: dict, qr_id: str
) -> None:
    src = _logo_src(await _upload(client, auth_headers, qr_id, _image()))
    response = await client.get(f"/api{src}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert "sandbox" in response.headers["content-security-policy"]
