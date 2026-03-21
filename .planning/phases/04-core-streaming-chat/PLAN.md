---
phase: 04-core-streaming-chat
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - backend/app/models/conversation.py
  - backend/app/models/message.py
  - backend/app/models/__init__.py
  - backend/app/api/v1/chat.py
  - backend/app/api/v1/router.py
  - backend/alembic/versions/0004_add_conversation_message_tables.py
  - backend/app/api/v1/deps.py
autonomous: true
requirements:
  - CHAT-01
  - CHAT-02
  - CHAT-04
  - CHAT-05
  - CHAT-06
  - CHAT-07

must_haves:
  truths:
    - "POST /api/v1/conversations creates a new conversation and returns its id and title"
    - "GET /api/v1/conversations returns conversations sorted by updated_at desc"
    - "GET /api/v1/conversations/{id}/messages returns all messages for a conversation"
    - "PUT /api/v1/conversations/{id} renames a conversation; new title persists"
    - "DELETE /api/v1/conversations/{id} removes the conversation from the DB"
    - "POST /api/v1/chat/{conversation_id}/stream persists user message, streams tokens, persists complete assistant message on done"
    - "First user message triggers auto-title (first 50 chars of message content)"
  artifacts:
    - path: "backend/app/models/conversation.py"
      provides: "Conversation SQLModel (id, title, user_id, created_at, updated_at)"
      contains: "class Conversation"
    - path: "backend/app/models/message.py"
      provides: "Message SQLModel (id, conversation_id, role, content, created_at)"
      contains: "class Message"
    - path: "backend/app/api/v1/chat.py"
      provides: "CRUD endpoints + SSE streaming endpoint"
      exports: ["router"]
    - path: "backend/alembic/versions/0004_add_conversation_message_tables.py"
      provides: "Alembic migration creating conversations and messages tables"
      contains: "def upgrade"
  key_links:
    - from: "backend/app/api/v1/chat.py"
      to: "backend/app/models/llm_provider.py"
      via: "select default provider to get base_url + api_key_encrypted"
      pattern: "is_default.*True"
    - from: "backend/app/api/v1/chat.py"
      to: "backend/app/core/encryption.py"
      via: "decrypt_value(provider.api_key_encrypted)"
      pattern: "decrypt_value"
    - from: "backend/app/api/v1/router.py"
      to: "backend/app/api/v1/chat.py"
      via: "api_router.include_router(chat_router, prefix='/chat')"
      pattern: "include_router.*chat"
---

<objective>
Backend chat foundation: Conversation and Message SQLModel models with Alembic migration, conversation CRUD endpoints, and the SSE streaming endpoint that calls the configured LLM and streams tokens back to the browser.

Purpose: Delivers the complete server-side chat capability for Phase 4. Frontend plans (Wave 2) depend on these endpoints existing.
Output: Running FastAPI endpoints at /api/v1/conversations (CRUD) and /api/v1/chat/{id}/stream (SSE); Alembic migration applied; assistant messages persisted after streaming completes.
</objective>

<execution_context>
@/Users/przbadu/.claude/get-shit-done/workflows/execute-plan.md
@/Users/przbadu/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/phases/04-core-streaming-chat/4-CONTEXT.md
@.planning/research/STACK.md
@.planning/research/PITFALLS.md

<interfaces>
<!-- Existing code the executor will build against. No codebase exploration needed. -->

From backend/app/models/llm_provider.py:
```python
class LLMProvider(SQLModel, table=True):
    __tablename__ = "llm_provider"
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True, max_length=100)
    base_url: str = Field(max_length=500)
    api_key_encrypted: str = Field(default="")
    models: str = Field(default="[]")  # JSON array as text
    is_default: bool = Field(default=False)
    created_at: datetime = Field(default_factory=_utcnow)
```

From backend/app/core/encryption.py:
```python
def decrypt_value(ciphertext: str) -> str: ...
```

From backend/app/core/database.py:
```python
# Engine: sqlite+aiosqlite, NullPool, WAL mode enabled via pragma on connect
engine = create_async_engine(...)
AsyncSessionFactory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
async def get_session() -> AsyncGenerator[AsyncSession, None]: ...
```

From backend/app/api/v1/deps.py:
```python
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_session),
) -> User: ...
```

From backend/app/api/v1/router.py (current — must be updated):
```python
api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(providers_router, prefix="/settings/providers", tags=["settings"])
```

Alembic migration numbering: existing migrations are 0002, 0003. Next is 0004.
Batch mode is enabled (render_as_batch=True in env.py).
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Conversation and Message SQLModel models + Alembic migration</name>
  <files>
    backend/app/models/conversation.py,
    backend/app/models/message.py,
    backend/app/models/__init__.py,
    backend/alembic/versions/0004_add_conversation_message_tables.py
  </files>
  <action>
Create backend/app/models/conversation.py:

