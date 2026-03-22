"""McpExecutor — BaseExecutor implementation backed by an MCP server (stdio, SSE, or streamable HTTP)."""

import asyncio
import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from mcp import ClientSession
from mcp.client.sse import sse_client
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.streamable_http import streamablehttp_client

from app.models.mcp_server import McpServer
from app.services.executors.base import ExecutorResult
from app.services.mcp_process_manager import McpProcessManager
from app.services.trace_emitter import TraceEmitter

logger = logging.getLogger(__name__)


@asynccontextmanager
async def _connect_session(server: McpServer, timeout: float) -> AsyncIterator[ClientSession]:
    """Yield a connected ClientSession for any transport type.

    Supports stdio, sse, and streamable_http transports.
    """
    transport_type = server.transport_type or "stdio"
    env_vars: dict[str, str] = json.loads(server.env_vars)

    if transport_type == "stdio":
        args_list: list[str] = json.loads(server.args)
        params = StdioServerParameters(
            command=server.command or "",
            args=args_list,
            env=env_vars if env_vars else None,
        )
        async with (
            stdio_client(params) as (read, write),
            ClientSession(read, write) as session,
        ):
            await asyncio.wait_for(session.initialize(), timeout=timeout)
            yield session

    elif transport_type == "sse":
        async with (
            sse_client(url=server.url or "") as (read, write),
            ClientSession(read, write) as session,
        ):
            await asyncio.wait_for(session.initialize(), timeout=timeout)
            yield session

    elif transport_type == "streamable_http":
        async with (
            streamablehttp_client(url=server.url or "") as (read, write, _),
            ClientSession(read, write) as session,
        ):
            await asyncio.wait_for(session.initialize(), timeout=timeout)
            yield session

    else:
        raise ValueError(f"Unsupported transport type: {transport_type}")


class McpExecutor:
    """Executes a named MCP tool on a specific MCP server.

    One McpExecutor instance per MCP server. Registered in ExecutorRegistry
    for each tool name as "{server_name}.{tool_name}".
    """

    def __init__(
        self,
        server: McpServer,
        process_manager: McpProcessManager,
        tracer: TraceEmitter,
        timeout: float = 30.0,
    ) -> None:
        self.server = server
        self.process_manager = process_manager
        self.tracer = tracer
        self.timeout = timeout

    async def execute(self, name: str, input: dict[str, Any]) -> ExecutorResult:
        """Invoke an MCP tool. name is "{server_name}.{tool_name}"."""
        # Extract the bare tool_name (strip server prefix)
        tool_name = name.split(".", 1)[-1] if "." in name else name

        self.tracer.emit_tool_start(name, input)

        try:
            async with _connect_session(self.server, self.timeout) as session:
                result = await asyncio.wait_for(
                    session.call_tool(tool_name, arguments=input),
                    timeout=self.timeout,
                )

            # Extract text content from result
            output: Any = None
            if result.content:
                texts = [c.text for c in result.content if hasattr(c, "text")]
                output = "\n".join(texts) if texts else str(result.content)

            self.tracer.emit_tool_end(name, output)
            return ExecutorResult(output=output)

        except TimeoutError:
            error_msg = f"MCP tool '{name}' timed out after {self.timeout}s"
            self.tracer.emit_tool_end(name, None, error=error_msg)
            return ExecutorResult(output=None, error=error_msg)
        except Exception as exc:
            error_msg = f"MCP tool '{name}' failed: {exc}"
            logger.exception("MCP tool execution error: %s", name)
            self.tracer.emit_tool_end(name, None, error=error_msg)
            return ExecutorResult(output=None, error=error_msg)


async def discover_and_register_mcp_tools(
    servers: list[McpServer],
    registry: Any,  # ExecutorRegistry
    process_manager: McpProcessManager,
    tracer: TraceEmitter,
    timeout: float = 10.0,
) -> list[dict[str, Any]]:
    """Query each enabled MCP server for its tools and register them in the registry.

    Tool names are namespaced as "{server_name}.{tool_name}".
    Called at chat-turn start so tools are fresh. Failures are logged, not raised.

    Returns a list of OpenAI-format tool schemas for the discovered tools.
    """
    tool_schemas: list[dict[str, Any]] = []

    for server in servers:
        if not server.is_enabled:
            continue
        try:
            async with _connect_session(server, timeout) as session:
                tools_result = await asyncio.wait_for(session.list_tools(), timeout=timeout)

            executor = McpExecutor(
                server=server,
                process_manager=process_manager,
                tracer=tracer,
                timeout=30.0,
            )
            for tool in tools_result.tools:
                namespaced = f"{server.name}.{tool.name}"
                registry.register(namespaced, executor)
                logger.info("Registered MCP tool: %s", namespaced)

                # Build OpenAI-format tool schema
                schema: dict[str, Any] = {
                    "type": "function",
                    "function": {
                        "name": namespaced,
                        "description": tool.description or f"MCP tool: {tool.name}",
                        "parameters": (
                            tool.inputSchema
                            if hasattr(tool, "inputSchema") and tool.inputSchema
                            else {"type": "object", "properties": {}}
                        ),
                    },
                }
                tool_schemas.append(schema)
        except Exception:
            logger.exception("Failed to discover tools from MCP server: %s", server.name)

    return tool_schemas
