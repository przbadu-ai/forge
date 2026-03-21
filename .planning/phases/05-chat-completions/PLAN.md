---
phase: 05-chat-completions
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - backend/app/models/conversation.py
  - backend/app/models/settings.py
  - backend/alembic/versions/0005_chat_completions_fields.py
  - backend/app/api/v1/chat.py
  - backend/app/api/v1/settings/general.py
  - backend/app/api/v1/router.py
  - frontend/src/types/chat.ts
  - frontend/src/lib/chat-api.ts
  - frontend/src/hooks/useChat.ts
  - frontend/src/components/chat/ChatInput.tsx
  - frontend/src/components/chat/ChatPanel.tsx
  - frontend/src/components/chat/ConversationList.tsx
  - frontend/src/components/settings/GeneralSection.tsx
  - frontend/src/app/(protected)/settings/page.tsx
  - frontend/src/app/(protected)/chat/page.tsx
autonomous: true
requirements:
  - CHAT-08
  - CHAT-09
  - CHAT-10
  - CHAT-11
  - CHAT-12
  - SET-07
  - UX-02

must_haves:
  truths:
    - "Global system prompt set in Settings applies to all new conversation API calls"
    - "Per-conversation system prompt override persists and takes precedence over global"
    - "Stop button halts SSE stream immediately; partial tokens already received are saved"
    - "Regenerate deletes the last assistant message and re-streams a fresh response"
    - "Temperature and max_tokens are adjustable globally and per-conversation"
    - "JSON export downloads a .json file with conversation title and all messages"
    - "Search endpoint returns conversations whose messages match the query string"
  artifacts:
    - path: "backend/app/models/conversation.py"
      provides: "Conversation model with system_prompt, temperature, max_tokens fields"
      contains: "system_prompt"
    - path: "backend/app/models/settings.py"
      provides: "AppSettings model storing global system_prompt, temperature, max_tokens"
      contains: "class AppSettings"
    - path: "backend/alembic/versions/0005_chat_completions_fields.py"
      provides: "Migration adding new columns to conversation + new app_settings table"
      contains: "op.add_column"
    - path: "backend/app/api/v1/chat.py"
      provides: "Regenerate endpoint, export endpoint, search endpoint, stop-aware streaming"
      exports: ["POST /{id}/regenerate", "GET /{id}/export", "GET /search"]
    - path: "backend/app/api/v1/settings/general.py"
      provides: "GET/PUT /settings/general endpoints for global system_prompt + model params"
      exports: ["GET /", "PUT /"]
    - path: "frontend/src/hooks/useChat.ts"
      provides: "stopGeneration() and regenerate() added to hook return"
      contains: "stopGeneration"
    - path: "frontend/src/components/chat/ChatInput.tsx"
      provides: "Stop button shown during streaming; send button hidden during streaming"
      contains: "onStop"
    - path: "frontend/src/components/chat/ChatPanel.tsx"
      provides: "Regenerate button on last assistant message; export button in header"
      contains: "onRegenerate"
    - path: "frontend/src/components/settings/GeneralSection.tsx"
      provides: "Settings UI for global system prompt + temperature + max_tokens"
      contains: "system_prompt"
    - path: "frontend/src/components/chat/ConversationList.tsx"
      provides: "Search input filtering conversations by query; calls /chat/search API"
      contains: "search"
  key_links:
    - from: "backend/app/api/v1/chat.py (_token_generator)"
      to: "AppSettings + Conversation"
      via: "system prompt prepended as first message in openai_messages list"
      pattern: "system_prompt"
    - from: "frontend/src/hooks/useChat.ts"
      to: "abortControllerRef"
      via: "stopGeneration calls abortControllerRef.current?.abort(); partial content saved via stopped SSE event"
      pattern: "abort"
    - from: "frontend/src/components/chat/ChatPanel.tsx"
      to: "useChat.regenerate"
      via: "Regenerate button on last assistant MessageBubble"
      pattern: "regenerate"
---

<objective>
Extend Phase 4 streaming chat with full generation control, system prompts, model parameters, export, and search.

Purpose: Gives users control over AI behavior (system prompts, temperature), generation lifecycle (stop/regenerate), and data portability (export, search).
Output: 3 backend endpoints (regenerate, export, search), 1 settings endpoint (general), DB migration, updated streaming to inject system prompt + params, and matching frontend UI wired end-to-end.
</objective>

