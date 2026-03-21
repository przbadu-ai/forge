# Pitfalls Research

**Domain:** Local-first AI assistant (Next.js + FastAPI + SQLite + ChromaDB + MCP)
**Researched:** 2026-03-21
**Confidence:** HIGH (multiple verified sources per pitfall)

## Critical Pitfalls

### Pitfall 1: Next.js Route Handler SSE Buffering — Tokens Arrive All at Once

**What goes wrong:**
Streaming tokens appear to work in development but the client receives ALL tokens in a single batch when deployed or when Next.js compression is active. The root cause is that Next.js Route Handlers (App Router) buffer the response until the handler function returns, and also gzip compression buffers chunks before flushing. The user sees a long pause then instant full response — no streaming.

**Why it happens:**
Developers wire up SSE correctly on the FastAPI side, proxy through a Next.js route handler for auth/header injection, and never notice buffering in development because localhost bypasses gzip. Production behind nginx or Vercel triggers it.

**How to avoid:**
- Set explicit headers: `Content-Type: text/event-stream; charset=utf-8`, `Cache-Control: no-cache, no-transform`, `Connection: keep-alive`, `X-Accel-Buffering: no`
- Disable Next.js response compression in `next.config.js`: `compress: false`
- Export `export const dynamic = 'force-dynamic'` on SSE route handlers
- Use the `ReadableStream` API in Next.js route handlers rather than older `res.write` patterns
- Alternatively, have the browser connect directly to the FastAPI SSE endpoint (avoid proxying through Next.js entirely for streaming routes)

**Warning signs:**
- Streaming works in `localhost:3000 -> localhost:8000` but fails in Docker or production
- DevTools Network tab shows the SSE request completing instantly with all data
- No incremental token display; full response appears after LLM finishes generating

**Phase to address:** Core Streaming Infrastructure (Phase 1 / foundation phase)

---

### Pitfall 2: OpenAI-Compatible API Behavioral Divergence Across Providers

**What goes wrong:**
The API accepts requests without error, but streaming behavior, tool call format, model name conventions, and error responses differ enough across Ollama, LM Studio, vLLM, and remote providers that code written against one breaks on another.

Specific divergences:
- **Tool/function calling**: LM Studio does not support streaming tool calls or parallel function invocation. vLLM requires `--enable-auto-tool-choice` with a parser flag (`hermes`, `llama3`, `mistral`). Ollama's tool support varies by model.
- **Streaming delta format**: Tool call arguments arrive as partial JSON deltas during streaming. Some providers emit differently structured `delta` events.
- **Model name format**: `llama3.2:3b` (Ollama) vs `lmstudio-community/Meta-Llama-3.2-3B-GGUF` vs `meta-llama/Llama-3.2-3B-Instruct` (vLLM).
- **Error response shape**: Some providers return HTTP 200 with an error in the body rather than HTTP 4xx/5xx.

**Why it happens:**
Developers test against one provider (usually Ollama), assume "OpenAI-compatible" means fully identical, and discover divergence only after adding a second provider or enabling tool calling.

**How to avoid:**
- Build a provider adapter layer that normalizes responses before they reach orchestration logic
- Test tool calling against each supported provider type in CI (mock or real)
- Never rely on raw model name as identifier — store a display name and API model string separately
- Handle partial JSON streaming for tool call arguments explicitly; don't assume arguments arrive in one chunk
- Implement a health-check / capability detection endpoint per provider (can it do tool calls? streaming? embeddings?)

**Warning signs:**
- Tool calls work with Ollama but silently fail with LM Studio
- Switching providers causes `undefined` errors in streaming handler
- Model selector shows raw API model names without normalization

**Phase to address:** Provider integration layer (Phase 1 or 2)

---

### Pitfall 3: Streaming Abort / Reconnect Incompatibility

**What goes wrong:**
Implementing both "stop generation" (client abort) and "resume after reconnect" in the same streaming path causes them to break each other. If resume is enabled, aborting the stream leaves the backend in an inconsistent state where it continues generating but the client has moved on. Partial responses are not persisted.

**Why it happens:**
Abort and resume are architecturally incompatible unless the generation is decoupled from the client connection. Most implementations couple generation to the HTTP request lifecycle: when the client disconnects, the backend stops generating. This makes abort easy but resume impossible.

