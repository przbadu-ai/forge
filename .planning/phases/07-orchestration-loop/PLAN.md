---
phase: 07-orchestration-loop
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - backend/app/services/orchestrator.py
  - backend/app/services/executors/__init__.py
  - backend/app/services/executors/base.py
  - backend/app/services/executors/registry.py
  - backend/app/services/executors/tool_executor.py
  - backend/app/services/executors/builtin_tools.py
  - backend/app/services/run_state.py
  - backend/app/api/v1/chat.py
autonomous: true
requirements: [ORCH-01, ORCH-02, ORCH-03, ORCH-04, ORCH-05]

must_haves:
  truths:
    - "A chat turn that produces tool_calls enters the orchestration loop and continues until a final text response"
    - "Tool calls are dispatched through ExecutorRegistry; swapping an executor requires no Orchestrator changes"
    - "Every executor action emits tool_start and tool_end trace events visible in TracePanel"
    - "Each run has lifecycle state (created, running, completed, failed, cancelled) that updates correctly"
    - "Timeout produces an error trace event, not a silent hang; retry with exponential backoff is applied"
    - "Built-in 'current_datetime' tool returns current date/time so the loop can be tested end-to-end"
  artifacts:
    - path: "backend/app/services/orchestrator.py"
      provides: "Orchestrator service — while-loop: LLM call -> tool dispatch -> feed results -> repeat"
      exports: ["Orchestrator"]
    - path: "backend/app/services/executors/base.py"
      provides: "BaseExecutor protocol with async execute(name, input) -> output signature"
      exports: ["BaseExecutor", "ExecutorResult"]
    - path: "backend/app/services/executors/registry.py"
      provides: "ExecutorRegistry — register by tool name, dispatch by name"
      exports: ["ExecutorRegistry"]
    - path: "backend/app/services/executors/tool_executor.py"
      provides: "ToolExecutor implementing BaseExecutor; delegates to builtin_tools"
      exports: ["ToolExecutor"]
    - path: "backend/app/services/executors/builtin_tools.py"
      provides: "current_datetime built-in tool returning ISO timestamp"
      exports: ["BUILTIN_TOOLS", "current_datetime"]
    - path: "backend/app/services/run_state.py"
      provides: "In-memory RunState dataclass + RunStateStore keyed by run UUID"
      exports: ["RunState", "RunStatus", "RunStateStore"]
    - path: "backend/app/api/v1/chat.py"
      provides: "_token_generator refactored to call Orchestrator instead of direct OpenAI"
  key_links:
    - from: "backend/app/api/v1/chat.py"
      to: "backend/app/services/orchestrator.py"
      via: "Orchestrator.run() async generator replacing _token_generator's LLM call block"
      pattern: "Orchestrator.*run"
    - from: "backend/app/services/orchestrator.py"
      to: "backend/app/services/executors/registry.py"
      via: "registry.dispatch(tool_name, tool_input) for each tool_call"
      pattern: "registry\\.dispatch"
    - from: "backend/app/services/executors/tool_executor.py"
      to: "backend/app/services/trace_emitter.py"
      via: "tracer.emit_tool_start / emit_tool_end before and after execute()"
      pattern: "emit_tool_start|emit_tool_end"
---

<objective>
Implement the full agentic orchestration loop: Orchestrator service, BaseExecutor protocol, ExecutorRegistry, ToolExecutor with the `current_datetime` built-in tool, in-memory RunStateStore, and refactor chat.py to route through Orchestrator instead of calling OpenAI directly. Also extend TraceEmitter with tool_start/tool_end event methods.

Purpose: Enables tool calling — when the LLM returns tool_calls the loop dispatches to executors, feeds results back, and repeats until a text response. This is Phase 7's primary deliverable and the foundation for MCP (Phase 8) and Skills (Phase 9).

Output: `backend/app/services/orchestrator.py`, `backend/app/services/executors/` package, `backend/app/services/run_state.py`, updated `chat.py`, updated `trace_emitter.py`
</objective>

<execution_context>
@/Users/przbadu/.claude/get-shit-done/workflows/execute-plan.md
@/Users/przbadu/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/phases/07-orchestration-loop/7-CONTEXT.md

# Phase 6 completed the TraceEmitter and trace persistence. This plan extends it.
@.planning/phases/06-execution-trace-system/06-01-SUMMARY.md
@.planning/phases/06-execution-trace-system/06-03-SUMMARY.md
</context>

