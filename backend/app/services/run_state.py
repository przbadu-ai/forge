"""In-memory RunState tracking for orchestration runs."""

import dataclasses
import enum
import uuid
from datetime import UTC, datetime


class RunStatus(enum.StrEnum):
    """Lifecycle status of an orchestration run."""

    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclasses.dataclass
class RunState:
    """Tracks the state of a single orchestration run."""

    run_id: str
    status: RunStatus
    created_at: datetime
    updated_at: datetime
    iteration: int = 0
    error: str | None = None


class RunStateStore:
    """Simple dict-backed store for RunState instances."""

    def __init__(self) -> None:
        self._states: dict[str, RunState] = {}

    def create(self) -> RunState:
        """Create a new RunState with UUID and status=CREATED."""
        now = datetime.now(UTC)
        run_id = str(uuid.uuid4())
        state = RunState(
            run_id=run_id,
            status=RunStatus.CREATED,
            created_at=now,
            updated_at=now,
        )
        self._states[run_id] = state
        return state

    def get(self, run_id: str) -> RunState | None:
        """Get a RunState by run_id, or None if not found."""
        return self._states.get(run_id)

    def update_status(self, run_id: str, status: RunStatus, error: str | None = None) -> None:
        """Update the status (and optionally error) of a run."""
        state = self._states.get(run_id)
        if state is None:
            raise KeyError(f"No run found with id: {run_id}")
        state.status = status
        state.error = error
        state.updated_at = datetime.now(UTC)

    def increment_iteration(self, run_id: str) -> None:
        """Increment the iteration counter for a run."""
        state = self._states.get(run_id)
        if state is None:
            raise KeyError(f"No run found with id: {run_id}")
        state.iteration += 1
        state.updated_at = datetime.now(UTC)

    def delete(self, run_id: str) -> None:
        """Remove a RunState from the store."""
        self._states.pop(run_id, None)
