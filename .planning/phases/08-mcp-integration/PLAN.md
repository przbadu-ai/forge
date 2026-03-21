---
phase: 08-mcp-integration
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - backend/app/models/mcp_server.py
  - backend/alembic/versions/0007_add_mcp_server_table.py
  - backend/app/api/v1/settings/mcp_servers.py
  - backend/app/api/v1/settings/__init__.py
  - backend/app/api/v1/router.py
  - backend/app/services/mcp_process_manager.py
  - backend/app/services/executors/mcp_executor.py
  - backend/app/services/executors/__init__.py
  - backend/app/main.py
  - backend/pyproject.toml
autonomous: true
requirements:
  - MCP-01
  - MCP-02
  - MCP-03
  - MCP-04
  - MCP-05

must_haves:
  truths:
    - "MCP server records can be created, listed, updated, and deleted via API"
    - "Enabling/disabling an MCP server persists in DB and controls invocation"
    - "McpProcessManager starts an MCP subprocess on-demand and shuts it down cleanly"
    - "McpExecutor discovers tools from a running MCP server and registers them in ExecutorRegistry"
    - "MCP tool calls emit mcp_tool_start and mcp_tool_end trace events with full metadata"
    - "MCP timeout or subprocess failure produces an error ExecutorResult (no crash)"
  artifacts:
    - path: "backend/app/models/mcp_server.py"
      provides: "McpServer SQLModel with id, name, command, args, env_vars, is_enabled, created_at"
      exports: ["McpServer"]
    - path: "backend/alembic/versions/0007_add_mcp_server_table.py"
      provides: "Alembic migration for mcp_server table"
    - path: "backend/app/api/v1/settings/mcp_servers.py"
      provides: "CRUD endpoints at /api/v1/settings/mcp-servers"
      exports: ["router"]
    - path: "backend/app/services/mcp_process_manager.py"
      provides: "McpProcessManager: start, stop, is_running, cleanup_orphans"
      exports: ["McpProcessManager"]
    - path: "backend/app/services/executors/mcp_executor.py"
      provides: "McpExecutor implementing BaseExecutor, tool discovery, trace emission"
      exports: ["McpExecutor"]
  key_links:
    - from: "backend/app/services/executors/mcp_executor.py"
      to: "backend/app/services/mcp_process_manager.py"
      via: "McpExecutor holds McpProcessManager reference, calls start() before tool invocation"
      pattern: "self\\.process_manager\\.start"
    - from: "backend/app/main.py"
      to: "backend/app/services/mcp_process_manager.py"
      via: "startup event: cleanup_orphans(); shutdown event: stop all servers"
      pattern: "cleanup_orphans"
    - from: "backend/app/api/v1/settings/mcp_servers.py"
      to: "backend/app/models/mcp_server.py"
      via: "CRUD endpoints query McpServer model via SQLAlchemy async session"
      pattern: "McpServer"
---

<objective>
Build the complete MCP backend: McpServer model + CRUD API, McpProcessManager (subprocess lifecycle), and McpExecutor (MCP SDK client, tool discovery, tool invocation with trace events).

Purpose: Establishes the data model, API surface, and runtime services for MCP integration. After this plan, the orchestrator can invoke MCP tools automatically — no orchestrator code changes required because McpExecutor registers tools in the existing ExecutorRegistry.

Output: McpServer DB table + CRUD endpoints, McpProcessManager service, McpExecutor registered via startup hook, `mcp` package installed.
</objective>

<execution_context>
@/Users/przbadu/.claude/get-shit-done/workflows/execute-plan.md
@/Users/przbadu/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/phases/08-mcp-integration/8-CONTEXT.md

<interfaces>
<!-- Key contracts the executor needs. Do not re-explore these files. -->

From backend/app/services/executors/base.py:
```python
@dataclasses.dataclass
class ExecutorResult:
    output: Any
    error: str | None = None

class BaseExecutor(Protocol):
    async def execute(self, name: str, input: dict[str, Any]) -> ExecutorResult: ...
```

