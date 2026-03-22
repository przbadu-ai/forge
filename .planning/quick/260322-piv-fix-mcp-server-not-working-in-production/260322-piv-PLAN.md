---
phase: quick
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - backend/app/services/executors/mcp_executor.py
  - backend/app/services/trace_emitter.py
  - backend/app/api/v1/settings/mcp_servers.py
  - backend/app/api/v1/chat.py
autonomous: true
must_haves:
  truths:
    - "MCP discovery failures are visible in the execution trace panel"
    - "Users can test MCP server connectivity from the settings page"
    - "Per-server discovery status (success/failure with tool count or error) is emitted as trace events"
  artifacts:
    - path: "backend/app/services/trace_emitter.py"
      provides: "MCP discovery trace event methods"
    - path: "backend/app/services/executors/mcp_executor.py"
      provides: "Discovery with trace emission and per-server error reporting"
    - path: "backend/app/api/v1/settings/mcp_servers.py"
      provides: "POST test-connection endpoint"
  key_links:
    - from: "backend/app/services/executors/mcp_executor.py"
      to: "backend/app/services/trace_emitter.py"
      via: "tracer.emit_mcp_discovery_start/end calls"
    - from: "backend/app/api/v1/settings/mcp_servers.py"
      to: "backend/app/services/executors/mcp_executor.py"
      via: "_connect_session used for test connection"
---

<objective>
Fix MCP servers being silently invisible in production by adding trace visibility for MCP discovery and a test-connection endpoint for diagnostics.

Purpose: In production (Docker behind Cloudflare Tunnel), MCP server discovery fails silently — the AI has zero awareness of MCP tools and the user sees no error. This makes MCP completely unusable with no way to diagnose.

Output: Trace events for MCP discovery (visible in execution trace panel), per-server error reporting, and a test-connection endpoint for settings UI.
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-plan.md
@~/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@backend/app/services/executors/mcp_executor.py
@backend/app/services/trace_emitter.py
@backend/app/api/v1/settings/mcp_servers.py
@backend/app/api/v1/chat.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add MCP discovery trace events to TraceEmitter and emit them in discover_and_register_mcp_tools</name>
  <files>backend/app/services/trace_emitter.py, backend/app/services/executors/mcp_executor.py</files>
  <action>
1. In `trace_emitter.py`, add the `"mcp_discovery"` literal to the `TraceEvent.type` field union:
   - Change `Literal["run_start", "run_end", "token_generation", "error", "tool_call"]` to also include `"mcp_discovery"`

2. Add two new methods to `TraceEmitter`:

   `emit_mcp_discovery_start(server_name: str, transport_type: str) -> TraceEvent`:
   - type="mcp_discovery", name=f"mcp_discovery:{server_name}", status="running"
   - metadata={"server_name": server_name, "transport_type": transport_type}

   `emit_mcp_discovery_end(server_name: str, tools_found: list[str] | None = None, error: str | None = None) -> TraceEvent`:
   - type="mcp_discovery", name=f"mcp_discovery:{server_name}"
   - status="error" if error else "completed"
   - output={"tools": tools_found, "count": len(tools_found)} if tools_found else None
   - error=error if error

3. In `mcp_executor.py` `discover_and_register_mcp_tools()`, wrap each server's discovery loop iteration:

   BEFORE `async with _connect_session(...)`:
   ```python
   tracer.emit_mcp_discovery_start(server.name, server.transport_type or "stdio")
   ```

   AFTER successful tool registration (after the for-loop over tools_result.tools):
   ```python
   tool_names = [f"{server.name}.{t.name}" for t in tools_result.tools]
   tracer.emit_mcp_discovery_end(server.name, tools_found=tool_names)
   ```

   In the `except Exception` block, REPLACE the bare logger.exception with:
   ```python
   error_msg = f"Failed to discover tools from MCP server '{server.name}': {exc}"
   logger.exception("MCP discovery error: %s", server.name)
   tracer.emit_mcp_discovery_end(server.name, error=error_msg)
   ```

   This ensures discovery failures produce trace events visible in the UI execution trace panel.
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone && python -c "
from app.services.trace_emitter import TraceEmitter
t = TraceEmitter()
e1 = t.emit_mcp_discovery_start('test-server', 'stdio')
assert e1.type == 'mcp_discovery'
assert e1.status == 'running'
e2 = t.emit_mcp_discovery_end('test-server', tools_found=['test-server.tool1'])
assert e2.status == 'completed'
assert e2.output['count'] == 1
e3 = t.emit_mcp_discovery_end('bad-server', error='Connection refused')
assert e3.status == 'error'
assert e3.error == 'Connection refused'
print('All trace emitter checks passed')
"</automated>
  </verify>
  <done>MCP discovery emits mcp_discovery trace events for each server (start + end with tools or error). Discovery failures are no longer silent — they appear in the execution trace panel.</done>
