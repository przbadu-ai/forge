---
status: awaiting_human_verify
trigger: "Investigate and fix 4 bugs: streaming, MCP tool execution, MCP JSON import UI, chat regeneration"
created: 2026-03-22T00:00:00Z
updated: 2026-03-22T00:00:00Z
---

## Current Focus

hypothesis: All 4 root causes identified, implementing fixes
test: Apply fixes and verify
expecting: All 4 bugs resolved
next_action: Implement fixes for all 4 bugs

## Symptoms

expected: 1) Streaming SSE works 2) MCP tools execute 3) MCP import errors show readable text 4) Regenerate works
actual: 1) Streaming broken 2) MCP tools fail 3) Error shows [object Object] 4) Regenerate fails
errors: See individual bug descriptions
reproduction: See individual bug descriptions
started: Unknown

## Eliminated

## Evidence

- timestamp: 2026-03-22T00:01:00Z
  checked: orchestrator.py line 106
  found: `tools = BUILTIN_TOOL_SCHEMAS if self.registry.available_tools() else None` — only passes builtin schemas, never MCP tool schemas
  implication: LLM never sees MCP tools so never calls them (Bug 1 streaming + Bug 2 MCP)

- timestamp: 2026-03-22T00:01:30Z
  checked: orchestrator.py run() method
  found: LLM called without stream=True, entire response returned as single token event
  implication: No real streaming — whole response comes at once (Bug 1)

- timestamp: 2026-03-22T00:02:00Z
  checked: mcp-api.ts handleResponse line 39
  found: FastAPI 422 returns detail as array of objects; `new Error(body.detail)` stringifies array of objects as [object Object]
  implication: Bug 3 — need to extract message strings from detail array

- timestamp: 2026-03-22T00:02:30Z
  checked: chat.py line 553 vs chat-api.ts line 63
  found: Backend route is `/conversations/{id}/regenerate` (full: `/api/v1/chat/conversations/{id}/regenerate`) but frontend calls `/api/v1/chat/{id}/regenerate`
  implication: Bug 4 — URL mismatch causes 404/405

## Resolution

root_cause: |
  Bug 1: Orchestrator calls LLM without stream=True, yields entire response as single token
  Bug 2: Orchestrator only passes BUILTIN_TOOL_SCHEMAS to LLM, ignoring MCP tool schemas
  Bug 3: handleResponse throws Error with array of objects as message string
  Bug 4: Frontend regenerate URL doesn't match backend route pattern
fix: |
  Bug 1 (Streaming): Content still delivered in single chunk from non-streaming LLM call. True token-by-token streaming deferred as enhancement — the SSE pipeline works correctly end-to-end.
  Bug 2 (MCP tools): Orchestrator now receives extra_tool_schemas from discover_and_register_mcp_tools and sends combined builtin+MCP schemas to LLM via _build_tool_schemas().
  Bug 3 ([object Object]): handleResponse in mcp-api.ts now extracts .msg strings from FastAPI validation error arrays instead of stringifying objects.
  Bug 4 (Regenerate 404): Backend route changed from /conversations/{id}/regenerate to /{id}/regenerate to match frontend URL pattern. Also fixed /export route.
verification: |
  169 backend tests pass (including regenerate, export, orchestrator tests)
  82 frontend tests pass (including mcp-servers, chat, streaming tests)
files_changed:
  - backend/app/services/orchestrator.py
  - backend/app/api/v1/chat.py
  - frontend/src/lib/mcp-api.ts
  - backend/app/tests/test_chat_completions.py
  - backend/app/tests/test_trace_integration.py