```python
from datetime import UTC, datetime
from typing import Optional
from sqlmodel import Field, SQLModel

def _utcnow() -> datetime:
    return datetime.now(UTC)

class Conversation(SQLModel, table=True):
    __tablename__ = "conversation"
    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(default="New Conversation", max_length=200)
    user_id: int = Field(foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
```

Create backend/app/models/message.py:

```python
from datetime import UTC, datetime
from sqlmodel import Field, SQLModel

def _utcnow() -> datetime:
    return datetime.now(UTC)

class Message(SQLModel, table=True):
    __tablename__ = "message"
    id: int | None = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="conversation.id", index=True)
    role: str = Field(max_length=20)  # "user" | "assistant" | "system"
    content: str = Field(default="")
    created_at: datetime = Field(default_factory=_utcnow)
```

Update backend/app/models/__init__.py to add:
```python
from app.models.conversation import Conversation
from app.models.message import Message
# add Conversation, Message to __all__
```

Create backend/alembic/versions/0004_add_conversation_message_tables.py. Use `alembic revision --autogenerate -m "add_conversation_message_tables"` from the backend directory (ensure models are imported in alembic env.py first if not already). Verify the generated migration creates `conversation` and `message` tables with correct columns and foreign keys. Apply with `alembic upgrade head`.

IMPORTANT: Alembic env.py must import Conversation and Message so autogenerate detects them. Check backend/alembic/env.py — if it imports from `app.models`, the new models need to be in `__init__.py` (done above). Run `cd /path/to/backend && alembic upgrade head` to apply.
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/backend && python -c "from app.models.conversation import Conversation; from app.models.message import Message; print('models OK')" && python -c "from sqlmodel import select; print('imports OK')"</automated>
  </verify>
  <done>Conversation and Message models importable; migration file exists with upgrade/downgrade; `alembic upgrade head` exits 0; `conversation` and `message` tables exist in forge.db</done>
</task>

<task type="auto">
  <name>Task 2: Conversation CRUD endpoints + SSE streaming endpoint</name>
  <files>
    backend/app/api/v1/chat.py,
    backend/app/api/v1/router.py
  </files>
  <action>
Create backend/app/api/v1/chat.py with these sections:

**Schemas (Pydantic, not SQLModel table models):**
```python
class ConversationCreate(BaseModel):
    title: str | None = None  # omit for auto-title from first message

class ConversationRead(BaseModel):
    id: int
    title: str
    user_id: int
    created_at: datetime
    updated_at: datetime

class ConversationUpdate(BaseModel):
    title: str

class MessageRead(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    created_at: datetime

class ChatStreamRequest(BaseModel):
    content: str  # user message text
```

**CRUD endpoints (all require get_current_user):**

- `GET /` — list conversations for current user, ordered by updated_at DESC, returns list[ConversationRead]
- `POST /` — create conversation (title defaults to "New Conversation"), return ConversationRead
- `GET /{conversation_id}/messages` — load all messages for conversation (verify ownership), return list[MessageRead]
- `PUT /{conversation_id}` — rename conversation (verify ownership), update updated_at, return ConversationRead
- `DELETE /{conversation_id}` — delete conversation + cascade delete messages (verify ownership via WHERE clause), return 204

**SSE streaming endpoint:**

`POST /{conversation_id}/stream` — accepts ChatStreamRequest body, requires auth. Logic:

1. Verify conversation belongs to current user (404 if not)
2. Persist user Message(role="user", content=request.content) to DB, flush to get id
3. If this is the first message in the conversation (count == 1), auto-title: set conversation.title = request.content[:50].strip(), update conversation.updated_at, commit
4. Fetch default LLM provider: `SELECT * FROM llm_provider WHERE is_default = true LIMIT 1` — if none, yield SSE error event and return
5. Decrypt api_key: `decrypt_value(provider.api_key_encrypted)` — use "" if empty
6. Load conversation history: all messages for conversation_id ordered by created_at, build openai messages list
7. Return `EventSourceResponse(token_generator(...))` with the async generator

**token_generator async generator:**
```python
async def token_generator(messages, base_url, api_key, model, conversation_id, session):
    try:
        client = AsyncOpenAI(base_url=base_url, api_key=api_key or "no-key")
        full_content = ""
        async with client.chat.completions.stream(
            model=model,
            messages=messages,
        ) as stream:
            async for text in stream.text_stream:
                full_content += text
                yield {"data": json.dumps({"type": "token", "delta": text})}
        # After stream completes, persist assistant message
        assistant_msg = Message(
            conversation_id=conversation_id,
            role="assistant",
            content=full_content,
        )
        session.add(assistant_msg)
        # Update conversation.updated_at
        await session.execute(
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(updated_at=datetime.now(UTC))
        )
        await session.commit()
        yield {"data": json.dumps({"type": "done", "message_id": assistant_msg.id})}
    except Exception as e:
        yield {"data": json.dumps({"type": "error", "message": str(e)})}
```

