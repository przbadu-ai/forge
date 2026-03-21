# Architecture Research

**Domain:** Local-first AI assistant chat application (Next.js + FastAPI split stack)
**Researched:** 2026-03-21
**Confidence:** HIGH (patterns verified across official docs, multiple implementation guides, and production projects)

## Standard Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                        BROWSER / CLIENT                           │
├──────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │  Chat UI     │  │  Settings UI │  │  Trace UI    │            │
│  │  (Streaming) │  │  (CRUD)      │  │  (Expandable)│            │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘            │
│         │                 │                  │                    │
│  ┌──────▼─────────────────▼──────────────────▼───────┐            │
│  │           Next.js App Router (Frontend)            │            │
│  │  Server Components · Route Handlers · API Proxy    │            │
│  └──────────────────────────┬─────────────────────────┘            │
└─────────────────────────────┼────────────────────────────────────┘
                              │ HTTP / SSE
┌─────────────────────────────▼────────────────────────────────────┐
│                    FastAPI Backend (Python)                        │
├──────────────────────────────────────────────────────────────────┤
│  ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐  │
│  │  /chat     │  │  /files    │  │  /settings │  │  /health   │  │
│  │  Router    │  │  Router    │  │  Router    │  │  Router    │  │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  └────────────┘  │
│        │               │               │                          │
│  ┌─────▼───────────────▼───────────────▼──────────────────────┐  │
│  │                  Orchestrator Service                        │  │
│  │          model → tools/MCP/skills → model loop              │  │
│  │   ToolExecutor · McpExecutor · SkillExecutor · TraceEmitter │  │
│  └─────────────────────────┬──────────────────────────────────┘  │
│                             │                                     │
│  ┌──────────────────────────▼────────────────────────────────┐   │
│  │              External / Integration Layer                   │   │
│  │  OpenAI-compat LLM  ·  MCP Servers  ·  Web Search APIs    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                    │
│  ┌────────────────────┐  ┌────────────────────────────────────┐   │
│  │   SQLite (SQLModel)│  │  ChromaDB                          │   │
│  │  conversations     │  │  embeddings · collections          │   │
│  │  messages          │  │  chunks → similarity search        │   │
│  │  traces            │  │                                    │   │
│  │  settings          │  │                                    │   │
│  │  files             │  │                                    │   │
│  └────────────────────┘  └────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Implementation |
|-----------|----------------|----------------|
| Next.js App Router | Chat UI, settings pages, SSE consumption, React state | Next.js 15, shadcn/ui, Tailwind |
| Route Handlers (Next.js) | Auth middleware, session, optional API proxy to FastAPI | `app/api/**` routes |
| FastAPI Routers | HTTP endpoints, request validation, response shaping | `app/routers/` |
| Orchestrator Service | Core agent loop: model call → tool dispatch → observation → model | `app/services/orchestrator.py` |
| ToolExecutor | Execute built-in tools (web search, code run), return results | `app/executors/tool_executor.py` |
| McpExecutor | Connect to MCP servers, invoke tools, handle responses | `app/executors/mcp_executor.py` |
| SkillExecutor | Run skill workflows (multi-step sequences) | `app/executors/skill_executor.py` |
| TraceEmitter | Emit SSE events per step (tool_start, tool_end, token, etc.) | `app/services/trace_emitter.py` |
| RunStateStore | Persist in-progress run state for resume/retry | `app/services/run_state_store.py` |
| File Pipeline | Accept uploads, chunk, embed, store in ChromaDB + SQLite metadata | `app/services/file_pipeline.py` |
| SQLite (SQLModel) | Persistent store: conversations, messages, traces, settings | Alembic migrations |
| ChromaDB | Vector store: embedded chunks for retrieval | Local persistent mode |

---

## Recommended Project Structure

### Backend (Python / FastAPI)

