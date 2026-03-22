---
phase: quick
plan: 260322-cka
type: execute
wave: 1
depends_on: []
files_modified:
  - backend/app/models/mcp_server.py
  - backend/alembic/versions/0008_add_mcp_transport_type_and_url.py
  - backend/app/api/v1/settings/mcp_servers.py
  - backend/app/services/executors/mcp_executor.py
  - backend/app/tests/test_mcp_server_api.py
  - frontend/src/lib/mcp-api.ts
  - frontend/src/components/settings/mcp-server-form.tsx
  - frontend/src/components/settings/mcp-server-card.tsx
  - frontend/src/components/layout/app-header.tsx
  - frontend/src/app/(protected)/layout.tsx
  - frontend/src/app/(protected)/chat/layout.tsx
  - frontend/src/__tests__/mcp-servers.test.tsx
autonomous: true
requirements: []
must_haves:
  truths:
    - "User can register MCP servers with stdio, SSE, or streamable_http transport types"
    - "SSE and streamable_http servers require a URL instead of command+args"
    - "MCP tool discovery and execution works for all three transport types"
    - "User can navigate between Chat and Settings pages via a persistent header"
  artifacts:
    - path: "backend/alembic/versions/0008_add_mcp_transport_type_and_url.py"
      provides: "Migration adding transport_type and url columns"
    - path: "frontend/src/components/layout/app-header.tsx"
      provides: "Global navigation header component"
  key_links:
    - from: "backend/app/services/executors/mcp_executor.py"
      to: "mcp.client.sse / mcp.client.streamable_http"
      via: "conditional transport client selection"
      pattern: "sse_client|streamable_http_client"
    - from: "frontend/src/components/layout/app-header.tsx"
      to: "/chat, /settings"
      via: "Next.js Link navigation"
      pattern: "Link.*href=.*/chat|/settings"
---

<objective>
Add full MCP transport support (stdio, SSE, streamable HTTP) and a global navigation header for moving between Chat and Settings.

Purpose: Currently MCP only supports stdio (local subprocess) servers. Many MCP servers expose SSE or streamable HTTP endpoints (e.g., MCP Studio, remote servers). Users also lack a way to navigate between Chat and Settings without manually editing the URL.

Output: Updated MCP model with transport types, working SSE/HTTP executor, navigation header.
</objective>

<execution_context>
@/Users/przbadu/.claude/get-shit-done/workflows/execute-plan.md
@/Users/przbadu/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@.planning/PROJECT.md
@.planning/phases/08-mcp-integration/08-01-SUMMARY.md
@.planning/phases/08-mcp-integration/08-02-SUMMARY.md

<interfaces>
<!-- Backend MCP model (current) -->
From backend/app/models/mcp_server.py:
```python
class McpServer(SQLModel, table=True):
    __tablename__ = "mcp_server"
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True, max_length=100)
    command: str = Field(max_length=500)
    args: str = Field(default="[]")       # JSON array
    env_vars: str = Field(default="{}")    # JSON object
    is_enabled: bool = Field(default=True)
    created_at: datetime
    updated_at: datetime
```

<!-- MCP SDK available clients -->
From mcp.client module:
- mcp.client.stdio: StdioServerParameters, stdio_client (context manager)
- mcp.client.sse: sse_client (context manager, takes url + optional headers/timeout/httpx_client_factory)
- mcp.client.streamable_http: streamablehttp_client (context manager, takes url + optional headers/timeout)

<!-- Frontend MCP types (current) -->
From frontend/src/lib/mcp-api.ts:
```typescript
export interface McpServerRead {
  id: number; name: string; command: string;
  args: string[]; env_vars: Record<string, string>;
  is_enabled: boolean; created_at: string;
}
export interface McpServerCreate {
  name: string; command: string;
  args?: string[]; env_vars?: Record<string, string>;
  is_enabled?: boolean;
}
```

<!-- Current chat layout sidebar -->
From frontend/src/app/(protected)/chat/layout.tsx:
```tsx
<div className="flex h-screen overflow-hidden">
  <aside className="w-64 shrink-0 border-r bg-muted/30">
    <ConversationList activeId={activeId} />
  </aside>
  <main className="flex flex-1 flex-col overflow-hidden">{children}</main>
</div>
```