**How to avoid:**
- Choose one model: **abort-only** (simpler) or **durable generation** (resilient but complex)
- For abort-only (recommended for MVP): propagate `AbortSignal` from client through to the upstream LLM request; use `try/except asyncio.CancelledError` in FastAPI generator; persist whatever was generated up to the abort point
- Never implement `resume: true` alongside client-side abort without decoupling generation to a background task
- Persist partial response chunks to the DB as they arrive (not only on completion) so aborted messages are recoverable

**Warning signs:**
- Stop button works but the backend keeps running (consuming GPU/API budget)
- Resumed page loads show empty messages for in-progress generations
- "Regenerate" creates a duplicate message instead of replacing the partial one

**Phase to address:** Streaming infrastructure + chat message persistence (Phase 1)

---

### Pitfall 4: SQLite "Database Is Locked" Under Async Concurrency

**What goes wrong:**
`sqlite3.OperationalError: database is locked` errors appear intermittently in FastAPI, especially during periods where streaming writes (persisting chunks) overlap with read requests (loading conversation history). The app works fine in single-request testing but fails under moderate load.

**Why it happens:**
SQLite allows only one writer at a time. FastAPI is async and can process multiple requests concurrently. Without WAL mode, any read blocks on pending writes. With WAL mode, multiple readers are allowed concurrent with one writer, but checkpointing can still briefly block readers. Async SQLAlchemy with SQLite uses `aiosqlite` under the hood — connection pool misconfiguration (sharing connections across coroutines) is a common source.

**How to avoid:**
- Enable WAL mode immediately: `PRAGMA journal_mode=WAL;` on connection creation
- Set busy timeout: `PRAGMA busy_timeout=5000;` (5 seconds) to retry rather than fail instantly
- Use `create_async_engine` with `aiosqlite` and `NullPool` (or `StaticPool` for single-file SQLite) — never share connections across async tasks
- Use `check_same_thread=False` only if you understand the implications; prefer one connection per request
- For Forge's use case (single user, low concurrency), WAL + busy_timeout should be sufficient. Document the path to PostgreSQL for multi-user v2.
- Keep write operations short; never hold a write transaction open during LLM streaming

**Warning signs:**
- Errors appear only under "fast clicking" or parallel tab usage
- Logs show `OperationalError` with no stack trace pointing to application code
- Works fine with `pytest` (sequential) but fails with `pytest -n 4` (parallel)

**Phase to address:** Database layer setup (Phase 1, before any feature work)

---

### Pitfall 5: ChromaDB Library Mode Data Staleness in Multi-Process Environments

**What goes wrong:**
When FastAPI runs with multiple workers (e.g., `uvicorn --workers 4` or Gunicorn), ChromaDB in embedded/library mode maintains a separate in-memory index per worker. Worker A adds a document and persists it to disk, but Workers B, C, D never see it — their in-memory state is stale. Queries return outdated results without any error.

**Why it happens:**
ChromaDB's embedded mode loads the collection into memory when the process starts. It writes to disk but does not signal other processes to reload. This is a fundamental design constraint of embedded/library mode — it is not safe for multi-process use.

**How to avoid:**
- Run ChromaDB as a standalone HTTP server (`chroma run --path ./chroma_data`) even locally — not in embedded library mode
- Connect from FastAPI using `chromadb.HttpClient` pointing at the local Chroma server
- For MVP single-process Uvicorn (`--workers 1`), embedded mode is safe, but document the constraint explicitly
- Add a health check that validates the Chroma server is reachable at startup
- Do NOT use `chromadb.Client()` (deprecated library mode) in any environment where worker count may exceed 1

**Warning signs:**
- Document uploads return 200 but queries don't return the new documents
- Restarting the server "fixes" retrieval temporarily
- Results are inconsistent between requests

**Phase to address:** RAG / embedding infrastructure (before file upload feature is built)

---

### Pitfall 6: MCP Process Lifecycle Not Managed — Zombie Processes and Resource Leaks

**What goes wrong:**
MCP servers launched via stdio transport (the most common local transport) are child processes. If the host application crashes, exits abnormally, or the MCP server errors out, the child process can become a zombie or continue consuming resources. When the user reconfigures MCP servers in Settings, old processes are not cleanly terminated before new ones start.

