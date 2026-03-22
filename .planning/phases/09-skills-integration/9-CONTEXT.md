# Phase 9: Skills Integration - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Agent skills configuration (enable/disable in Settings), SkillExecutor implementing BaseExecutor, skill execution with trace visibility and persistence. Skills are modular capabilities (web search, code execution, etc.) that the LLM can invoke.

</domain>

<decisions>
## Implementation Decisions

### Skills model
- **D-01:** Skill model: id, name, description, is_enabled, config (JSON), created_at
- **D-02:** Pre-seeded skills (web_search, code_execution placeholder) — not user-created for MVP
- **D-03:** Skills are enable/disable only, not full CRUD for MVP

### SkillExecutor
- **D-04:** Implements BaseExecutor protocol
- **D-05:** Registered in ExecutorRegistry alongside ToolExecutor and McpExecutor
- **D-06:** Each skill has a handler function that does the actual work
- **D-07:** Skill execution emits trace events (skill_start, skill_end)

### Frontend
- **D-08:** Skills section in Settings with enable/disable toggles
- **D-09:** Trace events for skills already handled by TracePanel

### Claude's Discretion
- Which placeholder skills to include
- Skill handler implementation details
- Whether skills can have configuration options

</decisions>

<canonical_refs>
## Canonical References

- `PRD.md` §7.5 — Agent skills requirements
- `backend/app/services/executors/base.py` — BaseExecutor protocol
- `backend/app/services/executors/registry.py` — ExecutorRegistry

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- ExecutorRegistry — register SkillExecutor
- TraceEmitter — emit skill events
- MCP settings UI pattern — reuse for skills toggle list

### Integration Points
- SkillExecutor registered in ExecutorRegistry at chat turn start
- Orchestrator dispatches skill calls through registry (no changes needed)

</code_context>

<deferred>
## Deferred Ideas

- User-created custom skills — v2
- Skill marketplace — v2

</deferred>

---

*Phase: 09-skills-integration*
*Context gathered: 2026-03-21*
