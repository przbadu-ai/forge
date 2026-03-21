---
phase: 06-execution-trace-system
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - backend/app/models/message.py
  - backend/app/models/__init__.py
  - backend/app/services/trace_emitter.py
  - backend/app/api/v1/chat.py
  - backend/alembic/versions/0006_add_trace_data_to_message.py
autonomous: true
requirements:
  - TRACE-01
  - TRACE-02
  - TRACE-03
  - TRACE-04

must_haves:
  truths:
    - "Message model has a nullable trace_data JSON field persisted to SQLite"
    - "Alembic migration adds trace_data column without data loss"
    - "TraceEmitter collects run_start, token_generation, run_end, and error events"
    - "SSE stream emits trace_event messages alongside token messages"
    - "On run completion, the full trace array is written to message.trace_data"
  artifacts:
    - path: "backend/app/services/trace_emitter.py"
      provides: "TraceEmitter class and TraceEvent dataclass"
      exports: ["TraceEmitter", "TraceEvent"]
    - path: "backend/alembic/versions/0006_add_trace_data_to_message.py"
      provides: "Alembic migration adding trace_data column"
      contains: "op.add_column"
    - path: "backend/app/models/message.py"
      provides: "Message model with trace_data field"
      contains: "trace_data"
  key_links:
    - from: "backend/app/api/v1/chat.py _token_generator"
      to: "backend/app/services/trace_emitter.py TraceEmitter"
      via: "instantiate TraceEmitter, call emit(), serialize to JSON on completion"
      pattern: "TraceEmitter"
    - from: "_token_generator"
      to: "SSE stream"
      via: "yield trace_event SSE lines interleaved with token lines"
      pattern: "trace_event"
---

<objective>
Add the backend trace infrastructure: TraceEmitter service, trace_data column on Message, Alembic migration, and extended SSE stream that emits structured trace events alongside tokens.

Purpose: Establish the backend foundation for Forge's core differentiator. Every assistant message will carry a persisted, replayable execution trace.
Output: TraceEmitter service, migrated DB schema, extended _token_generator emitting trace SSE events, trace_data saved on message completion.
</objective>

<execution_context>
@/Users/przbadu/.claude/get-shit-done/workflows/execute-plan.md
@/Users/przbadu/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/phases/06-execution-trace-system/6-CONTEXT.md

Locked decisions from CONTEXT.md (NON-NEGOTIABLE):
- D-01: trace_data stored as JSON blob on Message model (not normalized rows)
- D-02: Each trace is an array of TraceEvent objects
- D-03: TraceEvent shape: {id, type, name, status, started_at, completed_at, input?, output?, error?, metadata?}
- D-04: Event types for Phase 6: run_start, run_end, token_generation, error
- D-05: TraceEmitter is a Python service collecting events during a chat turn
- D-06: Events emitted as SSE alongside token events (multiplexed stream)
- D-07: On run completion, full trace array persisted to message.trace_data

Deferred (do NOT include): tool_start/tool_end events (Phase 7), MCP events (Phase 8), skill events (Phase 9).

<interfaces>
From backend/app/models/message.py (current):
```python
class Message(SQLModel, table=True):
    __tablename__ = "message"
    id: int | None = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="conversation.id", index=True)
    role: str = Field(max_length=20)
    content: str = Field(default="")
    created_at: datetime = Field(default_factory=_utcnow)
```

From backend/app/api/v1/chat.py (key signature):
```python
async def _token_generator(
    messages: list[dict[str, str]],
    base_url: str, api_key: str, model: str,
    conversation_id: int, session: AsyncSession,
    system_prompt: str | None = None,
    temperature: float = 0.7, max_tokens: int = 2048,
) -> AsyncGenerator[str, None]:
    # yields: f"data: {json.dumps({'type': 'token', 'delta': text})}\n\n"
    # yields: f"data: {json.dumps({'type': 'done', 'message_id': ...})}\n\n"
    # yields: f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
```

