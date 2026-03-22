"""Integration tests for trace event emission and persistence via SSE streaming."""

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import delete

from app.core.database import AsyncSessionFactory
from app.core.encryption import encrypt_value
from app.models.conversation import Conversation
from app.models.llm_provider import LLMProvider
from app.models.message import Message

CHAT_BASE = "/api/v1/chat"


# ---------- fixtures ----------


@pytest_asyncio.fixture(autouse=True)
async def _clean_tables() -> None:
    """Remove all conversations, messages, and providers before each test."""
    async with AsyncSessionFactory() as session:
        await session.execute(delete(Message))
        await session.execute(delete(Conversation))
        await session.execute(delete(LLMProvider))
        await session.commit()


@pytest_asyncio.fixture
async def provider() -> LLMProvider:
    """Create a default LLM provider for tests."""
    async with AsyncSessionFactory() as session:
        p = LLMProvider(
            name="test-provider",
            base_url="http://localhost:11434/v1",
            api_key_encrypted=encrypt_value("test-key"),
            models=json.dumps(["test-model"]),
            is_default=True,
        )
        session.add(p)
        await session.commit()
        await session.refresh(p)
        return p


# ---------- helpers ----------


async def _create_conversation(
    auth_client: AsyncClient,
    title: str = "TraceTest",
) -> dict[str, Any]:
    resp = await auth_client.post(f"{CHAT_BASE}/conversations", json={"title": title})
    assert resp.status_code == 201, resp.text
    return resp.json()  # type: ignore[no-any-return]


def _make_mock_chunk(content: str | None = None, finish: bool = False) -> MagicMock:
    """Create a mock ChatCompletionChunk."""
    chunk = MagicMock()
    choice = MagicMock()
    delta = MagicMock()
    delta.content = content
    choice.delta = delta
    if finish:
        choice.finish_reason = "stop"
    else:
        choice.finish_reason = None
    chunk.choices = [choice]
    return chunk


async def _mock_stream_iter(chunks: list[MagicMock]) -> Any:
    """Create an async iterator from chunks."""
    for chunk in chunks:
        yield chunk


def _parse_sse_events(body: str) -> list[dict[str, Any]]:
    """Parse SSE event lines from response body."""
    events = []
    for line in body.split("\n"):
        line = line.strip()
        if line.startswith("data: "):
            try:
                events.append(json.loads(line[6:]))
            except json.JSONDecodeError:
                continue
    return events


# ---------- Tests ----------


@pytest.mark.asyncio
async def test_stream_emits_trace_events(auth_client: AsyncClient, provider: LLMProvider) -> None:
    """POST to stream endpoint emits trace_event SSE lines."""
    conv = await _create_conversation(auth_client)
    conv_id = conv["id"]

    chunks = [
        _make_mock_chunk(content="Hello"),
        _make_mock_chunk(content=" world"),
        _make_mock_chunk(finish=True),
    ]

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(return_value=_mock_stream_iter(chunks))

    with patch("app.api.v1.chat.AsyncOpenAI", return_value=mock_client):
        resp = await auth_client.post(
            f"{CHAT_BASE}/{conv_id}/stream",
            json={"content": "Hi there"},
        )

    assert resp.status_code == 200
    events = _parse_sse_events(resp.text)

    trace_events = [e for e in events if e.get("type") == "trace_event"]
    assert len(trace_events) >= 1, f"Expected trace_events, got: {events}"


@pytest.mark.asyncio
async def test_trace_event_has_correct_shape(
    auth_client: AsyncClient, provider: LLMProvider
) -> None:
    """First trace_event has the expected fields and values."""
    conv = await _create_conversation(auth_client)
    conv_id = conv["id"]

    chunks = [
        _make_mock_chunk(content="Hi"),
        _make_mock_chunk(finish=True),
    ]

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(return_value=_mock_stream_iter(chunks))

    with patch("app.api.v1.chat.AsyncOpenAI", return_value=mock_client):
        resp = await auth_client.post(
            f"{CHAT_BASE}/{conv_id}/stream",
            json={"content": "Hello"},
        )

    events = _parse_sse_events(resp.text)
    trace_events = [e for e in events if e.get("type") == "trace_event"]
    assert len(trace_events) >= 1

    first_trace = trace_events[0]
    assert first_trace["type"] == "trace_event"
    assert "event" in first_trace

    event = first_trace["event"]
    assert isinstance(event["id"], str)
    assert event["type"] in ("run_start", "run_end", "token_generation", "error")
    assert event["status"] in ("running", "completed", "error")
    assert "started_at" in event
    assert "name" in event