From backend/app/services/executors/registry.py:
```python
class ExecutorRegistry:
    def register(self, tool_name: str, executor: BaseExecutor) -> None: ...
    async def dispatch(self, tool_name: str, input: dict[str, Any]) -> ExecutorResult: ...
    def available_tools(self) -> list[str]: ...
```

From backend/app/services/trace_emitter.py:
```python
# TraceEvent type field uses: "run_start"|"run_end"|"token_generation"|"error"|"tool_call"
# For MCP calls, use type="tool_call" with metadata={"server_name": ..., "tool_name": ...}
def emit_tool_start(self, tool_name: str, tool_input: dict[str, Any]) -> TraceEvent: ...
def emit_tool_end(self, tool_name: str, output: Any, error: str | None = None) -> TraceEvent: ...
```

From backend/app/models/llm_provider.py (pattern to follow):
```python
class LLMProvider(SQLModel, table=True):
    __tablename__ = "llm_provider"
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True, max_length=100)
    # JSON fields stored as text
    models: str = Field(default="[]")  # JSON array as text
    is_default: bool = Field(default=False)
    created_at: datetime = Field(default_factory=_utcnow)
```

From backend/alembic/versions/0006_add_trace_data_to_message.py (migration pattern):
```python
revision = "0007_add_mcp_server_table"
down_revision = "0006_add_trace_data_to_message"
# Use op.batch_alter_table for SQLite compatibility
```
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: McpServer model, Alembic migration, and CRUD API endpoints</name>
  <files>
    backend/app/models/mcp_server.py,
    backend/alembic/versions/0007_add_mcp_server_table.py,
    backend/app/api/v1/settings/mcp_servers.py,
    backend/app/api/v1/settings/__init__.py,
    backend/app/models/__init__.py
  </files>
  <action>
**1. Install `mcp` package:**
```bash
cd backend && uv add mcp
```

**2. Create `backend/app/models/mcp_server.py`:**
```python
from datetime import UTC, datetime
from sqlmodel import Field, SQLModel

def _utcnow() -> datetime:
    return datetime.now(UTC)

class McpServer(SQLModel, table=True):
    __tablename__ = "mcp_server"
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True, max_length=100)
    command: str = Field(max_length=500)          # e.g. "uvx" or "/usr/local/bin/mcp-server"
    args: str = Field(default="[]")               # JSON array: ["--flag", "value"]
    env_vars: str = Field(default="{}")           # JSON object: {"KEY": "VALUE"}
    is_enabled: bool = Field(default=True)
    created_at: datetime = Field(default_factory=_utcnow)
```

Add `McpServer` to `backend/app/models/__init__.py` imports so Alembic autogenerate detects it.

**3. Create Alembic migration `backend/alembic/versions/0007_add_mcp_server_table.py`:**
- `revision = "0007_add_mcp_server_table"`
- `down_revision = "0006_add_trace_data_to_message"`
- Use `op.create_table("mcp_server", ...)` with columns matching the model
- Include `op.drop_table("mcp_server")` in `downgrade()`
- Do NOT use batch_alter_table for create_table; that pattern is only for ALTER operations

**4. Create `backend/app/api/v1/settings/mcp_servers.py`:**

Schemas:
- `McpServerCreate`: name (str), command (str), args (list[str] = []), env_vars (dict[str,str] = {}), is_enabled (bool = True)
- `McpServerUpdate`: all fields optional
- `McpServerRead`: id (int), name, command, args (list[str]), env_vars (dict[str,str]), is_enabled, created_at

Endpoints (all require `get_current_user`):
- `GET /` — list all MCP servers
- `POST /` — create, returns 201; raise 409 on duplicate name
- `PUT /{server_id}` — partial update, raise 404 if not found
- `DELETE /{server_id}` — delete, returns 204, raise 404 if not found
- `PATCH /{server_id}/toggle` — flip `is_enabled`, returns `McpServerRead`