Alembic conventions (from existing migrations 0003-0005):
- Filename: 0006_add_trace_data_to_message.py
- Uses op.batch_alter_table for SQLite ALTER TABLE compatibility
- revision and down_revision strings, upgrade()/downgrade() functions
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: TraceEmitter service and TraceEvent dataclass</name>
  <files>backend/app/services/trace_emitter.py</files>
  <behavior>
    - TraceEvent is a dataclass with fields: id (str uuid4), type (Literal["run_start","run_end","token_generation","error"]), name (str), status (Literal["running","completed","error"]), started_at (str ISO8601), completed_at (str | None), input (Any | None = None), output (Any | None = None), error (str | None = None), metadata (dict | None = None)
    - TraceEmitter.__init__ creates empty self._events: list[TraceEvent]
    - TraceEmitter.start_run() appends run_start event with status="running", returns the event
    - TraceEmitter.end_run(success: bool) appends run_end event, sets completed_at, status="completed" or "error"
    - TraceEmitter.emit_token_generation(token_count: int) appends token_generation event, status="completed"
    - TraceEmitter.emit_error(error_message: str) appends error event, status="error"
    - TraceEmitter.to_json() returns json.dumps([dataclasses.asdict(e) for e in self._events])
    - TraceEmitter.events property returns list copy of self._events
  </behavior>
  <action>
    Create backend/app/services/__init__.py (empty, to make it a package) and backend/app/services/trace_emitter.py.

    Use Python dataclasses (not Pydantic) since this is an internal service. Import: dataclasses, uuid, json, datetime, typing.

    TraceEvent dataclass — all fields as described in behavior block. Use field(default=None) for optional fields.

    TraceEmitter class:
    - _events: list[TraceEvent] initialized in __init__
    - _now() staticmethod returns datetime.now(UTC).isoformat()
    - start_run(name: str = "chat_turn") -> TraceEvent: creates run_start event with status="running", started_at=now, completed_at=None, appends, returns it
    - end_run(success: bool = True) -> TraceEvent: creates run_end event with status="completed" if success else "error", completed_at=now
    - emit_token_generation(token_count: int = 0) -> TraceEvent: type="token_generation", name="token_generation", status="completed"
    - emit_error(error_message: str) -> TraceEvent: type="error", name="error", status="error", error=error_message, completed_at=now
    - to_json() -> str: returns JSON array of all events as dicts
    - events property -> list[TraceEvent]: returns list(self._events)

    Write the test file at backend/app/tests/test_trace_emitter.py first (TDD RED), then implement until tests pass (TDD GREEN).
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/backend && python -m pytest app/tests/test_trace_emitter.py -v</automated>
  </verify>
  <done>
    All test cases pass. TraceEmitter collects events in order, to_json() produces valid JSON array matching TraceEvent schema.
  </done>
</task>

<task type="auto">
  <name>Task 2: Message.trace_data field and Alembic migration</name>
  <files>
    backend/app/models/message.py,
    backend/alembic/versions/0006_add_trace_data_to_message.py
  </files>
  <action>
    1. Edit backend/app/models/message.py — add nullable trace_data field:
       ```python
       from typing import Optional
       from sqlmodel import Field, SQLModel
       # add to Message class:
       trace_data: Optional[str] = Field(default=None, sa_column_kwargs={"nullable": True})
       ```
       The field is a nullable TEXT column storing the JSON-serialized trace array. Store as str (not JSON type) for SQLite compatibility.

    2. Create backend/alembic/versions/0006_add_trace_data_to_message.py:
       - revision = "0006"
       - down_revision = "0005"  (match the actual revision ID from 0005_chat_completions_fields.py)
       - upgrade(): use op.batch_alter_table("message") context manager, add column "trace_data" as sa.Text, nullable=True
       - downgrade(): use op.batch_alter_table("message"), drop_column("trace_data")

       IMPORTANT: Check the actual down_revision by reading the revision string from 0005_chat_completions_fields.py before writing. Do not hardcode "0005" if the actual revision ID differs.

    3. Run migration: cd /Users/przbadu/dev/claude-clone/backend && alembic upgrade head

    Verify migration applies cleanly and reverses cleanly.
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/backend && alembic upgrade head && alembic downgrade -1 && alembic upgrade head</automated>
  </verify>
  <done>
    Message model has trace_data: Optional[str] field. Migration applies and reverses without error. alembic upgrade head succeeds twice (idempotent).
  </done>
</task>

