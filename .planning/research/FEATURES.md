# Feature Research

**Domain:** Local-first self-hosted AI assistant / chat application
**Researched:** 2026-03-21
**Confidence:** HIGH (based on direct analysis of Open WebUI, LibreChat, Jan.ai, Msty, AnythingLLM, LobeChat)

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Streaming token output | All modern AI chat UIs stream; non-streaming feels broken | LOW | SSE or WebSocket; partial markdown must render as it arrives |
| Markdown + syntax-highlighted code rendering | Code blocks are primary output for developer users | LOW | Use a mature renderer (e.g., react-markdown + shiki/prism); inline code, fenced blocks, tables, lists |
| Conversation list (sidebar) with resume | Users expect to revisit prior sessions like any chat product | LOW | Title, timestamp, delete, rename — all expected |
| Conversation rename and delete | Basic conversation hygiene; users feel "trapped" without it | LOW | Inline rename on double-click or pencil icon is standard |
| Configurable LLM provider + model | Must support at least OpenAI-compatible endpoints (Ollama, LM Studio, vLLM) | MEDIUM | Model picker per-conversation or global default; test-connection button expected |
| System prompt / custom instructions | Users want to set persona or context without repeating it each conversation | LOW | Per-conversation override of a global default is expected |
| Message regeneration (retry) | Network errors and bad outputs happen; users expect one-click retry | LOW | Only applicable to the last assistant message |
| File upload for document Q&A | All major competitors (Open WebUI, LibreChat, AnythingLLM) support this | HIGH | PDF, DOCX, TXT at minimum; user expects to ask questions against uploaded docs |
| Light / Dark theme | Universal expectation; system-follow is a bonus | LOW | Tailwind CSS + shadcn makes this near-free |
| Single-user authentication | Even local apps need a login gate to protect data | LOW | Username + password session; bcrypt hashes; no OAuth required for single-user |
| Settings page for provider configuration | Users need a place to enter API keys, base URLs, model lists | LOW | Form-based; test-connection button validates connectivity |
| Conversation search | Users accumulate conversations and need to find prior ones | MEDIUM | Full-text search over message content; search-as-you-type in sidebar |
| Export / backup of conversations | Users want data portability; fear lock-in | LOW | JSON export at minimum; PDF or Markdown export is a plus |
| Adjustable model parameters | Temperature, max tokens expected by developer users | LOW | Surface in settings sidebar or message composer; save per-preset |

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but valued.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Execution trace UI per message | Forge's core differentiator — users see every tool call, MCP action, and skill trigger as an expandable tree. Competitors show tool results but not the full trace | HIGH | Collapsed by default; expandable to show input/output/duration/errors; persisted in DB and visible on chat resume |
| Trace persistence and replay | Unlike Open WebUI and LibreChat (which lose trace state on refresh), Forge replays the full trace from DB on conversation resume | HIGH | Requires trace schema in DB with FK to message; all trace events (tool, MCP, skill) stored as JSONB/JSON |
| MCP server registration + invocation | MCP is rapidly becoming the standard protocol for connecting AI to external tools. LibreChat added it; Open WebUI added it — but neither exposes the full execution context in the UI | HIGH | Settings page to add MCP servers; tool invocation shows server name, tool name, input params, output, errors |
| Agent skills (enable/disable per session) | Modular skill system lets users toggle capabilities (web search, code execution, file Q&A) without reconfiguring the model | MEDIUM | Skills register as tools; disable = exclude from tool list sent to model |
| Source attribution for RAG answers | All competitors do RAG; few show *which chunk from which file* was used. Forge shows inline citations with file name, chunk preview, and similarity score | HIGH | Requires storing retrieval results per message; UI shows collapsible source list below assistant message |
| Health diagnostics panel | Developers running local infrastructure want a single status page showing: LLM endpoint, embedding model, ChromaDB, web search provider, MCP servers — all green/yellow/red | MEDIUM | Simple ping-based health checks; updates on demand or on settings save |
| Configurable timeout/retry for all external calls | Production-grade reliability without framework overhead | MEDIUM | Per-provider timeout and retry settings; not exposed by most competitors |
| Modular executor architecture (ToolExecutor, McpExecutor, SkillExecutor) | Clean separation lets future phases swap or extend components without rewriting the orchestration core | HIGH | Internal architecture benefit; user-visible as reliability and extensibility |
| Test-connection button for every endpoint | Saves frustrating debug loops when URL/key is wrong; competitors often only fail at inference time | LOW | POST to health-check endpoint; show latency and model list response |
| Reranker configuration | RAG quality improves significantly with a reranker; few self-hosted UIs expose this setting directly | MEDIUM | Optional; configured alongside embedding model in Settings |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Multi-user / team collaboration | Users who see it working on LibreChat ask for it | Requires auth middleware, per-user data isolation, RBAC, admin panel — 3x scope increase. Single-user local deployment is the entire target persona | Stay single-user for MVP; add multi-user only if there is validated demand post-launch |
| Real-time collaboration (shared sessions) | Looks impressive in demos | Requires WebSocket presence management, conflict resolution, operational transforms — none of which add value to a solo developer tool | Not applicable to solo use case |
| Mobile app | Users often ask for "an app" | React Native or native app is an entirely separate codebase and deployment surface. Web-first PWA is sufficient for local use | Build responsive web UI; PWA manifest allows "add to home screen" if needed |
| OAuth / SSO | Enterprise users request this | OAuth complexity (callback URLs, token refresh, provider registration) vastly exceeds the need of a single-user local installation | Username + password + secure session cookie is correct for MVP |
| Advanced agent frameworks (LangGraph, AutoGen) | Framework demos look powerful | Adds heavy dependency, reduces debuggability, tightly couples orchestration logic to external API surface. Custom loop is more transparent and testable | Custom lightweight orchestration loop with clean executor interfaces |
| Graph RAG / adaptive chunking | Appears in research papers and some tools | Significant implementation complexity and unclear benefit at personal-use document scale. Recursive fixed chunking at 512 tokens outperformed semantic chunking in Feb 2026 benchmarks | Simple recursive chunking with configurable size and overlap |
| Image generation | Open WebUI and LibreChat both support it | Adds DALL-E/ComfyUI dependencies and significant UI surface for a feature unrelated to Forge's core value (execution transparency) | Can be added in v2 if demanded; exclude from MVP |
| Voice call / video call integration | Open WebUI has this; users notice | Adds WebRTC, Whisper, and TTS orchestration — significant complexity for a feature that rarely gets used in developer tools | Text-first; optional TTS toggle could be v1.x addition |
| Parallel model comparison (side-by-side chats) | Msty's "Parallel Multiverse Chats" is a popular feature | Requires significant UI complexity (split pane, independent stream management) and has limited value for a workflow-focused tool | Single-model focus; model switching per-conversation is sufficient |
| Multilingual UI | LibreChat supports 30+ languages | Translation maintenance overhead is high; target audience is developers who likely work in English | English-only for MVP; i18n structure can be added later if warranted |