Helper `_to_read(server: McpServer) -> McpServerRead`: parse `args` with `json.loads`, parse `env_vars` with `json.loads`.

**5. Register in `backend/app/api/v1/settings/__init__.py`:**
Import and include the new router at prefix `/mcp-servers`, tag `mcp-servers`.
Also verify the settings router is included in `backend/app/api/v1/router.py` at prefix `/settings` (it should be from Phase 3 — do not break existing).
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/backend && uv run alembic upgrade head && uv run python -c "from app.models.mcp_server import McpServer; print('McpServer OK')" && uv run pytest tests/ -k "mcp_server" -x --tb=short 2>/dev/null || echo "no mcp tests yet - model import OK"</automated>
  </verify>
  <done>
    - `uv run alembic upgrade head` completes without error (mcp_server table created)
    - `GET /api/v1/settings/mcp-servers` returns 200 with empty list
    - `POST /api/v1/settings/mcp-servers` creates a record and returns 201
    - `PATCH /api/v1/settings/mcp-servers/{id}/toggle` flips is_enabled
    - `DELETE /api/v1/settings/mcp-servers/{id}` returns 204
  </done>
</task>

<task type="auto">
  <name>Task 2: McpProcessManager and McpExecutor with trace integration</name>
  <files>
    backend/app/services/mcp_process_manager.py,
    backend/app/services/executors/mcp_executor.py,
    backend/app/main.py
  </files>
  <action>
**1. Create `backend/app/services/mcp_process_manager.py`:**

```python
"""McpProcessManager — on-demand subprocess lifecycle for MCP servers."""
import asyncio
import json
import logging
import os
import signal

logger = logging.getLogger(__name__)

class McpProcessManager:
    """Manages MCP server subprocesses. Start on-demand, shut down cleanly."""

    def __init__(self) -> None:
        # server_id -> asyncio.subprocess.Process
        self._processes: dict[int, asyncio.subprocess.Process] = {}

    async def start(self, server_id: int, command: str, args: list[str],
                    env_vars: dict[str, str]) -> None:
        """Start an MCP server subprocess if not already running."""
        if self.is_running(server_id):
            return
        env = {**os.environ, **env_vars}
        proc = await asyncio.create_subprocess_exec(
            command, *args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        self._processes[server_id] = proc
        logger.info("Started MCP server %s (pid=%s)", server_id, proc.pid)

    async def stop(self, server_id: int) -> None:
        """Stop a running MCP server: close stdin -> SIGTERM -> SIGKILL after 5s."""
        proc = self._processes.pop(server_id, None)
        if proc is None or proc.returncode is not None:
            return
        try:
            if proc.stdin:
                proc.stdin.close()
            proc.terminate()  # SIGTERM
            try:
                await asyncio.wait_for(proc.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                proc.kill()  # SIGKILL
                await proc.wait()
        except ProcessLookupError:
            pass
        logger.info("Stopped MCP server %s", server_id)

    def is_running(self, server_id: int) -> bool:
        proc = self._processes.get(server_id)
        return proc is not None and proc.returncode is None

    async def stop_all(self) -> None:
        """Stop all running MCP servers (called on app shutdown)."""
        for server_id in list(self._processes):
            await self.stop(server_id)

    async def cleanup_orphans(self) -> None:
        """No-op on startup — processes dict is empty at cold start.
        Implement PGID-based cleanup here if needed in future."""
        pass
```

**2. Create `backend/app/services/executors/mcp_executor.py`:**

McpExecutor uses the `mcp` Python SDK (`from mcp import ClientSession`, `from mcp.client.stdio import stdio_client`). It wraps one MCP server and implements BaseExecutor.

