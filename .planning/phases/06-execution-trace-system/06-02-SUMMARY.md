---
phase: 06-execution-trace-system
plan: 02
subsystem: frontend-trace-ui
tags: [trace, frontend, sse, react, component]
dependency_graph:
  requires: [06-01]
  provides: [trace-panel-component, trace-sse-handler, trace-replay]
  affects: [message-bubble, chat-panel, useChat-hook]
tech_stack:
  added: []
  patterns: [ref-based-accumulation, sse-trace-multiplexing, json-blob-parsing]
key_files:
  created:
    - frontend/src/components/chat/TracePanel.tsx
  modified:
    - frontend/src/types/chat.ts
    - frontend/src/hooks/useChat.ts
    - frontend/src/components/chat/MessageBubble.tsx
    - frontend/src/components/chat/ChatPanel.tsx
decisions:
  - "TracePanel uses native useState toggle (no shadcn Collapsible needed)"
  - "Trace events accumulated via useRef for synchronous access in SSE handler"
  - "lucide-react icons: Activity for run_start/run_end, Zap for token_generation, AlertCircle for error"
  - "Status badge colors: yellow=running, green=completed, red=error with dark mode variants"
metrics:
  duration: 3min
  completed: 2026-03-21
  tasks: 3
  files: 5
---

# Phase 6 Plan 2: Frontend Trace UI Summary

TracePanel component with collapsible event list, SSE trace event accumulation in useChat via ref, and trace replay from persisted trace_data on conversation load.

## What Was Built

### TraceEvent Types (`frontend/src/types/chat.ts`)
- **TraceEvent interface**: id, type (run_start|run_end|token_generation|error), name, status (running|completed|error), started_at, completed_at, input, output, error, metadata
- **SSETraceEvent interface**: type="trace_event" with nested TraceEvent
- **Message.trace_data**: string | null field for JSON-serialized trace array
- **SSEEvent union**: Updated to include SSETraceEvent

### TracePanel Component (`frontend/src/components/chat/TracePanel.tsx`)
- Collapsible section with "Execution Trace" header and event count badge
- Collapsed by default, toggles with ChevronDown/ChevronUp icon
- Per-event row: type icon, name (truncated 40 chars), status badge pill, duration/timestamp
- Error text shown in red (truncated 100 chars)
- Input/output preview as truncated JSON (200 char max) in monospace
- Streaming indicator: pulsing yellow dot with "Recording..." text
- Uses cn() for conditional Tailwind classes, no external dependencies

### useChat Hook Updates (`frontend/src/hooks/useChat.ts`)
- **streamingTraceEvents state**: TraceEvent[] exposed for live streaming display
- **messageTraces state**: Record<number, TraceEvent[]> keyed by message ID
- **traceEventsRef**: useRef for synchronous trace accumulation during SSE parsing (avoids closure staleness)
- SSE "trace_event" handler pushes to ref and updates state
- On "done"/"stopped" events: snapshot traces to messageTraces, clear accumulation
- On conversation load: parse trace_data from each assistant message into messageTraces
- Clears trace state when conversationId changes

### MessageBubble Integration
- New props: traceEvents (completed messages), liveTraceEvents (streaming message)
- Renders TracePanel below MarkdownRenderer for assistant messages with trace data

### ChatPanel Integration
- Destructures messageTraces and streamingTraceEvents from useChat
- Passes traceEvents to message list, liveTraceEvents to streaming bubble

## Trace Replay on Conversation Load

When a conversation is loaded via GET /messages:
1. Each message includes `trace_data: string | null` from the API
2. The useEffect in useChat iterates assistant messages
3. Non-null trace_data is JSON.parsed into TraceEvent[]
4. Parsed traces are stored in messageTraces keyed by message ID
5. MessageBubble receives traceEvents and renders TracePanel immediately

## Deviations from Plan

None - plan executed exactly as written.

## Commits
| Hash | Description |
|---|---|
| c135548 | TracePanel UI, trace event handling, trace replay on resume |