<!-- Protected layout (no navigation currently) -->
From frontend/src/app/(protected)/layout.tsx:
```tsx
// Just auth guard, renders children directly
```
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Backend -- Add transport_type/url to McpServer model, update API and executor</name>
  <files>
    backend/app/models/mcp_server.py,
    backend/alembic/versions/0008_add_mcp_transport_type_and_url.py,
    backend/app/api/v1/settings/mcp_servers.py,
    backend/app/services/executors/mcp_executor.py,
    backend/app/tests/test_mcp_server_api.py
  </files>
  <action>
    **1. Update McpServer model** (`backend/app/models/mcp_server.py`):
    - Add `transport_type: str = Field(default="stdio", max_length=20)` -- values: "stdio", "sse", "streamable_http"
    - Add `url: str | None = Field(default=None, max_length=500)` -- required for sse and streamable_http transports
    - Make `command` nullable: `command: str | None = Field(default=None, max_length=500)` -- required for stdio only

    **2. Create Alembic migration**:
    - Run `cd backend && alembic revision --autogenerate -m "add_mcp_transport_type_and_url"` (or create manually)
    - Add columns: `transport_type` (VARCHAR(20), default "stdio", NOT NULL), `url` (VARCHAR(500), nullable)
    - Make `command` nullable (batch mode for SQLite: create new table, copy data, drop old, rename)
    - Use `render_as_batch=True` pattern per project convention
    - Run `alembic upgrade head`

    **3. Update API schemas** (`backend/app/api/v1/settings/mcp_servers.py`):
    - Add to McpServerCreate: `transport_type: str = "stdio"`, `url: str | None = None`
    - Add to McpServerUpdate: `transport_type: str | None = None`, `url: str | None = None`
    - Add to McpServerRead: `transport_type: str`, `url: str | None`
    - Add validation in create endpoint: if transport_type is "sse" or "streamable_http", `url` is required (raise 422 if missing). If transport_type is "stdio", `command` is required (raise 422 if missing).
    - Update `_to_read` helper to include new fields

    **4. Update McpExecutor** (`backend/app/services/executors/mcp_executor.py`):
    - Import `from mcp.client.sse import sse_client` and `from mcp.client.streamable_http import streamablehttp_client`
    - In `execute()`: branch on `self.server.transport_type`:
      - "stdio": existing StdioServerParameters + stdio_client logic (unchanged)
      - "sse": use `sse_client(url=self.server.url)` context manager, then `ClientSession(read, write)`, then `session.initialize()`, then `session.call_tool()`
      - "streamable_http": use `streamablehttp_client(url=self.server.url)` context manager, same session pattern
    - In `discover_and_register_mcp_tools()`: same branching for tool discovery (list_tools). Extract a helper `_connect_session(server, timeout)` async context manager that yields a `ClientSession` regardless of transport type, to avoid duplicating the branch logic.

    **5. Update tests** (`backend/app/tests/test_mcp_server_api.py`):
    - Update existing create test to pass `transport_type: "stdio"` explicitly
    - Add test: create SSE server (transport_type="sse", url="http://localhost:8080/sse", no command) returns 201
    - Add test: create SSE server without url returns 422
    - Add test: create stdio server without command returns 422
    - Add test: read server includes transport_type and url fields
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/backend && python -m pytest app/tests/test_mcp_server_api.py -x -v && python -m pytest app/tests/test_mcp_executor.py -x -v && ruff check app/ && python -m mypy app/ --ignore-missing-imports</automated>
  </verify>
  <done>McpServer model supports stdio/sse/streamable_http transport types. API validates transport-specific required fields. McpExecutor uses correct MCP SDK client per transport type. All tests pass.</done>
</task>