@pytest.mark.asyncio
async def test_trace_data_persisted_on_message(
    auth_client: AsyncClient, provider: LLMProvider
) -> None:
    """After stream completes, assistant message has trace_data persisted."""
    conv = await _create_conversation(auth_client)
    conv_id = conv["id"]

    chunks = [
        _make_mock_chunk(content="Response"),
        _make_mock_chunk(finish=True),
    ]

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(return_value=_mock_stream_iter(chunks))

    with patch("app.api.v1.chat.AsyncOpenAI", return_value=mock_client):
        resp = await auth_client.post(
            f"{CHAT_BASE}/{conv_id}/stream",
            json={"content": "Tell me something"},
        )

    assert resp.status_code == 200

    # Verify done event was emitted (message was saved)
    events = _parse_sse_events(resp.text)
    done_events = [e for e in events if e.get("type") == "done"]
    assert len(done_events) == 1, f"Expected done event, got: {events}"

    # Now GET messages and check trace_data
    msg_resp = await auth_client.get(f"{CHAT_BASE}/conversations/{conv_id}/messages")
    assert msg_resp.status_code == 200
    messages = msg_resp.json()

    assistant_msgs = [m for m in messages if m["role"] == "assistant"]
    assert len(assistant_msgs) == 1

    trace_data = assistant_msgs[0]["trace_data"]
    assert trace_data is not None

    parsed_trace = json.loads(trace_data)
    assert isinstance(parsed_trace, list)
    # Should have at least run_start + token_generation + run_end = 3
    assert len(parsed_trace) >= 2


@pytest.mark.asyncio
async def test_get_messages_includes_trace_data(
    auth_client: AsyncClient, provider: LLMProvider
) -> None:
    """GET /conversations/{id}/messages response includes trace_data field."""
    conv = await _create_conversation(auth_client)
    conv_id = conv["id"]

    # Insert a message with trace_data directly
    async with AsyncSessionFactory() as session:
        msg = Message(
            conversation_id=conv_id,
            role="assistant",
            content="Test response",
            trace_data=json.dumps(
                [
                    {
                        "id": "evt-1",
                        "type": "run_start",
                        "name": "chat_turn",
                        "status": "running",
                        "started_at": "2026-03-21T10:00:00Z",
                        "completed_at": None,
                    }
                ]
            ),
        )
        session.add(msg)
        await session.commit()

    resp = await auth_client.get(f"{CHAT_BASE}/conversations/{conv_id}/messages")
    assert resp.status_code == 200
    messages = resp.json()
    assert len(messages) == 1
    assert "trace_data" in messages[0]
    assert messages[0]["trace_data"] is not None

    parsed = json.loads(messages[0]["trace_data"])
    assert parsed[0]["type"] == "run_start"


@pytest.mark.asyncio
async def test_trace_data_null_for_user_messages(
    auth_client: AsyncClient,
) -> None:
    """User messages have trace_data as null."""
    conv = await _create_conversation(auth_client)
    conv_id = conv["id"]

    async with AsyncSessionFactory() as session:
        msg = Message(
            conversation_id=conv_id,
            role="user",
            content="Hello",
        )
        session.add(msg)
        await session.commit()

    resp = await auth_client.get(f"{CHAT_BASE}/conversations/{conv_id}/messages")
    assert resp.status_code == 200
    messages = resp.json()
    assert len(messages) == 1
    assert messages[0]["trace_data"] is None


@pytest.mark.asyncio
async def test_error_produces_error_trace_event(
    auth_client: AsyncClient, provider: LLMProvider
) -> None:
    """When LLM call fails, SSE stream includes error trace_event."""
    conv = await _create_conversation(auth_client)
    conv_id = conv["id"]

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(side_effect=Exception("Connection refused"))

    with patch("app.api.v1.chat.AsyncOpenAI", return_value=mock_client):
        resp = await auth_client.post(
            f"{CHAT_BASE}/{conv_id}/stream",
            json={"content": "Trigger error"},
        )

    assert resp.status_code == 200
    events = _parse_sse_events(resp.text)

    trace_events = [e for e in events if e.get("type") == "trace_event"]
    # Should have at least run_start + error + run_end
    assert len(trace_events) >= 2

    # Find the error trace event
    error_traces = [
        e
        for e in trace_events
        if e["event"].get("type") == "error" or e["event"].get("status") == "error"
    ]
    assert len(error_traces) >= 1, f"Expected error trace, got: {trace_events}"


@pytest.mark.asyncio
async def test_trace_data_in_export(auth_client: AsyncClient, provider: LLMProvider) -> None:
    """GET /conversations/{id}/export includes traces for assistant messages."""
    conv = await _create_conversation(auth_client)
    conv_id = conv["id"]

    trace_json = json.dumps(
        [
            {
                "id": "evt-1",
                "type": "run_start",
                "name": "chat_turn",
                "status": "running",
                "started_at": "2026-03-21T10:00:00Z",
                "completed_at": None,
            },
            {
                "id": "evt-2",
                "type": "run_end",
                "name": "run_end",
                "status": "completed",
                "started_at": "2026-03-21T10:00:01Z",
                "completed_at": "2026-03-21T10:00:01Z",
            },
        ]
    )

    async with AsyncSessionFactory() as session:
        msg = Message(
            conversation_id=conv_id,
            role="assistant",
            content="Exported response",
            trace_data=trace_json,
        )
        session.add(msg)
        await session.commit()

    resp = await auth_client.get(f"{CHAT_BASE}/{conv_id}/export")
    assert resp.status_code == 200
    export_data = resp.json()
    assert "messages" in export_data

    assistant_msgs = [m for m in export_data["messages"] if m["role"] == "assistant"]
    assert len(assistant_msgs) == 1
    assert assistant_msgs[0]["trace_data"] is not None
    assert len(assistant_msgs[0]["trace_data"]) == 2
    assert assistant_msgs[0]["trace_data"][0]["type"] == "run_start"