<task type="auto">
  <name>Task 3: Extend _token_generator with TraceEmitter and trace SSE events</name>
  <files>backend/app/api/v1/chat.py</files>
  <action>
    Modify _token_generator in backend/app/api/v1/chat.py to integrate TraceEmitter:

    1. Import TraceEmitter at top of file:
       ```python
       from app.services.trace_emitter import TraceEmitter
       ```

    2. At the start of _token_generator body (before the try block):
       ```python
       tracer = TraceEmitter()
       run_event = tracer.start_run(name="chat_turn")
       yield f"data: {json.dumps({'type': 'trace_event', 'event': dataclasses.asdict(run_event)})}\n\n"
       ```
       Add `import dataclasses` at the top of the file.

    3. After the streaming loop completes successfully (after `async for chunk in stream`), before persisting the message:
       ```python
       token_event = tracer.emit_token_generation(token_count=len(full_content))
       yield f"data: {json.dumps({'type': 'trace_event', 'event': dataclasses.asdict(token_event)})}\n\n"
       end_event = tracer.end_run(success=True)
       yield f"data: {json.dumps({'type': 'trace_event', 'event': dataclasses.asdict(end_event)})}\n\n"
       ```

    4. When persisting assistant_msg after successful stream, add trace_data:
       ```python
       assistant_msg = Message(
           conversation_id=conversation_id,
           role="assistant",
           content=full_content,
           trace_data=tracer.to_json(),
       )
       ```

    5. In the except Exception as e block, emit error trace event before yielding the error SSE:
       ```python
       error_event = tracer.emit_error(str(e))
       yield f"data: {json.dumps({'type': 'trace_event', 'event': dataclasses.asdict(error_event)})}\n\n"
       end_event = tracer.end_run(success=False)
       yield f"data: {json.dumps({'type': 'trace_event', 'event': dataclasses.asdict(end_event)})}\n\n"
       ```
       When saving partial content on error, include trace_data=tracer.to_json() on the Message.

    6. In the CancelledError/GeneratorExit block: emit end_run(success=False) but do NOT yield it (stream is cancelled). When saving partial content, include trace_data=tracer.to_json().

    Also update MessageRead schema in chat.py to include trace_data:
    ```python
    class MessageRead(BaseModel):
        id: int
        conversation_id: int
        role: str
        content: str
        trace_data: str | None = None
        created_at: datetime
    ```

    Update get_messages endpoint to include trace_data in the MessageRead mapping:
    ```python
    MessageRead(
        id=m.id,
        conversation_id=m.conversation_id,
        role=m.role,
        content=m.content,
        trace_data=m.trace_data,
        created_at=m.created_at,
    )
    ```

    Run ruff and mypy after changes.
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/backend && python -m pytest app/tests/test_chat.py -v -k "stream" 2>/dev/null || python -m pytest app/tests/test_chat.py -v && python -m ruff check app/api/v1/chat.py && python -m mypy app/api/v1/chat.py --ignore-missing-imports</automated>
  </verify>
  <done>
    _token_generator emits trace_event SSE lines for run_start, token_generation, run_end. On completion, assistant_msg.trace_data is populated with JSON array. MessageRead includes trace_data. ruff and mypy pass.
  </done>
</task>

</tasks>

<verification>
1. `cd /Users/przbadu/dev/claude-clone/backend && python -m pytest app/tests/test_trace_emitter.py -v` — all tests pass
2. `cd /Users/przbadu/dev/claude-clone/backend && alembic upgrade head` — migration applies cleanly
3. `cd /Users/przbadu/dev/claude-clone/backend && python -m ruff check app/ && python -m mypy app/ --ignore-missing-imports` — no violations
4. `cd /Users/przbadu/dev/claude-clone/backend && python -m pytest app/tests/test_chat.py -v` — existing chat tests still pass
</verification>

<success_criteria>
- TraceEmitter.to_json() produces a valid JSON array with at minimum run_start and run_end events in order
- Alembic migration 0006 applies and reverses without error
- SSE stream yields `{"type": "trace_event", "event": {...}}` lines alongside token lines
- Completed assistant messages have trace_data populated (non-null) in the database
- MessageRead includes trace_data field; GET /conversations/{id}/messages returns trace_data for each message
- ruff, mypy, and existing pytest suite all pass
</success_criteria>

<output>
After completion, create `.planning/phases/06-execution-trace-system/06-01-SUMMARY.md` documenting:
- TraceEmitter API (methods, event types, JSON shape)
- SSE event type added: trace_event with nested event object
- Message.trace_data field type (nullable str/TEXT)
- Migration revision ID for 0006
- Any deviations from plan
</output>

---
---
phase: 06-execution-trace-system
plan: 02
type: execute
wave: 2
depends_on:
  - "06-01"
files_modified:
  - frontend/src/types/chat.ts
  - frontend/src/hooks/useChat.ts
  - frontend/src/components/chat/TracePanel.tsx
  - frontend/src/components/chat/MessageBubble.tsx
autonomous: true
requirements:
  - TRACE-01
  - TRACE-02
  - TRACE-03
  - TRACE-05

must_haves:
  truths:
    - "Each assistant message renders a collapsible Execution Trace section below the content"
    - "Trace section is collapsed by default, expands on click"
    - "Expanded trace shows ordered events with type icon, name, status badge, and timestamps"
    - "Trace events accumulate in useChat state during SSE streaming"
    - "On conversation resume, trace_data from API is parsed and rendered immediately"
  artifacts:
    - path: "frontend/src/components/chat/TracePanel.tsx"
      provides: "Collapsible trace event list component"
      exports: ["TracePanel"]
    - path: "frontend/src/types/chat.ts"
      provides: "TraceEvent type, SSETraceEvent type, updated Message type"
      exports: ["TraceEvent", "SSETraceEvent", "Message"]
  key_links:
    - from: "frontend/src/hooks/useChat.ts"
      to: "frontend/src/types/chat.ts TraceEvent"
      via: "messageTraces state: Record<number, TraceEvent[]>"
      pattern: "messageTraces"
    - from: "frontend/src/components/chat/MessageBubble.tsx"
      to: "frontend/src/components/chat/TracePanel.tsx"
      via: "traceEvents prop passed to TracePanel when role=assistant"
      pattern: "TracePanel"
    - from: "frontend/src/hooks/useChat.ts"
      to: "SSE trace_event events"
      via: "parse event.type === 'trace_event', accumulate by pending message id"
      pattern: "trace_event"