Use `from fastapi.responses import EventSourceResponse` (native in FastAPI 0.135+).
Use `from openai import AsyncOpenAI`.
Import `json`, `datetime`, `UTC` from datetime.

SSE event format per PITFALLS: set response headers `Cache-Control: no-cache`, `X-Accel-Buffering: no` via EventSourceResponse's `headers` param.

**Router registration:**

In backend/app/api/v1/router.py, add:
```python
from app.api.v1.chat import router as chat_router
api_router.include_router(chat_router, prefix="/chat", tags=["chat"])
```
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/backend && python -c "from app.api.v1.chat import router; print('chat router OK')" && python -m pytest tests/ -x -q --tb=short 2>/dev/null || echo "no tests yet"</automated>
  </verify>
  <done>All five CRUD endpoints importable; SSE endpoint defined; router registered in api_router; `GET /api/v1/chat/` returns 200 with auth token; `POST /api/v1/chat/{id}/stream` returns EventSourceResponse content-type</done>
</task>

</tasks>

<verification>
```bash
# Start backend and verify endpoints exist
cd /Users/przbadu/dev/claude-clone/backend
python -c "from app.api.v1.chat import router; from app.models.conversation import Conversation; from app.models.message import Message; print('all imports OK')"
alembic upgrade head
# Check tables
python -c "import sqlite3; conn = sqlite3.connect('forge.db'); print(conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall())"
```
</verification>

<success_criteria>
- `conversation` and `message` tables exist in forge.db with correct schema
- All 5 CRUD endpoints at /api/v1/chat/ respond correctly with a valid JWT
- SSE endpoint returns text/event-stream content-type
- Auto-title logic sets conversation.title from first 50 chars of first user message
- Assistant message persisted to DB after stream completion
- `alembic upgrade head` exits 0 on a fresh and existing DB
</success_criteria>

<output>
After completion, create `.planning/phases/04-core-streaming-chat/04-01-SUMMARY.md` documenting:
- Models created (Conversation, Message fields)
- Endpoints created (method, path, behavior)
- Migration file name
- Any deviations from this plan and why
</output>

---
phase: 04-core-streaming-chat
plan: 02
type: execute
wave: 2
depends_on: ["04-01"]
files_modified:
  - frontend/src/types/chat.ts
  - frontend/src/lib/chat-api.ts
  - frontend/src/hooks/useConversations.ts
  - frontend/src/hooks/useChat.ts
  - frontend/src/components/chat/ConversationList.tsx
  - frontend/src/components/chat/ChatPanel.tsx
  - frontend/src/components/chat/MessageBubble.tsx
  - frontend/src/components/chat/ChatInput.tsx
  - frontend/src/components/chat/MarkdownRenderer.tsx
  - frontend/src/app/(protected)/chat/layout.tsx
  - frontend/src/app/(protected)/chat/page.tsx
  - frontend/src/app/(protected)/chat/[id]/page.tsx
  - frontend/src/app/(protected)/page.tsx
autonomous: true
requirements:
  - CHAT-01
  - CHAT-02
  - CHAT-03
  - CHAT-04
  - CHAT-05
  - CHAT-06
  - CHAT-07

must_haves:
  truths:
    - "User sees sidebar with conversation list on the left and chat area on the right"
    - "Clicking 'New Conversation' opens a blank chat panel"
    - "Typing a message and pressing Send causes tokens to stream in immediately, one by one"
    - "Assistant messages render markdown with syntax-highlighted code blocks"
    - "Completed assistant message does not re-render from scratch after streaming ends"
    - "Conversations appear in sidebar immediately after user sends first message"
    - "Clicking a conversation in sidebar loads its messages"
    - "Double-clicking a conversation title in sidebar lets user rename it inline"
    - "Clicking delete on a conversation removes it from the sidebar"
    - "No XSS: injecting <script>alert(1)</script> as LLM output does not execute"
  artifacts:
    - path: "frontend/src/types/chat.ts"
      provides: "Conversation, Message, SSEEvent TypeScript types"
      exports: ["Conversation", "Message", "SSEEvent"]
    - path: "frontend/src/lib/chat-api.ts"
      provides: "Typed REST functions for conversation CRUD"
      exports: ["getConversations", "createConversation", "getMessages", "renameConversation", "deleteConversation"]
    - path: "frontend/src/hooks/useChat.ts"
      provides: "SSE stream consumer + message state (streaming + completed)"
      exports: ["useChat"]
    - path: "frontend/src/hooks/useConversations.ts"
      provides: "Conversation list state with optimistic updates"
      exports: ["useConversations"]
    - path: "frontend/src/components/chat/MarkdownRenderer.tsx"
      provides: "react-markdown + rehype-highlight + rehype-sanitize renderer"
      contains: "rehype-sanitize"
    - path: "frontend/src/app/(protected)/chat/layout.tsx"
      provides: "Chat shell: sidebar + main content split layout"
  key_links:
    - from: "frontend/src/hooks/useChat.ts"
      to: "http://localhost:8000/api/v1/chat/{id}/stream"
      via: "fetch + ReadableStream + TextDecoder (NOT EventSource — POST not supported)"
      pattern: "ReadableStream|getReader"
    - from: "frontend/src/components/chat/MarkdownRenderer.tsx"
      to: "rehype-sanitize"
      via: "rehypePlugins: [rehypeSanitize, rehypeHighlight]"
      pattern: "rehypeSanitize"
    - from: "frontend/src/app/(protected)/chat/[id]/page.tsx"
      to: "frontend/src/hooks/useConversations.ts"
      via: "invalidate conversation list after first message to update title in sidebar"
      pattern: "invalidate|refetch"
