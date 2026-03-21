"""Tests for web search settings API."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_web_search_defaults(auth_client: AsyncClient) -> None:
    resp = await auth_client.get("/api/v1/settings/web-search/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["searxng_base_url"] is None
    assert data["exa_api_key_set"] is False


@pytest.mark.asyncio
async def test_update_searxng_url(auth_client: AsyncClient) -> None:
    resp = await auth_client.put(
        "/api/v1/settings/web-search/",
        json={"searxng_base_url": "http://localhost:8888"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["searxng_base_url"] == "http://localhost:8888"

    # Verify persistence
    resp2 = await auth_client.get("/api/v1/settings/web-search/")
    assert resp2.json()["searxng_base_url"] == "http://localhost:8888"


@pytest.mark.asyncio
async def test_update_exa_api_key(auth_client: AsyncClient) -> None:
    resp = await auth_client.put(
        "/api/v1/settings/web-search/",
        json={"exa_api_key": "exa-test-key-123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["exa_api_key_set"] is True
    # Key should not be returned in plaintext
    assert "exa_api_key" not in data or data.get("exa_api_key") is None


@pytest.mark.asyncio
async def test_clear_searxng_url(auth_client: AsyncClient) -> None:
    # Set
    await auth_client.put(
        "/api/v1/settings/web-search/",
        json={"searxng_base_url": "http://localhost:8888"},
    )
    # Clear
    resp = await auth_client.put(
        "/api/v1/settings/web-search/",
        json={"searxng_base_url": ""},
    )
    assert resp.status_code == 200
    assert resp.json()["searxng_base_url"] is None


@pytest.mark.asyncio
async def test_clear_exa_api_key(auth_client: AsyncClient) -> None:
    # Set
    await auth_client.put(
        "/api/v1/settings/web-search/",
        json={"exa_api_key": "exa-key"},
    )
    # Clear
    resp = await auth_client.put(
        "/api/v1/settings/web-search/",
        json={"exa_api_key": ""},
    )
    assert resp.status_code == 200
    assert resp.json()["exa_api_key_set"] is False


@pytest.mark.asyncio
async def test_web_search_requires_auth(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/settings/web-search/")
    assert resp.status_code == 401