---

<objective>
Build the frontend trace infrastructure: TraceEvent types, SSE handler in useChat, TracePanel component, MessageBubble integration, and trace replay on conversation load.

Purpose: Make execution traces visible and interactive in the chat UI, collapsed by default and expandable per message.
Output: TracePanel component, updated useChat accumulating trace events, MessageBubble rendering TracePanel for assistant messages.
</objective>

<execution_context>
@/Users/przbadu/.claude/get-shit-done/workflows/execute-plan.md
@/Users/przbadu/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/phases/06-execution-trace-system/6-CONTEXT.md
@.planning/phases/06-execution-trace-system/06-01-SUMMARY.md

Locked decisions from CONTEXT.md (NON-NEGOTIABLE):
- D-08: Each assistant message has a collapsible "Execution Trace" section
- D-09: Collapsed by default — click to expand
- D-10: Shows ordered events with type icon, name, status badge, timestamps
- D-11: Compact input/output preview with safe truncation
- D-12: Resuming conversation loads traces from DB and renders in UI
- D-13: No re-execution — render persisted trace data only

Claude's Discretion (make reasonable choices):
- Trace panel visual design (use Tailwind + shadcn Collapsible or simple state toggle)
- Type icons: use lucide-react icons (Activity for run_start/run_end, Zap for token_generation, AlertCircle for error)
- Status badge colors: running=yellow, completed=green, error=red
- Timestamp format: relative time (e.g., "12ms") for completed_at - started_at delta, absolute ISO for display
- Truncation: cap input/output preview at 200 chars

<interfaces>
From frontend/src/types/chat.ts (current):
```typescript
export interface Message {
  id: number;
  conversation_id: number;
  role: "user" | "assistant" | "system";
  content: string;
  created_at: string;
}
export type SSEEvent = SSETokenEvent | SSEDoneEvent | SSEErrorEvent | SSEStoppedEvent;
```

From 06-01 plan output (TraceEvent JSON shape — confirm exact fields from 06-01-SUMMARY.md):
```typescript
// TraceEvent from backend
export interface TraceEvent {
  id: string;           // uuid4
  type: "run_start" | "run_end" | "token_generation" | "error";
  name: string;
  status: "running" | "completed" | "error";
  started_at: string;   // ISO8601
  completed_at: string | null;
  input?: unknown;
  output?: unknown;
  error?: string | null;
  metadata?: Record<string, unknown> | null;
}
```

From 06-01 plan: SSE now emits an additional event type:
```typescript
export interface SSETraceEvent {
  type: "trace_event";
  event: TraceEvent;
}
// Update SSEEvent union:
export type SSEEvent = SSETokenEvent | SSEDoneEvent | SSEErrorEvent | SSEStoppedEvent | SSETraceEvent;
```

Message.trace_data is now `string | null` (JSON array of TraceEvent).

From frontend/src/hooks/useChat.ts (existing):
- messages: Message[] state
- sendMessage accumulates SSE events in the streaming loop
- On "done" event: creates assistantMsg from accumulated content

From frontend/src/components/chat/MessageBubble.tsx (existing):
```typescript
interface MessageBubbleProps {
  role: "user" | "assistant";
  content: string;
  isStreaming?: boolean;
}
```
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add TraceEvent types and update SSEEvent union</name>
  <files>frontend/src/types/chat.ts</files>
  <action>
    Edit frontend/src/types/chat.ts:

    1. Add TraceEvent interface after the existing Message interface:
    ```typescript
    export interface TraceEvent {
      id: string;
      type: "run_start" | "run_end" | "token_generation" | "error";
      name: string;
      status: "running" | "completed" | "error";
      started_at: string;
      completed_at: string | null;
      input?: unknown;
      output?: unknown;
      error?: string | null;
      metadata?: Record<string, unknown> | null;
    }
    ```

    2. Add trace_data field to Message interface:
    ```typescript
    export interface Message {
      // ...existing fields...
      trace_data: string | null;  // JSON array of TraceEvent
    }
    ```

    3. Add SSETraceEvent interface:
    ```typescript
    export interface SSETraceEvent {
      type: "trace_event";
      event: TraceEvent;
    }
    ```

    4. Update SSEEvent union to include SSETraceEvent:
    ```typescript
    export type SSEEvent = SSETokenEvent | SSEDoneEvent | SSEErrorEvent | SSEStoppedEvent | SSETraceEvent;
    ```
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/frontend && npx tsc --noEmit 2>&1 | head -30</automated>
  </verify>
  <done>TypeScript compiles with no new errors. TraceEvent, SSETraceEvent exported from types/chat.ts.</done>
</task>

