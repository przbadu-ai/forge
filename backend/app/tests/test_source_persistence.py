"""Tests for source citation persistence and reranker fallback."""

import json

import pytest
from httpx import AsyncClient

from app.services.retrieval_service import rerank


@pytest.mark.asyncio
async def test_message_source_data_roundtrip(auth_client: AsyncClient) -> None:
    """Message model can store and retrieve source_data via API."""
    # Create a conversation
    conv_resp = await auth_client.post(
        "/api/v1/chat/conversations",
        json={"title": "Source Test"},
    )
    assert conv_resp.status_code == 201
    conv_id = conv_resp.json()["id"]

    # Insert a message with source_data directly via the DB
    # We'll do this by checking that GET /messages returns sources when present
    # First, we need to create a message with source_data.
    # Since there's no direct "create message" endpoint, we'll use the DB.
    from app.core.database import AsyncSessionFactory
    from app.models.message import Message

    sources = [{"file_name": "test.pdf", "chunk_text": "sample text", "score": 0.85}]
    async with AsyncSessionFactory() as session:
        msg = Message(
            conversation_id=conv_id,
            role="assistant",
            content="Here is some info from the document.",
            source_data=json.dumps(sources),
        )
        session.add(msg)
        await session.commit()
        await session.refresh(msg)
        msg_id = msg.id

    # Now GET /messages and verify sources are returned
    resp = await auth_client.get(f"/api/v1/chat/conversations/{conv_id}/messages")
    assert resp.status_code == 200
    messages = resp.json()

    # Find the assistant message
    assistant_msgs = [m for m in messages if m["role"] == "assistant"]
    assert len(assistant_msgs) >= 1

    found = [m for m in assistant_msgs if m["id"] == msg_id]
    assert len(found) == 1
    assert found[0]["sources"] is not None
    assert len(found[0]["sources"]) == 1
    assert found[0]["sources"][0]["file_name"] == "test.pdf"
    assert found[0]["sources"][0]["chunk_text"] == "sample text"
    assert found[0]["sources"][0]["score"] == 0.85


@pytest.mark.asyncio
async def test_get_messages_returns_null_sources_when_none(auth_client: AsyncClient) -> None:
    """Messages without source_data return sources=null."""
    # Create a conversation
    conv_resp = await auth_client.post(
        "/api/v1/chat/conversations",
        json={"title": "No Sources Test"},
    )
    assert conv_resp.status_code == 201
    conv_id = conv_resp.json()["id"]

    # Insert a message without source_data
    from app.core.database import AsyncSessionFactory
    from app.models.message import Message

    async with AsyncSessionFactory() as session:
        msg = Message(
            conversation_id=conv_id,
            role="assistant",
            content="A plain response.",
        )
        session.add(msg)
        await session.commit()

    resp = await auth_client.get(f"/api/v1/chat/conversations/{conv_id}/messages")
    assert resp.status_code == 200
    messages = resp.json()
    assistant_msgs = [m for m in messages if m["role"] == "assistant"]
    assert len(assistant_msgs) >= 1
    assert assistant_msgs[0]["sources"] is None


@pytest.mark.asyncio
async def test_rerank_fallback_on_error() -> None:
    """Reranker returns original documents when endpoint is unreachable."""
    docs = [
        {"file_id": 1, "chunk_text": "hello", "score": 0.9, "chunk_index": 0},
        {"file_id": 2, "chunk_text": "world", "score": 0.8, "chunk_index": 1},
    ]
    result = await rerank(
        query="test",
        documents=docs,
        reranker_base_url="http://localhost:99999",  # unreachable
        reranker_model="test-model",
        top_k=2,
    )
    assert len(result) == 2
    assert result[0]["chunk_text"] == "hello"
    assert result[1]["chunk_text"] == "world"
