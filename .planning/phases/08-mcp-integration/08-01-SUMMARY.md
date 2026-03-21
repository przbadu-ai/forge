---
phase: 08-mcp-integration
plan: 01
subsystem: mcp-backend
tags: [mcp, model, crud-api, executor, process-manager, tests]
dependency_graph:
  requires: [phase-7-orchestration]
  provides: [McpServer-model, mcp-crud-api, McpExecutor, McpProcessManager, mcp-tool-discovery]
  affects: [chat-endpoint, executor-registry, app-lifespan]
tech_stack:
  added: [mcp-sdk-1.26.0]
  patterns: [BaseExecutor-protocol, stdio-client, tool-namespacing]
key_files:
  created:
    - backend/app/models/mcp_server.py
    - backend/alembic/versions/0007_add_mcp_server_table.py
    - backend/app/api/v1/settings/mcp_servers.py
    - backend/app/services/mcp_process_manager.py
    - backend/app/services/executors/mcp_executor.py
    - backend/app/tests/test_mcp_server_api.py
    - backend/app/tests/test_mcp_executor.py
  modified:
    - backend/app/models/__init__.py
    - backend/app/api/v1/router.py
    - backend/app/services/executors/__init__.py
    - backend/app/main.py
    - backend/app/api/v1/chat.py
    - backend/pyproject.toml
decisions:
  - "Tool namespacing: server_name.tool_name (e.g. filesystem.read_file)"
  - "MCP discovery per-chat-turn (not app startup) for fresh tool lists"
  - "McpExecutor uses stdio_client context manager per invocation rather than persistent connection"
  - "PATCH for toggle endpoint instead of POST (more RESTful)"
metrics:
  duration: "7m 19s"
  completed: "2026-03-21T17:38:46Z"
  tasks: 3/3
  tests_added: 13
  tests_total: 118
---

# Phase 8 Plan 1: MCP Backend Summary

MCP server management with CRUD API, McpProcessManager for subprocess lifecycle, McpExecutor implementing BaseExecutor protocol with MCP SDK stdio_client, and per-turn tool discovery wired into the chat endpoint.

## What Was Built

### Task 1: McpServer Model + Migration + CRUD API
- **McpServer SQLModel**: id, name (unique), command, args (JSON), env_vars (JSON), is_enabled, created_at, updated_at
- **Alembic migration 0007_add_mcp_server**: Creates mcp_server table with unique index on name
- **CRUD endpoints** at `/api/v1/settings/mcp-servers`:
  - GET / -- list all servers
  - POST / -- create (409 on duplicate name)
  - PUT /{id} -- partial update
  - DELETE /{id} -- delete (204)
  - PATCH /{id}/toggle -- flip is_enabled

### Task 2: McpProcessManager + McpExecutor
- **McpProcessManager**: Manages MCP subprocess lifecycle (start, stop with stdin close -> SIGTERM -> SIGKILL, stop_all, cleanup_orphans)
- **McpExecutor**: Implements BaseExecutor protocol, uses MCP SDK `stdio_client` + `ClientSession` for tool invocation, emits tool_start/tool_end trace events
- **discover_and_register_mcp_tools**: Queries enabled MCP servers for tools, registers each as `{server_name}.{tool_name}` in ExecutorRegistry, returns OpenAI-format tool schemas
- **App lifespan hooks**: cleanup_orphans on startup, stop_all on shutdown
- **Chat endpoint integration**: Fetches enabled McpServers from DB and calls discover_and_register_mcp_tools before each orchestrator run

### Task 3: Backend Tests
- 9 integration tests for MCP CRUD API (auth, create, list, update, toggle, delete, duplicate conflict, not-found)
- 4 unit tests for McpExecutor (happy path, timeout, exception, tool name stripping)
- All use existing conftest fixtures (client, auth_client)

## Tool Namespacing

MCP tools are registered with namespaced names: `{server_name}.{tool_name}`. For example, a server named "filesystem" with a tool "read_file" becomes `filesystem.read_file`. The McpExecutor strips the server prefix before calling `session.call_tool()`.

## Migration

- Revision: `0007_add_mcp_server`
- Down revision: `0006_add_trace_data`
- Creates `mcp_server` table with unique index on `name`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed ruff lint: import ordering, unused imports, raise-from, asyncio.TimeoutError alias**
- **Found during:** Task 3 verification
- **Issue:** ruff reported I001, F401, B904, UP041, SIM117 errors
- **Fix:** Auto-fixed with `ruff --fix`, manually fixed B904 (raise from), SIM117 (combined async with), removed unused type: ignore comments
- **Files modified:** chat.py, mcp_servers.py, mcp_executor.py, mcp_process_manager.py, test_mcp_executor.py

## Self-Check: PASSED