<task type="auto">
  <name>Task 2: TracePanel component</name>
  <files>frontend/src/components/chat/TracePanel.tsx</files>
  <action>
    Create frontend/src/components/chat/TracePanel.tsx as a "use client" component.

    Props interface:
    ```typescript
    interface TracePanelProps {
      events: TraceEvent[];
      isStreaming?: boolean;  // show live indicator when trace is still accumulating
    }
    ```

    Implementation:
    - Use React useState for isOpen: boolean (default false)
    - Render a trigger button: "Execution Trace" label with ChevronDown/ChevronUp icon from lucide-react toggling on click
    - When collapsed: show only the trigger button row
    - When expanded: render an ordered list of trace events

    Per-event row layout (use Tailwind):
    - Type icon (lucide-react): Activity for run_start/run_end, Zap for token_generation, AlertCircle for error
    - Event name (truncated to 40 chars)
    - Status badge: small pill with color — running=yellow bg, completed=green bg, error=red bg
    - Timestamp: if completed_at and started_at present, show duration in ms (e.g., "12ms"); otherwise show started_at time only (format: HH:mm:ss)
    - If event.error is non-null: show error text below in red, truncated to 100 chars
    - If event.input or event.output present: show as truncated JSON preview (max 200 chars) in a monospace code element

    Helper: truncateJson(val: unknown, maxLen = 200): string — JSON.stringify(val).slice(0, maxLen) + (longer ? "…" : "")

    When isStreaming=true and isOpen=true: show a subtle "Recording..." indicator with a pulsing dot at the bottom of the event list.

    Import TraceEvent from "@/types/chat".
    Use cn() from "@/lib/utils" for conditional classes.
    No external dependencies beyond lucide-react (already installed).
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/frontend && npx tsc --noEmit 2>&1 | head -30</automated>
  </verify>
  <done>TracePanel.tsx compiles. Component accepts TraceEvent[], renders collapsed by default, expands to show event list with icons, status badges, and timestamps.</done>
</task>

<task type="auto">
  <name>Task 3: Wire useChat trace accumulation and integrate TracePanel into MessageBubble</name>
  <files>
    frontend/src/hooks/useChat.ts,
    frontend/src/components/chat/MessageBubble.tsx,
    frontend/src/components/chat/ChatPanel.tsx
  </files>
  <action>
    ### useChat.ts changes

    1. Import TraceEvent from "@/types/chat"

    2. Add state for in-flight trace accumulation:
       ```typescript
       const [streamingTraceEvents, setStreamingTraceEvents] = useState<TraceEvent[]>([]);
       const [messageTraces, setMessageTraces] = useState<Record<number, TraceEvent[]>>({});
       ```

    3. In the SSE parsing loop inside sendMessage, add handler for trace_event:
       ```typescript
       } else if (event.type === "trace_event") {
         setStreamingTraceEvents(prev => [...prev, event.event]);
       }
       ```

    4. On "done" event: attach accumulated trace to the message, clear streaming trace:
       ```typescript
       } else if (event.type === "done") {
         const traceSnapshot = streamingTraceEvents; // capture ref
         const assistantMsg: Message = {
           id: event.message_id,
           conversation_id: conversationId,
           role: "assistant",
           content: accumulated,
           trace_data: null,  // raw field; use messageTraces for live data
           created_at: new Date().toISOString(),
         };
         setMessages(prev => [...prev, assistantMsg]);
         setMessageTraces(prev => ({ ...prev, [event.message_id]: traceSnapshot }));
         setStreamingTraceEvents([]);
         setStreamingContent(null);
         setIsStreaming(false);
         // ... (keep existing onConversationUpdated logic)
       }
       ```

       NOTE: Because streamingTraceEvents is state (not a ref), capture it before the async setState to avoid closure staleness. Use a ref to track the accumulation synchronously:
       - Add `const traceEventsRef = useRef<TraceEvent[]>([])`
       - In trace_event handler: push to traceEventsRef.current AND call setStreamingTraceEvents
       - On "done": use traceEventsRef.current snapshot, then clear both

    5. On conversation load (getMessages call in useEffect), parse trace_data from loaded messages:
       ```typescript
       const traces: Record<number, TraceEvent[]> = {};
       msgs.forEach(m => {
         if (m.role === "assistant" && m.trace_data) {
           try {
             traces[m.id] = JSON.parse(m.trace_data) as TraceEvent[];
           } catch { /* skip malformed */ }
         }
       });
       setMessageTraces(traces);
       ```

    6. Clear messageTraces and traceEventsRef when conversationId changes (in the useEffect cleanup or at the top of the effect before loading).

    7. Update UseChatReturn interface to expose:
       ```typescript
       messageTraces: Record<number, TraceEvent[]>;
       streamingTraceEvents: TraceEvent[];
       ```

    ### MessageBubble.tsx changes

    Update props interface:
    ```typescript
    interface MessageBubbleProps {
      role: "user" | "assistant";
      content: string;
      isStreaming?: boolean;
      traceEvents?: TraceEvent[];  // for completed messages
      liveTraceEvents?: TraceEvent[];  // for currently streaming message
    }
    ```

    Import TraceEvent from "@/types/chat" and TracePanel from "./TracePanel".

    For assistant messages, render TracePanel below the markdown content:
    ```typescript
    {!isUser && (
      <>
        <MarkdownRenderer content={content} />
        {isStreaming && <span className="..." />}
        {(traceEvents?.length || liveTraceEvents?.length) ? (
          <div className="mt-2 border-t border-muted pt-2">
            <TracePanel
              events={traceEvents ?? liveTraceEvents ?? []}
              isStreaming={!!isStreaming}
            />
          </div>
        ) : null}
      </>
    )}
    ```

    ### ChatPanel.tsx changes

    Destructure messageTraces and streamingTraceEvents from useChat:
    ```typescript
    const {
      messages, streamingContent, isStreaming, error,
      sendMessage, stopGeneration, regenerate,
      messageTraces, streamingTraceEvents,
    } = useChat({ conversationId, onConversationUpdated });
    ```

    Pass trace data to MessageBubble renders:
    ```typescript
    {messages.map(msg => (
      <MessageBubble
        key={msg.id}
        role={msg.role as "user" | "assistant"}
        content={msg.content}
        traceEvents={messageTraces[msg.id]}
      />
    ))}

    {streamingContent !== null && (
      <MessageBubble
        role="assistant"
        content={streamingContent}
        isStreaming
        liveTraceEvents={streamingTraceEvents}
      />
    )}
    ```
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/frontend && npx tsc --noEmit 2>&1 | head -30</automated>
  </verify>
  <done>
    TypeScript compiles with no errors. useChat exposes messageTraces and streamingTraceEvents. MessageBubble accepts and renders TracePanel for assistant messages. ChatPanel passes trace data through.
  </done>
