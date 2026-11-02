"""Tests for QR code CRUD and export endpoints."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TEST_EMAIL = "qrtest@pointqr.dev"
TEST_PASSWORD = "securepassword123"


async def _register_and_login(client: AsyncClient) -> str:
    """Register a user and return a valid Bearer access token."""
    await client.post("/v1/auth/register", json={"email": TEST_EMAIL, "password": TEST_PASSWORD})
    resp = await client.post(
        "/v1/auth/login",
        data={"username": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    return resp.json()["access_token"]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
async def client() -> AsyncClient:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict:
    token = await _register_and_login(client)
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# QR Code CRUD tests
# ---------------------------------------------------------------------------

async def test_create_qrcode(client: AsyncClient, auth_headers: dict) -> None:
    response = await client.post(
        "/v1/qrcodes",
        json={"title": "Test QR", "type": "STATIC"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test QR"
    assert data["type"] == "STATIC"
    assert data["short_code"] is None
    assert data["scan_count"] == 0


async def test_create_dynamic_qrcode_gets_short_code(
    client: AsyncClient, auth_headers: dict
) -> None:
    response = await client.post(
        "/v1/qrcodes",
        json={
            "title": "Dynamic QR",
            "type": "DYNAMIC",
            "target_url": "https://example.com",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["type"] == "DYNAMIC"
    assert data["short_code"] is not None
    assert len(data["short_code"]) == 8


async def test_list_qrcodes(client: AsyncClient, auth_headers: dict) -> None:
    # Create two QR codes
    for i in range(2):
        await client.post(
            "/v1/qrcodes",
            json={"title": f"QR {i}", "type": "STATIC"},
            headers=auth_headers,
        )

    response = await client.get("/v1/qrcodes", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 2
    assert "items" in data
    assert "pages" in data


async def test_get_qrcode(client: AsyncClient, auth_headers: dict) -> None:
    create_resp = await client.post(
        "/v1/qrcodes",
        json={"title": "Get Me", "type": "STATIC"},
        headers=auth_headers,
    )
    qr_id = create_resp.json()["id"]

    response = await client.get(f"/v1/qrcodes/{qr_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == qr_id


async def test_update_qrcode(client: AsyncClient, auth_headers: dict) -> None:
    create_resp = await client.post(
        "/v1/qrcodes",
        json={"title": "Original Title", "type": "STATIC"},
        headers=auth_headers,
    )
    qr_id = create_resp.json()["id"]

    response = await client.patch(
        f"/v1/qrcodes/{qr_id}",
        json={"title": "Updated Title"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Title"


async def test_delete_qrcode(client: AsyncClient, auth_headers: dict) -> None:
    create_resp = await client.post(
        "/v1/qrcodes",
        json={"title": "Delete Me", "type": "STATIC"},
        headers=auth_headers,
    )
    qr_id = create_resp.json()["id"]

    delete_resp = await client.delete(f"/v1/qrcodes/{qr_id}", headers=auth_headers)
    assert delete_resp.status_code == 204

    # Should no longer appear in list
    list_resp = await client.get("/v1/qrcodes", headers=auth_headers)
    ids = [item["id"] for item in list_resp.json()["items"]]
    assert qr_id not in ids


async def test_get_nonexistent_qrcode_returns_404(
    client: AsyncClient, auth_headers: dict
) -> None:
    import uuid
    response = await client.get(f"/v1/qrcodes/{uuid.uuid4()}", headers=auth_headers)
    assert response.status_code == 404


async def test_export_png(client: AsyncClient, auth_headers: dict) -> None:
    create_resp = await client.post(
        "/v1/qrcodes",
        json={
            "title": "Export Test",
            "type": "STATIC",
            "design_config": {"content": "https://pointqr.app"},
        },
        headers=auth_headers,
    )
    qr_id = create_resp.json()["id"]

    response = await client.post(
        f"/v1/qrcodes/{qr_id}/export?format=png",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert len(response.content) > 0


async def test_export_svg(client: AsyncClient, auth_headers: dict) -> None:
    create_resp = await client.post(
        "/v1/qrcodes",
        json={"title": "SVG Export", "type": "STATIC", "design_config": {"content": "hello"}},
        headers=auth_headers,
    )
    qr_id = create_resp.json()["id"]

    response = await client.post(
        f"/v1/qrcodes/{qr_id}/export?format=svg",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert "svg" in response.headers["content-type"]
    assert b"<svg" in response.content


async def test_qrcodes_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/v1/qrcodes")
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Contact (vCard) QR codes
# ---------------------------------------------------------------------------

CONTACT = {
    "first_name": "José",
    "last_name": "Ñúñez",
    "organization": "Acme, Inc.",
    "phones": [{"type": "mobile", "number": "+1 555 0100"}],
    "emails": [{"type": "work", "address": "jose@example.com"}],
}


async def _create_contact(client: AsyncClient, headers: dict, **overrides) -> dict:
    body = {
        "title": "Contact QR",
        "type": "STATIC",
        "content_type": "VCARD",
        "content_data": CONTACT,
        **overrides,
    }
    response = await client.post("/v1/qrcodes", json=body, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


async def test_url_qrcode_defaults_content_type(client: AsyncClient, auth_headers: dict) -> None:
    response = await client.post(
        "/v1/qrcodes", json={"title": "Plain", "type": "STATIC"}, headers=auth_headers
    )
    data = response.json()
    assert data["content_type"] == "URL"
    assert data["content_data"] is None


async def test_create_static_contact_encodes_vcard(client: AsyncClient, auth_headers: dict) -> None:
    data = await _create_contact(
        client,
        auth_headers,
        target_url="https://ignored.example.com",
        design_config={"content": "client-supplied content is replaced"},
    )
    assert data["content_type"] == "VCARD"
    assert data["content_data"]["first_name"] == "José"
    assert data["content_data"]["phones"] == [{"type": "mobile", "number": "+1 555 0100"}]
    assert data["target_url"] is None
    content = data["design_config"]["content"]
    assert content.startswith("BEGIN:VCARD\r\nVERSION:3.0\r\n")
    assert "FN:José Ñúñez\r\n" in content
    assert "ORG:Acme\\, Inc.\r\n" in content


async def test_get_and_list_return_contact_fields(client: AsyncClient, auth_headers: dict) -> None:
    created = await _create_contact(client, auth_headers)

    response = await client.get(f"/v1/qrcodes/{created['id']}", headers=auth_headers)
    assert response.json()["content_data"]["organization"] == "Acme, Inc."

    items = (await client.get("/v1/qrcodes", headers=auth_headers)).json()["items"]
    listed = next(item for item in items if item["id"] == created["id"])
    assert listed["content_type"] == "VCARD"


async def test_create_dynamic_contact_encodes_redirect_url(
    client: AsyncClient, auth_headers: dict
) -> None:
    data = await _create_contact(
        client,
        auth_headers,
        type="DYNAMIC",
        content_data={
            **CONTACT,
            "social_links": [{"label": "LinkedIn", "url": "https://linkedin.com/in/jose"}],
            "theme_color": "#336699",
        },
    )
    assert data["short_code"] is not None
    assert data["target_url"] is None
    assert data["design_config"]["content"].endswith(f"/r/{data['short_code']}")
    assert data["content_data"]["social_links"][0]["label"] == "LinkedIn"


async def test_static_contact_rejects_dynamic_only_fields(
    client: AsyncClient, auth_headers: dict
) -> None:
    response = await client.post(
        "/v1/qrcodes",
        json={
            "title": "Bad",
            "type": "STATIC",
            "content_type": "VCARD",
            "content_data": {**CONTACT, "theme_color": "#336699"},
        },
        headers=auth_headers,
    )
    assert response.status_code == 422
    assert "theme_color" in response.json()["detail"]


@pytest.mark.parametrize(
    "body",
    [
        # VCARD without content_data
        {"content_type": "VCARD"},
        # content_data on a URL code
        {"content_type": "URL", "content_data": CONTACT},
        # no name or organization
        {"content_type": "VCARD", "content_data": {"job_title": "CEO"}},
        # javascript: link
        {"content_type": "VCARD", "content_data": {**CONTACT, "website": "javascript:alert(1)"}},
    ],
)
async def test_create_contact_validation_errors(
    client: AsyncClient, auth_headers: dict, body: dict
) -> None:
    response = await client.post(
        "/v1/qrcodes", json={"title": "Bad", "type": "STATIC", **body}, headers=auth_headers
    )
    assert response.status_code == 422


async def test_update_contact_regenerates_vcard(client: AsyncClient, auth_headers: dict) -> None:
    created = await _create_contact(client, auth_headers)

    response = await client.patch(
        f"/v1/qrcodes/{created['id']}",
        json={"content_data": {**CONTACT, "job_title": "Head of QR"}},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["content_data"]["job_title"] == "Head of QR"
    assert "TITLE:Head of QR\r\n" in data["design_config"]["content"]


async def test_update_design_cannot_overwrite_contact_content(
    client: AsyncClient, auth_headers: dict
) -> None:
    created = await _create_contact(client, auth_headers)

    response = await client.patch(
        f"/v1/qrcodes/{created['id']}",
        json={"design_config": {"content": "https://evil.example.com", "margin": 20}},
        headers=auth_headers,
    )
    data = response.json()
    assert data["design_config"]["margin"] == 20
    assert data["design_config"]["content"] == created["design_config"]["content"]


async def test_update_contact_to_mecard(client: AsyncClient, auth_headers: dict) -> None:
    created = await _create_contact(client, auth_headers)

    response = await client.patch(
        f"/v1/qrcodes/{created['id']}",
        json={"content_data": {**CONTACT, "encoding": "mecard"}},
        headers=auth_headers,
    )
    assert response.json()["design_config"]["content"].startswith("MECARD:N:Ñúñez,José;")


async def test_update_dynamic_contact_keeps_redirect_url(
    client: AsyncClient, auth_headers: dict
) -> None:
    created = await _create_contact(client, auth_headers, type="DYNAMIC")

    response = await client.patch(
        f"/v1/qrcodes/{created['id']}",
        json={"content_data": {**CONTACT, "first_name": "Pepe"}},
        headers=auth_headers,
    )
    data = response.json()
    assert data["content_data"]["first_name"] == "Pepe"
    assert data["design_config"]["content"] == created["design_config"]["content"]


async def test_update_static_contact_rejects_dynamic_only_fields(
    client: AsyncClient, auth_headers: dict
) -> None:
    created = await _create_contact(client, auth_headers)

    response = await client.patch(
        f"/v1/qrcodes/{created['id']}",
        json={"content_data": {**CONTACT, "photo_url": "https://example.com/me.png"}},
        headers=auth_headers,
    )
    assert response.status_code == 422


async def test_switch_contact_to_url(client: AsyncClient, auth_headers: dict) -> None:
    created = await _create_contact(client, auth_headers)

    response = await client.patch(
        f"/v1/qrcodes/{created['id']}",
        json={"content_type": "URL", "design_config": {"content": "https://pointqr.app"}},
        headers=auth_headers,
    )
    data = response.json()
    assert data["content_type"] == "URL"
    assert data["content_data"] is None
    assert data["design_config"]["content"] == "https://pointqr.app"


async def test_switch_url_to_contact_requires_content_data(
    client: AsyncClient, auth_headers: dict
) -> None:
    create_resp = await client.post(
        "/v1/qrcodes", json={"title": "URL QR", "type": "STATIC"}, headers=auth_headers
    )
    qr_id = create_resp.json()["id"]

    missing = await client.patch(
        f"/v1/qrcodes/{qr_id}", json={"content_type": "VCARD"}, headers=auth_headers
    )
    assert missing.status_code == 422

    response = await client.patch(
        f"/v1/qrcodes/{qr_id}",
        json={"content_type": "VCARD", "content_data": CONTACT},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["design_config"]["content"].startswith("BEGIN:VCARD")


async def test_export_contact_png(client: AsyncClient, auth_headers: dict) -> None:
    created = await _create_contact(client, auth_headers)

    response = await client.post(
        f"/v1/qrcodes/{created['id']}/export?format=png", headers=auth_headers
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"

