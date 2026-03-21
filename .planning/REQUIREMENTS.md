# Requirements: Forge

**Defined:** 2026-03-21
**Core Value:** Every AI interaction — chat, tool call, MCP action, skill execution — is visible, persisted, and reviewable.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Authentication

- [x] **AUTH-01**: User can log in with username and password
- [x] **AUTH-02**: User session persists across browser refresh
- [x] **AUTH-03**: User can log out from any page
- [x] **AUTH-04**: All API routes are protected behind authentication

### Chat

- [ ] **CHAT-01**: User can start a new chat conversation
- [ ] **CHAT-02**: User receives streaming token output via SSE
- [ ] **CHAT-03**: Assistant messages render markdown with syntax-highlighted code blocks
- [ ] **CHAT-04**: User can view conversation list in sidebar
- [ ] **CHAT-05**: User can resume a previous conversation
- [ ] **CHAT-06**: User can rename a conversation
- [ ] **CHAT-07**: User can delete a conversation
- [ ] **CHAT-08**: User can set a global system prompt / custom instructions
- [ ] **CHAT-09**: User can override system prompt per conversation
- [ ] **CHAT-10**: User can regenerate the last assistant response on failure
- [ ] **CHAT-11**: User can stop an in-progress generation
- [ ] **CHAT-12**: User can search across all conversations by message content

### Execution Trace

- [ ] **TRACE-01**: Each assistant message displays an expandable execution trace section
- [ ] **TRACE-02**: Trace shows ordered events: tool calls, MCP calls, skill triggers
- [ ] **TRACE-03**: Each trace event shows type, name, status, timestamps, and compact input/output
- [ ] **TRACE-04**: Trace events persist in the database linked to their message
- [ ] **TRACE-05**: Traces re-render correctly when resuming a conversation

### Orchestration

- [ ] **ORCH-01**: Backend runs a custom orchestration loop (model -> tools/MCP/skills -> model)
- [ ] **ORCH-02**: Orchestration uses modular executor interfaces (ToolExecutor, McpExecutor, SkillExecutor)
- [ ] **ORCH-03**: TraceEmitter emits structured events for all executor actions
- [ ] **ORCH-04**: RunStateStore tracks run lifecycle (created, running, completed, failed, cancelled)
- [ ] **ORCH-05**: Orchestration supports configurable timeout/retry for all external calls

### MCP Integration

- [ ] **MCP-01**: User can register MCP servers in Settings (name, command, args, env)
- [ ] **MCP-02**: User can enable/disable individual MCP servers
- [ ] **MCP-03**: Chat runtime can invoke MCP tools during orchestration
- [ ] **MCP-04**: MCP tool calls appear in the execution trace with full metadata
- [ ] **MCP-05**: MCP failures/timeouts show user-visible error status in trace

### Skills

- [ ] **SKILL-01**: User can view and enable/disable skills in Settings
- [ ] **SKILL-02**: Skill triggers and outputs appear in message execution trace
- [ ] **SKILL-03**: Skill execution metadata persists in the database

### Retrieval & Files

- [ ] **RAG-01**: User can upload files (PDF, DOCX, TXT, MD) for document Q&A
- [ ] **RAG-02**: Uploaded files are chunked and embedded into ChromaDB
- [ ] **RAG-03**: Chat retrieves relevant chunks from ChromaDB when files are referenced
- [ ] **RAG-04**: Assistant responses show source attribution (file name, chunk preview, relevance score)
- [ ] **RAG-05**: User can view and manage uploaded files

### Settings

- [ ] **SET-01**: User can configure LLM providers with multiple profiles (base URL, API key, models)
- [ ] **SET-02**: User can configure embedding model endpoint
- [ ] **SET-03**: User can configure reranker endpoint
- [ ] **SET-04**: User can configure web search providers (SearXNG, Exa)
- [ ] **SET-05**: User can test-connection for any configured endpoint
- [ ] **SET-06**: Health diagnostics panel shows status of all configured integrations
- [ ] **SET-07**: User can adjust model parameters (temperature, max tokens) per conversation or globally

### Theme & Export

- [ ] **UX-01**: User can switch between Light, Dark, and System themes
- [ ] **UX-02**: User can export chat sessions as JSON for backup

### Testing & Quality

- [ ] **TEST-01**: Every shipped feature includes corresponding tests at the appropriate layer
- [ ] **TEST-02**: E2E tests cover: auth, chat streaming, tool trace rendering, settings persistence
- [ ] **TEST-03**: Streaming tests verify ordered delivery, interruption handling, and trace integrity
- [x] **TEST-04**: CI validates: lint, type-check, unit/integration tests, E2E smoke, build

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Advanced Retrieval

- **RAG-V2-01**: Semantic chunking with configurable strategies
- **RAG-V2-02**: Hybrid search (keyword + vector)
- **RAG-V2-03**: Graph RAG for complex document relationships