</task>

</tasks>

<verification>
1. `cd /Users/przbadu/dev/claude-clone/frontend && npx tsc --noEmit` — zero type errors
2. `cd /Users/przbadu/dev/claude-clone/frontend && npx eslint src/types/chat.ts src/hooks/useChat.ts src/components/chat/TracePanel.tsx src/components/chat/MessageBubble.tsx src/components/chat/ChatPanel.tsx` — zero lint errors
3. `cd /Users/przbadu/dev/claude-clone/frontend && npx vitest run src/__tests__/chat.test.tsx` — existing tests pass
</verification>

<success_criteria>
- TraceEvent and SSETraceEvent types exported from types/chat.ts
- Message type includes trace_data: string | null
- useChat accumulates trace_event SSE lines into streamingTraceEvents during streaming
- On "done" event, traces are moved into messageTraces keyed by message_id
- On conversation load, existing trace_data parsed from messages and populated into messageTraces
- MessageBubble renders TracePanel for assistant messages when traceEvents present
- TracePanel collapsed by default; expands on click to show event list with icons, badges, timestamps
- All TypeScript and ESLint checks pass
</success_criteria>

<output>
After completion, create `.planning/phases/06-execution-trace-system/06-02-SUMMARY.md` documenting:
- TracePanel component API and visual design choices (icons, colors, truncation)
- useChat state additions (messageTraces, streamingTraceEvents, traceEventsRef)
- How trace replay works on conversation load (parse trace_data in getMessages effect)
- Any deviations from plan
</output>

---
---
phase: 06-execution-trace-system
plan: 03
type: execute
wave: 3
depends_on:
  - "06-01"
  - "06-02"
files_modified:
  - backend/app/tests/test_trace_emitter.py
  - backend/app/tests/test_trace_integration.py
  - frontend/src/__tests__/trace-panel.test.tsx
autonomous: true
requirements:
  - TRACE-01
  - TRACE-02
  - TRACE-03
  - TRACE-04
  - TRACE-05

must_haves:
  truths:
    - "TraceEmitter unit tests verify event ordering, JSON serialization, and all event types"
    - "Backend integration test verifies trace_event SSE lines in stream response"
    - "Backend integration test verifies trace_data persisted on message after stream"
    - "Backend integration test verifies GET messages returns trace_data for assistant messages"
    - "Frontend component test verifies TracePanel renders collapsed, expands on click, shows events"
  artifacts:
    - path: "backend/app/tests/test_trace_emitter.py"
      provides: "Unit tests for TraceEmitter service"
      contains: "test_event_ordering"
    - path: "backend/app/tests/test_trace_integration.py"
      provides: "Integration tests for trace SSE and persistence"
      contains: "test_trace_events_in_stream"
    - path: "frontend/src/__tests__/trace-panel.test.tsx"
      provides: "Component tests for TracePanel"
      contains: "TracePanel"
  key_links:
    - from: "backend/app/tests/test_trace_integration.py"
      to: "backend/app/api/v1/chat.py /_token_generator"
      via: "httpx AsyncClient SSE response parsing"
      pattern: "trace_event"
    - from: "frontend/src/__tests__/trace-panel.test.tsx"
      to: "frontend/src/components/chat/TracePanel.tsx"
      via: "Vitest + @testing-library/react render + userEvent.click"
      pattern: "TracePanel"