```
backend/
├── app/
│   ├── main.py                 # FastAPI app factory, middleware, lifespan
│   ├── config.py               # Settings from env (pydantic-settings)
│   ├── dependencies.py         # Shared FastAPI deps (db session, auth)
│   │
│   ├── routers/
│   │   ├── chat.py             # POST /chat/stream (SSE), CRUD conversations
│   │   ├── files.py            # POST /files/upload, GET /files/{id}
│   │   ├── settings.py         # GET/PUT settings, test-connection
│   │   ├── health.py           # GET /health, diagnostics panel
│   │   └── auth.py             # POST /auth/login, session
│   │
│   ├── models/                 # SQLModel ORM models (table=True)
│   │   ├── conversation.py
│   │   ├── message.py
│   │   ├── trace.py
│   │   ├── file_record.py
│   │   └── settings.py
│   │
│   ├── schemas/                # Pydantic request/response schemas
│   │   ├── chat.py
│   │   ├── file.py
│   │   └── settings.py
│   │
│   ├── services/
│   │   ├── orchestrator.py     # Core agent loop (model → tools → model)
│   │   ├── llm_client.py       # OpenAI-compat client wrapper
│   │   ├── trace_emitter.py    # SSE event emission, trace persistence
│   │   ├── run_state_store.py  # In-progress run state
│   │   ├── file_pipeline.py    # Upload → chunk → embed → store
│   │   ├── retrieval.py        # Query ChromaDB, rerank, return chunks
│   │   └── settings_service.py
│   │
│   ├── executors/
│   │   ├── tool_executor.py    # Built-in tool dispatch
│   │   ├── mcp_executor.py     # MCP server client + tool invocation
│   │   └── skill_executor.py   # Skill workflow runner
│   │
│   ├── db/
│   │   ├── database.py         # SQLModel engine, get_session
│   │   └── migrations/         # Alembic revisions
│   │
│   └── core/
│       ├── auth.py             # Password hash, session token verify
│       └── exceptions.py       # Domain exceptions
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── uploads/                    # File storage (not public/)
├── chroma_data/                # ChromaDB persistent storage
├── pyproject.toml
└── alembic.ini
```

### Frontend (Next.js / TypeScript)

```
frontend/
├── app/
│   ├── layout.tsx              # Root layout, theme provider
│   ├── page.tsx                # Redirect to /chat
│   ├── (auth)/
│   │   └── login/page.tsx      # Login page
│   ├── chat/
│   │   ├── layout.tsx          # Chat shell: sidebar + main area
│   │   ├── page.tsx            # New conversation entry
│   │   └── [id]/page.tsx       # Active conversation view
│   ├── settings/
│   │   ├── layout.tsx          # Settings shell with nav
│   │   ├── providers/page.tsx  # LLM providers + models
│   │   ├── mcp/page.tsx        # MCP server registration
│   │   ├── skills/page.tsx     # Skill enable/disable
│   │   ├── embeddings/page.tsx # Embedding model config
│   │   └── health/page.tsx     # Health diagnostics panel
│   └── api/
│       ├── auth/[...]/route.ts # Auth endpoints
│       └── proxy/[...]/route.ts # Optional proxy to FastAPI
│
├── components/
│   ├── ui/                     # shadcn/ui primitives
│   ├── chat/
│   │   ├── MessageList.tsx     # Conversation message feed
│   │   ├── MessageBubble.tsx   # Single message + trace accordion
│   │   ├── TracePanel.tsx      # Execution trace (tool calls, MCP, skills)
│   │   ├── ChatInput.tsx       # Composer with file attach
│   │   └── ConversationSidebar.tsx
│   ├── settings/
│   │   ├── ProviderForm.tsx
│   │   ├── McpServerCard.tsx
│   │   └── HealthCheck.tsx
│   └── shared/
│       ├── MarkdownRenderer.tsx
│       └── ThemeToggle.tsx
│
├── lib/
│   ├── api.ts                  # Typed API client (fetch wrappers)
│   ├── sse.ts                  # SSE connection manager
│   └── auth.ts                 # Client-side auth helpers
│
├── hooks/
│   ├── useChat.ts              # Chat state + SSE stream consumer
│   ├── useConversations.ts
│   └── useSettings.ts
│
├── stores/                     # Zustand state (or React Context)
│   ├── chatStore.ts
│   └── settingsStore.ts
│
└── types/
    ├── api.ts                  # API response types
    └── chat.ts                 # Domain types
```

### Structure Rationale

