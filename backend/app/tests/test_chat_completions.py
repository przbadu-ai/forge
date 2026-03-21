"""Tests for chat completions features: regenerate, export, search, system prompt."""

from typing import Any

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import delete

from app.core.database import AsyncSessionFactory
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.settings import AppSettings

CHAT_BASE = "/api/v1/chat"


# ---------- fixtures ----------


@pytest_asyncio.fixture(autouse=True)
async def _clean_tables() -> None:
    """Remove all conversations, messages and settings before each test."""
    async with AsyncSessionFactory() as session:
        await session.execute(delete(Message))
        await session.execute(delete(Conversation))
        await session.execute(delete(AppSettings))
        await session.commit()


# ---------- helpers ----------


async def _create_conversation(
    auth_client: AsyncClient,
    title: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if title is not None:
        payload["title"] = title
    resp = await auth_client.post(f"{CHAT_BASE}/conversations", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()  # type: ignore[no-any-return]


async def _add_messages(conv_id: int, messages: list[dict[str, str]]) -> None:
    """Insert messages directly into DB."""
    async with AsyncSessionFactory() as session:
        for m in messages:
            msg = Message(
                conversation_id=conv_id,
                role=m["role"],
                content=m["content"],
            )
            session.add(msg)
        await session.commit()


# ---------- 1. Regenerate: success ----------


async def test_regenerate_deletes_last_assistant(auth_client: AsyncClient) -> None:
    """POST /{id}/regenerate deletes last assistant message."""
    conv = await _create_conversation(auth_client, title="RegenTest")
    conv_id = conv["id"]

    await _add_messages(
        conv_id,
        [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ],
    )

    resp = await auth_client.post(f"{CHAT_BASE}/conversations/{conv_id}/regenerate")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

    # Verify assistant message is gone
    msgs_resp = await auth_client.get(f"{CHAT_BASE}/conversations/{conv_id}/messages")
    messages = msgs_resp.json()
    assert len(messages) == 1
    assert messages[0]["role"] == "user"


# ---------- 2. Regenerate: no assistant message ----------


async def test_regenerate_no_assistant_returns_404(auth_client: AsyncClient) -> None:
    """POST /{id}/regenerate with no assistant message returns 404."""
    conv = await _create_conversation(auth_client, title="RegenFail")
    conv_id = conv["id"]

    await _add_messages(
        conv_id,
        [{"role": "user", "content": "Hello"}],
    )

    resp = await auth_client.post(f"{CHAT_BASE}/conversations/{conv_id}/regenerate")
    assert resp.status_code == 404
    assert "No assistant message" in resp.json()["detail"]


# ---------- 3. Regenerate: empty conversation ----------


async def test_regenerate_empty_conversation_returns_404(
    auth_client: AsyncClient,
) -> None:
    """POST /{id}/regenerate on empty conversation returns 404."""
    conv = await _create_conversation(auth_client, title="EmptyConv")
    conv_id = conv["id"]

    resp = await auth_client.post(f"{CHAT_BASE}/conversations/{conv_id}/regenerate")
    assert resp.status_code == 404


# ---------- 4. Export ----------


async def test_export_conversation(auth_client: AsyncClient) -> None:
    """GET /{id}/export returns JSON with correct shape and Content-Disposition."""
    conv = await _create_conversation(auth_client, title="ExportTest")
    conv_id = conv["id"]

    await _add_messages(
        conv_id,
        [
            {"role": "user", "content": "What is 2+2?"},
            {"role": "assistant", "content": "4"},
        ],
    )

    resp = await auth_client.get(f"{CHAT_BASE}/conversations/{conv_id}/export")
    assert resp.status_code == 200

    # Check Content-Disposition header
    content_disp = resp.headers.get("content-disposition", "")
    assert "attachment" in content_disp
    assert f"conversation-{conv_id}.json" in content_disp

    # Check body
    data = resp.json()
    assert data["id"] == conv_id
    assert data["title"] == "ExportTest"
    assert len(data["messages"]) == 2
    assert data["messages"][0]["role"] == "user"
    assert data["messages"][0]["content"] == "What is 2+2?"
    assert data["messages"][1]["role"] == "assistant"
    assert data["messages"][1]["content"] == "4"
    # Each message should have created_at
    assert "created_at" in data["messages"][0]


# ---------- 5. Search: matching ----------


async def test_search_returns_matching_conversations(
    auth_client: AsyncClient,
) -> None:
    """GET /search?q=hello returns conversations with matching messages."""
    conv1 = await _create_conversation(auth_client, title="Conv1")
    conv2 = await _create_conversation(auth_client, title="Conv2")

    await _add_messages(
        conv1["id"],
        [{"role": "user", "content": "hello world"}],
    )
    await _add_messages(
        conv2["id"],
        [{"role": "user", "content": "goodbye world"}],
    )

    resp = await auth_client.get(f"{CHAT_BASE}/search", params={"q": "hello"})
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 1
    assert results[0]["id"] == conv1["id"]


# ---------- 6. Search: empty query returns 422 ----------


async def test_search_empty_query_returns_422(auth_client: AsyncClient) -> None:
    """GET /search?q= returns 422."""
    resp = await auth_client.get(f"{CHAT_BASE}/search", params={"q": ""})
    assert resp.status_code == 422


# ---------- 7. Search: no results ----------


async def test_search_no_match_returns_empty(auth_client: AsyncClient) -> None:
    """GET /search?q=xyz returns empty list when nothing matches."""
    conv = await _create_conversation(auth_client, title="NoMatch")
    await _add_messages(
        conv["id"],
        [{"role": "user", "content": "hello world"}],
    )

    resp = await auth_client.get(f"{CHAT_BASE}/search", params={"q": "xyz"})
    assert resp.status_code == 200
    assert resp.json() == []


# ---------- 8. Conversation CRUD with new fields ----------


async def test_create_conversation_with_system_prompt(
    auth_client: AsyncClient,
) -> None:
    """POST /conversations accepts system_prompt, temperature, max_tokens."""
    resp = await auth_client.post(
        f"{CHAT_BASE}/conversations",
        json={
            "title": "CustomConv",
            "system_prompt": "Be concise",
            "temperature": 0.5,
            "max_tokens": 1024,
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["system_prompt"] == "Be concise"
    assert data["temperature"] == 0.5
    assert data["max_tokens"] == 1024


async def test_update_conversation_system_prompt(
    auth_client: AsyncClient,
) -> None:
    """PUT /conversations/{id} updates system_prompt."""
    conv = await _create_conversation(auth_client, title="UpdateSP")
    conv_id = conv["id"]

    resp = await auth_client.put(
        f"{CHAT_BASE}/conversations/{conv_id}",
        json={"system_prompt": "New prompt", "temperature": 1.5},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["system_prompt"] == "New prompt"
    assert data["temperature"] == 1.5


# ---------- 9. Export on nonexistent conversation ----------


async def test_export_nonexistent_returns_404(auth_client: AsyncClient) -> None:
    """GET /conversations/99999/export returns 404."""
    resp = await auth_client.get(f"{CHAT_BASE}/conversations/99999/export")
    assert resp.status_code == 404


# ---------- 10. Search deduplicates conversations ----------


async def test_search_deduplicates(auth_client: AsyncClient) -> None:
    """Search returns unique conversations even when multiple messages match."""
    conv = await _create_conversation(auth_client, title="DedupConv")

    await _add_messages(
        conv["id"],
        [
            {"role": "user", "content": "hello friend"},
            {"role": "assistant", "content": "hello back"},
        ],
    )

    resp = await auth_client.get(f"{CHAT_BASE}/search", params={"q": "hello"})
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) == 1
