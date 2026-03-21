"""Tests for health diagnostics API."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_diagnostics_requires_auth(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/diagnostics/")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_diagnostics_returns_services(auth_client: AsyncClient) -> None:
    resp = await auth_client.get("/api/v1/diagnostics/")
    assert resp.status_code == 200
    data = resp.json()
    assert "services" in data
    assert isinstance(data["services"], list)
    # At minimum: Embedding, Reranker, ChromaDB, SearXNG, Exa
    assert len(data["services"]) >= 4


@pytest.mark.asyncio
async def test_diagnostics_unconfigured_defaults(auth_client: AsyncClient) -> None:
    """Without any providers or settings configured, services should be unconfigured or error."""
    resp = await auth_client.get("/api/v1/diagnostics/")
    data = resp.json()
    statuses = {s["name"]: s["status"] for s in data["services"]}
    # These should be unconfigured since no settings have been set
    assert statuses.get("Embedding Model") == "unconfigured"
    assert statuses.get("Reranker") == "unconfigured"
    assert statuses.get("SearXNG") == "unconfigured"
    assert statuses.get("Exa Search") == "unconfigured"


@pytest.mark.asyncio
async def test_diagnostics_service_status_shape(auth_client: AsyncClient) -> None:
    """Verify each service has the expected fields."""
    resp = await auth_client.get("/api/v1/diagnostics/")
    data = resp.json()
    for svc in data["services"]:
        assert "name" in svc
        assert "status" in svc
        assert svc["status"] in ("ok", "error", "unconfigured")
        assert "latency_ms" in svc
        assert "error" in svc