---

<objective>
Frontend chat UI: types, API client, custom hooks for SSE streaming and conversation management, all UI components (ConversationList, ChatPanel, MessageBubble, ChatInput, MarkdownRenderer), and the chat route layout with sidebar. Includes installing react-markdown, rehype-highlight, and rehype-sanitize.

Purpose: Delivers the complete user-facing chat interface. Depends on 04-01 backend endpoints.
Output: Navigating to /chat shows sidebar + chat panel. User can create conversations, stream responses, see markdown with syntax highlighting, rename and delete conversations.
</objective>

<execution_context>
@/Users/przbadu/.claude/get-shit-done/workflows/execute-plan.md
@/Users/przbadu/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/phases/04-core-streaming-chat/4-CONTEXT.md
@.planning/research/STACK.md
@.planning/research/PITFALLS.md
@.planning/phases/04-core-streaming-chat/04-01-SUMMARY.md

<interfaces>
<!-- Existing frontend code to build against. -->

From frontend/src/lib/api.ts:
```typescript
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function apiFetch(
  path: string,
  token: string,
  options: RequestInit = {}
): Promise<Response> {
  return fetch(`${API_BASE}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...(options.headers ?? {}),
    },
  });
}
```

From frontend/src/context/auth-context.tsx:
```typescript
export function useAuth(): AuthContextValue {
  // Returns: { token: string | null, user: UserResponse | null, isLoading: boolean, login, logout }
}
```

From frontend/src/app/(protected)/layout.tsx:
```typescript
// Guards: redirects to /login if no token. Children render when token exists.
export default function ProtectedLayout({ children }: { children: React.ReactNode })
```

Backend SSE event shape (from 04-01):
```typescript
// Each SSE line: "data: <JSON>\n\n"
// JSON shapes:
{ type: "token", delta: string }     // streaming token
{ type: "done", message_id: number } // stream complete
{ type: "error", message: string }   // error
```

Backend REST API (from 04-01):
GET    /api/v1/chat/                              → Conversation[]
POST   /api/v1/chat/                              → Conversation
GET    /api/v1/chat/{id}/messages                 → Message[]
PUT    /api/v1/chat/{id}                          → Conversation  body: { title }
DELETE /api/v1/chat/{id}                          → 204
POST   /api/v1/chat/{id}/stream                   → SSE stream   body: { content }

Next.js version is 16.2.1 — App Router. Read node_modules/next/dist/docs/ before writing route files.
This project uses @base-ui/react (not shadcn) — check frontend/src/components/ui/ for existing primitives.
Existing components use lucide-react for icons.
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Install packages + define types + build API client and hooks</name>
  <files>
    frontend/src/types/chat.ts,
    frontend/src/lib/chat-api.ts,
    frontend/src/hooks/useConversations.ts,
    frontend/src/hooks/useChat.ts
  </files>
  <action>
**Install packages:**
```bash
cd /Users/przbadu/dev/claude-clone/frontend
npm install react-markdown remark-gfm rehype-highlight rehype-sanitize highlight.js
npm install zustand
```

**frontend/src/types/chat.ts:**
```typescript
export interface Conversation {
  id: number;
  title: string;
  user_id: number;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: number;
  conversation_id: number;
  role: "user" | "assistant" | "system";
  content: string;
  created_at: string;
}

export type MessageState =
  | { status: "complete"; message: Message }
  | { status: "streaming"; content: string; conversationId: number };

