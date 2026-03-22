"""Tests for GET/PUT /api/v1/settings/general endpoints."""

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import delete

from app.core.database import AsyncSessionFactory
from app.models.settings import AppSettings

SETTINGS_BASE = "/api/v1/settings/general/"


@pytest_asyncio.fixture(autouse=True)
async def _clean_settings() -> None:
    """Remove all app_settings rows before each test."""
    async with AsyncSessionFactory() as session:
        await session.execute(delete(AppSettings))
        await session.commit()


# ---------- 1. GET returns defaults when no rows ----------


async def test_get_defaults_when_empty(auth_client: AsyncClient) -> None:
    """GET /settings/general with no rows returns defaults."""
    resp = await auth_client.get(SETTINGS_BASE)
    assert resp.status_code == 200
    data = resp.json()
    assert data["system_prompt"] is None
    assert data["temperature"] == 0.7
    assert data["max_tokens"] == 2048


# ---------- 2. PUT updates and GET returns new values ----------


async def test_put_then_get(auth_client: AsyncClient) -> None:
    """PUT /settings/general updates values; GET returns them."""
    resp = await auth_client.put(
        SETTINGS_BASE,
        json={"system_prompt": "Be helpful", "temperature": 1.0, "max_tokens": 4096},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["system_prompt"] == "Be helpful"
    assert data["temperature"] == 1.0
    assert data["max_tokens"] == 4096

    # Verify via GET
    resp = await auth_client.get(SETTINGS_BASE)
    assert resp.status_code == 200
    data = resp.json()
    assert data["system_prompt"] == "Be helpful"
    assert data["temperature"] == 1.0
    assert data["max_tokens"] == 4096


# ---------- 3. Temperature validation ----------


async def test_temperature_out_of_range(auth_client: AsyncClient) -> None:
    """PUT with temperature=2.1 returns 422."""
    resp = await auth_client.put(
        SETTINGS_BASE,
        json={"temperature": 2.1},
    )
    assert resp.status_code == 422


# ---------- 4. max_tokens validation ----------


async def test_max_tokens_zero(auth_client: AsyncClient) -> None:
    """PUT with max_tokens=0 returns 422."""
    resp = await auth_client.put(
        SETTINGS_BASE,
        json={"max_tokens": 0},
    )
    assert resp.status_code == 422


# ---------- 5. Auth required ----------


async def test_settings_general_requires_auth(client: AsyncClient) -> None:
    """Endpoints require authentication."""
    resp = await client.get(SETTINGS_BASE)
    assert resp.status_code in (401, 403)

    resp = await client.put(SETTINGS_BASE, json={"temperature": 0.5})
    assert resp.status_code in (401, 403)