## Feature Dependencies

```
Authentication (session)
    └──required by──> All protected routes
    └──required by──> Conversation storage
    └──required by──> Settings persistence

LLM Provider Configuration
    └──required by──> Chat interface (streaming)
    └──required by──> Agent orchestration loop
    └──required by──> Tool / MCP / skill execution

Chat Interface (streaming + markdown)
    └──required by──> Conversation history (something to persist)
    └──required by──> Execution trace UI (messages to annotate)
    └──required by──> Retry/regenerate

Conversation Storage (DB)
    └──required by──> Conversation list + resume
    └──required by──> Trace persistence
    └──required by──> Source attribution storage

Orchestration Loop (model → tools → model)
    └──required by──> Tool execution + trace
    └──required by──> MCP invocation + trace
    └──required by──> Skill execution + trace

Embedding Configuration
    └──required by──> File upload + chunking
    └──required by──> RAG retrieval
    └──required by──> Source attribution

File Upload + Chunking + Embedding
    └──required by──> RAG retrieval in chat
    └──required by──> Source attribution UI

MCP Server Registration (Settings)
    └──required by──> MCP tool invocation
    └──required by──> MCP trace events

Skills Configuration (Settings)
    └──required by──> Skill execution
    └──required by──> Skill trace events

Execution Trace Events (runtime)
    └──required by──> Trace UI (per-message display)
    └──required by──> Trace persistence (DB storage)
    └──required by──> Trace replay on conversation resume

Health Diagnostics Panel
    └──depends on──> LLM provider config
    └──depends on──> Embedding config
    └──depends on──> MCP server config
    └──depends on──> ChromaDB connection
```

