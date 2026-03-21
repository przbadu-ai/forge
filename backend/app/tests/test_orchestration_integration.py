"""Integration tests for orchestration loop via SSE stream endpoint."""

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


# ---------- Fixtures ----------


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


# ---------- Helpers ----------


async def _create_conversation(
    auth_client: AsyncClient,
    title: str = "OrchTest",
) -> dict[str, Any]:
    resp = await auth_client.post(f"{CHAT_BASE}/conversations", json={"title": title})
    assert resp.status_code == 201, resp.text
    return resp.json()  # type: ignore[no-any-return]


def _parse_sse(response_text: str) -> list[dict[str, Any]]:
    """Parse SSE data lines from response body."""
    events = []
    for line in response_text.splitlines():
        if line.startswith("data: "):
            try:
                events.append(json.loads(line[6:]))
            except json.JSONDecodeError:
                continue
    return events


def _make_text_response(content: str = "Hello world") -> MagicMock:
    """Create a mock non-streaming LLM response with text content."""
    response = MagicMock()
    choice = MagicMock()
    choice.finish_reason = "stop"
    choice.message.content = content
    choice.message.tool_calls = None
    response.choices = [choice]
    return response


def _make_tool_call_response(
    tool_name: str = "current_datetime",
    arguments: str = "{}",
    call_id: str = "call_456",
) -> MagicMock:
    """Create a mock non-streaming LLM response with a tool call."""
    response = MagicMock()
    choice = MagicMock()
    choice.finish_reason = "tool_calls"

    tool_call = MagicMock()
    tool_call.id = call_id
    tool_call.function.name = tool_name
    tool_call.function.arguments = arguments

    choice.message.content = None
    choice.message.tool_calls = [tool_call]
    response.choices = [choice]
    return response


# ---------- Tests ----------


@pytest.mark.asyncio
async def test_text_only_response_streams_trace_events(
    auth_client: AsyncClient, provider: LLMProvider
) -> None:
    """Text-only LLM response streams tokens and emits run_start + token_generation + run_end."""
    conv = await _create_conversation(auth_client)
    conv_id = conv["id"]

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(return_value=_make_text_response("Hello world"))

    with patch("app.api.v1.chat.AsyncOpenAI", return_value=mock_client):
        resp = await auth_client.post(
            f"{CHAT_BASE}/{conv_id}/stream",
            json={"content": "Hi there"},
        )

    assert resp.status_code == 200
    events = _parse_sse(resp.text)

    # Should have trace events: run_start, token_generation, run_end
    trace_events = [e for e in events if e.get("type") == "trace_event"]
    trace_types = [e["event"]["type"] for e in trace_events]
    assert "run_start" in trace_types
    assert "token_generation" in trace_types
    assert "run_end" in trace_types

    # Should have token event
    token_events = [e for e in events if e.get("type") == "token"]
    assert len(token_events) >= 1

    # Should end with done
    done_events = [e for e in events if e.get("type") == "done"]
    assert len(done_events) == 1


@pytest.mark.asyncio
async def test_tool_call_produces_tool_trace_events(
    auth_client: AsyncClient, provider: LLMProvider
) -> None:
    """Tool call then text response produces tool_start and tool_end trace events."""
    conv = await _create_conversation(auth_client)
    conv_id = conv["id"]

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(
        side_effect=[
            _make_tool_call_response(),
            _make_text_response("The current time is 2026-01-01T00:00:00Z"),
        ]
    )

    with patch("app.api.v1.chat.AsyncOpenAI", return_value=mock_client):
        resp = await auth_client.post(
            f"{CHAT_BASE}/{conv_id}/stream",
            json={"content": "What time is it?"},
        )

    assert resp.status_code == 200
    events = _parse_sse(resp.text)

    # Should have tool_call trace events
    trace_events = [e for e in events if e.get("type") == "trace_event"]
    tool_traces = [e["event"] for e in trace_events if e["event"].get("type") == "tool_call"]

    # At least tool_start (running) and tool_end (completed)
    assert len(tool_traces) >= 2
    statuses = [t["status"] for t in tool_traces]
    assert "running" in statuses
    assert "completed" in statuses


@pytest.mark.asyncio
async def test_tool_end_has_correct_output(auth_client: AsyncClient, provider: LLMProvider) -> None:
    """tool_end trace event has output matching what ToolExecutor returned."""
    conv = await _create_conversation(auth_client)
    conv_id = conv["id"]

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(
        side_effect=[
            _make_tool_call_response(),
            _make_text_response("Done"),
        ]
    )

    with patch("app.api.v1.chat.AsyncOpenAI", return_value=mock_client):
        resp = await auth_client.post(
            f"{CHAT_BASE}/{conv_id}/stream",
            json={"content": "What time?"},
        )

    events = _parse_sse(resp.text)
    trace_events = [e for e in events if e.get("type") == "trace_event"]
    tool_end_events = [
        e["event"]
        for e in trace_events
        if e["event"].get("type") == "tool_call" and e["event"].get("status") == "completed"
    ]

    assert len(tool_end_events) >= 1
    # Output should be an ISO datetime string (from built-in current_datetime tool)
    assert tool_end_events[0]["output"] is not None
    assert "2026" in tool_end_events[0]["output"] or "T" in tool_end_events[0]["output"]


@pytest.mark.asyncio
async def test_tool_call_ends_with_done(auth_client: AsyncClient, provider: LLMProvider) -> None:
    """After tool_call + text loop, SSE ends with done event with message_id."""
    conv = await _create_conversation(auth_client)
    conv_id = conv["id"]

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(
        side_effect=[
            _make_tool_call_response(),
            _make_text_response("The time is now"),
        ]
    )

    with patch("app.api.v1.chat.AsyncOpenAI", return_value=mock_client):
        resp = await auth_client.post(
            f"{CHAT_BASE}/{conv_id}/stream",
            json={"content": "time please"},
        )

    events = _parse_sse(resp.text)
    done_events = [e for e in events if e.get("type") == "done"]
    assert len(done_events) == 1
    assert "message_id" in done_events[0]


@pytest.mark.asyncio
async def test_timeout_produces_error_event(
    auth_client: AsyncClient, provider: LLMProvider
) -> None:
    """Timeout on LLM call produces error SSE event and does not hang."""
    conv = await _create_conversation(auth_client)
    conv_id = conv["id"]

    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(
        side_effect=TimeoutError("Connection timed out")
    )

    with patch("app.api.v1.chat.AsyncOpenAI", return_value=mock_client):
        resp = await auth_client.post(
            f"{CHAT_BASE}/{conv_id}/stream",
            json={"content": "Will timeout"},
        )

    assert resp.status_code == 200
    events = _parse_sse(resp.text)

    # Should have error events (either trace_event with error type, or type=error)
    error_events = [e for e in events if e.get("type") == "error"]
    error_trace_events = [
        e
        for e in events
        if e.get("type") == "trace_event" and e.get("event", {}).get("type") == "error"
    ]

    # At least one error indicator in the stream
    assert len(error_events) + len(error_trace_events) >= 1