**Why it happens:**
Developers treat MCP servers as "fire and start" — spawn the process, use it, never implement shutdown. The MCP spec defines a shutdown sequence (close stdin → wait → SIGTERM → SIGKILL) but nothing enforces it. Application restarts during development accumulate orphaned processes.

**How to avoid:**
- Implement a `McpProcessManager` that tracks all running MCP child processes by server ID
- On application shutdown: close stdin → wait 5s → send SIGTERM → wait 5s → SIGKILL
- On Settings reconfiguration: stop old process cleanly before starting replacement
- Store PID in the database; on startup, check if stale PIDs are still running and kill them
- Set connection timeouts per the MCP spec; don't let hung requests block indefinitely
- Use `asyncio.create_subprocess_exec` with explicit stdin/stdout pipes rather than `subprocess.Popen`

**Warning signs:**
- `ps aux | grep mcp` shows multiple copies of the same server
- Settings changes don't take effect until restart
- System RAM climbs after repeated MCP server reconfiguration

**Phase to address:** MCP integration phase (dedicated lifecycle management before tool invocation)

---

### Pitfall 7: Alembic + SQLite ALTER TABLE Failures on Schema Changes

**What goes wrong:**
Alembic-generated migrations work on PostgreSQL but fail silently or with confusing errors on SQLite when they involve column modifications, drops, renames, or constraint changes. SQLite only supports `RENAME TABLE` and `ADD COLUMN` in `ALTER TABLE`. Running a standard Alembic migration that drops a column causes `NotSupportedError`.

**Why it happens:**
Alembic auto-generates migrations using the database dialect. When configured for SQLite, it should use batch mode, but the default configuration does not enable batch mode automatically. Adding a non-nullable column to a populated table will also fail without a server default.

**How to avoid:**
- Enable Alembic batch mode for SQLite in `env.py`:
  ```python
  with context.begin_transaction():
      context.run_migrations(render_as_batch=True)
  ```
- Always provide `server_default` when adding `NOT NULL` columns to existing tables
- Review auto-generated migrations before applying them — never run `alembic upgrade head` blindly
- Test migrations against a copy of the production DB, not just an empty one
- Avoid unnamed constraints (always name CHECK and UNIQUE constraints explicitly)

**Warning signs:**
- `alembic upgrade head` fails on `ALTER TABLE ... DROP COLUMN`
- Migration works in clean test DB but fails on an existing DB with data
- Schema drifts silently when developers skip migration and recreate DB

**Phase to address:** Database setup phase (establish batch mode before first migration)

---

### Pitfall 8: Markdown Rendering XSS via LLM Output

**What goes wrong:**
The LLM generates response content that includes HTML, JavaScript, or crafted markdown that, when rendered, executes scripts in the user's browser. Since LLM output is inherently untrusted, any markdown renderer that passes raw HTML through is a security hole. This is especially acute when RAG retrieval injects content from user-uploaded files into the context.

**Why it happens:**
Developers use markdown renderers (react-markdown, marked, markdown-it) with default settings that allow raw HTML passthrough. The assumption is "this is my own assistant, I trust it" — but indirect prompt injection via retrieved documents or tool results can weaponize the output.

**How to avoid:**
- Use `react-markdown` with `rehype-sanitize` plugin enabled (enabled is the correct default but verify)
- Never use `dangerouslySetInnerHTML` for LLM output under any circumstances
- Disable raw HTML passthrough: `allowDangerousHtml: false` (markdown-it default is safe; react-markdown v6+ is safe by default)
- For code blocks: use a syntax highlighter that does not eval code (Prism, Shiki — both are safe)
- Test by injecting `<script>alert(1)</script>` and `[click me](javascript:alert(1))` as LLM responses

**Warning signs:**
- Code blocks display but also execute in browser
- Links in responses can navigate to `javascript:` URIs
- Using `marked` without DOMPurify (marked allows raw HTML by default)

**Phase to address:** Chat UI foundation (before first streaming response is rendered)

---

### Pitfall 9: LLM API Keys Stored in Frontend or Logged in Plain Text