### Dependency Notes

- **Auth required by everything:** Auth gates all routes; must be Phase 1 before any feature can be tested end-to-end.
- **LLM provider config required by chat:** No chat is possible until a working endpoint is configured; provider settings must exist before building the chat UI.
- **Orchestration loop required by trace:** The trace system is only meaningful if there is an orchestration loop that emits trace events; these must be built together.
- **Embedding config required by RAG:** File upload is inert without embedding; they belong in the same phase.
- **Trace persistence depends on trace events:** You can build the UI shell early, but trace replay requires both the DB schema and the runtime emitter to be in place.

## MVP Definition

### Launch With (v1)

Minimum viable product — what's needed to validate the concept.

- [ ] Single-user authentication — gates all routes; prerequisite for everything
- [ ] Settings: LLM provider configuration with test-connection — without this nothing works
- [ ] Chat interface with streaming, markdown, and syntax highlighting — core product experience
- [ ] Conversation list with resume, rename, delete — without this it's a single-session toy
- [ ] Message retry / regenerate — first thing users reach for when output is bad
- [ ] System prompt / custom instructions — developers expect this from day one
- [ ] Execution trace UI per message (collapsed by default, expandable) — Forge's primary differentiator; must ship in v1 to validate the concept
- [ ] Trace persistence in DB + replay on resume — trace without persistence is a demo, not a product
- [ ] Custom orchestration loop (model → tools/MCP/skills → model) — backbone for all agent features
- [ ] MCP server registration + invocation with trace — validates the MCP integration story
- [ ] Agent skills configuration (enable/disable) + execution with trace — validates the skills story
- [ ] File upload, chunking, embedding, RAG retrieval — needed to validate the document Q&A use case
- [ ] Source attribution (which file/chunk) — differentiator that justifies building RAG at all
- [ ] Light/Dark/System theme — expected; near-free with shadcn
- [ ] JSON export of conversations — basic data portability

### Add After Validation (v1.x)

Features to add once core is working.

- [ ] Conversation search — add when conversation count makes it painful to browse
- [ ] Health diagnostics panel — add when MCP/embeddings are live and need observability
- [ ] Reranker configuration — add when users report RAG quality issues
- [ ] Web search provider configuration + tool — add when users request real-time data access
- [ ] Model parameter controls (temperature, max tokens) — add when power users ask for it
- [ ] Configurable timeout/retry settings per provider — add when reliability issues surface

### Future Consideration (v2+)

Features to defer until product-market fit is established.

- [ ] Advanced RAG (semantic chunking, hybrid search, graph RAG) — defer; simple RAG must prove value first
- [ ] Image generation support — defer; unrelated to core transparency value prop
- [ ] Voice input / TTS — defer; text-first is appropriate for developer tooling
- [ ] Multi-user support — defer; requires full auth overhaul and RBAC
- [ ] Parallel model comparison — defer; workflow-focused users rarely need side-by-side at this stage

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Auth + session | HIGH | LOW | P1 |
| LLM provider config + test-connection | HIGH | LOW | P1 |
| Streaming chat + markdown rendering | HIGH | LOW | P1 |
| Conversation list + resume + rename + delete | HIGH | LOW | P1 |
| Execution trace UI per message | HIGH | HIGH | P1 |
| Trace persistence + replay | HIGH | HIGH | P1 |
| Custom orchestration loop | HIGH | MEDIUM | P1 |
| MCP server registration + invocation | HIGH | HIGH | P1 |
| Agent skills config + execution | HIGH | MEDIUM | P1 |
| File upload + chunking + RAG | HIGH | HIGH | P1 |
| Source attribution in answers | HIGH | MEDIUM | P1 |
| System prompt / custom instructions | MEDIUM | LOW | P1 |
| Light/Dark theme | MEDIUM | LOW | P1 |
| JSON export | MEDIUM | LOW | P1 |
| Message retry/regenerate | MEDIUM | LOW | P1 |
| Conversation search | MEDIUM | MEDIUM | P2 |
| Health diagnostics panel | MEDIUM | MEDIUM | P2 |
| Model parameter controls | MEDIUM | LOW | P2 |
| Web search tool integration | MEDIUM | MEDIUM | P2 |
| Reranker configuration | MEDIUM | MEDIUM | P2 |
| Configurable timeout/retry | LOW | LOW | P2 |
| Image generation | LOW | HIGH | P3 |
| Voice input / TTS | LOW | HIGH | P3 |
| Parallel model comparison | LOW | HIGH | P3 |
| Multi-user / RBAC | LOW | HIGH | P3 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

