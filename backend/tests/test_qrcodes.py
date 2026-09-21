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
