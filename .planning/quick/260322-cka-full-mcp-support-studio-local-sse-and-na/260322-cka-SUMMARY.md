---
phase: quick
plan: 260322-cka
tags: [mcp, transport, sse, streamable-http, navigation, ui]
key-files:
  created:
    - backend/alembic/versions/37f1742a38bd_add_mcp_transport_type_and_url.py
    - frontend/src/components/layout/app-header.tsx
  modified:
    - backend/app/models/mcp_server.py
    - backend/app/api/v1/settings/mcp_servers.py
    - backend/app/services/executors/mcp_executor.py
    - backend/app/tests/test_mcp_server_api.py
    - backend/app/tests/test_mcp_executor.py
    - frontend/src/lib/mcp-api.ts
    - frontend/src/components/settings/mcp-server-form.tsx
    - frontend/src/components/settings/mcp-server-card.tsx
    - frontend/src/app/(protected)/layout.tsx
    - frontend/src/app/(protected)/chat/layout.tsx
    - frontend/src/__tests__/mcp-servers.test.tsx
metrics:
  duration: 4min
  completed: "2026-03-22T03:25:00Z"
  tasks: 2
  files: 13
---

# Quick Task 260322-cka: Full MCP Transport Support + Navigation Header

Full MCP transport support (stdio/SSE/streamable HTTP) with transport-aware API validation, executor client selection, conditional form fields, and a global navigation header for Chat/Settings.

## Task 1: Backend -- MCP Transport Support

- **Model:** Added `transport_type` (stdio/sse/streamable_http) and `url` fields; made `command` nullable
- **Migration:** `37f1742a38bd` adds columns with SQLite batch mode compatibility
- **API:** Transport-specific validation (stdio requires command, SSE/HTTP require url)
- **Executor:** `_connect_session()` async context manager for transport-agnostic tool execution
- **Tests:** 13 API + 4 executor tests passing, ruff + mypy clean

## Task 2: Frontend -- Transport Form + Navigation

- **MCP Form:** Segmented transport type selector with conditional fields (command+args for stdio, URL for SSE/HTTP)
- **Server Cards:** Transport type badge, URL display for remote transports
- **AppHeader:** Compact navigation with Chat/Settings links, active state, logout button
- **Layout:** Protected layout wraps AppHeader; chat layout adjusted to h-full
- **Tests:** 82/82 tests passing across 15 files, zero TypeScript/lint errors

## Commits

| Commit | Description |
|--------|-------------|
| d171e4c | feat(260322-cka): add transport type support to MCP form and global navigation header |
| f7ac030 | docs(260322-cka): add task 2 partial summary |
| 9ed9f5d | docs(260322-cka): add task 1 backend summary |
