# Phase 8: MCP Integration - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

<domain>
## Phase Boundary

MCP server registration in Settings, McpProcessManager for subprocess lifecycle, McpExecutor for tool invocation, and trace visibility for MCP calls. Users can add MCP servers and the orchestrator can invoke their tools.

</domain>

<decisions>
## Implementation Decisions

### MCP settings
- **D-01:** McpServer model: id, name, command, args (JSON), env_vars (JSON), is_enabled, created_at
- **D-02:** CRUD endpoints at /api/v1/settings/mcp-servers
- **D-03:** Enable/disable toggle per server

### Process management
- **D-04:** McpProcessManager handles subprocess lifecycle (start, health-check, shutdown)
- **D-05:** Start MCP servers on-demand (when first tool call needs them), not at app startup
- **D-06:** Clean shutdown: stdin close → SIGTERM → SIGKILL after timeout
- **D-07:** Orphan cleanup on app startup (kill any stale MCP processes)

### McpExecutor
- **D-08:** Implements BaseExecutor protocol from Phase 7
- **D-09:** Uses MCP Python SDK (mcp package) for client communication
- **D-10:** Tool discovery: list tools from MCP server and register in ExecutorRegistry
- **D-11:** MCP tool calls emit trace events (mcp_tool_start, mcp_tool_end)

### Frontend
- **D-12:** MCP servers settings page section with add/edit/delete/enable-disable
- **D-13:** MCP trace events visible in TracePanel (already handles trace_event SSE)

### Claude's Discretion
- MCP server health check implementation
- Process restart strategy on failure
- Tool name namespacing (server_name.tool_name)

</decisions>

<canonical_refs>
## Canonical References

- `PRD.md` §7.4 — MCP support requirements
- `.planning/research/PITFALLS.md` — MCP zombie processes pitfall
- `backend/app/services/executors/base.py` — BaseExecutor protocol
- `backend/app/services/executors/registry.py` — ExecutorRegistry
- `backend/app/services/orchestrator.py` — Orchestrator loop

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- ExecutorRegistry — register McpExecutor tools
- TraceEmitter — emit_tool_start/end for MCP calls
- Settings UI pattern from Phase 3 (providers) — reuse for MCP servers

### Integration Points
- McpExecutor registers tools in ExecutorRegistry at server startup
- Orchestrator dispatches MCP tool calls through registry (no changes needed)
- TracePanel already renders trace_event SSE events

</code_context>

<deferred>
## Deferred Ideas

None — all within scope

</deferred>

---

*Phase: 08-mcp-integration*
*Context gathered: 2026-03-21*
