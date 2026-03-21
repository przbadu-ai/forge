"""Integration tests for the LLM provider settings API."""

from typing import Any

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import delete, select

from app.core.database import AsyncSessionFactory
from app.core.encryption import decrypt_value
from app.models.llm_provider import LLMProvider

PROVIDERS_BASE = "/api/v1/settings/providers"
PROVIDERS_URL = f"{PROVIDERS_BASE}/"  # trailing slash for collection endpoints


# ---------- fixtures ----------


@pytest_asyncio.fixture(autouse=True)
async def _clean_providers() -> None:
    """Remove all providers before each test so tests are independent."""
    async with AsyncSessionFactory() as session:
        await session.execute(delete(LLMProvider))
        await session.commit()


# ---------- helpers ----------


async def _create_provider(
    auth_client: AsyncClient,
    *,
    name: str = "Ollama",
    base_url: str = "http://localhost:11434/v1",
    api_key: str = "sk-test-key-123",
    models: list[str] | None = None,
    is_default: bool = False,
) -> dict[str, Any]:
    resp = await auth_client.post(
        PROVIDERS_URL,
        json={
            "name": name,
            "base_url": base_url,
            "api_key": api_key,
            "models": models or [],
            "is_default": is_default,
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()  # type: ignore[no-any-return]


# ---------- 1. Auth ----------


async def test_providers_requires_auth(client: AsyncClient) -> None:
    """GET /settings/providers without token returns 401."""
    resp = await client.get(PROVIDERS_URL)
    assert resp.status_code in (401, 403)


# ---------- 2. Create ----------


async def test_create_provider(auth_client: AsyncClient) -> None:
    """POST with valid data returns 201 and the created provider."""
    data = await _create_provider(auth_client, name="TestProvider")
    assert data["name"] == "TestProvider"
    assert data["base_url"] == "http://localhost:11434/v1"
    assert "id" in data
    assert "created_at" in data


# ---------- 3. List ----------


async def test_list_providers(auth_client: AsyncClient) -> None:
    """GET returns a list including the providers we created."""
    await _create_provider(auth_client, name="ProvA")
    await _create_provider(auth_client, name="ProvB")
    resp = await auth_client.get(PROVIDERS_URL)
    assert resp.status_code == 200
    names = [p["name"] for p in resp.json()]
    assert "ProvA" in names
    assert "ProvB" in names


# ---------- 4. Update ----------


async def test_update_provider(auth_client: AsyncClient) -> None:
    """PUT updates the provider name and url."""
    created = await _create_provider(auth_client, name="OldName")
    pid = created["id"]

    resp = await auth_client.put(
        f"{PROVIDERS_BASE}/{pid}",
        json={"name": "NewName", "base_url": "http://new-url/v1"},
    )
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["name"] == "NewName"
    assert updated["base_url"] == "http://new-url/v1"


# ---------- 5. Delete ----------


async def test_delete_provider(auth_client: AsyncClient) -> None:
    """DELETE removes the provider; subsequent GET no longer lists it."""
    created = await _create_provider(auth_client, name="ToDelete")
    pid = created["id"]

    resp = await auth_client.delete(f"{PROVIDERS_BASE}/{pid}")
    assert resp.status_code == 204

    # Verify it's gone
    list_resp = await auth_client.get(PROVIDERS_URL)
    ids = [p["id"] for p in list_resp.json()]
    assert pid not in ids


# ---------- 6. API key encrypted in DB ----------


async def test_api_key_encrypted_in_db(auth_client: AsyncClient) -> None:
    """The api_key_encrypted column is NOT plaintext; it decrypts to original."""
    plaintext_key = "sk-super-secret-key-abc123"
    created = await _create_provider(auth_client, name="EncTest", api_key=plaintext_key)

    # Access the DB directly through the shared session factory
    async with AsyncSessionFactory() as session:
        result = await session.execute(select(LLMProvider).where(LLMProvider.id == created["id"]))
        provider = result.scalar_one()
        # The stored value must not be the plaintext
        assert provider.api_key_encrypted != plaintext_key
        assert provider.api_key_encrypted != ""
        # It must decrypt back to the original
        assert decrypt_value(provider.api_key_encrypted) == plaintext_key


# ---------- 7. API key not in response ----------


async def test_api_key_not_in_response(auth_client: AsyncClient) -> None:
    """Neither POST nor GET responses contain the api_key field."""
    created = await _create_provider(auth_client, name="NoKeyResp", api_key="sk-hidden")
    assert "api_key" not in created
    assert "api_key_encrypted" not in created

    resp = await auth_client.get(PROVIDERS_URL)
    for provider in resp.json():
        assert "api_key" not in provider
        assert "api_key_encrypted" not in provider


# ---------- 8. is_default exclusivity ----------


async def test_is_default_exclusivity(auth_client: AsyncClient) -> None:
    """Setting a new provider as default unsets the previous default."""
    first = await _create_provider(auth_client, name="Default1", is_default=True)
    assert first["is_default"] is True

    second = await _create_provider(auth_client, name="Default2", is_default=True)
    assert second["is_default"] is True

    # Re-fetch all providers
    resp = await auth_client.get(PROVIDERS_URL)
    providers = resp.json()
    defaults = [p for p in providers if p["is_default"]]
    assert len(defaults) == 1
    assert defaults[0]["name"] == "Default2"


# ---------- 9. test-connection failure ----------


async def test_test_connection_failure(auth_client: AsyncClient) -> None:
    """POST /test-connection with unreachable URL returns {ok: false}."""
    resp = await auth_client.post(
        f"{PROVIDERS_BASE}/test-connection",
        json={"base_url": "http://localhost:9999/v1", "api_key": ""},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is False
    assert "error" in data
    assert isinstance(data["error"], str)
    assert len(data["error"]) > 0


# ---------- 10. Validation ----------


async def test_create_provider_validation(auth_client: AsyncClient) -> None:
    """POST with missing required fields returns 422."""
    # Missing name and base_url (both required)
    resp = await auth_client.post(PROVIDERS_URL, json={})
    assert resp.status_code == 422