export interface SSETokenEvent { type: "token"; delta: string }
export interface SSEDoneEvent  { type: "done"; message_id: number }
export interface SSEErrorEvent { type: "error"; message: string }
export type SSEEvent = SSETokenEvent | SSEDoneEvent | SSEErrorEvent;
```

**frontend/src/lib/chat-api.ts:**
Typed REST wrappers using `apiFetch` from `@/lib/api`. Functions:
- `getConversations(token): Promise<Conversation[]>` — GET /api/v1/chat/
- `createConversation(token): Promise<Conversation>` — POST /api/v1/chat/
- `getMessages(token, conversationId): Promise<Message[]>` — GET /api/v1/chat/{id}/messages
- `renameConversation(token, id, title): Promise<Conversation>` — PUT /api/v1/chat/{id}
- `deleteConversation(token, id): Promise<void>` — DELETE /api/v1/chat/{id}

**frontend/src/hooks/useConversations.ts:**
Custom hook using `@tanstack/react-query` (already in package.json). Returns:
- `conversations: Conversation[]`
- `isLoading: boolean`
- `createConversation(): Promise<Conversation>` — calls createConversation API, invalidates query
- `renameConversation(id, title): Promise<void>` — optimistic update, calls API
- `deleteConversation(id): Promise<void>` — optimistic update, calls API
- `refetch(): void` — manual refetch (called after auto-title update)

Uses `useAuth()` to get token. Query key: `["conversations"]`.

**frontend/src/hooks/useChat.ts:**
Custom hook for SSE stream consumption and message state. Parameters: `conversationId: number | null`.

State:
- `messages: Message[]` — loaded from API on conversationId change
- `streamingContent: string | null` — accumulates delta tokens during stream
- `isStreaming: boolean`
- `error: string | null`

Methods:
- `sendMessage(content: string): Promise<void>` — implementation:
  1. Optimistically append user message to `messages` state
  2. Set `isStreaming = true`, `streamingContent = ""`
  3. Create `AbortController`
  4. Call `fetch` directly to `${API_BASE}/api/v1/chat/${conversationId}/stream` with method POST, Authorization header, body `{ content }` (NOT via apiFetch — need raw Response for streaming)
  5. Read `response.body.getReader()`, `TextDecoder`
  6. Loop: `reader.read()` → decode → split on `\n` → parse lines starting with `data: ` → JSON.parse → dispatch SSEEvent
  7. On `type: "token"`: append delta to `streamingContent`
  8. On `type: "done"`: set `isStreaming = false`, convert `streamingContent` to a Message object and append to `messages`, clear `streamingContent`. Call `onConversationUpdated?.()` callback (for sidebar refetch).
  9. On `type: "error"`: set `error`, `isStreaming = false`
  10. Handle AbortController signal for future stop support
- `loadMessages(conversationId): void` — fetches messages from API and sets state

CRITICAL (from PITFALLS): Use `fetch` + `ReadableStream` + `TextDecoder`, NOT the browser `EventSource` API — EventSource only supports GET.
CRITICAL (from CONTEXT D-14): Browser connects directly to FastAPI at port 8000, not through Next.js.
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/frontend && npx tsc --noEmit 2>&1 | head -30</automated>
  </verify>
  <done>TypeScript compiles without errors on types/chat.ts, lib/chat-api.ts, hooks/useConversations.ts, hooks/useChat.ts; react-markdown, rehype-highlight, rehype-sanitize, highlight.js present in node_modules</done>
</task>

<task type="auto">
  <name>Task 2: Chat UI components + chat route layout and pages</name>
  <files>
    frontend/src/components/chat/MarkdownRenderer.tsx,
    frontend/src/components/chat/MessageBubble.tsx,
    frontend/src/components/chat/ChatInput.tsx,
    frontend/src/components/chat/ConversationList.tsx,
    frontend/src/components/chat/ChatPanel.tsx,
    frontend/src/app/(protected)/chat/layout.tsx,
    frontend/src/app/(protected)/chat/page.tsx,
    frontend/src/app/(protected)/chat/[id]/page.tsx,
    frontend/src/app/(protected)/page.tsx
  </files>
  <action>
**frontend/src/components/chat/MarkdownRenderer.tsx:**
"use client" component. Uses react-markdown with:
- `remarkPlugins={[remarkGfm]}`
- `rehypePlugins={[rehypeSanitize, [rehypeHighlight, { detect: true }]]}`
- `rehypeSanitize` MUST come before `rehypeHighlight` in the array (sanitize first, then highlight)
- Custom `components` prop: style `pre` with dark background, `code` with monospace font, horizontal scroll
- Import highlight.js CSS theme: `import 'highlight.js/styles/github-dark.css'` (or github.css for light)
Props: `{ content: string; className?: string }`.

Security requirement (PITFALLS §Markdown XSS): Never use `dangerouslySetInnerHTML`. rehype-sanitize must be present. Test renders `<script>alert(1)</script>` safely.

**frontend/src/components/chat/MessageBubble.tsx:**
"use client" component. Props: `{ role: "user" | "assistant"; content: string; isStreaming?: boolean }`.
- User messages: right-aligned or visually distinct (per design discretion), plain text
- Assistant messages: left-aligned, uses `<MarkdownRenderer content={content} />`
- `isStreaming=true` shows blinking cursor at end of content (CSS animation `animate-pulse` on a `|` character appended after content)

**frontend/src/components/chat/ChatInput.tsx:**
"use client" component. Props: `{ onSend: (content: string) => void; disabled?: boolean }`.
- Textarea (auto-growing) with Send button
- Enter key sends (Shift+Enter adds newline)
- Disabled while `disabled=true` (streaming in progress)
- Clears input after send

**frontend/src/components/chat/ConversationList.tsx:**
"use client" component. Props: `{ activeId?: number }`. Uses `useConversations()` hook.
- List of conversations ordered by updated_at desc (API already returns sorted)
- Each item: click navigates to `/chat/{id}` using Next.js `useRouter`
- Active item visually highlighted (Tailwind `bg-accent` or similar)
- Inline rename: double-click conversation title → show input field → blur/Enter saves → calls `renameConversation`
- Delete button: icon button (Trash2 from lucide-react) per item, confirm with `window.confirm`, calls `deleteConversation`, navigates to `/chat` if deleted conversation was active
- "New Chat" button at top: calls `createConversation`, navigates to `/chat/{newId}`

**frontend/src/components/chat/ChatPanel.tsx:**
"use client" component. Props: `{ conversationId: number; onConversationUpdated?: () => void }`. Uses `useChat(conversationId)`.
- Renders scrollable message list using `MessageBubble` for each message
- During streaming: shows current `streamingContent` as a `MessageBubble` with `isStreaming=true`
- Auto-scroll: `useEffect` with ref on the bottom div; scroll whenever messages or streamingContent changes. Pause auto-scroll if user scrolled up (detect with `scrollTop + clientHeight < scrollHeight - 50`)
- Shows loading state while messages are fetching
- Shows error state if `error` is set
- `ChatInput` at bottom, disabled while `isStreaming=true`
- Calls `onConversationUpdated` after first message sent (so sidebar refetches for auto-title update)

**frontend/src/app/(protected)/chat/layout.tsx:**
"use client". Imports the `(protected)` layout indirectly (already wraps all protected routes). This layout creates the two-panel shell:
- Left panel: fixed-width sidebar (e.g. `w-64`) containing `<ConversationList activeId={...} />`
- Right panel: `flex-1` main area for `{children}`
- Use `useParams()` from next/navigation to get active conversation id for ConversationList
- Full height: `h-screen flex overflow-hidden`

**frontend/src/app/(protected)/chat/page.tsx:**
"use client". Empty state: shows a centered message like "Select a conversation or start a new one" with a "New Chat" button. Button calls `createConversation` from `useConversations` and navigates to the new conversation.

**frontend/src/app/(protected)/chat/[id]/page.tsx:**
"use client". Reads `params.id` (string), converts to number. Renders `<ChatPanel conversationId={id} onConversationUpdated={refetch} />`. The `refetch` function comes from `useConversations().refetch`.

**frontend/src/app/(protected)/page.tsx:**
Update to redirect to `/chat` instead of showing the placeholder home page. Use `useRouter().replace('/chat')` in a `useEffect` on mount, or render a Link to /chat. Keep it simple: redirect immediately.

IMPORTANT: Read the Next.js 16 docs at `node_modules/next/dist/docs/01-app/` before creating route files. Confirm correct conventions for "use client", params access, and layout nesting for this version.
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/frontend && npx tsc --noEmit 2>&1 | head -40 && npm run lint 2>&1 | tail -20</automated>
  </verify>
  <done>TypeScript compiles clean; ESLint passes; `npm run dev` starts without errors; navigating to http://localhost:3000/chat shows sidebar + empty chat panel; all chat route files exist</done>
</task>

<task type="checkpoint:human-verify" gate="blocking">
  <what-built>
    Complete chat UI: sidebar with conversation list, streaming chat panel, markdown renderer with syntax highlighting, rename/delete, and auto-title from first message. Connects to FastAPI backend SSE endpoint at port 8000.
  </what-built>
  <how-to-verify>
    Prerequisites: Backend running (`make dev` or `cd backend && uvicorn app.main:app --reload`), frontend running (`cd frontend && npm run dev`), at least one LLM provider configured as default in Settings.

    1. Navigate to http://localhost:3000 — should redirect to /chat
    2. Sidebar shows "New Chat" button and empty conversation list
    3. Click "New Chat" — navigates to /chat/{id}, chat panel is empty
    4. Type a message (e.g. "Write a short Python hello world with a docstring") and press Send
    5. User message appears immediately; assistant starts streaming tokens in real time
    6. Verify tokens appear incrementally (not all at once after a delay)
    7. After streaming: assert the response renders markdown (code block with syntax highlighting for Python)
    8. Conversation title in sidebar updates from "New Conversation" to first 50 chars of your message
    9. Double-click the conversation title in sidebar — editable input appears, type new name, press Enter — new name persists
    10. Click delete (trash icon) on the conversation — confirm dialog — conversation removed from sidebar
    11. XSS check: create new conversation, send message containing `<script>alert(1)</script>` — no alert should fire; text appears escaped in the response area

    Expected: All 11 steps pass without errors. Streaming feels real-time. Markdown renders correctly. No XSS execution.
  </how-to-verify>
  <resume-signal>Type "approved" if all steps pass, or describe which steps failed and what you observed</resume-signal>
</task>

</tasks>

<verification>
```bash
# TypeScript and lint gates
cd /Users/przbadu/dev/claude-clone/frontend
npx tsc --noEmit
npm run lint

