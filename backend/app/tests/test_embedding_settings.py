"""Tests for embedding settings endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_embedding_settings_defaults(auth_client: AsyncClient) -> None:
    """Get embedding settings returns defaults when nothing configured."""
    resp = await auth_client.get("/api/v1/settings/embeddings/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["embedding_base_url"] is None
    assert data["embedding_model"] is None
    assert data["reranker_base_url"] is None
    assert data["reranker_model"] is None


@pytest.mark.asyncio
async def test_update_embedding_settings(auth_client: AsyncClient) -> None:
    """Update and retrieve embedding settings."""
    update_data = {
        "embedding_base_url": "http://localhost:11434",
        "embedding_model": "nomic-embed-text",
    }
    resp = await auth_client.put("/api/v1/settings/embeddings/", json=update_data)
    assert resp.status_code == 200
    data = resp.json()
    assert data["embedding_base_url"] == "http://localhost:11434"
    assert data["embedding_model"] == "nomic-embed-text"

    # Verify with a GET
    get_resp = await auth_client.get("/api/v1/settings/embeddings/")
    assert get_resp.status_code == 200
    get_data = get_resp.json()
    assert get_data["embedding_base_url"] == "http://localhost:11434"


@pytest.mark.asyncio
async def test_clear_embedding_settings(auth_client: AsyncClient) -> None:
    """Setting fields to empty string clears them."""
    # First set values
    await auth_client.put(
        "/api/v1/settings/embeddings/",
        json={"embedding_base_url": "http://test", "embedding_model": "test-model"},
    )
    # Clear them
    resp = await auth_client.put(
        "/api/v1/settings/embeddings/",
        json={"embedding_base_url": "", "embedding_model": ""},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["embedding_base_url"] is None
    assert data["embedding_model"] is None


@pytest.mark.asyncio
async def test_embedding_settings_requires_auth(client: AsyncClient) -> None:
    """Embedding settings endpoints require authentication."""
    resp = await client.get("/api/v1/settings/embeddings/")
    assert resp.status_code == 401