## Competitor Feature Analysis

| Feature | Open WebUI | LibreChat | Jan.ai | Msty | Forge Approach |
|---------|------------|-----------|--------|------|----------------|
| Streaming chat | Yes | Yes | Yes | Yes | Yes — SSE |
| Markdown + code rendering | Yes | Yes | Yes | Yes | Yes — react-markdown + syntax highlight |
| Conversation history | Yes | Yes | Yes | Yes | Yes — sidebar list |
| Multi-provider LLM | Yes (15+ providers) | Yes (all major) | Yes (local + cloud) | Yes (local + cloud) | Yes — any OpenAI-compatible endpoint |
| System prompt | Yes (per model) | Yes (presets) | Yes | Yes | Yes — global default + per-conversation override |
| File upload + RAG | Yes (9 vector DBs) | Yes (custom RAG API) | Limited | Yes (Knowledge Stacks) | Yes — SQLite + ChromaDB, simple recursive chunking |
| Source attribution | Inline citations | Yes | No | Partial | Yes — file name, chunk preview, similarity score |
| MCP support | Yes (added 2025) | Yes (added 2025) | Yes | No | Yes — first-class with trace visibility |
| Tool use / function calling | Yes (Python functions) | Yes (Code Interpreter, Actions) | Limited | No | Yes — ToolExecutor + McpExecutor + SkillExecutor |
| Execution trace visibility | No — hidden | Partial — debug logs only; UI refresh planned Q2 2026 | No | No | Yes — full expandable trace tree per message, persisted |
| Trace persistence + replay | No | No | No | No | Yes — unique differentiator |
| Web search | Yes (15+ providers) | Yes | Yes | Yes (real-time data) | Yes (v1.x) |
| Image generation | Yes | Yes | No | No | Deferred to v2+ |
| Voice / TTS | Yes | Yes | No | No | Deferred to v2+ |
| Multi-user / RBAC | Yes (enterprise) | Yes (OAuth2, LDAP) | No | No | No — single-user MVP |
| Conversation branching | No | Yes | No | No | Not in MVP |
| Health diagnostics | No | No | No | No | Yes (v1.x) |
| Theme (light/dark) | Yes | Yes | Yes | Yes | Yes |
| Export conversations | Yes (JSON/PDF/TXT) | Yes | Yes | No | Yes (JSON export) |

## Sources

- [Open WebUI GitHub](https://github.com/open-webui/open-webui)
- [Open WebUI Features Documentation](https://docs.openwebui.com/features/)
- [LibreChat GitHub](https://github.com/danny-avila/LibreChat)
- [LibreChat Features Overview](https://www.librechat.ai/docs/features)
- [LibreChat 2025 Roadmap](https://www.librechat.ai/blog/2025-02-20_2025_roadmap)
- [Jan.ai Official Site](https://www.jan.ai/)
- [Jan.ai GitHub](https://github.com/janhq/jan)
- [Msty Official Site](https://msty.ai/)
- [AnythingLLM Documentation](https://docs.anythingllm.com/chatting-with-documents/introduction)
- [Best Open-Source ChatGPT Interfaces: LobeChat vs Open WebUI vs LibreChat](https://blog.elest.io/the-best-open-source-chatgpt-interfaces-lobechat-vs-open-webui-vs-librechat/)
- [LibreChat vs Open WebUI Comparison](https://blog.houseoffoss.com/post/open-webui-vs-librechat-2025-which-open-source-ai-chat-platform-is-better-for-you)
- [Open WebUI Complete Guide (2026)](https://www.mayhemcode.com/2026/03/open-webui-complete-guide-install-rag.html)

---
*Feature research for: local-first self-hosted AI assistant (Forge)*
*Researched: 2026-03-21*
