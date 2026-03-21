"""SkillExecutor — BaseExecutor implementation for agent skills."""

import logging
from collections.abc import Callable, Coroutine
from typing import Any

from app.services.executors.base import ExecutorResult
from app.services.trace_emitter import TraceEmitter

logger = logging.getLogger(__name__)

# Type alias for async skill handler functions
SkillHandler = Callable[[dict[str, Any]], Coroutine[Any, Any, str]]


# ---------- Default placeholder handlers ----------


async def _web_search_handler(input: dict[str, Any]) -> str:
    query = input.get("query", "")
    return f"Web search is not yet configured. Query received: {query}"


async def _code_execution_handler(input: dict[str, Any]) -> str:
    code = input.get("code", "")
    return f"Code execution is not yet configured. Code received: {code[:200]}"


# Registry of default skill handlers keyed by skill name
DEFAULT_SKILL_HANDLERS: dict[str, SkillHandler] = {
    "web_search": _web_search_handler,
    "code_execution": _code_execution_handler,
}


class SkillExecutor:
    """Executor that delegates to skill handler functions.

    One SkillExecutor instance per skill. Registered in ExecutorRegistry
    for each enabled skill name.
    """

    def __init__(
        self,
        handlers: dict[str, SkillHandler] | None = None,
        tracer: TraceEmitter | None = None,
    ) -> None:
        self.handlers = handlers if handlers is not None else DEFAULT_SKILL_HANDLERS
        self.tracer = tracer

    async def execute(self, name: str, input: dict[str, Any]) -> ExecutorResult:
        """Execute a skill by name with the given input."""
        if self.tracer:
            self.tracer.emit_tool_start(name, input)

        handler = self.handlers.get(name)
        if handler is None:
            error_msg = f"No handler registered for skill: {name}"
            if self.tracer:
                self.tracer.emit_tool_end(name, None, error=error_msg)
            return ExecutorResult(output=None, error=error_msg)

        try:
            result = await handler(input)
            if self.tracer:
                self.tracer.emit_tool_end(name, result)
            return ExecutorResult(output=result)
        except Exception as e:
            error_msg = f"Skill '{name}' failed: {e}"
            logger.exception("Skill execution error: %s", name)
            if self.tracer:
                self.tracer.emit_tool_end(name, None, error=error_msg)
            return ExecutorResult(output=None, error=error_msg)
