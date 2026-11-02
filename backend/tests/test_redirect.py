"""Tests for the redirect service: URL redirects and hosted contact pages."""

from __future__ import annotations

import io
import uuid
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from PIL import Image

from app.config import get_settings
from app.main import app
from app.tasks import analytics

PASSWORD = "securepassword123"
CONTACT = {
    "first_name": "José",
    "last_name": "Núñez",
    "job_title": "Engineer",
    "organization": "Acme, Inc.",
    "phones": [{"type": "mobile", "number": "+1 (555) 010-0100 x42"}],
    "emails": [{"type": "work", "address": "jose@example.com"}],
    "website": "https://example.com",
    "note": "line one\nline two",
}


# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------

@pytest.fixture
async def client() -> AsyncClient:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict:
    # Each test gets its own user, since a free account only allows 3 dynamic codes
    email = f"redirect-{uuid.uuid4().hex}@pointqr.dev"
    await client.post("/v1/auth/register", json={"email": email, "password": PASSWORD})
    resp = await client.post("/v1/auth/login", data={"username": email, "password": PASSWORD})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
def scans(monkeypatch: pytest.MonkeyPatch) -> list:
    """Capture scan events instead of sending them to Celery."""
    events: list = []
    monkeypatch.setattr(
        analytics.log_scan_event, "apply_async", lambda *args, **kwargs: events.append(kwargs)
    )
    return events