- **`services/` vs `executors/`:** Services contain business workflows and orchestration. Executors are single-responsibility adapters that wrap external systems (tools, MCP servers, skills). This separation means the orchestrator can be unit-tested by mocking executors.
- **`models/` vs `schemas/`:** SQLModel ORM models define the DB tables. Pydantic schemas define HTTP contract. Keeping them separate avoids leaking DB fields in API responses.
- **`uploads/` outside `app/`:** Files served via controlled FastAPI endpoint, not directly from the filesystem via Next.js static serving. Prevents path traversal exposure.
- **`hooks/` in frontend:** SSE stream state and conversation management are complex enough to warrant custom hooks. Keeps components focused on rendering.

---

## Architectural Patterns

### Pattern 1: Orchestrator Loop (Model → Tool → Model)

**What:** The orchestrator runs a while-loop that sends messages to the LLM, checks whether the response contains tool calls, executes them via the appropriate executor, appends results to the message history, and repeats until the model emits a final text response.

**When to use:** Any multi-step AI response where tools, MCP actions, or skills may be invoked before the final answer.

**Trade-offs:** Simple to implement and debug without a framework dependency. Lacks graph-level parallelism; sequential only. Acceptable for MVP single-user workload.

**Example:**

```python
# app/services/orchestrator.py
async def run(
    messages: list[Message],
    config: RunConfig,
    trace: TraceEmitter,
) -> AsyncIterator[ServerSentEvent]:
    history = [m.to_openai() for m in messages]
    max_iterations = config.max_iterations or 10

    for _ in range(max_iterations):
        # 1. Call LLM (streaming tokens to client via trace)
        response = await llm_client.complete(history, tools=config.tools)
        await trace.emit_token_stream(response.stream)

        item = response.first_item

        if item.type == "tool_call":
            # 2. Dispatch to appropriate executor
            await trace.emit(TraceEvent(type="tool_start", name=item.name))
            result = await dispatch_tool(item, config)
            await trace.emit(TraceEvent(type="tool_end", name=item.name, result=result))

            # 3. Feed result back into history
            history.append(item.to_openai())
            history.append({"role": "tool", "content": result, "tool_call_id": item.id})

        else:
            # 4. Final text response — exit loop
            await trace.persist()
            return

    await trace.emit(TraceEvent(type="error", message="max iterations reached"))
```

### Pattern 2: SSE Multiplexed Event Stream

**What:** A single SSE connection carries multiple named event types over the life of one orchestrator run: token deltas, trace events (tool_start, tool_end, mcp_call, skill_start), and control events (run_complete, run_error).

**When to use:** Any streaming AI response that needs concurrent token output and execution visibility in the frontend.

**Trade-offs:** One connection per chat turn (not persistent). Reconnect via `Last-Event-ID` for reliability. No WebSocket needed for this unidirectional flow.

**Example:**

```python
# SSE event types sent on single stream
{"event": "token",      "data": {"delta": "Hello"}}
{"event": "tool_start", "data": {"name": "web_search", "input": {...}}}
{"event": "tool_end",   "data": {"name": "web_search", "output": "..."}}
{"event": "mcp_call",   "data": {"server": "filesystem", "tool": "read_file"}}
{"event": "skill_start","data": {"skill": "code_review"}}
{"event": "run_done",   "data": {"message_id": "msg_123"}}
{"event": "run_error",  "data": {"error": "timeout"}}
```

```typescript
// hooks/useChat.ts — frontend SSE consumer
function consumeStream(url: string, onEvent: (e: SSEEvent) => void) {
  const es = new EventSource(url);
  es.addEventListener("token", e => onEvent({ type: "token", data: JSON.parse(e.data) }));
  es.addEventListener("tool_start", e => onEvent({ type: "tool_start", ...JSON.parse(e.data) }));
  es.addEventListener("run_done", e => { onEvent({ type: "done" }); es.close(); });
  es.addEventListener("run_error", e => { onEvent({ type: "error" }); es.close(); });
}
```

### Pattern 3: File Upload → Chunk → Embed → Retrieve Pipeline

**What:** Files are uploaded to `./uploads/`, metadata written to SQLite, content chunked and embedded, then stored in ChromaDB. At inference time, the user query is embedded and ChromaDB returns top-K similar chunks, which are injected into the LLM context.

**When to use:** Any message where document context is needed (RAG).

**Trade-offs:** SQLite holds file metadata and chunk associations; ChromaDB holds the vectors. Separating them allows richer filtering (by file, by conversation) before vector similarity. Reranking is optional but improves precision.