```python
"""McpExecutor — BaseExecutor implementation backed by an MCP server subprocess."""
import asyncio
import json
import logging
from typing import Any

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

from app.models.mcp_server import McpServer
from app.services.executors.base import BaseExecutor, ExecutorResult
from app.services.mcp_process_manager import McpProcessManager
from app.services.trace_emitter import TraceEmitter

logger = logging.getLogger(__name__)


class McpExecutor:
    """Executes a named MCP tool on a specific MCP server subprocess.

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

        args_list: list[str] = json.loads(self.server.args)
        env_vars: dict[str, str] = json.loads(self.server.env_vars)

        start_event = self.tracer.emit_tool_start(name, input)

        try:
            params = StdioServerParameters(
                command=self.server.command,
                args=args_list,
                env=env_vars if env_vars else None,
            )
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await asyncio.wait_for(session.initialize(), timeout=self.timeout)
                    result = await asyncio.wait_for(
                        session.call_tool(tool_name, arguments=input),
                        timeout=self.timeout,
                    )

            # Extract text content from result
            output: Any = None
            if result.content:
                texts = [c.text for c in result.content if hasattr(c, "text")]
                output = "\n".join(texts) if texts else str(result.content)

            end_event = self.tracer.emit_tool_end(name, output)
            return ExecutorResult(output=output)

        except asyncio.TimeoutError:
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
) -> None:
    """Query each enabled MCP server for its tools and register them in the registry.

    Tool names are namespaced as "{server_name}.{tool_name}".
    Called at chat-turn start so tools are fresh. Failures are logged, not raised.
    """
    for server in servers:
        if not server.is_enabled:
            continue
        try:
            args_list: list[str] = json.loads(server.args)
            env_vars: dict[str, str] = json.loads(server.env_vars)
            params = StdioServerParameters(
                command=server.command,
                args=args_list,
                env=env_vars if env_vars else None,
            )
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as session:
                    await asyncio.wait_for(session.initialize(), timeout=timeout)
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
        except Exception:
            logger.exception("Failed to discover tools from MCP server: %s", server.name)
```

Note: `McpExecutor` implements the `BaseExecutor` protocol structurally (has `async def execute(name, input) -> ExecutorResult`). No explicit inheritance needed — Python structural typing via Protocol.

**3. Update `backend/app/main.py`:**

Add a module-level `mcp_process_manager = McpProcessManager()` singleton.

In the `lifespan` context manager (or startup/shutdown events):
- Startup: `await mcp_process_manager.cleanup_orphans()`
- Shutdown: `await mcp_process_manager.stop_all()`

Export `mcp_process_manager` so it can be imported by the chat endpoint to pass into `discover_and_register_mcp_tools` at turn start.

The discovery function is called per-chat-turn (in `backend/app/api/v1/chat.py`) — not at app startup — because tools change as servers are enabled/disabled. In `chat.py` (the SSE endpoint), before constructing the Orchestrator, fetch enabled McpServers from DB and call `discover_and_register_mcp_tools(servers, registry, mcp_process_manager, tracer)`. The `TraceEmitter` instance is created fresh per chat turn already.
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/backend && uv run python -c "
from app.services.mcp_process_manager import McpProcessManager
from app.services.executors.mcp_executor import McpExecutor, discover_and_register_mcp_tools
print('McpProcessManager import OK')
print('McpExecutor import OK')
print('discover_and_register_mcp_tools import OK')
"</automated>
  </verify>
  <done>
    - `McpProcessManager` imports cleanly with no errors
    - `McpExecutor` imports cleanly (mcp package available)
    - `discover_and_register_mcp_tools` is importable
    - `backend/app/main.py` has `mcp_process_manager` singleton with cleanup_orphans on startup and stop_all on shutdown
    - `backend/app/api/v1/chat.py` calls `discover_and_register_mcp_tools` before building Orchestrator so MCP tools appear in registry
  </done>
</task>

<task type="auto">
  <name>Task 3: Backend MCP tests (CRUD, process lifecycle, executor error paths)</name>
  <files>
    backend/tests/test_mcp_server_api.py,
    backend/tests/test_mcp_executor.py
  </files>
  <action>
**1. Create `backend/tests/test_mcp_server_api.py`:**

