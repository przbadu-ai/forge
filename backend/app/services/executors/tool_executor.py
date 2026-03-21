"""ToolExecutor — implements BaseExecutor for built-in tools."""

from collections.abc import Callable
from typing import Any

from app.services.executors.base import ExecutorResult
from app.services.executors.builtin_tools import BUILTIN_TOOLS


class ToolExecutor:
    """Executor that delegates to built-in tool functions."""

    def __init__(self, tools: dict[str, Callable[..., Any]] | None = None) -> None:
        self.tools = tools if tools is not None else BUILTIN_TOOLS

    async def execute(self, name: str, input: dict[str, Any]) -> ExecutorResult:
        """Execute a tool by name with the given input.

        Returns ExecutorResult with output on success, or error on failure.
        """
        tool_fn = self.tools.get(name)
        if tool_fn is None:
            return ExecutorResult(output=None, error=f"Unknown tool: {name}")
        try:
            result = await tool_fn(input)
            return ExecutorResult(output=result)
        except Exception as e:
            return ExecutorResult(output=None, error=str(e))
