"""Unit tests for McpExecutor with mocked MCP client."""

from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.mcp_server import McpServer
from app.services.executors.mcp_executor import McpExecutor
from app.services.mcp_process_manager import McpProcessManager
from app.services.trace_emitter import TraceEmitter


def _make_server(
    name: str = "test-server",
    command: str = "echo",
    args: str = "[]",
    env_vars: str = "{}",
) -> McpServer:
    """Create a minimal McpServer instance (no DB needed)."""
    return McpServer(
        id=1,
        name=name,
        command=command,
        args=args,
        env_vars=env_vars,
        is_enabled=True,
    )


def _make_executor(
    server: McpServer | None = None,
    tracer: TraceEmitter | None = None,
) -> McpExecutor:
    """Create an McpExecutor with default mocks."""
    return McpExecutor(
        server=server or _make_server(),
        process_manager=McpProcessManager(),
        tracer=tracer or TraceEmitter(),
        timeout=5.0,
    )


# ---------- Happy path ----------


@patch("app.services.executors.mcp_executor.ClientSession")
@patch("app.services.executors.mcp_executor.stdio_client")
async def test_execute_happy_path(
    mock_stdio: MagicMock,
    mock_session_cls: MagicMock,
) -> None:
    """Successful MCP tool call returns ExecutorResult with output."""
    # Set up mock session
    mock_session = AsyncMock()
    mock_session.initialize = AsyncMock()
    mock_content = MagicMock()
    mock_content.text = "result text"
    mock_call_result = MagicMock()
    mock_call_result.content = [mock_content]
    mock_session.call_tool = AsyncMock(return_value=mock_call_result)

    # Mock the context managers
    @asynccontextmanager
    async def fake_stdio(params: Any) -> Any:
        yield AsyncMock(), AsyncMock()

    mock_stdio.side_effect = fake_stdio

    @asynccontextmanager
    async def fake_session(read: Any, write: Any) -> Any:
        yield mock_session

    mock_session_cls.side_effect = fake_session

    tracer = TraceEmitter()
    executor = _make_executor(tracer=tracer)
    result = await executor.execute("test-server.my_tool", {"arg": "value"})

    assert result.output == "result text"
    assert result.error is None
    mock_session.call_tool.assert_awaited_once_with("my_tool", arguments={"arg": "value"})

    # Verify trace events were emitted (tool_start + tool_end)
    tool_events = [e for e in tracer.events if e.type == "tool_call"]
    assert len(tool_events) == 2
    assert tool_events[0].status == "running"
    assert tool_events[1].status == "completed"


# ---------- Timeout path ----------


@patch("app.services.executors.mcp_executor.ClientSession")
@patch("app.services.executors.mcp_executor.stdio_client")
async def test_execute_timeout(
    mock_stdio: MagicMock,
    mock_session_cls: MagicMock,
) -> None:
    """Timeout during MCP call returns error ExecutorResult."""
    mock_session = AsyncMock()
    mock_session.initialize = AsyncMock()
    mock_session.call_tool = AsyncMock(side_effect=TimeoutError())

    @asynccontextmanager
    async def fake_stdio(params: Any) -> Any:
        yield AsyncMock(), AsyncMock()

    mock_stdio.side_effect = fake_stdio

    @asynccontextmanager
    async def fake_session(read: Any, write: Any) -> Any:
        yield mock_session

    mock_session_cls.side_effect = fake_session

    tracer = TraceEmitter()
    executor = _make_executor(tracer=tracer)
    result = await executor.execute("test-server.slow_tool", {})

    assert result.output is None
    assert result.error is not None
    assert "timed out" in result.error

    # Verify error trace event
    tool_events = [e for e in tracer.events if e.type == "tool_call"]
    assert any(e.status == "error" for e in tool_events)


# ---------- Exception path ----------


@patch("app.services.executors.mcp_executor.ClientSession")
@patch("app.services.executors.mcp_executor.stdio_client")
async def test_execute_exception(
    mock_stdio: MagicMock,
    mock_session_cls: MagicMock,
) -> None:
    """Runtime error during MCP call returns error ExecutorResult."""
    mock_session = AsyncMock()
    mock_session.initialize = AsyncMock()
    mock_session.call_tool = AsyncMock(side_effect=RuntimeError("connection refused"))

    @asynccontextmanager
    async def fake_stdio(params: Any) -> Any:
        yield AsyncMock(), AsyncMock()

    mock_stdio.side_effect = fake_stdio

    @asynccontextmanager
    async def fake_session(read: Any, write: Any) -> Any:
        yield mock_session

    mock_session_cls.side_effect = fake_session

    tracer = TraceEmitter()
    executor = _make_executor(tracer=tracer)
    result = await executor.execute("test-server.broken_tool", {})

    assert result.output is None
    assert result.error is not None
    assert "connection refused" in result.error

    # Verify error trace
    tool_events = [e for e in tracer.events if e.type == "tool_call"]
    assert any(e.status == "error" for e in tool_events)


# ---------- Name parsing ----------


@patch("app.services.executors.mcp_executor.ClientSession")
@patch("app.services.executors.mcp_executor.stdio_client")
async def test_tool_name_stripping(
    mock_stdio: MagicMock,
    mock_session_cls: MagicMock,
) -> None:
    """Tool name with server prefix is stripped to bare tool name for call_tool."""
    mock_session = AsyncMock()
    mock_session.initialize = AsyncMock()
    mock_result = MagicMock()
    mock_result.content = []
    mock_session.call_tool = AsyncMock(return_value=mock_result)

    @asynccontextmanager
    async def fake_stdio(params: Any) -> Any:
        yield AsyncMock(), AsyncMock()

    mock_stdio.side_effect = fake_stdio

    @asynccontextmanager
    async def fake_session(read: Any, write: Any) -> Any:
        yield mock_session

    mock_session_cls.side_effect = fake_session

    executor = _make_executor()
    await executor.execute("my-server.get_weather", {"city": "NYC"})

    # call_tool should receive the bare name without server prefix
    mock_session.call_tool.assert_awaited_once_with("get_weather", arguments={"city": "NYC"})