<execution_context>
@/Users/przbadu/.claude/get-shit-done/workflows/execute-plan.md
@/Users/przbadu/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/phases/05-chat-completions/5-CONTEXT.md

<!-- Key locked decisions from CONTEXT.md:
  D-01: Global system prompt in AppSettings table (key=system_prompt)
  D-02: Per-conversation system_prompt field on Conversation model
  D-03: System prompt prepended as first message in openai_messages (NOT a persisted Message row)
  D-04: Stop = AbortController.abort() on frontend; backend stream will error/disconnect naturally
  D-05: Regenerate = DELETE last assistant Message row, re-POST to stream endpoint
  D-06: Stop saves partial content received before abort via a "stopped" SSE event type
  D-07: temperature and max_tokens globally in AppSettings + per-conversation on Conversation (null = use global)
  D-08: Stored on Conversation model
  D-09: Global defaults in AppSettings
  D-10: JSON export = GET /chat/{id}/export returns application/json download
  D-11: Full-text search on message.content via SQLite LIKE query
  D-12: Search returns matching Conversation objects (not individual messages)
-->
</context>

<interfaces>
<!-- Existing contracts the executor must build against. -->

From backend/app/models/conversation.py (current, to be extended):
```python
class Conversation(SQLModel, table=True):
    __tablename__ = "conversation"
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(default="New Conversation", max_length=200)
    user_id: int = Field(foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
    # ADD: system_prompt: str | None = Field(default=None)
    # ADD: temperature: float | None = Field(default=None)
    # ADD: max_tokens: int | None = Field(default=None)
```

From backend/app/api/v1/chat.py (current _token_generator signature):
```python
async def _token_generator(
    messages: list[dict[str, str]],
    base_url: str,
    api_key: str,
    model: str,
    conversation_id: int,
    session: AsyncSession,
) -> AsyncGenerator[str, None]:
    # Extend to accept: system_prompt: str | None, temperature: float | None, max_tokens: int | None
```

From frontend/src/hooks/useChat.ts (current return type):
```typescript
interface UseChatReturn {
  messages: Message[];
  streamingContent: string | null;
  isStreaming: boolean;
  error: string | null;
  sendMessage: (content: string) => Promise<void>;
  // ADD: stopGeneration: () => void;
  // ADD: regenerate: () => Promise<void>;
}
```

From frontend/src/components/chat/ChatInput.tsx (current props):
```typescript
interface ChatInputProps {
  onSend: (content: string) => void;
  disabled?: boolean;
  // ADD: onStop?: () => void;
  // ADD: isStreaming?: boolean;
}
```

From frontend/src/app/(protected)/settings/page.tsx:
```tsx
// Currently has "providers" and "appearance" tabs
// ADD: "general" tab for AppSettings (system prompt + model params)
```
</interfaces>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Backend — DB migration + model extensions + AppSettings CRUD</name>
  <files>
    backend/app/models/conversation.py,
    backend/app/models/settings.py,
    backend/alembic/versions/0005_chat_completions_fields.py,
    backend/app/api/v1/settings/general.py,
    backend/app/api/v1/router.py,
    backend/tests/test_settings_general.py
  </files>
  <behavior>
    - GET /api/v1/settings/general with no rows returns defaults: system_prompt=null, temperature=0.7, max_tokens=2048
    - PUT /api/v1/settings/general updates values and GET returns them
    - PUT with temperature=2.1 returns 422 (out of range 0.0–2.0)
    - PUT with max_tokens=0 returns 422 (must be >= 1)
    - Alembic upgrade/downgrade 0005 completes without error
  </behavior>
  <action>
1. Extend `backend/app/models/conversation.py` — add three nullable fields:
   ```python
   system_prompt: str | None = Field(default=None)
   temperature: float | None = Field(default=None)
   max_tokens: int | None = Field(default=None)
   ```

2. Create `backend/app/models/settings.py` — a single-row key/value settings table:
   ```python
   class AppSettings(SQLModel, table=True):
       __tablename__ = "app_settings"
       id: int | None = Field(default=None, primary_key=True)
       system_prompt: str | None = Field(default=None)
       temperature: float = Field(default=0.7)
       max_tokens: int = Field(default=2048)
   ```