---

<objective>
Write all tests for Phase 6: TraceEmitter unit tests (if not already written by Task 1 of Plan 01), backend SSE integration tests verifying trace event emission and persistence, and frontend component tests for TracePanel.

Purpose: Validate the full trace pipeline from emission to UI rendering, and establish regression coverage for Phase 7 trace extensions.
Output: Passing test suites at all layers with verified trace event ordering, persistence, and UI interactions.
</objective>

<execution_context>
@/Users/przbadu/.claude/get-shit-done/workflows/execute-plan.md
@/Users/przbadu/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/phases/06-execution-trace-system/6-CONTEXT.md
@.planning/phases/06-execution-trace-system/06-01-SUMMARY.md
@.planning/phases/06-execution-trace-system/06-02-SUMMARY.md

<interfaces>
From backend/app/tests/conftest.py:
```python
@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    # Starts app lifespan (creates DB tables, seeds admin)
    # Returns AsyncClient with base_url="http://test"

@pytest_asyncio.fixture
async def auth_client(client: AsyncClient) -> AsyncGenerator[AsyncClient, None]:
    # Logs in as admin, sets Authorization header
    # Returns authenticated AsyncClient
```

Pattern for SSE testing (from existing test_chat.py — check and follow its patterns):
- POST to `/api/v1/chat/{conversation_id}/stream` with stream=False to get full response
- Split response.text by "\n\n" to get SSE lines
- Parse each line: strip "data: ", json.loads()
- Filter by type to find specific events

From frontend/src/__tests__/chat.test.tsx (check existing patterns for consistency):
- Uses vitest, @testing-library/react, MSW (or fetch mocks)
- Check what mock patterns are already established

TraceEvent shape (from 06-01-SUMMARY.md):
- Confirm exact field names before writing assertions
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Backend TraceEmitter unit tests (if not created in Plan 01) + SSE integration tests</name>
  <files>
    backend/app/tests/test_trace_emitter.py,
    backend/app/tests/test_trace_integration.py
  </files>
  <action>
    ### test_trace_emitter.py

    If this file was already created as part of Plan 01 Task 1 (TDD), check if it's complete. If incomplete or missing, write it now.

    Required test cases:
    1. test_start_run_creates_run_start_event: TraceEmitter().start_run() produces event with type="run_start", status="running", completed_at=None
    2. test_end_run_success: end_run(success=True) produces event with type="run_end", status="completed", completed_at not None
    3. test_end_run_failure: end_run(success=False) produces event with type="run_end", status="error"
    4. test_emit_token_generation: produces event with type="token_generation", status="completed"
    5. test_emit_error: produces event with type="error", status="error", error field populated
    6. test_event_ordering: start_run, emit_token_generation, end_run — events list is in insertion order, len==3
    7. test_to_json_produces_valid_json: to_json() parses back as list, each item has "id", "type", "name", "status", "started_at"
    8. test_events_property_returns_copy: mutating returned list doesn't affect internal state

    ### test_trace_integration.py

    Write integration tests using auth_client fixture. Check test_chat.py for the pattern to create a conversation and set up a default LLM provider (or mock the LLM call).

    IMPORTANT: The stream endpoint calls an external LLM. Look at existing test_chat.py to see how it handles this — either it mocks the OpenAI client or skips if no provider. Follow the same pattern.

    Required test cases:
    1. test_stream_emits_trace_events: POST to stream endpoint, collect SSE events, assert at least one event with type="trace_event" exists in the response
    2. test_trace_event_has_correct_shape: first trace_event has fields: type="trace_event", event.type in ["run_start", "run_end", "token_generation"], event.id is a string, event.status in ["running", "completed", "error"]
    3. test_trace_data_persisted_on_message: after stream completes, GET /conversations/{id}/messages, find the assistant message, assert trace_data is not None, parse JSON, assert it's a list of at least 2 items
    4. test_get_messages_includes_trace_data: verify MessageRead response includes trace_data field (can be null for old messages, non-null for traced ones)
    5. test_error_produces_error_trace_event: mock a streaming error (or use an invalid model), assert the SSE stream includes a trace_event with event.type="error" or event.status="error"

    For tests that require LLM mocking, use unittest.mock.patch or pytest monkeypatch to mock `AsyncOpenAI` or the specific streaming call. Look at the existing test pattern in test_chat.py first.
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/backend && python -m pytest app/tests/test_trace_emitter.py app/tests/test_trace_integration.py -v</automated>
  </verify>
  <done>All TraceEmitter unit tests pass. At least 3 integration tests pass (trace events in SSE, trace_data persisted, MessageRead includes trace_data).</done>
</task>

