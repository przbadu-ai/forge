"""Integration tests for the MCP server settings API."""

from typing import Any

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import delete

from app.core.database import AsyncSessionFactory
from app.models.mcp_server import McpServer

MCP_BASE = "/api/v1/settings/mcp-servers"
MCP_URL = f"{MCP_BASE}/"  # trailing slash for collection endpoints


# ---------- fixtures ----------


@pytest_asyncio.fixture(autouse=True)
async def _clean_mcp_servers() -> None:
    """Remove all MCP servers before each test so tests are independent."""
    async with AsyncSessionFactory() as session:
        await session.execute(delete(McpServer))
        await session.commit()


# ---------- helpers ----------


async def _create_server(
    auth_client: AsyncClient,
    *,
    name: str = "test-server",
    transport_type: str = "stdio",
    command: str | None = "echo",
    url: str | None = None,
    args: list[str] | None = None,
    env_vars: dict[str, str] | None = None,
    is_enabled: bool = True,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "name": name,
        "transport_type": transport_type,
        "args": args or [],
        "env_vars": env_vars or {},
        "is_enabled": is_enabled,
    }
    if command is not None:
        payload["command"] = command
    if url is not None:
        payload["url"] = url
    resp = await auth_client.post(MCP_URL, json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()  # type: ignore[no-any-return]


# ---------- 1. Auth ----------


async def test_mcp_servers_requires_auth(client: AsyncClient) -> None:
    """GET /settings/mcp-servers without token returns 401."""
    resp = await client.get(MCP_URL)
    assert resp.status_code in (401, 403)


# ---------- 2. Create (stdio) ----------


async def test_create_mcp_server_stdio(auth_client: AsyncClient) -> None:
    """POST with valid stdio data returns 201 and the created server."""
    data = await _create_server(auth_client, name="my-server", transport_type="stdio", command="uvx")
    assert data["name"] == "my-server"
    assert data["transport_type"] == "stdio"
    assert data["command"] == "uvx"
    assert data["url"] is None
    assert data["args"] == []
    assert data["env_vars"] == {}
    assert data["is_enabled"] is True
    assert "id" in data
    assert "created_at" in data


# ---------- 2b. Create (SSE) ----------


async def test_create_mcp_server_sse(auth_client: AsyncClient) -> None:
    """POST with SSE transport and URL returns 201."""
    data = await _create_server(
        auth_client,
        name="sse-server",
        transport_type="sse",
        command=None,
        url="http://localhost:8080/sse",
    )
    assert data["name"] == "sse-server"
    assert data["transport_type"] == "sse"
    assert data["url"] == "http://localhost:8080/sse"
    assert data["command"] is None


# ---------- 2c. Create SSE without URL returns 422 ----------


async def test_create_sse_server_without_url_returns_422(auth_client: AsyncClient) -> None:
    """POST with SSE transport but no URL returns 422."""
    resp = await auth_client.post(
        MCP_URL,
        json={
            "name": "bad-sse",
            "transport_type": "sse",
        },
    )
    assert resp.status_code == 422


# ---------- 2d. Create stdio without command returns 422 ----------


async def test_create_stdio_server_without_command_returns_422(auth_client: AsyncClient) -> None:
    """POST with stdio transport but no command returns 422."""
    resp = await auth_client.post(
        MCP_URL,
        json={
            "name": "bad-stdio",
            "transport_type": "stdio",
        },
    )
    assert resp.status_code == 422


# ---------- 2e. Read includes transport fields ----------


async def test_read_server_includes_transport_fields(auth_client: AsyncClient) -> None:
    """GET returns transport_type and url fields."""
    created = await _create_server(auth_client, name="read-test", command="echo")
    resp = await auth_client.get(MCP_URL)
    assert resp.status_code == 200
    servers = resp.json()
    server = next(s for s in servers if s["id"] == created["id"])
    assert "transport_type" in server
    assert server["transport_type"] == "stdio"
    assert "url" in server


# ---------- 3. List ----------


async def test_list_mcp_servers(auth_client: AsyncClient) -> None:
    """GET returns a list including the servers we created."""
    await _create_server(auth_client, name="server-a")
    await _create_server(auth_client, name="server-b")
    resp = await auth_client.get(MCP_URL)
    assert resp.status_code == 200
    names = [s["name"] for s in resp.json()]
    assert "server-a" in names
    assert "server-b" in names


# ---------- 4. Update ----------


async def test_update_mcp_server(auth_client: AsyncClient) -> None:
    """PUT updates the server fields."""
    created = await _create_server(auth_client, name="old-name")
    sid = created["id"]

    resp = await auth_client.put(
        f"{MCP_BASE}/{sid}",
        json={"name": "new-name", "command": "new-cmd", "args": ["--verbose"]},
    )
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["name"] == "new-name"
    assert updated["command"] == "new-cmd"
    assert updated["args"] == ["--verbose"]


# ---------- 5. Toggle ----------


async def test_toggle_mcp_server(auth_client: AsyncClient) -> None:
    """PATCH /{id}/toggle flips is_enabled."""
    created = await _create_server(auth_client, name="toggle-test", is_enabled=True)
    sid = created["id"]
    assert created["is_enabled"] is True

    resp = await auth_client.patch(f"{MCP_BASE}/{sid}/toggle")
    assert resp.status_code == 200
    assert resp.json()["is_enabled"] is False

    resp2 = await auth_client.patch(f"{MCP_BASE}/{sid}/toggle")
    assert resp2.status_code == 200
    assert resp2.json()["is_enabled"] is True


# ---------- 6. Delete ----------


async def test_delete_mcp_server(auth_client: AsyncClient) -> None:
    """DELETE removes the server; subsequent GET no longer lists it."""
    created = await _create_server(auth_client, name="to-delete")
    sid = created["id"]

    resp = await auth_client.delete(f"{MCP_BASE}/{sid}")
    assert resp.status_code == 204

    # Verify it's gone
    list_resp = await auth_client.get(MCP_URL)
    ids = [s["id"] for s in list_resp.json()]
    assert sid not in ids


# ---------- 7. Duplicate name conflict ----------


async def test_duplicate_name_conflict(auth_client: AsyncClient) -> None:
    """POST with duplicate name returns 409."""
    await _create_server(auth_client, name="unique-name")
    resp = await auth_client.post(
        MCP_URL,
        json={"name": "unique-name", "command": "echo"},
    )
    assert resp.status_code == 409


# ---------- 8. Not found ----------


async def test_update_not_found(auth_client: AsyncClient) -> None:
    """PUT on non-existent ID returns 404."""
    resp = await auth_client.put(
        f"{MCP_BASE}/99999",
        json={"name": "no-exist"},
    )
    assert resp.status_code == 404


async def test_delete_not_found(auth_client: AsyncClient) -> None:
    """DELETE on non-existent ID returns 404."""
    resp = await auth_client.delete(f"{MCP_BASE}/99999")
    assert resp.status_code == 404