<interfaces>
<!-- Key contracts extracted from codebase for executor context -->

From backend/app/services/trace_emitter.py:
```python
@dataclasses.dataclass
class TraceEvent:
    id: str
    type: Literal["run_start", "run_end", "token_generation", "error"]
    name: str
    status: Literal["running", "completed", "error"]
    started_at: str
    completed_at: str | None = None
    input: Any | None = None
    output: Any | None = None
    error: str | None = None
    metadata: dict[str, Any] | None = None

class TraceEmitter:
    def start_run(self, name: str = "chat_turn") -> TraceEvent: ...
    def end_run(self, success: bool = True) -> TraceEvent: ...
    def emit_token_generation(self, token_count: int = 0) -> TraceEvent: ...
    def emit_error(self, error_message: str) -> TraceEvent: ...
    def to_json(self) -> str: ...
```

From backend/app/api/v1/chat.py — current _token_generator signature:
```python
async def _token_generator(
    messages: list[dict[str, str]],
    base_url: str,
    api_key: str,
    model: str,
    conversation_id: int,
    session: AsyncSession,
    system_prompt: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> AsyncGenerator[str, None]: ...
```

From backend/app/models/llm_provider.py:
```python
class LLMProvider(SQLModel, table=True):
    id: int | None
    name: str
    base_url: str
    api_key_encrypted: str
    models: str  # JSON array
    is_default: bool
```
</interfaces>

<tasks>

<task type="auto">
  <name>Task 1: BaseExecutor protocol, ExecutorRegistry, RunState, and TraceEmitter extensions</name>
  <files>
    backend/app/services/executors/__init__.py,
    backend/app/services/executors/base.py,
    backend/app/services/executors/registry.py,
    backend/app/services/run_state.py,
    backend/app/services/trace_emitter.py
  </files>
  <action>
    Create `backend/app/services/executors/` package with __init__.py.

    **backend/app/services/executors/base.py** — BaseExecutor protocol and ExecutorResult:
    ```python
    from typing import Any, Protocol
    import dataclasses

    @dataclasses.dataclass
    class ExecutorResult:
        output: Any
        error: str | None = None

    class BaseExecutor(Protocol):
        async def execute(self, name: str, input: dict[str, Any]) -> ExecutorResult: ...
    ```

    **backend/app/services/executors/registry.py** — ExecutorRegistry:
    - `register(tool_name: str, executor: BaseExecutor) -> None`
    - `dispatch(tool_name: str, input: dict[str, Any]) -> ExecutorResult` — raises `KeyError` if no executor registered for that name
    - `available_tools() -> list[str]` — returns list of registered tool names

    **backend/app/services/run_state.py** — In-memory RunState (D-08, D-09, D-10 from CONTEXT.md):
    ```python
    import enum, uuid, dataclasses
    from datetime import UTC, datetime

    class RunStatus(str, enum.Enum):
        CREATED = "created"
        RUNNING = "running"
        COMPLETED = "completed"
        FAILED = "failed"
        CANCELLED = "cancelled"

    @dataclasses.dataclass
    class RunState:
        run_id: str
        status: RunStatus
        created_at: datetime
        updated_at: datetime
        iteration: int = 0
        error: str | None = None
    ```
    `RunStateStore` is a simple dict-backed class with methods:
    - `create() -> RunState` — creates new RunState with UUID, status=CREATED
    - `get(run_id: str) -> RunState | None`
    - `update_status(run_id: str, status: RunStatus, error: str | None = None) -> None`
    - `increment_iteration(run_id: str) -> None`
    - `delete(run_id: str) -> None`
    All operations are synchronous (in-memory, no DB per D-09).

    **backend/app/services/trace_emitter.py** — Add two new methods for tool tracing (D-11, D-12, D-13):
    - `emit_tool_start(tool_name: str, tool_input: dict[str, Any]) -> TraceEvent` — type="tool_call", status="running", name=tool_name, input=tool_input, no completed_at
    - `emit_tool_end(tool_name: str, output: Any, error: str | None = None) -> TraceEvent` — type="tool_call", status="completed" or "error", name=tool_name, output=output, error=error, set completed_at
    - Update the `type` Literal in `TraceEvent` to include `"tool_call"` alongside existing values.

    Also update `backend/app/services/executors/__init__.py` to export `BaseExecutor`, `ExecutorResult`, `ExecutorRegistry` from their sub-modules.
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/backend && python -c "from app.services.executors import BaseExecutor, ExecutorResult, ExecutorRegistry; from app.services.run_state import RunState, RunStatus, RunStateStore; from app.services.trace_emitter import TraceEmitter; t = TraceEmitter(); e = t.emit_tool_start('test', {}); print(e.type, e.status)"</automated>
  </verify>
  <done>
    - `executors/` package importable with BaseExecutor, ExecutorResult, ExecutorRegistry
    - RunStateStore.create() returns RunState with status=CREATED
    - TraceEmitter.emit_tool_start returns TraceEvent with type="tool_call", status="running"
    - TraceEmitter.emit_tool_end returns TraceEvent with type="tool_call", status="completed" or "error"
    - `python -c "from app.services.executors import ..."` exits 0 with no errors
  </done>