# Packages installed
node -e "require('react-markdown'); require('rehype-sanitize'); require('rehype-highlight'); require('highlight.js'); require('zustand'); console.log('all packages OK')"
```
</verification>

<success_criteria>
- All TypeScript files compile without errors
- ESLint passes with no violations
- Chat layout renders: sidebar (left) + main area (right)
- Conversations stream tokens incrementally from FastAPI SSE
- react-markdown renders code blocks with syntax highlighting
- rehype-sanitize prevents XSS in LLM output
- Conversation create/rename/delete all function correctly
- Auto-title updates sidebar after first message
- Human verification checkpoint approved
</success_criteria>

<output>
After completion, create `.planning/phases/04-core-streaming-chat/04-02-SUMMARY.md` documenting:
- Components created and their props
- SSE consumption pattern (fetch + ReadableStream approach)
- Packages installed and versions
- Any deviations from this plan and why
- Checkpoint verification result
</output>

---
phase: 04-core-streaming-chat
plan: 03
type: tdd
wave: 3
depends_on: ["04-01", "04-02"]
files_modified:
  - backend/tests/test_chat_crud.py
  - backend/tests/test_chat_streaming.py
  - frontend/src/components/chat/__tests__/MarkdownRenderer.test.tsx
  - frontend/src/components/chat/__tests__/ChatInput.test.tsx
  - frontend/src/hooks/__tests__/useChat.test.ts
  - tests/e2e/chat.spec.ts
autonomous: true
requirements:
  - CHAT-01
  - CHAT-02
  - CHAT-03
  - CHAT-04
  - CHAT-05
  - CHAT-06
  - CHAT-07

must_haves:
  truths:
    - "pytest passes all backend chat tests (CRUD + streaming unit) with no failures"
    - "vitest passes all frontend component and hook tests with no failures"
    - "Playwright E2E test covers: new conversation, send message, streaming response visible, rename, delete"
  artifacts:
    - path: "backend/tests/test_chat_crud.py"
      provides: "Integration tests for all 5 CRUD endpoints"
      contains: "test_create_conversation"
    - path: "backend/tests/test_chat_streaming.py"
      provides: "Unit tests for streaming endpoint and auto-title logic"
      contains: "test_stream_endpoint"
    - path: "frontend/src/components/chat/__tests__/MarkdownRenderer.test.tsx"
      provides: "XSS safety and markdown rendering correctness tests"
      contains: "script alert"
    - path: "tests/e2e/chat.spec.ts"
      provides: "Playwright E2E for complete chat flow"
      contains: "streaming"
  key_links:
    - from: "backend/tests/test_chat_streaming.py"
      to: "backend/app/api/v1/chat.py"
      via: "AsyncClient with ASGITransport, iterating SSE lines"
      pattern: "ASGITransport"
    - from: "tests/e2e/chat.spec.ts"
      to: "http://localhost:3000/chat"
      via: "Playwright page.goto + waitForSelector"
      pattern: "waitForSelector|locator"
---

<objective>
Test coverage for Phase 4: backend pytest integration tests (CRUD + streaming), frontend Vitest component and hook tests (markdown renderer XSS, chat input behavior), and Playwright E2E for the full conversation flow.

Purpose: Validates correctness, prevents regressions, and meets project mandate (TEST-01) that every shipped feature has tests.
Output: `pytest` and `vitest run` both pass. E2E smoke test covers the happy-path chat flow.
</objective>

<execution_context>
@/Users/przbadu/.claude/get-shit-done/workflows/execute-plan.md
@/Users/przbadu/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/phases/04-core-streaming-chat/4-CONTEXT.md
@.planning/research/STACK.md
@.planning/phases/04-core-streaming-chat/04-01-SUMMARY.md
@.planning/phases/04-core-streaming-chat/04-02-SUMMARY.md

<interfaces>
<!-- Test patterns from existing backend tests. -->

Backend test pattern (from existing tests in backend/tests/):
```python
# conftest.py pattern
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
```

SSE response reading pattern for httpx:
```python
async with client.stream("POST", "/api/v1/chat/{id}/stream", json={"content": "hello"}) as resp:
    events = []
    async for line in resp.aiter_lines():
        if line.startswith("data: "):
            events.append(json.loads(line[6:]))