3. Create `backend/alembic/versions/0005_chat_completions_fields.py`:
   - Revision ID: `0005_chat_completions_fields`
   - down_revision: `'100955aaddd5'` (the 0004 migration ID)
   - upgrade(): batch_alter conversation → add_column for system_prompt (String, nullable), temperature (Float, nullable), max_tokens (Integer, nullable); create app_settings table with id, system_prompt, temperature, max_tokens
   - downgrade(): batch_alter conversation → drop those 3 columns; drop app_settings table
   - Use `with op.batch_alter_table('conversation', schema=None) as batch_op:` pattern (required for SQLite)

4. Create `backend/app/api/v1/settings/general.py`:
   - Router with prefix (mounted later), auth dependency
   - Pydantic schemas: `GeneralSettingsRead` (system_prompt, temperature, max_tokens), `GeneralSettingsUpdate` (all Optional with validators: temperature in [0.0, 2.0], max_tokens >= 1)
   - GET `/` — fetch single AppSettings row; if none, return defaults (system_prompt=None, temperature=0.7, max_tokens=2048)
   - PUT `/` — upsert AppSettings row (create if id=1 missing, update otherwise)

5. Register the new router in `backend/app/api/v1/router.py`:
   - Import general router, include at prefix `/settings/general`

6. Add `AppSettings` to `backend/app/models/__init__.py` imports so Alembic detects it.

7. Write `backend/tests/test_settings_general.py` — pytest-asyncio tests covering the behavior cases above using the existing httpx async test client pattern from other test files.

Run migration: `cd /Users/przbadu/dev/claude-clone/backend && uv run alembic upgrade head`
Verify: `cd /Users/przbadu/dev/claude-clone/backend && uv run pytest tests/test_settings_general.py -x -q`
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/backend && uv run alembic upgrade head && uv run pytest tests/test_settings_general.py -x -q</automated>
  </verify>
  <done>Migration applies cleanly; AppSettings CRUD returns correct defaults and validates ranges; all 5 behavior tests pass.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Backend — Extend streaming + regenerate + export + search endpoints</name>
  <files>
    backend/app/api/v1/chat.py,
    backend/tests/test_chat_completions.py
  </files>
  <behavior>
    - POST /{id}/stream now prepends system prompt (conversation override > global) as first message with role="system" when non-null
    - POST /{id}/stream passes temperature and max_tokens to openai call (conversation override > global default)
    - SSE emits {"type": "stopped", "message_id": N} when client aborts and partial content was received; partial message is persisted
    - POST /{id}/regenerate on conversation with last message role=assistant: deletes that message, returns 200 with {"status": "ok"}
    - POST /{id}/regenerate on conversation with no assistant message: returns 404
    - GET /{id}/export returns Content-Disposition: attachment; filename="conversation-{id}.json" with body {"id", "title", "messages": [...]}
    - GET /search?q=hello returns list of conversations whose messages contain "hello" (LIKE %hello%)
    - GET /search?q= (empty) returns 422
  </behavior>
  <action>
1. Update `_token_generator` signature to accept `system_prompt: str | None`, `temperature: float`, `max_tokens: int`.
   - If system_prompt is not None, prepend `{"role": "system", "content": system_prompt}` to the messages list BEFORE passing to openai.
   - Pass `temperature=temperature, max_tokens=max_tokens` to `client.chat.completions.create(...)`.
   - Add abort/stop handling: wrap the `async for chunk in stream:` loop in try/except. On `asyncio.CancelledError` or when the generator is closed early: if `full_content` is non-empty, persist the partial message and yield `{"type": "stopped", "message_id": N}`. Re-raise CancelledError after yield.

2. Update `stream_chat` endpoint to:
   - Fetch AppSettings (single row, or use defaults if absent)
   - Resolve effective system_prompt: `conversation.system_prompt or global_settings.system_prompt`
   - Resolve effective temperature: `conversation.temperature if conversation.temperature is not None else global_settings.temperature`
   - Resolve effective max_tokens: `conversation.max_tokens if conversation.max_tokens is not None else global_settings.max_tokens`
   - Pass all three to `_token_generator`.

3. Add `POST /{conversation_id}/regenerate` endpoint:
   - Verify conversation ownership.
   - Query last message by created_at desc.
   - If last message role != "assistant": raise 404 with detail "No assistant message to regenerate".
   - Delete that message, commit.
   - Return `{"status": "ok"}` with 200.

