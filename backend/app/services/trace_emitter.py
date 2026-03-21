"""TraceEmitter service for collecting execution trace events during a chat turn."""

import dataclasses
import json
import uuid
from datetime import UTC, datetime
from typing import Any, Literal


@dataclasses.dataclass
class TraceEvent:
    """A single trace event in an execution trace."""

    id: str
    type: Literal["run_start", "run_end", "token_generation", "error", "tool_call"]
    name: str
    status: Literal["running", "completed", "error"]
    started_at: str
    completed_at: str | None = None
    input: Any | None = None
    output: Any | None = None
    error: str | None = None
    metadata: dict[str, Any] | None = None


class TraceEmitter:
    """Collects TraceEvent instances during a chat turn and serializes them."""

    def __init__(self) -> None:
        self._events: list[TraceEvent] = []

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    def start_run(self, name: str = "chat_turn") -> TraceEvent:
        """Create and append a run_start event."""
        event = TraceEvent(
            id=str(uuid.uuid4()),
            type="run_start",
            name=name,
            status="running",
            started_at=self._now(),
        )
        self._events.append(event)
        return event

    def end_run(self, success: bool = True) -> TraceEvent:
        """Create and append a run_end event."""
        now = self._now()
        event = TraceEvent(
            id=str(uuid.uuid4()),
            type="run_end",
            name="run_end",
            status="completed" if success else "error",
            started_at=now,
            completed_at=now,
        )
        self._events.append(event)
        return event

    def emit_token_generation(self, token_count: int = 0) -> TraceEvent:
        """Create and append a token_generation event."""
        now = self._now()
        event = TraceEvent(
            id=str(uuid.uuid4()),
            type="token_generation",
            name="token_generation",
            status="completed",
            started_at=now,
            completed_at=now,
            metadata={"token_count": token_count},
        )
        self._events.append(event)
        return event

    def emit_error(self, error_message: str) -> TraceEvent:
        """Create and append an error event."""
        now = self._now()
        event = TraceEvent(
            id=str(uuid.uuid4()),
            type="error",
            name="error",
            status="error",
            started_at=now,
            completed_at=now,
            error=error_message,
        )
        self._events.append(event)
        return event

    def emit_tool_start(self, tool_name: str, tool_input: dict[str, Any]) -> TraceEvent:
        """Create and append a tool_call start event."""
        event = TraceEvent(
            id=str(uuid.uuid4()),
            type="tool_call",
            name=tool_name,
            status="running",
            started_at=self._now(),
            input=tool_input,
        )
        self._events.append(event)
        return event

    def emit_tool_end(
        self, tool_name: str, output: Any, error: str | None = None
    ) -> TraceEvent:
        """Create and append a tool_call completion event."""
        now = self._now()
        event = TraceEvent(
            id=str(uuid.uuid4()),
            type="tool_call",
            name=tool_name,
            status="error" if error else "completed",
            started_at=now,
            completed_at=now,
            output=output,
            error=error,
        )
        self._events.append(event)
        return event

    def to_json(self) -> str:
        """Serialize all events to a JSON string."""
        return json.dumps([dataclasses.asdict(e) for e in self._events])

    @property
    def events(self) -> list[TraceEvent]:
        """Return a copy of the events list."""
        return list(self._events)
