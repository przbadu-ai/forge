# Phase 6: Execution Trace System - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

<domain>
## Phase Boundary

TraceEmitter service, trace UI panel per message, trace persistence as JSON blob in DB, and trace replay on conversation resume. This is Forge's core differentiator — every assistant message shows what happened during generation.

</domain>

<decisions>
## Implementation Decisions

### Trace data model
- **D-01:** Traces stored as JSON blob on Message model (not normalized rows)
- **D-02:** Each trace is an array of TraceEvent objects
- **D-03:** TraceEvent: {id, type, name, status, started_at, completed_at, input?, output?, error?, metadata?}
- **D-04:** Event types for now: run_start, run_end, token_generation, error

### TraceEmitter
- **D-05:** TraceEmitter is a Python service that collects events during a chat turn
- **D-06:** Events are emitted as SSE alongside token events (multiplexed stream)
- **D-07:** On run completion, the full trace array is persisted to the message's trace_data field

### Trace UI
- **D-08:** Each assistant message has a collapsible "Execution Trace" section
- **D-09:** Collapsed by default — click to expand
- **D-10:** Shows ordered events with type icon, name, status badge, timestamps
- **D-11:** Compact input/output preview with safe truncation

### Trace replay
- **D-12:** When resuming a conversation, traces are loaded from DB and rendered in the UI
- **D-13:** No re-execution — just render the persisted trace data

### Claude's Discretion
- Trace panel visual design
- Event type icons
- Truncation thresholds for input/output preview
- Timestamp formatting

</decisions>

<canonical_refs>
## Canonical References

- `PRD.md` §7.3 — Execution trace UI requirements
- `.planning/research/ARCHITECTURE.md` — Trace storage as JSON blob pattern
- `backend/app/api/v1/chat.py` — SSE streaming to extend with trace events
- `backend/app/models/message.py` — Message model to add trace_data field

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/api/v1/chat.py` — SSE _token_generator to extend with trace events
- `frontend/src/hooks/useChat.ts` — SSE consumer to handle trace events
- `frontend/src/components/chat/message-bubble.tsx` — Add trace panel below message

### Integration Points
- Message model needs trace_data JSON field + migration
- SSE stream needs new event types (trace_start, trace_end, trace_event)
- Phase 7 (orchestration) will emit tool_start/tool_end trace events through this system

</code_context>

<deferred>
## Deferred Ideas

- Tool call trace events — Phase 7
- MCP trace events — Phase 8
- Skill trace events — Phase 9

</deferred>

---

*Phase: 06-execution-trace-system*
*Context gathered: 2026-03-21*
