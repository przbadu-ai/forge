# Phase 7: Orchestration Loop - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Custom agentic orchestration loop (model -> tools -> model) with modular executor interfaces, run state tracking, and configurable timeout/retry. The loop enables tool calling — when the LLM returns tool_calls, executors handle them and feed results back.

</domain>

<decisions>
## Implementation Decisions

### Orchestrator
- **D-01:** While-loop pattern: call LLM → if tool_calls, dispatch → feed results → repeat until text response
- **D-02:** Maximum 10 iterations to prevent infinite loops
- **D-03:** Orchestrator is a service class, not coupled to FastAPI routes

### Executor interfaces
- **D-04:** BaseExecutor protocol: async execute(name, input) -> output
- **D-05:** ExecutorRegistry: register executors by tool name, dispatch by name
- **D-06:** ToolExecutor, McpExecutor, SkillExecutor all implement BaseExecutor
- **D-07:** For now, only ToolExecutor with basic built-in tools (Phase 7). MCP and Skills in Phases 8-9.

### Run state
- **D-08:** RunState: created, running, completed, failed, cancelled
- **D-09:** Stored in-memory per run (not persisted to DB for MVP)
- **D-10:** Run ID is a UUID, tracked per streaming turn

### Trace integration
- **D-11:** Every executor action emits trace events via TraceEmitter
- **D-12:** tool_start event when executor begins, tool_end when complete
- **D-13:** Error in executor emits error trace event

### Timeout/retry
- **D-14:** Configurable timeout per external call (default 30s)
- **D-15:** Retry with exponential backoff (max 3 retries)
- **D-16:** Timeout produces error trace event, not silent hang

### Claude's Discretion
- Exact retry backoff timing
- Built-in tool selection for Phase 7 demo
- RunState implementation details

</decisions>

<canonical_refs>
## Canonical References

- `PRD.md` §7.9 — Backend orchestration requirements
- `.planning/research/ARCHITECTURE.md` — Executor adapter pattern
- `backend/app/services/trace_emitter.py` — TraceEmitter to integrate
- `backend/app/api/v1/chat.py` — SSE streaming to refactor into orchestrator

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/services/trace_emitter.py` — TraceEmitter for event collection
- `backend/app/api/v1/chat.py` — _token_generator to refactor into orchestrator
- `backend/app/core/encryption.py` — decrypt API keys for provider

### Integration Points
- Refactor chat.py streaming to use Orchestrator instead of direct openai calls
- MCP executor registration in Phase 8
- Skill executor registration in Phase 9

</code_context>

<deferred>
## Deferred Ideas

- MCP executor — Phase 8
- Skill executor — Phase 9
- Persistent run state in DB — v2

</deferred>

---

*Phase: 07-orchestration-loop*
*Context gathered: 2026-03-21*