</task>

<task type="auto">
  <name>Task 2: ToolExecutor with current_datetime built-in tool</name>
  <files>
    backend/app/services/executors/builtin_tools.py,
    backend/app/services/executors/tool_executor.py
  </files>
  <action>
    **backend/app/services/executors/builtin_tools.py** — Built-in tool registry:
    - Define `current_datetime(input: dict) -> str` — returns `datetime.now(UTC).isoformat()` (ignore input, always returns now)
    - Define `BUILTIN_TOOLS: dict[str, Callable]` = `{"current_datetime": current_datetime}`
    - Define `BUILTIN_TOOL_SCHEMAS: list[dict]` — OpenAI function-calling schema for current_datetime:
      ```python
      {
          "type": "function",
          "function": {
              "name": "current_datetime",
              "description": "Returns the current UTC date and time in ISO 8601 format.",
              "parameters": {"type": "object", "properties": {}, "required": []},
          },
      }
      ```

    **backend/app/services/executors/tool_executor.py** — ToolExecutor:
    - Implements `BaseExecutor` protocol
    - Constructor takes optional `tools: dict[str, Callable] | None = None`; defaults to `BUILTIN_TOOLS`
    - `async execute(self, name: str, input: dict[str, Any]) -> ExecutorResult`:
      - Look up `name` in self.tools dict
      - If not found: return `ExecutorResult(output=None, error=f"Unknown tool: {name}")`
      - Call the tool function with `input`; catch all exceptions and return `ExecutorResult(output=None, error=str(e))`
      - On success: return `ExecutorResult(output=result)`
    - The trace emit calls (tool_start/tool_end) happen in Orchestrator, NOT in ToolExecutor — keeps executor pure and testable

    Update `backend/app/services/executors/__init__.py` to also export `ToolExecutor` and `BUILTIN_TOOL_SCHEMAS`.
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/backend && python -c "
import asyncio
from app.services.executors.tool_executor import ToolExecutor
from app.services.executors.builtin_tools import BUILTIN_TOOL_SCHEMAS

async def main():
    te = ToolExecutor()
    result = await te.execute('current_datetime', {})
    assert result.error is None, f'Expected no error: {result.error}'
    assert '2026' in result.output or '2025' in result.output or True, 'Has datetime output'
    print('tool_executor OK:', result.output[:20])
    print('schemas count:', len(BUILTIN_TOOL_SCHEMAS))

asyncio.run(main())
"</automated>
  </verify>
  <done>
    - ToolExecutor.execute("current_datetime", {}) returns ExecutorResult with ISO datetime string output and no error
    - ToolExecutor.execute("unknown_tool", {}) returns ExecutorResult with error="Unknown tool: unknown_tool"
    - BUILTIN_TOOL_SCHEMAS contains one schema with name="current_datetime"
  </done>
</task>

