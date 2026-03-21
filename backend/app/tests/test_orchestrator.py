"""Unit tests for Orchestrator loop with mock executor and mock LLM client."""

import asyncio
import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.executors.base import ExecutorResult
from app.services.executors.registry import ExecutorRegistry
from app.services.orchestrator import Orchestrator
from app.services.run_state import RunStateStore
from app.services.trace_emitter import TraceEmitter

# ---------- Helpers ----------


class MockExecutor:
    """Simple mock executor that returns a fixed result."""

    def __init__(self, output: Any = "2026-01-01T00:00:00Z", error: str | None = None) -> None:
        self._output = output
        self._error = error
        self.call_count = 0
        self.last_name: str | None = None
        self.last_input: dict[str, Any] | None = None

    async def execute(self, name: str, input: dict[str, Any]) -> ExecutorResult:
        self.call_count += 1
        self.last_name = name
        self.last_input = input
        return ExecutorResult(output=self._output, error=self._error)


def _make_text_response(content: str = "Hello world") -> MagicMock:
    """Create a mock LLM response with text content (no tool calls)."""
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
    call_id: str = "call_123",
) -> MagicMock:
    """Create a mock LLM response with a tool call."""
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


def _build_orchestrator(
    executor: MockExecutor | None = None,
    tool_name: str = "current_datetime",
    max_iterations: int = 10,
    timeout: float = 30.0,
) -> tuple[Orchestrator, RunStateStore, TraceEmitter, ExecutorRegistry]:
    """Build an Orchestrator with real store/tracer and optional mock executor."""
    registry = ExecutorRegistry()
    if executor is not None:
        registry.register(tool_name, executor)

    tracer = TraceEmitter()
    run_store = RunStateStore()

    orchestrator = Orchestrator(
        registry=registry,
        tracer=tracer,
        run_store=run_store,
        timeout=timeout,
        max_retries=0,  # No retries in unit tests for speed
        max_iterations=max_iterations,
    )
    return orchestrator, run_store, tracer, registry


def _parse_sse_events(sse_lines: list[str]) -> list[dict[str, Any]]:
    """Parse SSE lines into dicts."""
    events = []
    for line in sse_lines:
        line = line.strip()
        if line.startswith("data: "):
            try:
                events.append(json.loads(line[6:]))
            except json.JSONDecodeError:
                continue
    return events


async def _collect_sse(orchestrator: Orchestrator, client: AsyncMock, **kwargs: Any) -> list[str]:
    """Collect all SSE lines from orchestrator.run()."""
    defaults = {
        "model": "test-model",
        "messages": [{"role": "user", "content": "Hello"}],
        "temperature": 0.7,
        "max_tokens": 100,
    }
    defaults.update(kwargs)
    return [line async for line in orchestrator.run(client=client, **defaults)]


# ---------- Tests ----------


@pytest.mark.asyncio
async def test_text_response_completes_run() -> None:
    """When LLM responds with finish_reason='stop', run completes with COMPLETED status."""
    executor = MockExecutor()
    orchestrator, run_store, tracer, _ = _build_orchestrator(executor)

    client = AsyncMock()
    client.chat.completions.create = AsyncMock(return_value=_make_text_response("Hello world"))

    sse_lines = await _collect_sse(orchestrator, client)
    events = _parse_sse_events(sse_lines)

    # Should have token and token_generation trace events
    token_events = [e for e in events if e.get("type") == "token"]
    assert len(token_events) == 1
    assert token_events[0]["delta"] == "Hello world"

    # final_content should be set
    assert orchestrator.final_content == "Hello world"

    # No tool calls should have happened
    assert executor.call_count == 0


@pytest.mark.asyncio
async def test_tool_call_loop_two_iterations() -> None:
    """When LLM returns tool_call then text, the loop runs twice and completes."""
    executor = MockExecutor(output="2026-01-01T00:00:00Z")
    orchestrator, run_store, tracer, _ = _build_orchestrator(executor)

    client = AsyncMock()
    client.chat.completions.create = AsyncMock(
        side_effect=[
            _make_tool_call_response(),
            _make_text_response("The current time is 2026-01-01T00:00:00Z"),
        ]
    )

    sse_lines = await _collect_sse(orchestrator, client)
    events = _parse_sse_events(sse_lines)

    # Should have tool_start and tool_end trace events
    trace_events = [e for e in events if e.get("type") == "trace_event"]
    tool_traces = [e for e in trace_events if e.get("event", {}).get("type") == "tool_call"]
    assert len(tool_traces) >= 2  # tool_start + tool_end

    # Final content
    assert orchestrator.final_content == "The current time is 2026-01-01T00:00:00Z"

    # LLM was called twice
    assert client.chat.completions.create.call_count == 2


@pytest.mark.asyncio
async def test_executor_called_with_correct_args() -> None:
    """executor.execute is called with correct tool_name and input."""
    executor = MockExecutor()
    orchestrator, _, _, _ = _build_orchestrator(executor)

    client = AsyncMock()
    client.chat.completions.create = AsyncMock(
        side_effect=[
            _make_tool_call_response(tool_name="current_datetime", arguments='{"tz": "UTC"}'),
            _make_text_response("Done"),
        ]
    )

    await _collect_sse(orchestrator, client)

    assert executor.call_count == 1
    assert executor.last_name == "current_datetime"
    assert executor.last_input == {"tz": "UTC"}


