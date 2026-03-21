# Phase 3: LLM Provider Settings - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Settings pages for LLM providers/models with multiple profiles, test-connection button, and Light/Dark/System theme support. No chat functionality yet — just configuration and validation.

</domain>

<decisions>
## Implementation Decisions

### Provider model
- **D-01:** LLM providers stored in DB (not .env) so they can be managed via UI
- **D-02:** Each provider has: name, base_url, api_key (encrypted), model list, is_default flag
- **D-03:** API keys stored encrypted at rest (Fernet or similar symmetric encryption)
- **D-04:** Multiple providers supported (e.g., Ollama local + OpenAI cloud)
- **D-05:** One provider marked as default for new conversations

### Settings UI
- **D-06:** Settings accessible via a route (e.g., /settings or slide-out panel)
- **D-07:** Provider form: name, base URL, API key, models (auto-discovered or manual)
- **D-08:** "Test Connection" button pings the provider's /models endpoint
- **D-09:** Success shows latency + available models; failure shows error message
- **D-10:** Use shadcn/ui form components (Input, Button, Card, etc.)

### Theme
- **D-11:** next-themes for Light/Dark/System theme switching
- **D-12:** Theme toggle in settings or header/nav area
- **D-13:** Persist theme preference in localStorage (next-themes handles this)

### Claude's Discretion
- Settings page layout and navigation
- Provider form validation details
- Model auto-discovery implementation
- Exact encryption approach for API keys

</decisions>

<specifics>
## Specific Ideas

- Test connection should actually call the provider's /v1/models endpoint using the openai Python client
- Show a simple settings shell that will expand in later phases (MCP, skills, embedding, etc.)
- Keep the settings page modular — each category (providers, theme, etc.) as a separate section/tab

</specifics>

<canonical_refs>
## Canonical References

### Stack
- `.planning/research/STACK.md` — openai Python SDK version, next-themes usage
- `PRD.md` §7.7 — Settings requirements

### Phase 2 outputs
- `backend/app/api/v1/deps.py` — get_current_user dependency (protect settings endpoints)
- `backend/app/core/database.py` — get_session dependency
- `frontend/src/context/auth-context.tsx` — useAuth hook for authenticated API calls

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `backend/app/api/v1/deps.py` — get_current_user for protecting settings endpoints
- `backend/app/core/database.py` — AsyncSessionFactory, get_session
- `frontend/src/lib/api.ts` — apiFetch wrapper with auth token
- `frontend/src/components/ui/button.tsx` — shadcn Button component

### Established Patterns
- SQLModel for DB models, Alembic for migrations
- FastAPI router with Depends(get_current_user) for protection
- React context for state management

### Integration Points
- Provider settings will be queried by the chat system in Phase 4
- Settings page shell will be extended in Phases 8 (MCP), 9 (Skills), 10 (RAG)

</code_context>

<deferred>
## Deferred Ideas

- Embedding model config — Phase 10
- Reranker config — Phase 10
- MCP server config — Phase 8
- Skills config — Phase 9
- Web search providers — Phase 11

</deferred>

---

*Phase: 03-llm-provider-settings*
*Context gathered: 2026-03-21*
