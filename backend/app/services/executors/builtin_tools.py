"""Built-in tools for the orchestration loop."""

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any


async def current_datetime(input: dict[str, Any]) -> str:
    """Return the current UTC date and time in ISO 8601 format."""
    return datetime.now(UTC).isoformat()


BUILTIN_TOOLS: dict[str, Callable[..., Any]] = {
    "current_datetime": current_datetime,
}

BUILTIN_TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "current_datetime",
            "description": "Returns the current UTC date and time in ISO 8601 format.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]