**Example:**

```
POST /files/upload
    ↓
FilePipeline.process(file_bytes, mime_type)
    ↓
chunk_document(text)      → [chunk_0, chunk_1, ..., chunk_N]
    ↓
embed_chunks(chunks)      → [vector_0, ..., vector_N]
    ↓
chromadb.add(ids, embeddings, documents, metadata)
    ↓
SQLite: FileRecord(id, name, path, chunk_count, collection_id)
    ↓
Return: file_id to frontend

-- At chat time --
user_query → embed → chromadb.query(top_k=5)
    ↓
[chunk_0, chunk_2, chunk_4]  (+ SQLite metadata for source display)
    ↓
injected into LLM system prompt as [CONTEXT]
```

### Pattern 4: Executor Interface (Adapter Pattern)

**What:** Each external system (built-in tools, MCP servers, skills) is wrapped behind a common executor interface. The orchestrator calls `executor.invoke(name, input)` without knowing which system handles it.

**When to use:** Whenever you add a new tool type. Keeps orchestrator logic stable as capabilities grow.

**Trade-offs:** Adds one indirection layer. Worth the cost because it makes unit testing the orchestrator trivial (mock all executors).

```python
# Consistent interface across all executor types
class BaseExecutor(ABC):
    async def invoke(self, name: str, input: dict) -> str: ...
    async def list_tools(self) -> list[ToolDefinition]: ...

class ToolExecutor(BaseExecutor): ...    # built-ins
class McpExecutor(BaseExecutor): ...     # MCP servers
class SkillExecutor(BaseExecutor): ...   # multi-step skills
```

---

## Data Flow

### Streaming Chat Turn

```
User types message → ChatInput
    ↓
POST /api/chat  (Next.js Route Handler or direct to FastAPI)
    ↓
FastAPI: create Message record (SQLite), start orchestrator run
    ↓
Orchestrator loop begins → SSE stream opened (EventSourceResponse)
    ↓
For each iteration:
    LLM call → stream token events → frontend appends to MessageBubble
    Tool call detected → emit tool_start → execute → emit tool_end
    Result appended to history → next iteration
    ↓
Final text response → emit run_done
    ↓
FastAPI: persist final Message + Trace to SQLite
    ↓
Frontend: SSE connection closes, TracePanel populated from events
```

### Conversation Resume Flow

```
User opens existing conversation
    ↓
GET /conversations/{id}  →  SQLite: messages + traces
    ↓
Frontend renders MessageList with all messages
    ↓
For each message: TracePanel hydrated from persisted trace JSON
    ↓
User sends new message → streaming chat turn resumes
```

### File Retrieval at Chat Time

```
User sends message (with uploaded files in scope)
    ↓
Orchestrator: embed user query
    ↓
ChromaDB.query(query_embedding, collection=conversation_files, n=5)
    ↓
SQLite: resolve chunk → FileRecord (filename, page, section)
    ↓
Context block prepended to LLM system prompt
    ↓
LLM response cites [Source: filename.pdf, chunk 3]
    ↓
Frontend: source attribution visible in message
```

### Settings → Health Check

```
User configures LLM provider (base_url + api_key + model)
    ↓
PUT /settings/providers/{id}  →  SQLite: ProviderConfig
    ↓
POST /settings/providers/{id}/test
    ↓
FastAPI: send minimal request to provider endpoint
    ↓
Return: {status: ok/error, latency_ms, model_list}
    ↓
Health panel displays live status
```

---

## Database Schema Patterns

### Core Tables (SQLite via SQLModel)

```
conversations
  id          TEXT  PK  (uuid)
  title       TEXT
  created_at  DATETIME
  updated_at  DATETIME

messages
  id              TEXT  PK  (uuid)
  conversation_id TEXT  FK → conversations.id
  role            TEXT  (user | assistant | system | tool)
  content         TEXT
  model           TEXT  (model used to generate)
  created_at      DATETIME

traces
  id          TEXT  PK  (uuid)
  message_id  TEXT  FK → messages.id
  events      TEXT  (JSON array of SSE event payloads)
  created_at  DATETIME

file_records
  id              TEXT  PK  (uuid)
  conversation_id TEXT  FK → conversations.id  (nullable — global upload)
  filename        TEXT
  mime_type       TEXT
  storage_path    TEXT  (./uploads/{id}.ext)
  chunk_count     INT
  collection_id   TEXT  (ChromaDB collection name)
  created_at      DATETIME

settings (key-value or typed rows)
  id          TEXT  PK
  category    TEXT  (provider | embedding | mcp | skill | reranker)
  key         TEXT
  value       TEXT  (JSON)
  updated_at  DATETIME
```