**What goes wrong:**
API keys for remote LLM providers (OpenAI, Anthropic, etc.) configured in the Settings page are either: (a) stored in browser localStorage where they can be read by XSS, (b) sent in request bodies that get logged by FastAPI's default request logging, or (c) stored in the SQLite DB without encryption.

**Why it happens:**
Settings forms are wired to backend storage through the standard CRUD path. Developers don't think about the difference between configuration data and secret data. FastAPI's `--log-level debug` logs full request bodies.

**How to avoid:**
- Store API keys in the SQLite DB with at minimum environment-variable-keyed encryption (Fernet symmetric encryption is sufficient for single-user local deployment)
- Never return the full API key in any API response; return a masked value (`sk-...abc123`) for display
- Disable request body logging for provider configuration endpoints
- Use `SecretStr` from Pydantic for any field containing credentials — it prevents accidental logging
- Set `HTTPOnly` and `SameSite=Strict` on session cookies

**Warning signs:**
- API key is visible in browser DevTools → Application → Local Storage
- FastAPI logs show full request body on settings update
- `GET /api/providers/1` returns `{"api_key": "sk-full-key-here"}`

**Phase to address:** Settings + Auth phase (before provider configuration is built)

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Single Uvicorn worker (`--workers 1`) | Avoids ChromaDB multi-process staleness | Cannot scale; single point of failure | MVP only; document the constraint |
| Polling instead of SSE for trace events | Simpler to implement | Latency spikes, extra DB load | Never; SSE is not harder here |
| Hardcoded model name in orchestrator | Faster first demo | Breaks on provider switch | Never |
| Skip WAL mode for SQLite | Nothing needed upfront | Intermittent lock errors in production | Never; WAL is a one-liner |
| Embedded ChromaDB (`chromadb.Client()`) | No separate process | Data staleness with multiple workers | Only if single-process guarantee is enforced |
| No abort signal propagation to LLM | Simpler code | Backend keeps generating after client stops | Never; wastes GPU/API budget |
| Store API keys in plain text | No encryption setup needed | Security risk, user trust | Never |
| Skip Alembic batch mode | Shorter setup | First schema change breaks migration | Never |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Ollama | Assume tool calling works for all models | Check `ollama list` model capabilities; only llama3.1+ supports tools reliably |
| LM Studio | Try to use streaming tool calls | LM Studio does not support streaming tool calls; use non-streaming for tool use |
| vLLM | Forget `--enable-auto-tool-choice` flag | Add the flag with the correct parser (`hermes`, `llama3`, `mistral`) at server startup |
| ChromaDB HTTP server | Skip health check on startup | Add a `/api/v1/heartbeat` check; fail loudly if Chroma is unreachable |
| FastAPI SSE + nginx | Double CORS headers | Remove CORS headers from nginx if FastAPI already adds them |
| MCP stdio server | Not handling server crash | Implement restart-with-backoff logic in `McpProcessManager` |
| SQLite + async SQLAlchemy | `check_same_thread` errors | Use `aiosqlite` driver with `NullPool`; do not share connections across coroutines |
| Next.js App Router + SSE | Response buffered until completion | Set `X-Accel-Buffering: no`, disable `compress`, use `ReadableStream` |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Synchronous DB writes in streaming path | Each token write blocks the next | Use async writes; batch chunk persistence; write at turn completion if latency allows | From first concurrent user |
| Full conversation history loaded on every request | Context window bloat; slow response start | Load only last N turns; use summary/compression for long histories | At ~50 messages per conversation |
| ChromaDB querying without metadata filters | Retrieves from all documents globally | Always filter by `user_id`, `session_id`, or `collection_id` in metadata | At ~1000+ documents |
| Fetching all conversations for sidebar | Sidebar load time grows linearly | Paginate conversation list; use cursor-based pagination | At ~500+ conversations |
| Trace events stored as individual DB rows per token | DB fills with millions of tiny rows | Aggregate trace events; store as JSON blob per message turn | At ~1000 messages |
| No SSE connection keepalive/heartbeat | Connection drops silently after 30-60s idle | Send `event: ping\ndata: {}\n\n` every 15 seconds | On any proxy with connection timeout |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Raw HTML in markdown renderer (react-markdown without sanitize) | XSS via LLM output or injected documents | Use `rehype-sanitize`; verify default config is safe |
| API key returned in GET /providers response | Key leaks in logs, browser history | Return masked key; never return full secret |
| MCP tool invocation without input validation | Arbitrary command execution via crafted tool arguments | Validate all MCP tool inputs against schema before execution |
| Indirect prompt injection via RAG documents | Uploaded file instructs LLM to exfiltrate data | Display source provenance; consider a warning when LLM output diverges from expected patterns |
| `uploads/` directory served statically via Next.js | Direct file access bypasses auth | Serve file downloads through controlled FastAPI endpoint with session check |
| Session token in URL query parameter | Token visible in server logs, referrer headers | Use HTTPOnly cookie only; never put token in URL |
| No rate limiting on chat endpoint | API budget exhaustion if session is hijacked | Add per-session rate limiting even for single-user (defense in depth) |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| No loading state between send and first token | User thinks request was lost; double-submits | Show "thinking..." indicator immediately on send; disable input |
| Streaming stops but no visual indicator | User waits indefinitely after network drop | Add timeout detection; show "connection lost — retry?" after 30s of silence |
| Trace panel open by default per message | Clutters chat; distracting for normal use | Trace collapsed by default; expand icon on hover |
| Error messages show raw API error body | Confusing to user; may expose internal details | Map provider errors to human-readable messages |
| No scroll-lock during streaming | User reading earlier context gets auto-scrolled away | Detect manual scroll-up; pause auto-scroll until user scrolls back to bottom |
| Conversation list has no visual active state | User loses track of current conversation | Highlight active conversation; persist last-viewed conversation across reload |
| File upload succeeds but retrieval never uses it | User uploads files expecting them in context | Show source citations prominently; add "files used" section to RAG responses |

