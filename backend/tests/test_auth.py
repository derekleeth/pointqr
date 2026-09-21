"""Integration tests for authentication endpoints.

These tests use an in-memory SQLite database via httpx's AsyncClient.
For a full async PostgreSQL test setup, configure a test DATABASE_URL
pointing to a test database in conftest.py.
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client() -> AsyncClient:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


async def test_health_check(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


async def test_register_and_login(client: AsyncClient) -> None:
    # Register
    reg_response = await client.post(
        "/v1/auth/register",
        json={"email": "test@pointqr.dev", "password": "securepassword123"},
    )
    assert reg_response.status_code == 201
    data = reg_response.json()
    assert data["email"] == "test@pointqr.dev"
    assert "hashed_password" not in data

    # Login
    login_response = await client.post(
        "/v1/auth/login",
        data={"username": "test@pointqr.dev", "password": "securepassword123"},
    )
    assert login_response.status_code == 200
    tokens = login_response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens


async def test_duplicate_registration(client: AsyncClient) -> None:
    await client.post(
        "/v1/auth/register",
        json={"email": "duplicate@pointqr.dev", "password": "securepassword123"},
    )
    response = await client.post(
        "/v1/auth/register",
        json={"email": "duplicate@pointqr.dev", "password": "securepassword123"},
    )
    assert response.status_code == 409


async def test_me_requires_auth(client: AsyncClient) -> None:
    response = await client.get("/v1/auth/me")
    assert response.status_code == 401