```

Frontend test pattern (Vitest + Testing Library):
```typescript
import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
```
</interfaces>
</context>

<feature>
  <name>Phase 4 Chat Tests</name>
  <files>
    backend/tests/test_chat_crud.py,
    backend/tests/test_chat_streaming.py,
    frontend/src/components/chat/__tests__/MarkdownRenderer.test.tsx,
    frontend/src/components/chat/__tests__/ChatInput.test.tsx,
    frontend/src/hooks/__tests__/useChat.test.ts,
    tests/e2e/chat.spec.ts
  </files>
  <behavior>
    Backend CRUD tests (pytest, asyncio, httpx AsyncClient):
    - test_create_conversation: POST /api/v1/chat/ with valid JWT → 200, body has id and title
    - test_list_conversations: create 2, GET /api/v1/chat/ → both appear, ordered by updated_at desc
    - test_get_messages: create conversation + POST a user message directly, GET /api/v1/chat/{id}/messages → message appears
    - test_rename_conversation: PUT /api/v1/chat/{id} with {title: "new name"} → 200, title updated
    - test_delete_conversation: DELETE /api/v1/chat/{id} → 204, subsequent GET returns 404
    - test_conversation_ownership: user A cannot access user B's conversation → 404

    Backend streaming tests (pytest, mock AsyncOpenAI):
    - test_stream_returns_event_stream: POST /api/v1/chat/{id}/stream → Content-Type contains text/event-stream
    - test_stream_token_events: mock AsyncOpenAI.chat.completions.stream to yield ["Hello", " world"] → SSE lines contain {"type":"token","delta":"Hello"} and {"type":"token","delta":" world"}
    - test_stream_done_event: after mock stream completes → SSE line contains {"type":"done","message_id": ...}
    - test_auto_title_on_first_message: send first message to new conversation → conversation.title set to first 50 chars of message
    - test_stream_error_on_no_provider: DELETE all providers, POST stream → SSE line contains {"type":"error"}

    Frontend Vitest tests:
    - MarkdownRenderer: renders **bold** as <strong>, renders ```python print("hi")``` with highlighted class, renders <script>alert(1)</script> as escaped text (no script element in DOM)
    - ChatInput: typing text and pressing Enter calls onSend with that text; disabled=true prevents send; Shift+Enter adds newline instead of sending
    - useChat hook: sendMessage appends optimistic user message to messages state; on SSEDoneEvent, isStreaming becomes false and streamingContent is cleared (use vi.fn() to mock fetch)

    Playwright E2E (happy path, requires running app):
    - Login, navigate to /chat
    - Click "New Chat", verify empty panel
    - Type "Say hello in one word" and send
    - Wait for streaming to complete (waitForSelector for a message bubble with assistant role)
    - Assert conversation appears in sidebar
    - Rename conversation inline, assert new title persists after page reload
    - Delete conversation, assert it disappears from sidebar
  </behavior>
  <implementation>
    RED phase: Write all test files with tests that will fail (no implementation yet — but since this is Wave 3, implementation IS already done). Run `pytest backend/tests/test_chat_crud.py -v` and `vitest run` to confirm current status.

    GREEN phase: If any tests fail due to implementation gaps (not test setup issues), fix the implementation. If tests fail due to test setup (wrong import paths, missing fixtures), fix the tests.

    Backend test setup:
    - Check if backend/tests/conftest.py has auth token fixture. If not, add one that creates a test user and returns a valid JWT. Pattern: call POST /api/v1/auth/login with test credentials.
    - Use `pytest.mark.asyncio` (or asyncio_mode=auto in pyproject.toml — check existing config)
    - Mock `AsyncOpenAI` in streaming tests using `unittest.mock.patch` or `pytest-mock`

    Frontend test setup:
    - Check frontend/vitest.config.ts for jsdom environment config
    - Mock `fetch` in useChat tests using `vi.fn()`
    - Wrap components in QueryClientProvider where needed for hooks

    E2E test:
    - Check if tests/e2e/ directory exists or if Playwright config is at frontend level
    - Use `page.waitForResponse` to wait for streaming to complete rather than fixed delays
    - Tests must be idempotent: clean up created conversations

    REFACTOR: Remove any test duplication, extract shared fixtures to conftest.py.
  </implementation>
</feature>

<verification>
```bash
# Backend tests
cd /Users/przbadu/dev/claude-clone/backend
python -m pytest tests/test_chat_crud.py tests/test_chat_streaming.py -v --tb=short

# Frontend tests
cd /Users/przbadu/dev/claude-clone/frontend
npm test -- --reporter=verbose 2>&1 | tail -40

# E2E (requires running app)
# cd /Users/przbadu/dev/claude-clone && npx playwright test tests/e2e/chat.spec.ts
```
</verification>

<success_criteria>
- `pytest tests/test_chat_crud.py tests/test_chat_streaming.py` exits 0, all tests pass
- `npm test` exits 0, all frontend tests pass including MarkdownRenderer XSS test
- E2E test file exists and is syntactically valid (full E2E run requires running app)
- No test relies on hardcoded IDs or external network calls (mocked where needed)
</success_criteria>

<output>
After completion, create `.planning/phases/04-core-streaming-chat/04-03-SUMMARY.md` documenting:
- Tests written and what they cover
- Any bugs found and fixed during test writing
- Final pytest and vitest pass counts
- E2E test status (written / passing)
</output>