4. Add `GET /{conversation_id}/export` endpoint:
   - Verify ownership.
   - Fetch all messages ordered by created_at asc.
   - Return `JSONResponse` with header `Content-Disposition: attachment; filename="conversation-{id}.json"` and body `{"id": ..., "title": ..., "messages": [{"role": ..., "content": ..., "created_at": ...}, ...]}`.

5. Add `GET /search` endpoint:
   - Query param `q: str` with `min_length=1` (raises 422 if empty).
   - Query: `SELECT DISTINCT conversation.* FROM conversation JOIN message ON message.conversation_id = conversation.id WHERE conversation.user_id = :uid AND message.content LIKE :pattern` using `f"%{q}%"`.
   - Return list of `ConversationRead`.

6. Update `ConversationRead` schema to include new fields: `system_prompt: str | None`, `temperature: float | None`, `max_tokens: float | None`.

7. Update `create_conversation` and `update_conversation` endpoints (and schemas) to accept optional system_prompt, temperature, max_tokens.
   - `ConversationCreate` gains optional fields (all None by default).
   - `ConversationUpdate` gains optional system_prompt, temperature, max_tokens.

8. Write `backend/tests/test_chat_completions.py` covering the behavior cases above using mock or a test LLM provider fixture (mock the openai call with `monkeypatch` to avoid real network calls).

Run: `cd /Users/przbadu/dev/claude-clone/backend && uv run pytest tests/test_chat_completions.py -x -q`
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/backend && uv run pytest tests/test_chat_completions.py -x -q</automated>
  </verify>
  <done>All behavior cases pass; system prompt appears as first message in mocked openai calls; regenerate/export/search return correct shapes; ruff and mypy pass on chat.py.</done>
</task>

<task type="auto">
  <name>Task 3: Frontend — Stop/regenerate/export in chat + system prompt + model params in settings + search in sidebar</name>
  <files>
    frontend/src/types/chat.ts,
    frontend/src/lib/chat-api.ts,
    frontend/src/lib/settings-api.ts,
    frontend/src/hooks/useChat.ts,
    frontend/src/hooks/useGeneralSettings.ts,
    frontend/src/components/chat/ChatInput.tsx,
    frontend/src/components/chat/ChatPanel.tsx,
    frontend/src/components/chat/ConversationList.tsx,
    frontend/src/components/settings/GeneralSection.tsx,
    frontend/src/app/(protected)/settings/page.tsx
  </files>
  <action>
NOTE: This project's frontend/AGENTS.md warns that Next.js APIs may differ from training data. Read `node_modules/next/dist/docs/` if encountering unknown Next.js APIs. All patterns here follow the existing codebase conventions from Phase 4.

1. Update `frontend/src/types/chat.ts`:
   - Add to `Conversation`: `system_prompt: string | null; temperature: number | null; max_tokens: number | null;`
   - Add new type: `GeneralSettings { system_prompt: string | null; temperature: number; max_tokens: number; }`
   - Add to `SSEEvent` union: `| { type: "stopped"; message_id: number }`

2. Create `frontend/src/lib/settings-api.ts`:
   - `getGeneralSettings(token): Promise<GeneralSettings>` — GET /api/v1/settings/general
   - `updateGeneralSettings(token, data: Partial<GeneralSettings>): Promise<GeneralSettings>` — PUT /api/v1/settings/general

3. Update `frontend/src/lib/chat-api.ts`:
   - `regenerateLastMessage(token, conversationId): Promise<void>` — POST /api/v1/chat/{id}/regenerate
   - `exportConversation(token, conversationId): Promise<Blob>` — GET /api/v1/chat/{id}/export, return response.blob()
   - `searchConversations(token, q: string): Promise<Conversation[]>` — GET /api/v1/chat/search?q={q}
   - Update `createConversation` to accept optional `{ system_prompt?, temperature?, max_tokens? }` and POST body
   - Update `renameConversation` → make it `updateConversation(token, id, data: Partial<Pick<Conversation, 'title'|'system_prompt'|'temperature'|'max_tokens'>>)` — PUT /api/v1/chat/conversations/{id}

