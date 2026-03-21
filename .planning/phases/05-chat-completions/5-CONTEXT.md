# Phase 5: Chat Completions - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

<domain>
## Phase Boundary

System prompts (global + per-conversation), stop generation, regenerate last response, JSON export, conversation search, and model parameter controls (temperature, max_tokens). Builds on the core chat from Phase 4.

</domain>

<decisions>
## Implementation Decisions

### System prompts
- **D-01:** Global system prompt stored in settings (DB or config)
- **D-02:** Per-conversation system prompt override stored on Conversation model
- **D-03:** System prompt prepended as first message in LLM API call (not persisted as a Message row)

### Generation control
- **D-04:** Stop button aborts the SSE stream via AbortController on frontend + cancels the openai stream on backend
- **D-05:** Regenerate deletes the last assistant message and re-streams
- **D-06:** Stop should save partial assistant response if tokens were received

### Model parameters
- **D-07:** Temperature and max_tokens configurable globally and per-conversation
- **D-08:** Stored on Conversation model (null = use global default)
- **D-09:** Global defaults stored in settings

### Export & Search
- **D-10:** JSON export downloads conversation with all messages as a .json file
- **D-11:** Conversation search via full-text search on message content
- **D-12:** Search endpoint returns matching conversations (not individual messages)

### Claude's Discretion
- UI placement of system prompt editor
- Search UI design (sidebar filter or dedicated page)
- Export format details
- Model parameter slider ranges

</decisions>

<canonical_refs>
## Canonical References

- `PRD.md` §7.2 — Chat experience requirements
- `backend/app/api/v1/chat.py` — Existing chat endpoints to extend
- `backend/app/models/conversation.py` — Conversation model to add fields
- `frontend/src/hooks/useChat.ts` — Chat hook to extend

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/api/v1/chat.py` — SSE streaming endpoint to extend with system prompt + model params
- `frontend/src/hooks/useChat.ts` — Chat hook to add stop/regenerate
- `frontend/src/components/chat/composer.tsx` — Add stop button during streaming

### Integration Points
- System prompt settings page section (extend settings from Phase 3)
- Conversation model needs new fields (system_prompt, temperature, max_tokens)
- SSE endpoint needs abort handling improvement

</code_context>

<deferred>
## Deferred Ideas

None — all within scope

</deferred>

---

*Phase: 05-chat-completions*
*Context gathered: 2026-03-21*