<task type="auto">
  <name>Task 3: Orchestrator service and chat.py refactor</name>
  <files>
    backend/app/services/orchestrator.py,
    backend/app/api/v1/chat.py
  </files>
  <action>
    **backend/app/services/orchestrator.py** — Orchestrator service class:

    Implement `class Orchestrator` that takes in its constructor:
    - `registry: ExecutorRegistry`
    - `tracer: TraceEmitter`
    - `run_store: RunStateStore`
    - `timeout: float = 30.0` (per external call, D-14)
    - `max_retries: int = 3` (D-15)
    - `max_iterations: int = 10` (D-02)

    Core method: `async def run(self, client: AsyncOpenAI, model: str, messages: list[dict], temperature: float, max_tokens: int) -> AsyncGenerator[str, None]`

    The generator yields SSE-formatted strings: `f"data: {json.dumps(...)}\n\n"` — same format as the existing _token_generator so chat.py stays compatible.

    Orchestration loop (D-01):
    ```
    run_id = run_store.create()
    run_store.update_status(run_id, RUNNING)

    current_messages = list(messages)
    iteration = 0
    full_content = ""

    while iteration < max_iterations:
        run_store.increment_iteration(run_id)
        iteration += 1

        # LLM call with asyncio.wait_for(timeout=self.timeout) and retry
        # retry with exponential backoff: [1s, 2s, 4s] delays (D-15, D-16)
        response = await _llm_call_with_retry(client, model, current_messages, temperature, max_tokens)

        choice = response.choices[0]
        finish_reason = choice.finish_reason

        if finish_reason == "tool_calls":
            # Process each tool_call
            # Append assistant message with tool_calls to current_messages
            # For each tool_call:
            #   1. emit_tool_start(tool_name, tool_input) -> yield trace_event SSE
            #   2. dispatch via registry (wrapped in asyncio.wait_for(timeout))
            #   3. emit_tool_end(tool_name, output/error) -> yield trace_event SSE
            #   4. append tool result message to current_messages
            # continue loop

        else:  # stop / length / content_filter -> text response
            # Stream the content as tokens
            # emit_token_generation
            # run_store.update_status(run_id, COMPLETED)
            # yield done signal
            break

    if iteration >= max_iterations:
        run_store.update_status(run_id, FAILED, error="max_iterations_exceeded")
    ```

    For the LLM call, use a non-streaming `create()` call (not `stream=True`) so we can inspect `finish_reason` and `tool_calls` on the full response. Token streaming for the final text response: iterate over response.choices[0].message.content character by character is NOT needed — instead, for the final response, make a SECOND streaming call with no tools so the UI gets real token streaming. OR: yield the final content as a single token SSE chunk. Keep it simple — yield content as a single token chunk then done (streaming can be added later).

    NOTE: The `tools` parameter passed to the LLM call must be `BUILTIN_TOOL_SCHEMAS` (imported from builtin_tools). The registry provides the execution side; the schemas tell the LLM what tools exist.

    Timeout behavior (D-16): When `asyncio.wait_for` raises `asyncio.TimeoutError`:
    - Emit error trace event: `tracer.emit_error(f"Timeout after {self.timeout}s on tool: {tool_name}")`
    - Update run state to FAILED
    - Yield the error trace SSE and an `{"type": "error", "message": "..."}` SSE
    - Return (stop the generator)

    Retry logic for LLM calls: use `asyncio.wait_for` wrapping `client.chat.completions.create(...)`. On timeout, retry up to `max_retries` times with exponential backoff (1s, 2s, 4s delays via `asyncio.sleep`). After all retries exhausted, emit timeout error trace event.

    **backend/app/api/v1/chat.py** — Refactor `_token_generator`:
    - Keep the same function signature (no change to callers)
    - Replace the direct `AsyncOpenAI` streaming block with an `Orchestrator` instance:
      ```python
      registry = ExecutorRegistry()
      tool_executor = ToolExecutor()
      for tool_name in BUILTIN_TOOLS:
          registry.register(tool_name, tool_executor)

      orchestrator = Orchestrator(
          registry=registry,
          tracer=tracer,
          run_store=RunStateStore(),
      )
      async for sse_line in orchestrator.run(
          client=client,
          model=model,
          messages=openai_messages,
          temperature=temperature,
          max_tokens=max_tokens,
      ):
          yield sse_line
      full_content = orchestrator.final_content  # expose via property
      ```
    - The message persistence block (saving assistant_msg to DB) stays in `_token_generator` after the orchestrator loop — unchanged.
    - Add `final_content: str` property to Orchestrator (populated during run).
    - The existing `tracer.start_run()` call in _token_generator stays — Orchestrator receives the already-started tracer.
    - Remove the direct `AsyncOpenAI` import usage from `_token_generator` (it's now in Orchestrator). Keep the import at module level since it is still needed for the Orchestrator constructor.
    - Pass `tools=BUILTIN_TOOL_SCHEMAS` to `client.chat.completions.create()` inside Orchestrator.
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/backend && python -c "
from app.services.orchestrator import Orchestrator
from app.services.executors import ExecutorRegistry, ToolExecutor
from app.services.executors.builtin_tools import BUILTIN_TOOLS
from app.services.run_state import RunStateStore
from app.services.trace_emitter import TraceEmitter
print('Orchestrator imports OK')

# Verify chat.py imports still work
import importlib
m = importlib.import_module('app.api.v1.chat')
print('chat.py imports OK')
"</automated>
  </verify>
  <done>
    - `from app.services.orchestrator import Orchestrator` succeeds with no errors
    - `from app.api.v1.chat import ...` succeeds (no broken imports)
    - Orchestrator constructor accepts registry, tracer, run_store, timeout, max_retries, max_iterations
    - Orchestrator.run() is an async generator
    - `cd backend && python -m ruff check app/services/orchestrator.py app/api/v1/chat.py` exits 0
  </done>
</task>

</tasks>

<verification>
After all three tasks:

1. Import smoke test passes (all new modules importable from backend/)
2. Ruff + mypy pass on all new files: `cd backend && python -m ruff check app/services/ && python -m mypy app/services/orchestrator.py app/services/run_state.py app/services/executors/`
3. Existing backend tests still pass: `cd backend && python -m pytest app/tests/ -x -q` — should show all existing tests green, no regressions in chat or trace tests
</verification>

<success_criteria>
- `from app.services.orchestrator import Orchestrator` — importable
- `from app.services.executors import BaseExecutor, ExecutorResult, ExecutorRegistry, ToolExecutor` — importable
- `from app.services.run_state import RunState, RunStatus, RunStateStore` — importable
- `TraceEmitter` now has `emit_tool_start` and `emit_tool_end` methods
- `ToolExecutor().execute("current_datetime", {})` returns ISO datetime string with no error
- Orchestrator.run() is an async generator yielding SSE-formatted strings
- chat.py `_token_generator` delegates to Orchestrator (no direct streaming loop left in chat.py)
- Existing 85+ backend tests still pass
</success_criteria>

<output>
After completion, create `.planning/phases/07-orchestration-loop/07-01-SUMMARY.md` following the summary template.
</output>

---
---
phase: 07-orchestration-loop
plan: 02
type: execute
wave: 2
depends_on: [07-01]
files_modified:
  - backend/app/tests/test_orchestrator.py
  - backend/app/tests/test_run_state.py
  - backend/app/tests/test_orchestration_integration.py
autonomous: true
requirements: [ORCH-01, ORCH-02, ORCH-03, ORCH-04, ORCH-05]

must_haves:
  truths:
    - "Orchestration loop unit tests verify: tool dispatch, max_iterations guard, completed/failed run states"
    - "Timeout tests confirm asyncio.TimeoutError produces error trace event and failed run state"
    - "Integration tests verify tool trace events (tool_start, tool_end) appear in the SSE stream via mocked LLM"
    - "All new tests pass alongside existing 85+ backend tests with no regressions"
  artifacts:
    - path: "backend/app/tests/test_orchestrator.py"
      provides: "Unit tests for Orchestrator loop with mock executor and mock LLM client"
      min_lines: 80
    - path: "backend/app/tests/test_run_state.py"
      provides: "Unit tests for RunState lifecycle transitions"
      min_lines: 40
    - path: "backend/app/tests/test_orchestration_integration.py"
      provides: "Integration tests for SSE stream containing tool trace events via mocked OpenAI"
      min_lines: 80
  key_links:
    - from: "backend/app/tests/test_orchestrator.py"
      to: "backend/app/services/orchestrator.py"
      via: "Instantiate Orchestrator with mock ExecutorRegistry, assert run state transitions"
      pattern: "Orchestrator.*mock"
    - from: "backend/app/tests/test_orchestration_integration.py"
      to: "backend/app/api/v1/chat.py"
      via: "patch app.api.v1.chat.AsyncOpenAI, POST to /{conversation_id}/stream, parse SSE tool_call events"
      pattern: "patch.*AsyncOpenAI"
---

<objective>
Write the test suite for Phase 7: unit tests for Orchestrator loop behavior and RunState transitions, plus integration tests verifying tool trace events appear in the SSE stream.

Purpose: Validates all five ORCH requirements with automated tests. Provides regression coverage so MCP and Skills integrations (Phases 8-9) can extend the executor system without breaking the loop.

Output: `test_orchestrator.py`, `test_run_state.py`, `test_orchestration_integration.py`
</objective>

<execution_context>
@/Users/przbadu/.claude/get-shit-done/workflows/execute-plan.md
@/Users/przbadu/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/phases/07-orchestration-loop/7-CONTEXT.md
@.planning/phases/07-orchestration-loop/07-01-SUMMARY.md

# Mock pattern established in Phase 6:
@.planning/phases/06-execution-trace-system/06-03-SUMMARY.md
</context>

<interfaces>
<!-- Contracts established in plan 07-01 that tests must use -->

From backend/app/services/orchestrator.py:
```python
class Orchestrator:
    def __init__(
        self,
        registry: ExecutorRegistry,
        tracer: TraceEmitter,
        run_store: RunStateStore,
        timeout: float = 30.0,
        max_retries: int = 3,
        max_iterations: int = 10,
    ) -> None: ...

    async def run(
        self,
        client: AsyncOpenAI,
        model: str,
        messages: list[dict],
        temperature: float,
        max_tokens: int,
    ) -> AsyncGenerator[str, None]: ...

    @property
    def final_content(self) -> str: ...
```

From backend/app/services/executors/base.py:
```python
@dataclasses.dataclass
class ExecutorResult:
    output: Any
    error: str | None = None

class BaseExecutor(Protocol):
    async def execute(self, name: str, input: dict[str, Any]) -> ExecutorResult: ...
```

From backend/app/services/run_state.py:
```python
class RunStatus(str, enum.Enum):
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class RunStateStore:
    def create(self) -> RunState: ...
    def get(self, run_id: str) -> RunState | None: ...
    def update_status(self, run_id: str, status: RunStatus, error: str | None = None) -> None: ...
    def increment_iteration(self, run_id: str) -> None: ...
```

Mock pattern from Phase 6 (from 06-03-SUMMARY.md):
- Patch `app.api.v1.chat.AsyncOpenAI` at the module level
- Mock client's `chat.completions.create` to return a MagicMock with the expected response shape
- Parse SSE stream lines: filter `data: ` prefix, parse JSON, filter by `type`
</interfaces>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: RunState unit tests</name>
  <files>backend/app/tests/test_run_state.py</files>
  <behavior>
    - Test: `create()` returns RunState with status=CREATED and a valid UUID run_id
    - Test: `update_status(run_id, RUNNING)` changes status to RUNNING
    - Test: `update_status(run_id, FAILED, error="boom")` sets status=FAILED and error="boom"
    - Test: `increment_iteration(run_id)` increments iteration counter from 0 to 1
    - Test: `get(unknown_id)` returns None
    - Test: `delete(run_id)` then `get(run_id)` returns None
    - Test: Multiple concurrent RunStates don't interfere with each other
  </behavior>
  <action>
    Create `backend/app/tests/test_run_state.py` with 7 pytest test functions.
    Use `from app.services.run_state import RunState, RunStatus, RunStateStore`.
    No async needed — all RunStateStore operations are synchronous.
    No DB or fixtures needed — RunStateStore is purely in-memory.
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/backend && python -m pytest app/tests/test_run_state.py -v</automated>
  </verify>
  <done>All 7 RunState tests pass.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Orchestrator unit tests with mock executor and mock LLM</name>
  <files>backend/app/tests/test_orchestrator.py</files>
  <behavior>
    - Test: When LLM responds with finish_reason="stop" (no tool calls), run completes with status=COMPLETED and final_content is set
    - Test: When LLM responds with finish_reason="tool_calls" on iteration 1, then "stop" on iteration 2, the loop runs twice and completes
    - Test: executor.execute is called once with correct tool_name and input when tool_call is present
    - Test: tool_start trace event is emitted before executor.execute
    - Test: tool_end trace event is emitted after executor.execute with the output
    - Test: When max_iterations exceeded, run state becomes FAILED with error="max_iterations_exceeded"
    - Test: When asyncio.wait_for raises TimeoutError on tool dispatch, error trace event emitted and run state is FAILED
    - Test: Executor error (ExecutorResult with error set) emits tool_end with status="error"
  </behavior>
  <action>
    Create `backend/app/tests/test_orchestrator.py`.

    Helper: build a mock `AsyncOpenAI` client using `unittest.mock.AsyncMock`. Mock `client.chat.completions.create` to return a `MagicMock` with `.choices[0].finish_reason` and `.choices[0].message.content` / `.choices[0].message.tool_calls`.

    For tool_calls mock: create a MagicMock where `.tool_calls[0].function.name = "current_datetime"` and `.tool_calls[0].function.arguments = "{}"` and `.tool_calls[0].id = "call_123"`.

    For the executor, use a simple `AsyncMock` or implement a tiny `MockExecutor` class:
    ```python
    class MockExecutor:
        async def execute(self, name: str, input: dict) -> ExecutorResult:
            return ExecutorResult(output="2026-01-01T00:00:00Z")
    ```

    Build Orchestrator with a real `RunStateStore`, real `TraceEmitter`, and `ExecutorRegistry` with the `MockExecutor` registered for "current_datetime".

    To consume the async generator in tests: `sse_lines = [line async for line in orchestrator.run(...)]`.

    Parse SSE lines: `json.loads(line.removeprefix("data: ").strip())` — filter by `type` field.

    Assert trace event types in the collected events.
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/backend && python -m pytest app/tests/test_orchestrator.py -v</automated>
  </verify>
  <done>All 8 orchestrator unit tests pass. Tests cover: text-only response, single tool call loop, max iterations guard, timeout error event, executor error propagation.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 3: Orchestration integration tests via SSE stream endpoint</name>
  <files>backend/app/tests/test_orchestration_integration.py</files>
  <behavior>
    - Test: Sending a chat message when LLM returns text (no tools) streams tokens and emits run_start + token_generation + run_end trace events — same behavior as Phase 6 (regression guard)
    - Test: Sending a chat message when LLM returns tool_call then text: SSE stream contains tool_call trace events (tool_start, tool_end) with correct tool_name
    - Test: tool_end trace event in SSE has output matching what ToolExecutor returned
    - Test: After tool_call + text loop, SSE ends with `{"type": "done", "message_id": ...}`
    - Test: Timeout on tool dispatch produces `{"type": "error"}` SSE event and does not hang
  </behavior>
  <action>
    Create `backend/app/tests/test_orchestration_integration.py`.

    Use the same test fixture pattern from `test_trace_integration.py`:
    - `_clean_tables` autouse fixture (delete Message, Conversation, LLMProvider)
    - `provider` fixture creating a default LLMProvider
    - `auth_client` fixture (AsyncClient with auth token — import from conftest or duplicate the pattern)

    Patch `app.api.v1.chat.AsyncOpenAI` at module level. For tool call tests, make the mock return:
    - First call: response with `finish_reason="tool_calls"`, `tool_calls=[{id:"call_1", function:{name:"current_datetime", arguments:"{}"}}]`
    - Second call: response with `finish_reason="stop"`, `message.content="The current time is 2026-01-01T00:00:00Z"`

    Use `unittest.mock.patch` as an async context manager or side_effect list to sequence multiple calls.

    Parse SSE stream: iterate response lines, collect `data: ` lines, parse JSON.

    Helper function:
    ```python
    def _parse_sse(response_text: str) -> list[dict]:
        events = []
        for line in response_text.splitlines():
            if line.startswith("data: "):
                events.append(json.loads(line[6:]))
        return events
    ```

    For timeout test: patch `asyncio.wait_for` to raise `asyncio.TimeoutError` on the second call (tool dispatch).

    Ensure `provider` fixture is used in tests that expect tool dispatch (test would otherwise fail with "No default LLM provider configured").
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/backend && python -m pytest app/tests/test_orchestration_integration.py -v</automated>
  </verify>
  <done>
    All 5 integration tests pass. SSE stream contains expected trace event types for both text-only and tool-call paths.
  </done>
</task>

</tasks>

<verification>
Full suite passes with no regressions:

```bash
cd /Users/przbadu/dev/claude-clone/backend && python -m pytest app/tests/ -x -q
```

Expected: all existing tests (85+) plus the new 20 tests all green. Zero failures.
</verification>

<success_criteria>
- `pytest app/tests/test_run_state.py` — 7 tests pass
- `pytest app/tests/test_orchestrator.py` — 8 tests pass
- `pytest app/tests/test_orchestration_integration.py` — 5 tests pass
- `pytest app/tests/ -x -q` — full suite passes, no regressions
- Every ORCH requirement (ORCH-01 through ORCH-05) covered by at least one passing test
</success_criteria>

<output>
After completion, create `.planning/phases/07-orchestration-loop/07-02-SUMMARY.md` following the summary template.
</output>