Use the existing pytest + httpx async client pattern. Test:
- `POST /api/v1/settings/mcp-servers` — creates record, returns 201 with correct fields
- `GET /api/v1/settings/mcp-servers` — returns list containing created server
- `PUT /api/v1/settings/mcp-servers/{id}` — updates name/command
- `PATCH /api/v1/settings/mcp-servers/{id}/toggle` — flips is_enabled
- `DELETE /api/v1/settings/mcp-servers/{id}` — returns 204, subsequent GET returns 404 (or empty list)
- `POST /api/v1/settings/mcp-servers` with duplicate name — returns 409

Look at existing test files (e.g. `backend/tests/`) for the auth token fixture and async client setup pattern before writing these tests.

**2. Create `backend/tests/test_mcp_executor.py`:**

Test `McpExecutor.execute()` in isolation using `unittest.mock.AsyncMock`. Do NOT start real MCP subprocesses.

Mock `stdio_client` and `ClientSession`:
- Happy path: `session.call_tool` returns a result with `.content = [Mock(text="result text")]` — verify `ExecutorResult(output="result text", error=None)` returned and `tracer.emit_tool_end` called with no error
- Timeout path: `session.call_tool` raises `asyncio.TimeoutError` — verify `ExecutorResult(error=...)` returned and `tracer.emit_tool_end` called with error string containing "timed out"
- Exception path: `session.call_tool` raises `RuntimeError("connection refused")` — verify `ExecutorResult(error=...)` and trace error emitted

Use `unittest.mock.patch("app.services.executors.mcp_executor.stdio_client")` to mock at the module level.

Create a minimal `McpServer` object using `McpServer(id=1, name="test", command="echo", args="[]", env_vars="{}", is_enabled=True)` — no DB needed for unit tests.
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/backend && uv run pytest tests/test_mcp_server_api.py tests/test_mcp_executor.py -v --tb=short</automated>
  </verify>
  <done>
    - All MCP API CRUD tests pass (create, list, update, toggle, delete, 409 on duplicate)
    - All McpExecutor unit tests pass (happy path, timeout, exception)
    - `uv run pytest tests/test_mcp_server_api.py tests/test_mcp_executor.py` exits 0
  </done>
</task>

</tasks>

<verification>
After completing all three tasks:

```bash
cd /Users/przbadu/dev/claude-clone/backend

# 1. Migrations clean
uv run alembic upgrade head

# 2. Imports all healthy
uv run python -c "
from app.models.mcp_server import McpServer
from app.services.mcp_process_manager import McpProcessManager
from app.services.executors.mcp_executor import McpExecutor
from app.api.v1.settings.mcp_servers import router
print('All Wave 1 imports OK')
"

# 3. Tests pass
uv run pytest tests/test_mcp_server_api.py tests/test_mcp_executor.py -v
```
</verification>

<success_criteria>
- `alembic upgrade head` succeeds with mcp_server table present
- `GET /api/v1/settings/mcp-servers` returns 200 (requires auth)
- McpServer CRUD endpoints (create/list/update/toggle/delete) all work correctly
- McpProcessManager starts, tracks, and stops subprocesses cleanly
- McpExecutor implements BaseExecutor protocol and handles timeout/error without crashing
- `discover_and_register_mcp_tools` called at chat-turn start wires MCP tools into ExecutorRegistry
- MCP tool calls flow through the existing Orchestrator dispatch loop unchanged
- All backend tests pass: `uv run pytest tests/test_mcp_server_api.py tests/test_mcp_executor.py`
</success_criteria>

<output>
After completion, create `.planning/phases/08-mcp-integration/08-01-SUMMARY.md` with:
- What was built (McpServer model, CRUD API, McpProcessManager, McpExecutor, tests)
- Migration revision ID
- Tool namespacing scheme used (server_name.tool_name)
- Any deviations from this plan and why
- Files created/modified
</output>

---
phase: 08-mcp-integration
plan: 02
type: execute
wave: 2
depends_on:
  - 08-01