4. Update `frontend/src/hooks/useChat.ts`:
   - Add `stopGeneration: () => void` — calls `abortControllerRef.current?.abort()`, sets `isStreaming(false)`, preserves accumulated content in messages if "stopped" SSE event was received before abort
   - Add `regenerate: () => Promise<void>` — calls `regenerateLastMessage`, removes last assistant message from local state, then calls `sendMessage` with last user message content (read from `messages` state)
   - Handle new SSE event type `"stopped"` the same as `"done"` (persist partial message using `message_id`)
   - Return type gains `stopGeneration` and `regenerate`

5. Update `frontend/src/components/chat/ChatInput.tsx`:
   - Add props `onStop?: () => void` and `isStreaming?: boolean`
   - When `isStreaming` is true: hide the Send button, show a Square/Stop icon button that calls `onStop`
   - Use `lucide-react` `Square` icon for stop button, styled with `text-destructive` variant

6. Update `frontend/src/components/chat/ChatPanel.tsx`:
   - Destructure `stopGeneration` and `regenerate` from `useChat`
   - Pass `onStop={stopGeneration}` and `isStreaming={isStreaming}` to `ChatInput`
   - Add an Export button in the panel header area (top-right, `Download` lucide icon, `variant="ghost" size="icon"`). On click: call `exportConversation(token, conversationId)`, create a blob URL, trigger `<a>` download with `conversation-{id}.json` filename, revoke URL after click.
   - Show Regenerate button below the last assistant `MessageBubble` when `!isStreaming && messages.length > 0 && messages[messages.length-1].role === "assistant"`. Use `RefreshCw` lucide icon, `variant="ghost" size="sm"`. On click: call `regenerate()`.
   - Use `useAuth()` to get token for the export call.

7. Update `frontend/src/components/chat/ConversationList.tsx`:
   - Add a search input above the conversation list (shadcn `Input` component, placeholder "Search conversations...").
   - Use local state `searchQuery` (debounced 300ms with `useEffect`).
   - When `searchQuery.length >= 2`: call `searchConversations(token, searchQuery)` and show results instead of full list.
   - When empty: show full conversations list as before.
   - Use `useAuth()` for token.

8. Create `frontend/src/hooks/useGeneralSettings.ts`:
   - Uses `useQuery` (tanstack-query) with key `["general-settings"]`
   - `updateSettings` mutation calling `updateGeneralSettings`
   - Returns `{ settings, isLoading, updateSettings }`

9. Create `frontend/src/components/settings/GeneralSection.tsx`:
   - Form with three fields:
     a. "System Prompt" — shadcn `Textarea`, label "Custom Instructions / System Prompt", placeholder "You are a helpful assistant...", controlled by settings.system_prompt
     b. "Temperature" — shadcn `Slider` (range 0–2, step 0.1), with numeric display showing current value
     c. "Max Tokens" — shadcn `Input` type="number", min=1, max=32768
   - Save button triggers `updateSettings` mutation; show success toast via `sonner` on success.
   - Uses `useGeneralSettings()` hook.

10. Update `frontend/src/app/(protected)/settings/page.tsx`:
    - Add a third `TabsTrigger value="general"` labeled "General"
    - Add corresponding `TabsContent value="general"` rendering `<GeneralSection />`

TypeScript: run `cd /Users/przbadu/dev/claude-clone/frontend && npx tsc --noEmit` to verify no type errors.
ESLint: run `cd /Users/przbadu/dev/claude-clone/frontend && npx eslint src/components/chat/ChatPanel.tsx src/components/chat/ChatInput.tsx src/components/chat/ConversationList.tsx src/components/settings/GeneralSection.tsx src/hooks/useChat.ts --max-warnings=0`
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/frontend && npx tsc --noEmit 2>&1 | head -30</automated>
  </verify>
  <done>
    TypeScript compiles with no errors. ESLint passes. All new files exist. Key behaviors:
    - ChatInput shows Stop icon during streaming, Send icon otherwise
    - Last assistant message has Regenerate button visible when not streaming
    - Settings page has General tab with system prompt textarea, temperature slider, max_tokens input
    - ConversationList shows search input that filters via API when query length >= 2
    - Export button triggers .json download
  </done>
</task>

