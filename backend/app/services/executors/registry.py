"""ExecutorRegistry — register executors by tool name, dispatch by name."""

from typing import Any

from app.services.executors.base import BaseExecutor, ExecutorResult


class ExecutorRegistry:
    """Registry that maps tool names to executor instances."""

    def __init__(self) -> None:
        self._executors: dict[str, BaseExecutor] = {}

    def register(self, tool_name: str, executor: BaseExecutor) -> None:
        """Register an executor for a given tool name."""
        self._executors[tool_name] = executor

    async def dispatch(self, tool_name: str, input: dict[str, Any]) -> ExecutorResult:
        """Dispatch a tool call to the registered executor.

        Raises KeyError if no executor is registered for the given name.
        """
        if tool_name not in self._executors:
            raise KeyError(f"No executor registered for tool: {tool_name}")
        return await self._executors[tool_name].execute(tool_name, input)

    def available_tools(self) -> list[str]:
        """Return list of registered tool names."""
        return list(self._executors.keys())