files_modified:
  - frontend/src/lib/mcp-api.ts
  - frontend/src/components/settings/mcp-servers-section.tsx
  - frontend/src/components/settings/mcp-server-card.tsx
  - frontend/src/components/settings/mcp-server-form.tsx
  - frontend/src/app/(protected)/settings/page.tsx
autonomous: true
requirements:
  - MCP-01
  - MCP-02

must_haves:
  truths:
    - "Settings page has an MCP Servers tab"
    - "User can add a new MCP server via a form (name, command, args, env vars)"
    - "Each server card shows name, command, enabled/disabled status"
    - "User can toggle a server on/off from its card"
    - "User can edit or delete a server from its card"
    - "Form validates that name and command are non-empty before submitting"
  artifacts:
    - path: "frontend/src/lib/mcp-api.ts"
      provides: "Typed API client for /api/v1/settings/mcp-servers CRUD + toggle"
      exports: ["listMcpServers", "createMcpServer", "updateMcpServer", "deleteMcpServer", "toggleMcpServer", "McpServerRead", "McpServerCreate"]
    - path: "frontend/src/components/settings/mcp-servers-section.tsx"
      provides: "Main section component with query/mutation wiring"
    - path: "frontend/src/components/settings/mcp-server-card.tsx"
      provides: "Card showing server details with toggle, edit, delete"
    - path: "frontend/src/components/settings/mcp-server-form.tsx"
      provides: "Add/edit form for MCP server fields"
    - path: "frontend/src/app/(protected)/settings/page.tsx"
      provides: "Settings page with MCP Servers tab added"
  key_links:
    - from: "frontend/src/components/settings/mcp-servers-section.tsx"
      to: "frontend/src/lib/mcp-api.ts"
      via: "useQuery + useMutation wiring for CRUD operations"
      pattern: "useQuery.*mcp-servers"
    - from: "frontend/src/app/(protected)/settings/page.tsx"
      to: "frontend/src/components/settings/mcp-servers-section.tsx"
      via: "TabsContent value=mcp-servers imports McpServersSection"
      pattern: "McpServersSection"
---

<objective>
Add the MCP Servers settings tab to the frontend: API client, list/add/edit/delete/toggle UI following the existing providers-section pattern exactly.

Purpose: Users need a UI to register MCP servers before the orchestrator can use them. The TracePanel already renders MCP tool_call events — no trace UI changes needed.

Output: Working MCP Servers tab in Settings with full CRUD and enable/disable toggle.
</objective>

<execution_context>
@/Users/przbadu/.claude/get-shit-done/workflows/execute-plan.md
@/Users/przbadu/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/phases/08-mcp-integration/8-CONTEXT.md
@.planning/phases/08-mcp-integration/08-01-SUMMARY.md

<interfaces>
<!-- Existing frontend patterns to follow exactly. Do not re-explore. -->

From frontend/src/lib/providers-api.ts (follow this exact pattern):
```typescript
import { apiFetch } from "@/lib/api";

export interface ProviderRead { id: number; name: string; ... }
export interface ProviderCreate { name: string; ... }
export interface ProviderUpdate { name?: string; ... }

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail ?? `Request failed (${res.status})`);
  }
  return res.json() as Promise<T>;
}

export async function listProviders(token: string): Promise<ProviderRead[]> {
  const res = await apiFetch("/api/v1/settings/providers", token);
  return handleResponse<ProviderRead[]>(res);
}
```

From frontend/src/components/settings/providers-section.tsx (follow this pattern):
```typescript
"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/context/auth-context";
// useQuery for list, useMutation for create/update/delete
// invalidateQueries({ queryKey: ["mcp-servers"] }) on success
```

From frontend/src/app/(protected)/settings/page.tsx:
```typescript
// Add TabsTrigger value="mcp-servers" and TabsContent with <McpServersSection />
// Existing tabs: "providers", "general", "appearance"
```