---

## "Looks Done But Isn't" Checklist

- [ ] **Streaming:** Verify tokens arrive incrementally in production (with compression enabled, behind nginx) — not just on localhost
- [ ] **Tool calling:** Verify tool calls work with each configured provider type — Ollama, LM Studio, and vLLM all behave differently
- [ ] **Abort:** Verify stop button terminates the upstream LLM request, not just the client's listener
- [ ] **MCP servers:** Verify old MCP processes are killed when servers are reconfigured in Settings
- [ ] **File upload + RAG:** Verify recently uploaded files are findable immediately (not cached from before upload)
- [ ] **SQLite migrations:** Verify `alembic upgrade head` works on a DB with existing data, not just an empty DB
- [ ] **API key masking:** Verify GET /providers never returns full API key in any response
- [ ] **Markdown XSS:** Verify `<script>alert(1)</script>` in LLM response does not execute
- [ ] **Session persistence:** Verify trace events are reloaded correctly when resuming a conversation
- [ ] **ChromaDB multi-worker:** Verify document retrieval returns newly uploaded files when running with multiple Uvicorn workers (or document the single-worker constraint)

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| SSE buffering discovered in production | LOW | Add missing headers + disable Next.js compression; redeploy |
| Provider API divergence causes tool call failures | MEDIUM | Build adapter layer; add per-provider capability flags; re-test all providers |
| "Database is locked" in production | LOW | Enable WAL mode + busy_timeout; redeploy; no data loss |
| ChromaDB stale data in multi-worker | MEDIUM | Switch to ChromaDB HTTP server mode; update all client code to use `HttpClient` |
| MCP zombie processes | LOW | Add process manager with PID tracking; kill orphans on startup |
| API key stored in plain text | MEDIUM | Migrate keys to encrypted storage; force re-entry from Settings page |
| XSS via markdown | MEDIUM | Add rehype-sanitize to renderer; audit all places where LLM output is rendered |
| Alembic migration failure on schema change | MEDIUM | Enable batch mode; write corrective migration manually; test against data snapshot |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| SSE buffering in Next.js | Phase 1: Streaming infrastructure | Integration test: verify token-by-token delivery through nginx in CI |
| Provider API divergence | Phase 1-2: Provider adapter layer | Test matrix: run tool call test against each provider type |
| Streaming abort/resume incompatibility | Phase 1: Chat core | Test: stop mid-stream; verify backend terminates; verify partial message saved |
| SQLite "database is locked" | Phase 1: DB setup | Concurrent write test in pytest; verify no lock errors under 5 parallel requests |
| ChromaDB library mode staleness | Phase 3-4: RAG/embedding | Test: upload file, immediately query in separate process; verify result appears |
| MCP process lifecycle | Phase 4-5: MCP integration | Test: reconfigure MCP server; verify no zombie processes via `ps` |
| Alembic SQLite batch mode | Phase 1: DB setup | Test: run migration with existing data rows; verify no `NotSupportedError` |
| Markdown XSS | Phase 2: Chat UI | Automated test: render `<script>alert(1)</script>` as LLM output; assert no execution |
| API key plain text storage | Phase 2: Settings + Auth | Audit: GET /providers response must not contain full key; DB must not store plaintext |
| Trace event DB bloat | Phase 2-3: Trace persistence | Test: generate 100-message conversation; verify trace storage is bounded |