@pytest.mark.asyncio
async def test_tool_start_emitted_before_execute() -> None:
    """tool_start trace event is emitted before executor.execute."""
    executor = MockExecutor()
    orchestrator, _, tracer, _ = _build_orchestrator(executor)

    client = AsyncMock()
    client.chat.completions.create = AsyncMock(
        side_effect=[
            _make_tool_call_response(),
            _make_text_response("Done"),
        ]
    )

    sse_lines = await _collect_sse(orchestrator, client)
    events = _parse_sse_events(sse_lines)

    trace_events = [e for e in events if e.get("type") == "trace_event"]
    tool_events = [
        e["event"] for e in trace_events if e.get("event", {}).get("type") == "tool_call"
    ]

    # First tool event should be "running" (tool_start)
    assert len(tool_events) >= 1
    assert tool_events[0]["status"] == "running"
    assert tool_events[0]["name"] == "current_datetime"


@pytest.mark.asyncio
async def test_tool_end_emitted_after_execute() -> None:
    """tool_end trace event is emitted after executor.execute with output."""
    executor = MockExecutor(output="2026-01-01T00:00:00Z")
    orchestrator, _, tracer, _ = _build_orchestrator(executor)

    client = AsyncMock()
    client.chat.completions.create = AsyncMock(
        side_effect=[
            _make_tool_call_response(),
            _make_text_response("Done"),
        ]
    )

    sse_lines = await _collect_sse(orchestrator, client)
    events = _parse_sse_events(sse_lines)

    trace_events = [e for e in events if e.get("type") == "trace_event"]
    tool_events = [
        e["event"] for e in trace_events if e.get("event", {}).get("type") == "tool_call"
    ]

    # Second tool event should be "completed" (tool_end) with output
    assert len(tool_events) >= 2
    assert tool_events[1]["status"] == "completed"
    assert tool_events[1]["output"] == "2026-01-01T00:00:00Z"


@pytest.mark.asyncio
async def test_max_iterations_exceeded() -> None:
    """When max_iterations exceeded, run state becomes FAILED with error."""
    executor = MockExecutor()
    orchestrator, run_store, tracer, _ = _build_orchestrator(executor, max_iterations=2)

    # LLM always returns tool_calls — will hit max iterations
    client = AsyncMock()
    client.chat.completions.create = AsyncMock(return_value=_make_tool_call_response())

    sse_lines = await _collect_sse(orchestrator, client)
    events = _parse_sse_events(sse_lines)

    # Should have an error event about max_iterations
    error_events = [e for e in events if e.get("type") == "error"]
    assert len(error_events) >= 1
    assert "max_iterations" in error_events[0]["message"]


@pytest.mark.asyncio
async def test_timeout_on_tool_dispatch() -> None:
    """When asyncio.wait_for raises TimeoutError on tool dispatch, error trace is emitted."""

    class SlowExecutor:
        async def execute(self, name: str, input: dict[str, Any]) -> ExecutorResult:
            await asyncio.sleep(100)  # Will be cancelled by timeout
            return ExecutorResult(output="never")

    registry = ExecutorRegistry()
    registry.register("current_datetime", SlowExecutor())
    tracer = TraceEmitter()
    run_store = RunStateStore()

    orchestrator = Orchestrator(
        registry=registry,
        tracer=tracer,
        run_store=run_store,
        timeout=0.01,  # Very short timeout
        max_retries=0,
        max_iterations=10,
    )

    client = AsyncMock()
    client.chat.completions.create = AsyncMock(return_value=_make_tool_call_response())

    sse_lines = await _collect_sse(orchestrator, client)
    events = _parse_sse_events(sse_lines)

    # Should have error events about timeout
    error_events = [e for e in events if e.get("type") == "error"]
    assert len(error_events) >= 1
    assert "Timeout" in error_events[0]["message"]

    # Trace should have tool_end with error
    trace_events = [e for e in events if e.get("type") == "trace_event"]
    tool_end_events = [
        e["event"]
        for e in trace_events
        if e.get("event", {}).get("type") == "tool_call"
        and e.get("event", {}).get("status") == "error"
    ]
    assert len(tool_end_events) >= 1


@pytest.mark.asyncio
async def test_executor_error_emits_tool_end_with_error() -> None:
    """Executor returning error emits tool_end with status='error'."""
    executor = MockExecutor(output=None, error="Tool broke")
    orchestrator, _, tracer, _ = _build_orchestrator(executor)

    client = AsyncMock()
    client.chat.completions.create = AsyncMock(
        side_effect=[
            _make_tool_call_response(),
            _make_text_response("Recovered"),
        ]
    )

    sse_lines = await _collect_sse(orchestrator, client)
    events = _parse_sse_events(sse_lines)

    trace_events = [e for e in events if e.get("type") == "trace_event"]
    tool_events = [
        e["event"] for e in trace_events if e.get("event", {}).get("type") == "tool_call"
    ]

    # tool_end should have status="error"
    tool_end = [e for e in tool_events if e["status"] == "error"]
    assert len(tool_end) >= 1
    assert tool_end[0]["error"] == "Tool broke"
