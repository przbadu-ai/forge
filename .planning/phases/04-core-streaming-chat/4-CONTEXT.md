# Phase 4: Core Streaming Chat - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Streaming SSE chat with conversation CRUD and markdown rendering. User can start conversations, receive streaming tokens from configured LLM, view conversation history in sidebar, resume/rename/delete conversations. No system prompts, no tools, no traces — just core chat.

</domain>

<decisions>
## Implementation Decisions

### Backend chat
- **D-01:** Conversation and Message SQLModel models with Alembic migration
- **D-02:** SSE endpoint at POST /api/v1/chat/{conversation_id}/stream
- **D-03:** Uses openai Python client with base_url from configured default provider
- **D-04:** Stream tokens via FastAPI native EventSourceResponse (not sse-starlette)
- **D-05:** SSE events: token (content delta), done (completion), error (failure)
- **D-06:** Messages persisted with role (user/assistant), content, and timestamps
- **D-07:** Conversation auto-titled from first user message (truncated to 50 chars)

### Frontend chat
- **D-08:** Chat layout: sidebar (conversation list) + main panel (messages + composer)
- **D-09:** SSE consumed via fetch + ReadableStream (not EventSource — POST not supported)
- **D-10:** Markdown rendered with react-markdown + rehype-highlight + rehype-sanitize
- **D-11:** Syntax highlighting for code blocks
- **D-12:** Messages stream in real-time with cursor/typing indicator
- **D-13:** Message states: generating, completed, failed

### SSE pattern
- **D-14:** Browser connects directly to FastAPI SSE (not through Next.js proxy)
- **D-15:** CORS already configured for localhost:3000 → localhost:8000
- **D-16:** AbortController for cancelling in-flight streams

### Claude's Discretion
- Chat UI styling details
- Sidebar width and layout
- Message bubble design
- Loading states and animations
- Auto-scroll behavior

</decisions>

<specifics>
## Specific Ideas

- Chat should feel responsive — tokens should appear immediately, not buffer
- Sidebar should show most recent conversations first
- New conversation starts with an empty chat panel
- User messages appear immediately; assistant messages stream in

</specifics>

<canonical_refs>
## Canonical References

### Stack
- `.planning/research/STACK.md` — openai SDK streaming, FastAPI SSE
- `.planning/research/ARCHITECTURE.md` — SSE direct browser→FastAPI pattern
- `.planning/research/PITFALLS.md` — SSE buffering in Next.js, abort signal propagation
- `PRD.md` §7.2 — Chat experience requirements

### Previous phase outputs
- `backend/app/models/llm_provider.py` — LLM provider model (get default provider for chat)
- `backend/app/core/encryption.py` — decrypt API key for provider
- `frontend/src/lib/api.ts` — apiFetch wrapper

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/models/llm_provider.py` — query default provider for base_url + api_key
- `backend/app/core/encryption.py` — decrypt_value for API key
- `frontend/src/lib/api.ts` — apiFetch for REST calls
- `frontend/src/context/auth-context.tsx` — useAuth for token

### Established Patterns
- SQLModel + Alembic for models
- FastAPI with Depends(get_current_user)
- React context + shadcn/ui components

### Integration Points
- Chat streaming must work with the provider configured in Phase 3
- Messages will get trace metadata in Phase 6

</code_context>

<deferred>
## Deferred Ideas

- System prompts — Phase 5
- Stop/regenerate — Phase 5
- Conversation search — Phase 5
- Execution traces — Phase 6
- Tool calls in messages — Phase 7

</deferred>

---

*Phase: 04-core-streaming-chat*
*Context gathered: 2026-03-21*