---

## Sources

- [Server-Sent Events don't work in Next API routes — vercel/next.js Discussion #48427](https://github.com/vercel/next.js/discussions/48427)
- [Fixing Slow SSE Streaming in Next.js and Vercel (Jan 2026)](https://medium.com/@oyetoketoby80/fixing-slow-sse-server-sent-events-streaming-in-next-js-and-vercel-99f42fbdb996)
- [FastAPI streaming response not decoded in chunks with compression · Issue #62201 · vercel/next.js](https://github.com/vercel/next.js/issues/62201)
- [Stop streaming response when client disconnects · fastapi Discussion #7572](https://github.com/fastapi/fastapi/discussions/7572)
- [How to Build LLM Streams That Survive Reconnects, Refreshes, and Crashes — Upstash](https://upstash.com/blog/resumable-llm-streams)
- [AI SDK UI: Chatbot Resume Streams — Vercel AI SDK](https://ai-sdk.dev/docs/ai-sdk-ui/chatbot-resume-streams)
- [Ollama vs vLLM vs LM Studio for local LLM (2026)](https://www.clawctl.com/blog/ollama-vs-vllm-vs-lm-studio)
- [LM Studio Production Guide: Local OpenAI-Compatible LLMs](https://www.cohorte.co/blog/lm-studio-production-grade-local-llm-server)
- [Real Faults in Model Context Protocol (MCP) Software — arXiv 2603.05637](https://arxiv.org/html/2603.05637v1)
- [Six Fatal Flaws of the Model Context Protocol (MCP)](https://www.scalifiai.com/blog/model-context-protocol-flaws-2025)
- [MCP Servers in Production — systemprompt.io](https://systemprompt.io/guides/mcp-servers-production-deployment)
- [MCP Lifecycle — Model Context Protocol Specification](https://modelcontextprotocol.io/specification/2025-03-26/basic/lifecycle)
- [SQLite concurrent writes and "database is locked" errors — tenthousandmeters](https://tenthousandmeters.com/blog/sqlite-concurrent-writes-and-database-is-locked-errors/)
- [SQLite connection pool pitfalls: 5 major misunderstandings](https://www.jtti.cc/supports/3154.html)
- [ChromaDB Library Mode = Stale RAG Data — Never Use It in Production](https://medium.com/@okekechimaobi/chromadb-library-mode-stale-rag-data-never-use-it-in-production-heres-why-b6881bd63067)
- [Road To Production — Chroma Cookbook](https://cookbook.chromadb.dev/running/road-to-prod/)
- [Alembic Batch Migrations for SQLite — Official Docs](https://alembic.sqlalchemy.org/en/latest/batch.html)
- [Fixing ALTER TABLE errors with Flask-Migrate and SQLite — Miguel Grinberg](https://blog.miguelgrinberg.com/post/fixing-alter-table-errors-with-flask-migrate-and-sqlite)
- [Solving CORS Issues Between Next.js and Python Backend (Nov 2025)](https://medium.com/@nmlmadhusanka/solving-cors-issues-between-next-js-and-python-backend-93800a4ee633)
- [Handling State Update Race Conditions in React — CyberArk Engineering](https://medium.com/cyberark-engineering/handling-state-update-race-conditions-in-react-8e6c95b74c17)
- [LLM Security in 2025: Risks, Examples, and Best Practices — Oligo Security](https://www.oligo.security/academy/llm-security-in-2025-risks-examples-and-best-practices)

---
*Pitfalls research for: local-first AI assistant (Forge)*
*Researched: 2026-03-21*
