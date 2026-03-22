---
phase: quick
plan: 260322-piv
subsystem: api
tags: [mcp, trace, diagnostics, fastapi]

requires:
  - phase: none
    provides: n/a
provides:
  - MCP discovery trace events visible in execution trace panel
  - Test-connection endpoint for MCP server diagnostics
affects: [mcp, settings-ui, chat]

tech-stack:
  added: []
  patterns: [trace event emission for MCP discovery lifecycle]

key-files:
  created: []
  modified:
    - backend/app/services/trace_emitter.py
    - backend/app/services/executors/mcp_executor.py
    - backend/app/api/v1/settings/mcp_servers.py

key-decisions:
  - "Test-connection endpoint returns 200 even on failure (diagnostic endpoint, not resource creation)"
  - "Trace events use mcp_discovery type to distinguish from tool_call events"

patterns-established:
  - "MCP discovery lifecycle: emit start event before connection, end event with tools or error"

requirements-completed: []

duration: 2min
completed: 2026-03-22
---

# Quick Task 260322-piv: Fix MCP Server Not Working in Production Summary

**MCP discovery trace events for per-server visibility and test-connection diagnostic endpoint for settings UI**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-22T12:42:47Z
- **Completed:** 2026-03-22T12:44:36Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- MCP discovery failures now produce visible trace events (type="mcp_discovery", status="error") in the execution trace panel
- Each enabled MCP server gets its own discovery start/end trace events during chat turns
- New POST /{server_id}/test-connection endpoint returns tool list on success or error details on failure

## Task Commits

Each task was committed atomically:

1. **Task 1: Add MCP discovery trace events** - `6c0c617` (feat)
2. **Task 2: Add test-connection endpoint** - `1f90132` (feat)

## Files Created/Modified
- `backend/app/services/trace_emitter.py` - Added mcp_discovery type and emit_mcp_discovery_start/end methods
- `backend/app/services/executors/mcp_executor.py` - Emit trace events in discover_and_register_mcp_tools for each server
- `backend/app/api/v1/settings/mcp_servers.py` - Added McpTestConnectionResponse schema and POST test-connection endpoint

## Decisions Made
- Test-connection endpoint returns 200 even on connection failure (success=false in body) -- this is a diagnostic endpoint where the caller needs the error details
- Trace events use a dedicated "mcp_discovery" type to keep them distinct from "tool_call" events in the trace panel
- 10s timeout on test-connection matches the default discovery timeout

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Known Stubs
None - all functionality is fully wired.

## Next Steps
- Frontend settings UI can wire up "Test Connection" button to the new endpoint
- Execution trace panel already renders trace events; mcp_discovery events will appear automatically

---
*Quick task: 260322-piv*
*Completed: 2026-03-22*
