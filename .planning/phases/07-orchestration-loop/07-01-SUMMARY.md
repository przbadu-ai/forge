---
phase: 07-orchestration-loop
plan: "01"
subsystem: backend-orchestration
tags: [orchestrator, executor, tool-calling, run-state, trace]
dependency_graph:
  requires: [trace_emitter, chat_endpoint]
  provides: [orchestrator, executor_registry, run_state_store, tool_executor]
  affects: [chat.py, trace_emitter.py]
tech_stack:
  added: []
  patterns: [protocol-based-executor, registry-dispatch, while-loop-orchestration]
key_files:
  created:
    - backend/app/services/orchestrator.py
    - backend/app/services/executors/__init__.py
    - backend/app/services/executors/base.py
    - backend/app/services/executors/registry.py
    - backend/app/services/executors/tool_executor.py
    - backend/app/services/executors/builtin_tools.py
    - backend/app/services/run_state.py
  modified:
    - backend/app/services/trace_emitter.py
    - backend/app/api/v1/chat.py
decisions:
  - "BaseExecutor as Protocol (not ABC) for structural typing"
  - "Orchestrator uses non-streaming LLM call to inspect finish_reason and tool_calls"
  - "Final content yielded as single SSE token chunk (streaming deferred)"
  - "RunStatus uses enum.StrEnum per ruff UP042"
  - "Trace emit calls in Orchestrator, not ToolExecutor, for clean separation"
metrics:
  duration: 5min
  completed: 2026-03-21
---

# Phase 7 Plan 01: Orchestration Loop Backend Implementation Summary

Orchestrator service with while-loop (LLM -> tool dispatch -> feed results -> repeat), BaseExecutor protocol, ExecutorRegistry, ToolExecutor with current_datetime built-in, RunStateStore, and TraceEmitter tool_start/tool_end extensions.

## What Was Built

### Task 1: BaseExecutor, ExecutorRegistry, RunState, TraceEmitter extensions
- Created `executors/` package with BaseExecutor protocol and ExecutorResult dataclass
- ExecutorRegistry with register/dispatch/available_tools methods
- RunStateStore with in-memory dict-backed lifecycle management (create/get/update_status/increment_iteration/delete)
- Extended TraceEmitter with emit_tool_start and emit_tool_end methods, added "tool_call" to type Literal

### Task 2: ToolExecutor with current_datetime built-in tool
- ToolExecutor implementing BaseExecutor, delegates to registered tool functions
- current_datetime async function returning UTC ISO timestamp
- BUILTIN_TOOL_SCHEMAS for OpenAI function-calling format

### Task 3: Orchestrator service and chat.py refactor
- Orchestrator class with async generator run() method yielding SSE-formatted strings
- While-loop: call LLM (non-streaming) -> check tool_calls -> dispatch to executor -> feed results -> repeat
- Max 10 iterations guard, 30s timeout with 3x exponential backoff retry on LLM calls
- Timeout on tool dispatch emits error trace and fails run
- Refactored chat.py _token_generator to create Orchestrator and delegate to it
- final_content property on Orchestrator for message persistence

## Deviations from Plan

None - plan executed exactly as written.

## Decisions Made

1. Used non-streaming LLM call inside Orchestrator to inspect finish_reason and tool_calls on full response
2. Final text content yielded as single token SSE chunk (real token streaming can be added later)
3. Trace emit calls placed in Orchestrator (not ToolExecutor) to keep executors pure and testable
4. RunStatus uses enum.StrEnum instead of str+Enum per ruff UP042 recommendation

## Commits

- `99185fd`: feat(07-01): implement orchestration loop with executor framework