<task type="auto">
  <name>Task 2: Frontend TracePanel component tests</name>
  <files>frontend/src/__tests__/trace-panel.test.tsx</files>
  <action>
    Create frontend/src/__tests__/trace-panel.test.tsx.

    Check existing tests (e.g., chat.test.tsx, markdown-renderer.test.tsx) for import patterns, render setup, and any global test utilities.

    Sample TraceEvent fixtures to reuse across tests:
    ```typescript
    const runStartEvent: TraceEvent = {
      id: "evt-1",
      type: "run_start",
      name: "chat_turn",
      status: "running",
      started_at: "2026-03-21T10:00:00.000Z",
      completed_at: null,
    };
    const tokenEvent: TraceEvent = {
      id: "evt-2",
      type: "token_generation",
      name: "token_generation",
      status: "completed",
      started_at: "2026-03-21T10:00:00.010Z",
      completed_at: "2026-03-21T10:00:01.500Z",
    };
    const errorEvent: TraceEvent = {
      id: "evt-3",
      type: "error",
      name: "error",
      status: "error",
      started_at: "2026-03-21T10:00:00.000Z",
      completed_at: "2026-03-21T10:00:00.100Z",
      error: "LLM connection failed",
    };
    ```

    Required test cases:
    1. test_renders_collapsed_by_default: render TracePanel with events, assert "Execution Trace" button is visible, assert event names are NOT visible (collapsed)
    2. test_expands_on_click: click the "Execution Trace" button, assert event names become visible
    3. test_shows_event_names_when_expanded: expand panel, assert "chat_turn" (run_start name) is in document
    4. test_shows_status_badge: expand panel, assert status text "running" or "completed" appears
    5. test_error_event_shows_error_message: render with errorEvent, expand, assert "LLM connection failed" is visible
    6. test_empty_events_renders_without_crash: render TracePanel with events=[], should not throw
    7. test_streaming_indicator: render with isStreaming=true, expand panel, assert "Recording" text is present (or pulsing indicator)
    8. test_collapses_again_on_second_click: expand then click again, assert event names no longer visible

    Use @testing-library/react render and userEvent (or fireEvent) for click interactions. Import TracePanel from "@/components/chat/TracePanel".
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/frontend && npx vitest run src/__tests__/trace-panel.test.tsx</automated>
  </verify>
  <done>All 8 TracePanel tests pass. TracePanel collapse/expand, event rendering, error display, and streaming indicator are all verified.</done>
</task>

<task type="auto">
  <name>Task 3: Full suite verification and lint</name>
  <files></files>
  <action>
    Run the complete test suites and linters to confirm Phase 6 is complete and nothing is broken.

    Backend:
    1. `cd /Users/przbadu/dev/claude-clone/backend && python -m pytest app/tests/ -v --tb=short` — all tests pass
    2. `cd /Users/przbadu/dev/claude-clone/backend && python -m ruff check app/` — no violations
    3. `cd /Users/przbadu/dev/claude-clone/backend && python -m mypy app/ --ignore-missing-imports` — no errors

    Frontend:
    4. `cd /Users/przbadu/dev/claude-clone/frontend && npx vitest run` — all tests pass
    5. `cd /Users/przbadu/dev/claude-clone/frontend && npx tsc --noEmit` — no type errors
    6. `cd /Users/przbadu/dev/claude-clone/frontend && npx eslint src/` — no lint errors

    If any test fails, diagnose and fix before marking this task done. Do not skip or skip-mark failures — fix them.
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/backend && python -m pytest app/tests/ -v --tb=short 2>&1 | tail -20 && cd /Users/przbadu/dev/claude-clone/frontend && npx vitest run 2>&1 | tail -20</automated>
  </verify>
  <done>
    - Backend: all pytest tests pass, ruff and mypy clean
    - Frontend: all vitest tests pass, tsc --noEmit zero errors, eslint zero violations
  </done>
</task>

</tasks>

<verification>
1. `cd /Users/przbadu/dev/claude-clone/backend && python -m pytest app/tests/ -v` — all tests pass including new trace tests
2. `cd /Users/przbadu/dev/claude-clone/frontend && npx vitest run` — all tests pass including trace-panel.test.tsx
3. `cd /Users/przbadu/dev/claude-clone/backend && python -m ruff check app/ && python -m mypy app/ --ignore-missing-imports` — clean
4. `cd /Users/przbadu/dev/claude-clone/frontend && npx tsc --noEmit && npx eslint src/` — clean
</verification>

<success_criteria>
- 8+ TraceEmitter unit tests pass verifying event ordering, JSON serialization, error events
- 5+ backend integration tests pass verifying trace_event SSE emission and trace_data persistence
- 8+ TracePanel component tests pass verifying collapse/expand, event rendering, error display
- Full backend pytest suite green (no regressions)
- Full frontend vitest suite green (no regressions)
- All linters and type checkers pass
- Every TRACE-0x requirement (01-05) is covered by at least one passing test
</success_criteria>

<output>
After completion, create `.planning/phases/06-execution-trace-system/06-03-SUMMARY.md` documenting:
- Test counts per file
- Mock strategy used for LLM in integration tests
- Any test gaps or known limitations
- Phase 6 complete status confirmation
</output>