### ChromaDB Collections

```
collections:
  "forge_files"          — all uploaded file chunks
  "forge_conv_{id}"      — conversation-scoped file chunks (optional)

document metadata per chunk:
  file_id, filename, chunk_index, char_start, char_end, mime_type
```

---

## Build Order (Phase Implications)

The component dependency graph dictates this build sequence:

```
1. Infrastructure
   SQLite models + Alembic + FastAPI skeleton + Next.js shell
   (everything else depends on this)

2. Auth + Session
   Single-user password auth, session token
   (gates all API endpoints)

3. Basic Chat (no tools)
   Conversation CRUD, message persistence, LLM streaming via SSE
   (core value; validates SSE pattern early)

4. Execution Trace
   TraceEmitter, SSE event types, trace persistence, TracePanel UI
   (build alongside tools — shared infrastructure)

5. Tool/MCP Integration
   Orchestrator loop, ToolExecutor, McpExecutor, MCP settings UI
   (depends on 3 + 4)

6. Skills
   SkillExecutor, skill configuration UI
   (depends on 5 — reuses executor pattern)

7. File Upload + RAG
   FilePipeline, ChromaDB, retrieval, source attribution UI
   (independent track, can start after 3)

8. Settings + Health Panel
   All settings pages, test-connection endpoints, diagnostics
   (can be built incrementally alongside 4-7)

9. Quality / Polish
   Test coverage, export, theme, retry/regenerate
   (final pass)
```

---

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| OpenAI-compat LLM (Ollama, LM Studio, vLLM) | HTTP client (httpx async) with streaming | Use `stream=True`, handle SSE from provider |
| MCP Servers | MCP Python SDK client | Each server is a subprocess or network socket; tools discovered at connect time |
| Web Search API (Brave, etc.) | REST HTTP (httpx) | Wrapped in ToolExecutor; provider swappable via settings |
| ChromaDB | Python client (`chromadb`) | Local persistent mode; no separate server needed for MVP |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| Next.js UI ↔ FastAPI | HTTP REST + SSE | Direct fetch to FastAPI; or proxied through Next.js Route Handler |
| Orchestrator ↔ Executors | Async Python function calls | Executors return `str` result; orchestrator does not know the source |
| Orchestrator ↔ TraceEmitter | Async generator / callback | TraceEmitter both emits SSE and batches events for persistence |
| FastAPI ↔ SQLite | SQLModel sessions via dependency injection | One session per request; async sessions for streaming endpoints |
| FastAPI ↔ ChromaDB | ChromaDB Python client | Instantiated at app startup; collection references cached |
| File Router ↔ FilePipeline | Service layer call | Router validates, delegates to pipeline, returns file_id |

---

## Anti-Patterns

### Anti-Pattern 1: Streaming Through Next.js Route Handler

**What people do:** Route all FastAPI SSE through a Next.js API route handler, treating it as a universal proxy.

**Why it's wrong:** Next.js Route Handlers buffer responses in some deployment modes (especially Vercel edge). This destroys the streaming behavior for SSE and adds latency. The Next.js middleware layer is not designed to faithfully proxy long-lived streaming connections.

**Do this instead:** Have the browser connect to FastAPI directly for the streaming chat endpoint. Use `next.config.js` rewrites for non-streaming API calls. Keep the SSE connection direct: `browser → FastAPI /chat/stream`.

### Anti-Pattern 2: Storing Traces as Normalized Rows

**What people do:** Create a `trace_events` table with one row per event, FKed to the message.

**Why it's wrong:** Traces are append-only, always read as a complete set, and never queried individually. Normalizing them adds JOIN overhead with zero benefit for this access pattern.

**Do this instead:** Store the full trace as a JSON array in a single `traces.events` TEXT column, serialized at run completion. Fast reads, simple schema.