Backend API shape (from 08-01 plan):
```typescript
// McpServerRead shape:
{ id: number; name: string; command: string; args: string[]; env_vars: Record<string,string>; is_enabled: boolean; created_at: string; }

// Endpoints:
// GET    /api/v1/settings/mcp-servers        -> McpServerRead[]
// POST   /api/v1/settings/mcp-servers        -> McpServerRead (201)
// PUT    /api/v1/settings/mcp-servers/{id}   -> McpServerRead
// DELETE /api/v1/settings/mcp-servers/{id}   -> 204
// PATCH  /api/v1/settings/mcp-servers/{id}/toggle -> McpServerRead
```
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: MCP API client and McpServersSection with card + form components</name>
  <files>
    frontend/src/lib/mcp-api.ts,
    frontend/src/components/settings/mcp-servers-section.tsx,
    frontend/src/components/settings/mcp-server-card.tsx,
    frontend/src/components/settings/mcp-server-form.tsx,
    frontend/src/app/(protected)/settings/page.tsx
  </files>
  <action>
**1. Create `frontend/src/lib/mcp-api.ts`:**

Follow `providers-api.ts` exactly. Types:
```typescript
export interface McpServerRead {
  id: number;
  name: string;
  command: string;
  args: string[];
  env_vars: Record<string, string>;
  is_enabled: boolean;
  created_at: string;
}
export interface McpServerCreate {
  name: string;
  command: string;
  args?: string[];
  env_vars?: Record<string, string>;
  is_enabled?: boolean;
}
export interface McpServerUpdate {
  name?: string;
  command?: string;
  args?: string[];
  env_vars?: Record<string, string>;
  is_enabled?: boolean;
}
```

Functions: `listMcpServers(token)`, `createMcpServer(token, data)`, `updateMcpServer(token, id, data)`, `deleteMcpServer(token, id)`, `toggleMcpServer(token, id)` — use `PATCH /{id}/toggle` with no body.

**2. Create `frontend/src/components/settings/mcp-server-form.tsx`:**

Fields:
- `name` — text input (required, unique identifier shown in trace)
- `command` — text input (required, e.g. `uvx`, `node`, `/usr/local/bin/mcp-server`)
- `args` — textarea where each line is one arg (hint: "One argument per line"). On submit, split by `\n`, filter empty strings.
- `env_vars` — textarea for `KEY=VALUE` pairs, one per line. On submit, parse into `Record<string,string>`. Show hint: "KEY=VALUE, one per line".
- `is_enabled` — checkbox, defaults true

Props: `onSubmit(data: McpServerCreate | McpServerUpdate): Promise<void>`, `onCancel(): void`, `initialValues?: McpServerRead`, `isSubmitting: boolean`

Use shadcn/ui `Input`, `Textarea`, `Checkbox`, `Button`, `Label` components.

**3. Create `frontend/src/components/settings/mcp-server-card.tsx`:**

Display: server name (bold), command + args preview (monospace, truncated), enabled/disabled badge.

Actions:
- Toggle switch (shadcn `Switch` component) — calls `onToggle(id)` immediately, optimistic update via query invalidation
- Edit button — shows inline `McpServerForm` with `initialValues`
- Delete button with confirmation (use `window.confirm` or an `AlertDialog`) — calls `onDelete(id)`

**4. Create `frontend/src/components/settings/mcp-servers-section.tsx`:**

Mirror `providers-section.tsx` structure:
- `useQuery({ queryKey: ["mcp-servers"], queryFn: () => listMcpServers(token!) })`
- `useMutation` for create, update, delete, toggle — each calls `queryClient.invalidateQueries({ queryKey: ["mcp-servers"] })`
- "Add MCP Server" button shows `McpServerForm`
- Empty state: dashed border card "No MCP servers yet. Add one to enable tool use."
- Loading spinner, error display (same pattern as providers section)

**5. Update `frontend/src/app/(protected)/settings/page.tsx`:**