<task type="auto">
  <name>Task 2: Frontend -- Update MCP form for transport types + add global navigation header</name>
  <files>
    frontend/src/lib/mcp-api.ts,
    frontend/src/components/settings/mcp-server-form.tsx,
    frontend/src/components/settings/mcp-server-card.tsx,
    frontend/src/components/layout/app-header.tsx,
    frontend/src/app/(protected)/layout.tsx,
    frontend/src/app/(protected)/chat/layout.tsx,
    frontend/src/__tests__/mcp-servers.test.tsx
  </files>
  <action>
    **1. Update MCP API types** (`frontend/src/lib/mcp-api.ts`):
    - Add `transport_type: "stdio" | "sse" | "streamable_http"` to McpServerRead
    - Add `url: string | null` to McpServerRead
    - Add `transport_type?: "stdio" | "sse" | "streamable_http"` to McpServerCreate and McpServerUpdate
    - Add `url?: string | null` to McpServerCreate and McpServerUpdate

    **2. Update McpServerForm** (`frontend/src/components/settings/mcp-server-form.tsx`):
    - Add transport type selector: three buttons or a select with options "Local (stdio)", "SSE", "Streamable HTTP"
    - Use a simple set of three buttons styled as a segmented control (use existing Button + cn for active state), or a native select -- keep it simple
    - Default to "stdio"
    - When transport_type is "stdio": show command + args fields (existing), hide url field
    - When transport_type is "sse" or "streamable_http": show url field (Input with placeholder "http://localhost:8080/sse"), hide command + args fields
    - Env vars field always visible (all transports may use headers/env)
    - Update validate(): for stdio require command, for sse/streamable_http require url
    - Update handleSubmit(): include transport_type and url (or null) in submitted data

    **3. Update McpServerCard** (`frontend/src/components/settings/mcp-server-card.tsx`):
    - Show transport type badge next to the enabled/disabled badge (e.g., "stdio" / "SSE" / "HTTP")
    - For sse/streamable_http: show URL in monospace text instead of command preview
    - For stdio: show command preview as before

    **4. Create AppHeader** (`frontend/src/components/layout/app-header.tsx`):
    - Create a compact header component with:
      - App name "Forge" on the left (link to /chat)
      - Navigation links in the center or right: "Chat" and "Settings" using Next.js Link
      - Active state: highlight the current route using `usePathname()` from next/navigation
      - Logout button on the far right using `useAuth().logout`
    - Style: `h-12 border-b bg-background flex items-center px-4 gap-4` with Tailwind
    - Use lucide icons: `MessageSquare` for Chat, `Settings` for Settings, `LogOut` for logout
    - IMPORTANT: Read `node_modules/next/dist/docs/` for any Link or usePathname changes in this Next.js version before coding

    **5. Wire AppHeader into protected layout** (`frontend/src/app/(protected)/layout.tsx`):
    - Import and render AppHeader above {children}
    - Wrap in a flex column: `<div className="flex h-screen flex-col"><AppHeader /><div className="flex-1 overflow-hidden">{children}</div></div>`

    **6. Adjust chat layout** (`frontend/src/app/(protected)/chat/layout.tsx`):
    - Change `h-screen` to `h-full` since the parent protected layout now controls the full height
    - The chat layout's `<div className="flex h-screen overflow-hidden">` becomes `<div className="flex h-full overflow-hidden">`

    **7. Update tests** (`frontend/src/__tests__/mcp-servers.test.tsx`):
    - Update mock server data to include `transport_type: "stdio"` and `url: null`
    - Add test: form shows URL field when transport type is sse
    - Add test: server card shows transport type badge
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/frontend && npx tsc --noEmit && npm run lint && npm test</automated>
  </verify>
  <done>MCP form supports all three transport types with conditional field visibility. Server cards show transport type. Global navigation header with Chat/Settings links and logout button renders on all protected pages. Chat layout fills remaining height below header. All frontend tests pass.</done>
</task>

</tasks>

<verification>
1. Backend: `cd backend && python -m pytest -x -v` -- all tests pass including new transport type tests
2. Frontend: `cd frontend && npx tsc --noEmit && npm run lint && npm test` -- zero errors, all tests pass
3. Manual spot check: Start both servers, navigate between Chat and Settings via header links
</verification>

<success_criteria>
- McpServer model supports three transport types (stdio, sse, streamable_http) with appropriate field validation
- MCP tool discovery and execution uses the correct MCP SDK client per transport type
- Frontend MCP form shows/hides fields based on selected transport type
- Global navigation header allows moving between Chat and Settings without URL editing
- All backend and frontend tests pass with zero errors
</success_criteria>

<output>
After completion, create `.planning/quick/260322-cka-full-mcp-support-studio-local-sse-and-na/260322-cka-SUMMARY.md`
</output>