### Anti-Pattern 3: One ChromaDB Collection Per Conversation

**What people do:** Create a new ChromaDB collection for each conversation to scope retrieval.

**Why it's wrong:** ChromaDB has overhead per collection. At dozens of conversations with uploaded files, collection proliferation degrades performance and complicates cleanup.

**Do this instead:** Use one shared collection (`forge_files`) with metadata filtering on `file_id` or `conversation_id`. ChromaDB's `where` clause handles scoping efficiently.

### Anti-Pattern 4: Orchestrator Calling Executors Directly by Name

**What people do:** `if tool_name == "web_search": await web_search(...)` inside the orchestrator.

**Why it's wrong:** Every new tool requires modifying the orchestrator. The orchestrator becomes a dispatch table that grows without bound, is hard to test, and mixes concerns.

**Do this instead:** Register executors at startup. Orchestrator calls `executor_registry.invoke(tool_name, input)`. New tools register themselves without touching the loop.

### Anti-Pattern 5: Blocking Embedding During Chat

**What people do:** Embed and store file chunks inline during the chat turn (blocking the SSE stream).

**Why it's wrong:** Embedding large files takes seconds. Blocking the chat stream for embedding makes the interface feel broken.

**Do this instead:** Upload and embed files asynchronously (background task or pre-chat upload endpoint). File is available for retrieval by the time the user sends their first message about it.

---

## Scaling Considerations

This is a local-first, single-user tool. Scaling is not a priority, but these are the first things that would need attention if it were:

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 1 user (target) | Everything as described. SQLite is fine. ChromaDB local mode. |
| 5-10 users (team) | Add connection pooling for SQLite (or migrate to PostgreSQL). Add Redis for run state if concurrency spikes. |
| 100+ users | Replace SQLite with PostgreSQL. ChromaDB client-server mode. Separate embedding workers. Background job queue (Celery/ARQ). |

### Scaling Priorities

1. **First bottleneck:** SQLite write-locking under concurrent streaming requests. Fix: migrate to PostgreSQL or use WAL mode + async SQLAlchemy.
2. **Second bottleneck:** Embedding throughput. Fix: dedicated embedding worker process consuming an async queue.

---

## Sources

- [FastAPI SSE (EventSourceResponse) — Official Docs](https://fastapi.tiangolo.com/tutorial/server-sent-events/)
- [Streaming APIs with FastAPI and Next.js — Sahan Serasinghe](https://sahansera.dev/streaming-apis-python-nextjs-part1/)
- [Streaming AI Agents Responses with SSE — DEV Community](https://dev.to/sahan/streaming-apis-with-fastapi-and-nextjs-part-1-3ndj)
- [AI SDK UI Stream Protocols — ai-sdk.dev](https://ai-sdk.dev/docs/ai-sdk-ui/stream-protocol)
- [Agentic Loop with Tool Calling — Temporal Docs](https://docs.temporal.io/ai-cookbook/agentic-loop-tool-call-openai-python)
- [Agentic AI Architecture Patterns — Speakeasy](https://www.speakeasy.com/mcp/ai-agents/architecture-patterns)
- [MCP Clients + LLMs Orchestration Patterns — Medium](https://medium.com/@christoph.j.weisser28/%EF%B8%8F-mcp-clients-llms-orchestrator-agents-full-plan-and-step-by-step-orchestation-patterns-07af7dc0bce0)
- [ChromaDB Concepts — Chroma Cookbook](https://cookbook.chromadb.dev/core/concepts/)
- [Enhancing RAG with ChromaDB and SQLite — Medium](https://medium.com/@dassandipan9080/enhancing-retrieval-augmented-generation-with-chromadb-and-sqlite-c499109f8082)
- [FastAPI Project Structure Best Practices — zhanymkanov/fastapi-best-practices](https://github.com/zhanymkanov/fastapi-best-practices)
- [Next.js App Router Best Practices 2025 — Medium](https://medium.com/better-dev-nextjs-react/inside-the-app-router-best-practices-for-next-js-file-and-directory-structure-2025-edition-ed6bc14a8da3)
- [Next.js Backend for Frontend Guide](https://nextjs.org/docs/app/guides/backend-for-frontend)

---
*Architecture research for: local-first AI assistant (Forge)*
*Researched: 2026-03-21*