<task type="auto" tdd="true">
  <name>Task 4: Tests — backend completions + frontend Vitest component tests</name>
  <files>
    backend/tests/test_chat_completions.py,
    frontend/src/hooks/useChat.test.ts,
    frontend/src/components/chat/ChatInput.test.tsx,
    frontend/src/components/settings/GeneralSection.test.tsx
  </files>
  <behavior>
    Backend (pytest):
    - regenerate endpoint returns 200 and last assistant message is gone from DB
    - regenerate when no assistant message returns 404
    - export endpoint returns JSON body with correct shape and Content-Disposition header
    - search returns only conversations whose messages match query; empty q returns 422

    Frontend (vitest):
    - ChatInput renders Stop button when isStreaming=true
    - ChatInput renders Send button when isStreaming=false
    - ChatInput calls onStop when Stop button clicked
    - GeneralSection renders three fields and Save button
    - useChat.stopGeneration calls abort on abortControllerRef
  </behavior>
  <action>
1. Complete or extend `backend/tests/test_chat_completions.py` with the four backend behavior cases. Use `pytest-asyncio` and `httpx.AsyncClient` (same pattern as existing tests). Mock the OpenAI client where needed using `unittest.mock.patch("app.api.v1.chat.AsyncOpenAI")`.

2. Create `frontend/src/hooks/useChat.test.ts`:
   - Test `stopGeneration` calls `abortControllerRef.current.abort()` using a spy.
   - Use `renderHook` from `@testing-library/react` wrapped with required providers (QueryClientProvider, AuthContext mock).

3. Create `frontend/src/components/chat/ChatInput.test.tsx`:
   - Render with `isStreaming=false` → expect Send button present, no Stop button.
   - Render with `isStreaming=true` → expect Stop button present (aria-label="Stop generation"), Send button absent.
   - Click Stop button → expect `onStop` mock called once.
   - Use `@testing-library/react` render + `userEvent`.

4. Create `frontend/src/components/settings/GeneralSection.test.tsx`:
   - Mock `useGeneralSettings` hook return.
   - Render GeneralSection.
   - Expect textarea, temperature input/slider, max-tokens input, and Save button all present.

Run all:
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/backend && uv run pytest tests/test_chat_completions.py tests/test_settings_general.py -x -q && cd /Users/przbadu/dev/claude-clone/frontend && npx vitest run src/hooks/useChat.test.ts src/components/chat/ChatInput.test.tsx src/components/settings/GeneralSection.test.tsx --reporter=verbose 2>&1 | tail -20</automated>
  </verify>
  <done>All backend and frontend tests pass. Backend: regenerate/export/search endpoints behave correctly. Frontend: Stop/Send button toggle works, GeneralSection renders all fields.</done>
</task>

</tasks>

<verification>
After all tasks complete, verify the full phase:

1. Backend: `cd /Users/przbadu/dev/claude-clone/backend && uv run pytest -x -q` — all tests pass
2. Frontend types: `cd /Users/przbadu/dev/claude-clone/frontend && npx tsc --noEmit` — zero errors
3. Frontend lint: `cd /Users/przbadu/dev/claude-clone/frontend && npx eslint src --max-warnings=0`
4. Backend lint: `cd /Users/przbadu/dev/claude-clone/backend && uv run ruff check . && uv run mypy app`
5. Migration: `cd /Users/przbadu/dev/claude-clone/backend && uv run alembic downgrade -1 && uv run alembic upgrade head` — round-trips cleanly
</verification>

<success_criteria>
1. Global system prompt in AppSettings applies to all new streaming calls (prepended as role=system)
2. Per-conversation system prompt on Conversation model overrides global when set
3. Stop button aborts SSE stream; any partial tokens received are saved as an assistant message
4. Regenerate deletes last assistant message and frontend re-streams from same user message
5. Temperature (0.0–2.0) and max_tokens (>=1) configurable in General Settings and per-conversation
6. GET /chat/{id}/export returns downloadable JSON with all messages
7. GET /chat/search?q=... returns matching conversations; empty q returns 422
8. All pytest and Vitest tests pass; ruff, mypy, tsc, eslint all clean
</success_criteria>

<output>
After completion, create `.planning/phases/05-chat-completions/05-01-SUMMARY.md` covering:
- What was built (endpoints added, models extended, UI components)
- Migration revision ID
- Any implementation decisions made under Claude's discretion
- Patterns established (system prompt injection pattern, abort+partial-save pattern)
</output>