Add `import { McpServersSection } from "@/components/settings/mcp-servers-section"`.

Add to `TabsList`:
```tsx
<TabsTrigger value="mcp-servers">MCP Servers</TabsTrigger>
```

Add `TabsContent`:
```tsx
<TabsContent value="mcp-servers" className="mt-4">
  <McpServersSection />
</TabsContent>
```
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/frontend && npx tsc --noEmit 2>&1 | head -30</automated>
  </verify>
  <done>
    - `npx tsc --noEmit` passes with no errors in the new MCP files
    - Settings page renders MCP Servers tab (visible in browser at /settings)
    - Add form accepts name/command/args/env_vars and submits to backend
    - Toggle switch flips is_enabled and updates card display
    - Delete removes server from list
    - Empty state shown when no servers registered
  </done>
</task>

<task type="auto">
  <name>Task 2: Frontend MCP component tests</name>
  <files>
    frontend/src/components/settings/__tests__/mcp-servers-section.test.tsx,
    frontend/src/lib/__tests__/mcp-api.test.ts
  </files>
  <action>
**1. Create `frontend/src/lib/__tests__/mcp-api.test.ts`:**

Unit test each API function using `vi.stubGlobal("fetch", ...)` or `global.fetch = vi.fn(...)`:
- `listMcpServers(token)` — mock 200 response with array, verify returned array
- `createMcpServer(token, data)` — mock 201, verify correct POST body sent
- `toggleMcpServer(token, id)` — verify PATCH to `/{id}/toggle` with no body
- `deleteMcpServer(token, id)` — mock 204, verify no error thrown; mock 404, verify error thrown

**2. Create `frontend/src/components/settings/__tests__/mcp-servers-section.test.tsx`:**

Use Vitest + React Testing Library. Mock `@tanstack/react-query` or provide a real QueryClient wrapper.

Mock `@/lib/mcp-api` and `@/context/auth-context`:
```typescript
vi.mock("@/lib/mcp-api");
vi.mock("@/context/auth-context", () => ({
  useAuth: () => ({ token: "test-token" }),
}));
```

Tests:
- Loading state: shows spinner when `isLoading=true` (mock query pending)
- Empty state: renders "No MCP servers yet" when list is empty
- Server card rendered: given one server in list, name and command appear in DOM
- Add button: clicking "Add MCP Server" shows the form
- Toggle: clicking toggle on a server card calls `toggleMcpServer` mock

Look at existing test files in `frontend/src/components/` for the QueryClient wrapper setup pattern before writing.
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/frontend && npx vitest run src/lib/__tests__/mcp-api.test.ts src/components/settings/__tests__/mcp-servers-section.test.tsx --reporter=verbose 2>&1 | tail -20</automated>
  </verify>
  <done>
    - All MCP API client unit tests pass
    - McpServersSection component tests pass (loading, empty, render, add form, toggle)
    - `npx vitest run` exits 0 for both test files
  </done>
</task>

</tasks>

<verification>
After completing both tasks:

```bash
# TypeScript clean
cd /Users/przbadu/dev/claude-clone/frontend && npx tsc --noEmit

# Tests pass
npx vitest run src/lib/__tests__/mcp-api.test.ts src/components/settings/__tests__/mcp-servers-section.test.tsx

# Full frontend test suite still passes
npx vitest run
```
</verification>

<success_criteria>
- MCP Servers tab visible in Settings page
- CRUD operations (add, edit, toggle, delete) all work correctly against the backend
- TypeScript strict mode: no errors in new files
- Vitest: all new tests pass, no regressions in existing tests
- MCP trace events (tool_call type) already rendered by TracePanel from Phase 6 — no TracePanel changes needed
</success_criteria>

<output>
After completion, create `.planning/phases/08-mcp-integration/08-02-SUMMARY.md` with:
- What was built (API client, section/card/form components, settings page tab)
- Component hierarchy diagram (one-liner)
- Any shadcn/ui components used
- Test coverage summary
- Files created/modified
</output>
