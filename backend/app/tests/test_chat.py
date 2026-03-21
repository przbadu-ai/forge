"""Integration tests for the chat CRUD and streaming API."""

import json

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import delete

from app.core.database import AsyncSessionFactory
from app.models.conversation import Conversation
from app.models.message import Message


CHAT_BASE = "/api/v1/chat"


# ---------- fixtures ----------


@pytest_asyncio.fixture(autouse=True)
async def _clean_chat_tables() -> None:
    """Remove all conversations and messages before each test."""
    async with AsyncSessionFactory() as session:
        await session.execute(delete(Message))
        await session.execute(delete(Conversation))
        await session.commit()


# ---------- helpers ----------


async def _create_conversation(
    auth_client: AsyncClient,
    title: str | None = None,
) -> dict:
    payload: dict = {}
    if title is not None:
        payload["title"] = title
    resp = await auth_client.post(f"{CHAT_BASE}/conversations", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


# ---------- 1. Create conversation ----------


async def test_create_conversation(auth_client: AsyncClient) -> None:
    """POST /chat/conversations returns 201 with id and title."""
    data = await _create_conversation(auth_client, title="My Chat")
    assert "id" in data
    assert data["title"] == "My Chat"
    assert "user_id" in data
    assert "created_at" in data
    assert "updated_at" in data


async def test_create_conversation_default_title(auth_client: AsyncClient) -> None:
    """POST /chat/conversations without title uses default."""
    data = await _create_conversation(auth_client)
    assert data["title"] == "New Conversation"


# ---------- 2. List conversations ----------


async def test_list_conversations(auth_client: AsyncClient) -> None:
    """GET /chat/conversations returns list of conversations."""
    await _create_conversation(auth_client, title="First")
    await _create_conversation(auth_client, title="Second")

    resp = await auth_client.get(f"{CHAT_BASE}/conversations")
    assert resp.status_code == 200
    conversations = resp.json()
    assert len(conversations) == 2
    titles = [c["title"] for c in conversations]
    assert "First" in titles
    assert "Second" in titles


# ---------- 3. Get conversation messages ----------


async def test_get_conversation_messages(auth_client: AsyncClient) -> None:
    """GET /chat/conversations/{id}/messages returns messages."""
    conv = await _create_conversation(auth_client, title="MsgTest")
    conv_id = conv["id"]

    # Insert a message directly in DB
    async with AsyncSessionFactory() as session:
        msg = Message(
            conversation_id=conv_id,
            role="user",
            content="Hello world",
        )
        session.add(msg)
        await session.commit()

    resp = await auth_client.get(f"{CHAT_BASE}/conversations/{conv_id}/messages")
    assert resp.status_code == 200
    messages = resp.json()
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Hello world"


# ---------- 4. Update conversation title ----------


async def test_update_conversation_title(auth_client: AsyncClient) -> None:
    """PUT /chat/conversations/{id} updates the title."""
    conv = await _create_conversation(auth_client, title="Old Title")
    conv_id = conv["id"]

    resp = await auth_client.put(
        f"{CHAT_BASE}/conversations/{conv_id}",
        json={"title": "New Title"},
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "New Title"


# ---------- 5. Delete conversation ----------


async def test_delete_conversation(auth_client: AsyncClient) -> None:
    """DELETE /chat/conversations/{id} returns 204 and removes it."""
    conv = await _create_conversation(auth_client, title="ToDelete")
    conv_id = conv["id"]

    resp = await auth_client.delete(f"{CHAT_BASE}/conversations/{conv_id}")
    assert resp.status_code == 204

    # Verify it's gone
    resp = await auth_client.get(f"{CHAT_BASE}/conversations")
    ids = [c["id"] for c in resp.json()]
    assert conv_id not in ids


# ---------- 6. Auth required ----------


async def test_chat_requires_auth(client: AsyncClient) -> None:
    """All chat endpoints return 401/403 without token."""
    endpoints = [
        ("GET", f"{CHAT_BASE}/conversations"),
        ("POST", f"{CHAT_BASE}/conversations"),
        ("GET", f"{CHAT_BASE}/conversations/1/messages"),
        ("PUT", f"{CHAT_BASE}/conversations/1"),
        ("DELETE", f"{CHAT_BASE}/conversations/1"),
        ("POST", f"{CHAT_BASE}/1/stream"),
    ]
    for method, url in endpoints:
        resp = await client.request(method, url, json={})
        assert resp.status_code in (401, 403), (
            f"{method} {url} returned {resp.status_code}, expected 401/403"
        )


# ---------- 7. Stream endpoint exists ----------


async def test_stream_endpoint_exists(auth_client: AsyncClient) -> None:
    """POST /chat/{id}/stream is registered and returns proper error when no provider."""
    conv = await _create_conversation(auth_client, title="StreamTest")
    conv_id = conv["id"]

    # No LLM provider configured, so we expect the endpoint to respond
    # with an SSE error event rather than a 404
    resp = await auth_client.post(
        f"{CHAT_BASE}/{conv_id}/stream",
        json={"content": "hello"},
    )
    # The endpoint returns 200 with SSE even on error (error is in the stream)
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers.get("content-type", "")

    # Parse the SSE body to find the error event
    body = resp.text
    for line in body.split("\n"):
        if line.startswith("data: "):
            event = json.loads(line[6:])
            assert event["type"] == "error"
            assert "No default LLM provider" in event["message"]
            break
    else:
        pytest.fail("No SSE data event found in stream response")  # type: ignore[attr-defined]


# ---------- 8. Conversation not found ----------


async def test_get_nonexistent_conversation_messages(auth_client: AsyncClient) -> None:
    """GET /chat/conversations/99999/messages returns 404."""
    resp = await auth_client.get(f"{CHAT_BASE}/conversations/99999/messages")
    assert resp.status_code == 404


async def test_update_nonexistent_conversation(auth_client: AsyncClient) -> None:
    """PUT /chat/conversations/99999 returns 404."""
    resp = await auth_client.put(
        f"{CHAT_BASE}/conversations/99999",
        json={"title": "Nope"},
    )
    assert resp.status_code == 404


async def test_delete_nonexistent_conversation(auth_client: AsyncClient) -> None:
    """DELETE /chat/conversations/99999 returns 404."""
    resp = await auth_client.delete(f"{CHAT_BASE}/conversations/99999")
    assert resp.status_code == 404