### Extended Capabilities

- **EXT-01**: Image generation support (DALL-E/ComfyUI integration)
- **EXT-02**: Voice input with speech-to-text
- **EXT-03**: Text-to-speech output
- **EXT-04**: Conversation branching / forking
- **EXT-05**: Parallel model comparison (side-by-side)

### Multi-User

- **MULTI-01**: Multi-user support with signup/login
- **MULTI-02**: Per-user data isolation
- **MULTI-03**: Role-based access control

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| OAuth / SSO | Single-user MVP doesn't need it; adds significant complexity |
| Mobile native app | Web-first; responsive web UI is sufficient for local use |
| Real-time collaboration | Not applicable to solo developer use case |
| Agent frameworks (LangGraph, AutoGen) | Reduces debuggability; custom loop is more transparent |
| Enterprise governance/audit | Not the target audience |
| Multilingual UI | English-only for developer audience; i18n can be added later |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| TEST-04 | Phase 1: Infrastructure Foundation | Complete |
| AUTH-01 | Phase 2: Authentication | Complete |
| AUTH-02 | Phase 2: Authentication | Complete |
| AUTH-03 | Phase 2: Authentication | Complete |
| AUTH-04 | Phase 2: Authentication | Complete |
| SET-01 | Phase 3: LLM Provider Settings | Pending |
| SET-05 | Phase 3: LLM Provider Settings | Pending |
| UX-01 | Phase 3: LLM Provider Settings | Pending |
| CHAT-01 | Phase 4: Core Streaming Chat | Pending |
| CHAT-02 | Phase 4: Core Streaming Chat | Pending |
| CHAT-03 | Phase 4: Core Streaming Chat | Pending |
| CHAT-04 | Phase 4: Core Streaming Chat | Pending |
| CHAT-05 | Phase 4: Core Streaming Chat | Pending |
| CHAT-06 | Phase 4: Core Streaming Chat | Pending |
| CHAT-07 | Phase 4: Core Streaming Chat | Pending |
| CHAT-08 | Phase 5: Chat Completions | Pending |
| CHAT-09 | Phase 5: Chat Completions | Pending |
| CHAT-10 | Phase 5: Chat Completions | Pending |
| CHAT-11 | Phase 5: Chat Completions | Pending |
| CHAT-12 | Phase 5: Chat Completions | Pending |
| SET-07 | Phase 5: Chat Completions | Pending |
| UX-02 | Phase 5: Chat Completions | Pending |
| TRACE-01 | Phase 6: Execution Trace System | Pending |
| TRACE-02 | Phase 6: Execution Trace System | Pending |
| TRACE-03 | Phase 6: Execution Trace System | Pending |
| TRACE-04 | Phase 6: Execution Trace System | Pending |
| TRACE-05 | Phase 6: Execution Trace System | Pending |
| ORCH-01 | Phase 7: Orchestration Loop | Pending |
| ORCH-02 | Phase 7: Orchestration Loop | Pending |
| ORCH-03 | Phase 7: Orchestration Loop | Pending |
| ORCH-04 | Phase 7: Orchestration Loop | Pending |
| ORCH-05 | Phase 7: Orchestration Loop | Pending |
| MCP-01 | Phase 8: MCP Integration | Pending |
| MCP-02 | Phase 8: MCP Integration | Pending |
| MCP-03 | Phase 8: MCP Integration | Pending |
| MCP-04 | Phase 8: MCP Integration | Pending |
| MCP-05 | Phase 8: MCP Integration | Pending |
| SKILL-01 | Phase 9: Skills Integration | Pending |
| SKILL-02 | Phase 9: Skills Integration | Pending |
| SKILL-03 | Phase 9: Skills Integration | Pending |
| RAG-01 | Phase 10: File Upload + RAG | Pending |
| RAG-02 | Phase 10: File Upload + RAG | Pending |
| RAG-03 | Phase 10: File Upload + RAG | Pending |
| RAG-04 | Phase 10: File Upload + RAG | Pending |
| RAG-05 | Phase 10: File Upload + RAG | Pending |
| SET-02 | Phase 10: File Upload + RAG | Pending |
| SET-03 | Phase 10: File Upload + RAG | Pending |
| SET-04 | Phase 11: Settings Completion + Quality Gate | Pending |
| SET-06 | Phase 11: Settings Completion + Quality Gate | Pending |
| TEST-01 | Phase 11: Settings Completion + Quality Gate | Pending |
| TEST-02 | Phase 11: Settings Completion + Quality Gate | Pending |
| TEST-03 | Phase 11: Settings Completion + Quality Gate | Pending |

**Coverage:**
- v1 requirements: 52 total
- Mapped to phases: 52
- Unmapped: 0

---
*Requirements defined: 2026-03-21*
*Last updated: 2026-03-21 after roadmap creation — all 52 v1 requirements mapped*