</task>

<task type="auto">
  <name>Task 2: Add test-connection endpoint for MCP servers</name>
  <files>backend/app/api/v1/settings/mcp_servers.py</files>
  <action>
1. Add imports at the top of `mcp_servers.py`:
   ```python
   import asyncio
   from app.services.executors.mcp_executor import _connect_session
   ```

2. Add a response schema:
   ```python
   class McpTestConnectionResponse(BaseModel):
       success: bool
       server_name: str
       transport_type: str
       tools_found: list[str] = []
       tool_count: int = 0
       error: str | None = None
   ```

3. Add endpoint AFTER the existing toggle endpoint:
   ```python
   @router.post("/{server_id}/test-connection", response_model=McpTestConnectionResponse)
   async def test_mcp_connection(
       server_id: int,
       session: AsyncSession = Depends(get_session),
   ) -> McpTestConnectionResponse:
       """Test connectivity to an MCP server and list its available tools."""
       server = await _get_server(server_id, session)
       try:
           async with _connect_session(server, timeout=10.0) as mcp_session:
               tools_result = await asyncio.wait_for(mcp_session.list_tools(), timeout=10.0)
           tool_names = [t.name for t in tools_result.tools]
           return McpTestConnectionResponse(
               success=True,
               server_name=server.name,
               transport_type=server.transport_type,
               tools_found=tool_names,
               tool_count=len(tool_names),
           )
       except Exception as exc:
           return McpTestConnectionResponse(
               success=False,
               server_name=server.name,
               transport_type=server.transport_type,
               error=str(exc),
           )
   ```

   Key design decisions:
   - Returns 200 even on connection failure (success=false in body) — this is a diagnostic endpoint, not a resource creation. The caller needs the error details.
   - Uses the same `_connect_session` context manager as real discovery for accurate results.
   - 10s timeout matches the discovery timeout default.
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone && python -c "
from app.api.v1.settings.mcp_servers import McpTestConnectionResponse
r = McpTestConnectionResponse(success=False, server_name='test', transport_type='stdio', error='Connection refused')
assert r.success == False
assert r.error == 'Connection refused'
r2 = McpTestConnectionResponse(success=True, server_name='test', transport_type='sse', tools_found=['a','b'], tool_count=2)
assert r2.tool_count == 2
print('Schema checks passed')
" && python -c "
import inspect
from app.api.v1.settings.mcp_servers import router
routes = [r.path for r in router.routes]
assert '/{server_id}/test-connection' in routes, f'test-connection route not found in {routes}'
print('Route registered: OK')
"</automated>
  </verify>
  <done>POST /api/v1/settings/mcp-servers/{id}/test-connection endpoint exists, attempts real connection to the MCP server, returns success/failure with tool list or error message. Users can diagnose MCP connectivity issues from settings.</done>
</task>

</tasks>

<verification>
1. TraceEmitter has emit_mcp_discovery_start and emit_mcp_discovery_end methods
2. discover_and_register_mcp_tools emits trace events for each server (both success and failure paths)
3. Test connection endpoint is registered and returns structured response
4. No silent exception swallowing in MCP discovery — all failures produce trace events
</verification>

<success_criteria>
- MCP discovery failures produce visible trace events (type="mcp_discovery", status="error") in the execution trace panel
- Each enabled MCP server gets its own discovery start/end trace events during chat turns
- Test connection endpoint returns tool list on success and error details on failure
- Existing MCP execution (tool_call trace events) is unchanged
</success_criteria>

<output>
After completion, create `.planning/quick/260322-piv-fix-mcp-server-not-working-in-production/260322-piv-SUMMARY.md`
</output>
