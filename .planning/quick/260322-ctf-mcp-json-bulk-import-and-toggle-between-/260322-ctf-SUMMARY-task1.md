---
phase: quick
plan: 260322-ctf
task: 1
subsystem: backend
tags: [mcp, bulk-import, api]
key-files:
  modified:
    - backend/app/api/v1/settings/mcp_servers.py
decisions:
  - "Transport type inferred from entry fields: url present -> sse, otherwise stdio"
  - "Validation errors include server name for clear error attribution"
metrics:
  duration: 1min
  completed: "2026-03-22T03:32:00Z"
  tasks: 1/1
---

# Phase quick Plan 260322-ctf: Task 1 Summary (Backend Bulk Import)

POST /api/v1/settings/mcp-servers/import endpoint accepting Cursor/Claude Desktop mcp.json format with upsert-by-name semantics.

## What Was Done

### Task 1: Backend bulk import endpoint

Added three new Pydantic schemas and one endpoint to `mcp_servers.py`:

- **McpServerEntry**: Represents a single server in mcp.json format (command, args, env, url)
- **McpBulkImportRequest**: Wraps `mcpServers: dict[str, McpServerEntry]` matching the standard format
- **McpBulkImportResponse**: Returns `created`, `updated` counts and full `servers` list
- **POST /import endpoint**: Iterates entries, infers transport_type from fields, upserts by name, validates transport fields, commits in single transaction, returns result summary

Key behaviors:
- Existing servers matched by name are updated (command, args, env_vars, url, transport_type)
- New servers are created with `is_enabled=True`
- If any server fails validation, the entire import is rolled back with a 422 error identifying the failing server
- Database integrity errors return 409

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | 4951141 | feat(260322-ctf): add bulk import endpoint for MCP servers |

## Deviations from Plan

None - plan executed exactly as written.

## Self-Check: PASSED

- [x] backend/app/api/v1/settings/mcp_servers.py modified with new schemas and endpoint
- [x] Commit 4951141 exists
- [x] Python syntax validates
