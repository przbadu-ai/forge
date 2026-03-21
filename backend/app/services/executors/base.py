"""BaseExecutor protocol and ExecutorResult dataclass."""

import dataclasses
from typing import Any, Protocol


@dataclasses.dataclass
class ExecutorResult:
    """Result of an executor invocation."""

    output: Any
    error: str | None = None


class BaseExecutor(Protocol):
    """Protocol that all executors must implement."""

    async def execute(self, name: str, input: dict[str, Any]) -> ExecutorResult: ...