async def _create_contact(client: AsyncClient, headers: dict, **contact: object) -> dict:
    response = await client.post(
        "/v1/qrcodes",
        json={
            "title": "Contact",
            "type": "DYNAMIC",
            "content_type": "VCARD",
            "content_data": {**CONTACT, **contact},
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def _image(fmt: str = "PNG", size: tuple[int, int] = (800, 600), **save: object) -> bytes:
    out = io.BytesIO()
    Image.new("RGB", size, "#336699").save(out, format=fmt, **save)
    return out.getvalue()


def _stored_file(photo_url: str) -> Path:
    return Path(get_settings().storage_path) / photo_url.removeprefix("/static/")


async def _upload_photo(
    client: AsyncClient, headers: dict, qr_id: str, data: bytes, content_type: str = "image/png"
):
    return await client.post(
        f"/v1/qrcodes/{qr_id}/photo",
        files={"file": ("photo.png", data, content_type)},
        headers=headers,
    )


# ---------------------------------------------------------------------------
# Contact page
# ---------------------------------------------------------------------------

async def test_contact_page_shows_details_and_records_one_scan(
    client: AsyncClient, auth_headers: dict, scans: list
) -> None:
    qr = await _create_contact(client, auth_headers)
    response = await client.get(f"/r/{qr['short_code']}")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    body = response.text
    assert "José Núñez" in body
    assert "Engineer · Acme, Inc." in body
    assert f'href="/r/{qr["short_code"]}.vcf"' in body
    assert 'href="tel:+15550100100;ext=42"' in body
    assert 'href="mailto:jose@example.com"' in body
    assert len(scans) == 1


async def test_contact_page_blocks_indexing_and_caching(
    client: AsyncClient, auth_headers: dict, scans: list
) -> None:
    qr = await _create_contact(client, auth_headers)
    headers = (await client.get(f"/r/{qr['short_code']}")).headers
    assert headers["x-robots-tag"] == "noindex, nofollow"
    assert headers["cache-control"] == "no-store"
    assert "default-src 'none'" in headers["content-security-policy"]


async def test_contact_page_escapes_fields(
    client: AsyncClient, auth_headers: dict, scans: list
) -> None:
    qr = await _create_contact(
        client,
        auth_headers,
        first_name="<script>alert(1)</script>",
        note='"><img src=x onerror=alert(1)>',
        social_links=[{"label": "<b>Site</b>", "url": "https://example.com/?a=1&b=2"}],
    )
    body = (await client.get(f"/r/{qr['short_code']}")).text
    assert "<script>alert" not in body
    assert "<img src=x" not in body
    assert "<b>Site</b>" not in body
    assert "&lt;script&gt;alert(1)" in body
    assert 'href="https://example.com/?a=1&amp;b=2"' in body


@pytest.mark.parametrize("url", ["javascript:alert(1)", "data:text/html,x", "ftp://example.com"])
async def test_contact_links_must_be_http(client: AsyncClient, auth_headers: dict, url: str) -> None:
    response = await client.post(
        "/v1/qrcodes",
        json={
            "title": "Bad",
            "type": "DYNAMIC",
            "content_type": "VCARD",
            "content_data": {**CONTACT, "social_links": [{"label": "x", "url": url}]},
        },
        headers=auth_headers,
    )
    assert response.status_code == 422


async def test_contact_page_uses_a_readable_theme_color(
    client: AsyncClient, auth_headers: dict, scans: list
) -> None:
    light = await _create_contact(client, auth_headers, theme_color="#ffee00")
    dark = await _create_contact(client, auth_headers, theme_color="#112233")
    light_body = (await client.get(f"/r/{light['short_code']}")).text
    dark_body = (await client.get(f"/r/{dark['short_code']}")).text
    assert "--accent: #ffee00" in light_body and "--on-accent: #000000" in light_body
    assert "--accent: #112233" in dark_body and "--on-accent: #ffffff" in dark_body


async def test_edits_show_immediately(client: AsyncClient, auth_headers: dict, scans: list) -> None:
    qr = await _create_contact(client, auth_headers)
    await client.get(f"/r/{qr['short_code']}")  # Fills the redirect cache

    response = await client.patch(
        f"/v1/qrcodes/{qr['id']}",
        json={"content_data": {**CONTACT, "first_name": "Ana"}},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert "Ana Núñez" in (await client.get(f"/r/{qr['short_code']}")).text


# ---------------------------------------------------------------------------
# .vcf download
# ---------------------------------------------------------------------------

async def test_vcf_download_records_no_scan(
    client: AsyncClient, auth_headers: dict, scans: list
) -> None:
    qr = await _create_contact(
        client,
        auth_headers,
        social_links=[{"label": "Linked In", "url": "https://linkedin.com/in/jose"}],
    )
    response = await client.get(f"/r/{qr['short_code']}.vcf")

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/vcard; charset=utf-8"
    assert response.headers["x-robots-tag"] == "noindex, nofollow"
    disposition = response.headers["content-disposition"]
    assert 'filename="Jose Nunez.vcf"' in disposition
    assert "filename*=UTF-8''Jos%C3%A9%20N%C3%BA%C3%B1ez.vcf" in disposition
    assert response.content.decode().startswith("BEGIN:VCARD\r\n")
    assert "FN:José Núñez\r\n" in response.content.decode()
    assert "URL;TYPE=LINKEDIN:https://linkedin.com/in/jose\r\n" in response.content.decode()
    assert scans == []


async def test_vcf_ignores_compact_encoding(
    client: AsyncClient, auth_headers: dict, scans: list
) -> None:
    qr = await _create_contact(client, auth_headers, encoding="mecard")
    response = await client.get(f"/r/{qr['short_code']}.vcf")
    assert response.content.decode().startswith("BEGIN:VCARD")


async def test_vcf_filename_cannot_inject(
    client: AsyncClient, auth_headers: dict, scans: list
) -> None:
    qr = await _create_contact(client, auth_headers, display_name='../../etc/"passwd"; x=1')
    disposition = (await client.get(f"/r/{qr['short_code']}.vcf")).headers["content-disposition"]
    assert "/" not in disposition.split("filename*")[0]
    assert '"passwd"' not in disposition
    assert ";" not in disposition.split('filename="')[1].split('"')[0]


# ---------------------------------------------------------------------------
# Inactive, deleted and unknown codes
# ---------------------------------------------------------------------------

async def test_deactivating_hides_the_contact_immediately(
    client: AsyncClient, auth_headers: dict, scans: list
) -> None:
    qr = await _create_contact(client, auth_headers)
    assert (await client.get(f"/r/{qr['short_code']}")).status_code == 200

    await client.patch(f"/v1/qrcodes/{qr['id']}", json={"is_active": False}, headers=auth_headers)

    page = await client.get(f"/r/{qr['short_code']}")
    assert page.status_code == 404
    assert "Núñez" not in page.text
    assert (await client.get(f"/r/{qr['short_code']}.vcf")).status_code == 404
    assert len(scans) == 1


async def test_deleting_erases_contact_data(
    client: AsyncClient, auth_headers: dict, scans: list
) -> None:
    qr = await _create_contact(client, auth_headers)
    photo = (await _upload_photo(client, auth_headers, qr["id"], _image())).json()
    stored = _stored_file(photo["content_data"]["photo_url"])
    assert stored.exists()

    response = await client.delete(f"/v1/qrcodes/{qr['id']}", headers=auth_headers)
    assert response.status_code == 204

    deleted = (await client.get(f"/v1/qrcodes/{qr['id']}", headers=auth_headers)).json()
    assert deleted["content_data"] is None
    assert "Núñez" not in str(deleted["design_config"])
    assert not stored.exists()
    assert (await client.get(f"/r/{qr['short_code']}")).status_code == 404
    assert (await client.get(f"/r/{qr['short_code']}.vcf")).status_code == 404


async def test_deleting_a_static_contact_erases_the_vcard(
    client: AsyncClient, auth_headers: dict
) -> None:
    created = await client.post(
        "/v1/qrcodes",
        json={"title": "Static", "type": "STATIC", "content_type": "VCARD", "content_data": CONTACT},
        headers=auth_headers,
    )
    qr = created.json()
    assert "Núñez" in qr["design_config"]["content"]

    await client.delete(f"/v1/qrcodes/{qr['id']}", headers=auth_headers)

    deleted = (await client.get(f"/v1/qrcodes/{qr['id']}", headers=auth_headers)).json()
    assert deleted["content_data"] is None
    assert deleted["design_config"]["content"] == ""


async def test_unknown_codes_return_404(client: AsyncClient) -> None:
    assert (await client.get("/r/doesnotexist")).status_code == 404
    assert (await client.get("/r/doesnotexist.vcf")).status_code == 404


# ---------------------------------------------------------------------------
# URL codes keep redirecting
# ---------------------------------------------------------------------------

async def test_url_code_still_redirects(
    client: AsyncClient, auth_headers: dict, scans: list
) -> None:
    created = await client.post(
        "/v1/qrcodes",
        json={"title": "URL", "type": "DYNAMIC", "target_url": "https://example.com/landing"},
        headers=auth_headers,
    )
    code = created.json()["short_code"]

    for _ in range(2):  # Second request comes from the cache
        response = await client.get(f"/r/{code}")
        assert response.status_code == 302
        assert response.headers["location"] == "https://example.com/landing"
    assert len(scans) == 2
    assert (await client.get(f"/r/{code}.vcf")).status_code == 404


# ---------------------------------------------------------------------------
# Tier limits
# ---------------------------------------------------------------------------

async def test_dynamic_contacts_count_toward_the_tier_limit(
    client: AsyncClient, auth_headers: dict
) -> None:
    await client.post(
        "/v1/qrcodes",
        json={"title": "URL", "type": "DYNAMIC", "target_url": "https://example.com"},
        headers=auth_headers,
    )
    for _ in range(2):
        await _create_contact(client, auth_headers)

    response = await client.post(
        "/v1/qrcodes",
        json={"title": "One too many", "type": "DYNAMIC", "content_type": "VCARD", "content_data": CONTACT},
        headers=auth_headers,
    )
    assert response.status_code == 403
    assert "limit" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Contact photos
# ---------------------------------------------------------------------------

async def test_photo_is_shrunk_and_exif_is_removed(
    client: AsyncClient, auth_headers: dict, scans: list
) -> None:
    qr = await _create_contact(client, auth_headers)
    exif = Image.Exif()
    exif[0x010F] = "SecretCameraMaker"
    upload = _image("JPEG", (2000, 1000), exif=exif)
    assert b"SecretCameraMaker" in upload

    response = await _upload_photo(client, auth_headers, qr["id"], upload, "image/jpeg")
    assert response.status_code == 200, response.text

    photo_url = response.json()["content_data"]["photo_url"]
    assert photo_url.endswith(".webp")
    stored = _stored_file(photo_url)
    assert b"SecretCameraMaker" not in stored.read_bytes()
    with Image.open(stored) as img:
        assert img.format == "WEBP"
        assert max(img.size) == 512
    assert f'src="{photo_url}"' in (await client.get(f"/r/{qr['short_code']}")).text


async def test_replacing_or_removing_a_photo_deletes_the_old_file(
    client: AsyncClient, auth_headers: dict
) -> None:
    qr = await _create_contact(client, auth_headers)
    first = (await _upload_photo(client, auth_headers, qr["id"], _image())).json()
    second = (await _upload_photo(client, auth_headers, qr["id"], _image())).json()
    first_file = _stored_file(first["content_data"]["photo_url"])
    second_file = _stored_file(second["content_data"]["photo_url"])
    assert not first_file.exists()
    assert second_file.exists()

    removed = await client.patch(
        f"/v1/qrcodes/{qr['id']}",
        json={"content_data": {**CONTACT, "photo_url": None}},
        headers=auth_headers,
    )
    assert removed.status_code == 200
    assert not second_file.exists()


async def test_saving_a_contact_keeps_its_photo(client: AsyncClient, auth_headers: dict) -> None:
    qr = await _create_contact(client, auth_headers)
    uploaded = (await _upload_photo(client, auth_headers, qr["id"], _image())).json()
    photo_url = uploaded["content_data"]["photo_url"]

    await client.patch(
        f"/v1/qrcodes/{qr['id']}",
        json={"content_data": {**CONTACT, "first_name": "Ana", "photo_url": photo_url}},
        headers=auth_headers,
    )
    assert _stored_file(photo_url).exists()


@pytest.mark.parametrize(
    ("data", "content_type"),
    [
        (b"<svg xmlns='http://www.w3.org/2000/svg'><script>alert(1)</script></svg>", "image/svg+xml"),
        (b"<html><script>alert(1)</script></html>", "image/png"),
        (b"not an image", "image/jpeg"),
    ],
)
async def test_photo_rejects_non_images(
    client: AsyncClient, auth_headers: dict, data: bytes, content_type: str
) -> None:
    qr = await _create_contact(client, auth_headers)
    response = await _upload_photo(client, auth_headers, qr["id"], data, content_type)
    assert response.status_code == 422


async def test_photo_rejects_oversized_files(client: AsyncClient, auth_headers: dict) -> None:
    qr = await _create_contact(client, auth_headers)
    response = await _upload_photo(client, auth_headers, qr["id"], b"x" * (5 * 1024 * 1024 + 1))
    assert response.status_code == 422
    assert "5 MB" in response.json()["detail"]


async def test_photo_requires_a_dynamic_contact(client: AsyncClient, auth_headers: dict) -> None:
    static = await client.post(
        "/v1/qrcodes",
        json={"title": "Static", "type": "STATIC", "content_type": "VCARD", "content_data": CONTACT},
        headers=auth_headers,
    )
    response = await _upload_photo(client, auth_headers, static.json()["id"], _image())
    assert response.status_code == 422


async def test_photo_requires_ownership(client: AsyncClient, auth_headers: dict) -> None:
    qr = await _create_contact(client, auth_headers)
    email = f"redirect-{uuid.uuid4().hex}@pointqr.dev"
    await client.post("/v1/auth/register", json={"email": email, "password": PASSWORD})
    login = await client.post("/v1/auth/login", data={"username": email, "password": PASSWORD})
    other = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert (await _upload_photo(client, other, qr["id"], _image())).status_code == 404
