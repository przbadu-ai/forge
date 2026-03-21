---
phase: 03-llm-provider-settings
plans:
  - id: "03-01"
    wave: 1
    type: execute
    autonomous: true
    depends_on: []
    files_modified:
      - backend/app/models/llm_provider.py
      - backend/app/models/__init__.py
      - backend/app/core/encryption.py
      - backend/app/api/v1/settings/__init__.py
      - backend/app/api/v1/settings/providers.py
      - backend/app/api/v1/router.py
      - backend/pyproject.toml
      - alembic/versions/0003_add_llm_provider_table.py
    requirements: [SET-01, SET-05]
  - id: "03-02"
    wave: 2
    type: execute
    autonomous: false
    depends_on: ["03-01"]
    files_modified:
      - frontend/package.json
      - frontend/src/app/layout.tsx
      - frontend/src/app/settings/page.tsx
      - frontend/src/app/settings/layout.tsx
      - frontend/src/components/settings/providers-section.tsx
      - frontend/src/components/settings/provider-form.tsx
      - frontend/src/components/settings/provider-card.tsx
      - frontend/src/components/settings/theme-switcher.tsx
      - frontend/src/components/ui/card.tsx
      - frontend/src/components/ui/input.tsx
      - frontend/src/components/ui/label.tsx
      - frontend/src/components/ui/switch.tsx
      - frontend/src/components/ui/tabs.tsx
      - frontend/src/components/ui/badge.tsx
      - frontend/src/lib/providers-api.ts
    requirements: [SET-01, SET-05, UX-01]
  - id: "03-03"
    wave: 3
    type: execute
    autonomous: true
    depends_on: ["03-01", "03-02"]
    files_modified:
      - backend/app/tests/test_settings_providers.py
      - frontend/src/app/settings/__tests__/providers.test.tsx
      - frontend/src/app/settings/__tests__/theme-switcher.test.tsx
    requirements: [SET-01, SET-05, UX-01]

must_haves:
  truths:
    - "User can add an LLM provider with name, base URL, API key, and model names"
    - "User can update and delete an existing provider"
    - "User can click Test Connection and receive success (latency + model count) or error within seconds"
    - "One provider can be marked as default"
    - "API keys are stored encrypted at rest and never returned in plain text via API"
    - "User can switch Light / Dark / System theme and preference survives page refresh"
    - "Configured providers survive server restart (persisted in SQLite)"
  artifacts:
    - path: "backend/app/models/llm_provider.py"
      provides: "LLMProvider SQLModel table with encrypted api_key"
      contains: "class LLMProvider"
    - path: "backend/app/core/encryption.py"
      provides: "Fernet encrypt/decrypt helpers keyed to SECRET_KEY"
      exports: ["encrypt_value", "decrypt_value"]
    - path: "backend/app/api/v1/settings/providers.py"
      provides: "CRUD + test-connection router"
      exports: ["router"]
    - path: "frontend/src/app/settings/page.tsx"
      provides: "Settings page with Providers tab and Theme section"
    - path: "frontend/src/lib/providers-api.ts"
      provides: "Typed API client for provider CRUD + test-connection"
      exports: ["listProviders", "createProvider", "updateProvider", "deleteProvider", "testConnection"]
  key_links:
    - from: "backend/app/api/v1/settings/providers.py"
      to: "backend/app/core/encryption.py"
      via: "encrypt_value on write, decrypt_value omitted on read (api_key never returned)"
      pattern: "encrypt_value\\(.*api_key\\)"
    - from: "backend/app/api/v1/router.py"
      to: "backend/app/api/v1/settings/providers.py"
      via: "include_router with /settings/providers prefix"
      pattern: "settings_router"
    - from: "frontend/src/app/settings/page.tsx"
      to: "frontend/src/lib/providers-api.ts"
      via: "React Query useQuery/useMutation hooks"
      pattern: "useQuery.*listProviders|useMutation.*createProvider"
    - from: "frontend/src/app/layout.tsx"
      to: "next-themes ThemeProvider"
      via: "ThemeProvider wrapping body"
      pattern: "ThemeProvider"
---

<!-- ============================================================
     PLAN 03-01  (Wave 1)  Settings Backend
     ============================================================ -->

# Plan 03-01: Settings Backend

<objective>
Build the LLM provider data layer and API: SQLModel, Alembic migration, Fernet encryption
helper, and CRUD + test-connection FastAPI endpoints — all protected by get_current_user.

Purpose: Phase 4 (streaming chat) queries the default LLM provider; this plan makes that
data available and manageable.

Output: Working /api/v1/settings/providers endpoints, encrypted api_key storage, migration.
</objective>

<execution_context>
@/Users/przbadu/.claude/get-shit-done/workflows/execute-plan.md
@/Users/przbadu/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md

<interfaces>
<!-- Existing contracts the executor must build against. -->

From backend/app/core/config.py:
```python
class Settings(BaseSettings):
    secret_key: str = "change-me-in-production-32-chars-min"
    database_url: str = "sqlite+aiosqlite:///./forge.db"
```

From backend/app/core/database.py:
```python
AsyncSessionFactory: async_sessionmaker[AsyncSession]
async def get_session() -> AsyncGenerator[AsyncSession, None]: ...
```

From backend/app/api/v1/deps.py:
```python
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_session),
) -> User: ...
```

From backend/app/api/v1/router.py:
```python
api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
```

From backend/app/models/user.py:
```python
class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True, max_length=50)
    hashed_password: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=_utcnow)
```
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: LLMProvider model, encryption helper, and Alembic migration</name>
  <files>
    backend/app/models/llm_provider.py
    backend/app/models/__init__.py
    backend/app/core/encryption.py
    backend/pyproject.toml
    alembic/versions/0003_add_llm_provider_table.py
  </files>
  <behavior>
    - encrypt_value("secret") returns a non-empty string that is NOT "secret"
    - decrypt_value(encrypt_value("secret")) == "secret"
    - encrypt_value with the same input produces different ciphertext each call (Fernet uses random IV)
    - LLMProvider table columns: id (int PK), name (str unique), base_url (str), api_key_encrypted (str), models (str, JSON list serialized as text), is_default (bool default False), created_at (datetime)
    - Migration upgrades cleanly with `alembic upgrade head` and downgrades with `alembic downgrade -1`
  </behavior>
  <action>
    1. Add `cryptography>=43.0.0` to backend/pyproject.toml dependencies (run `uv add cryptography`).

    2. Create backend/app/core/encryption.py:
       - Derive a 32-byte URL-safe base64 key from settings.secret_key using SHA-256 then base64url-encode it to produce a valid Fernet key.
       - Provide `encrypt_value(plain: str) -> str` and `decrypt_value(cipher: str) -> str`.
       - Use `from cryptography.fernet import Fernet`.
       - Key derivation: `import hashlib, base64; raw = hashlib.sha256(settings.secret_key.encode()).digest(); fernet_key = base64.urlsafe_b64encode(raw)`.
       - Do NOT store the key in the module; derive it on each call from settings.

    3. Create backend/app/models/llm_provider.py:
       ```python
       class LLMProvider(SQLModel, table=True):
           id: int | None = Field(default=None, primary_key=True)
           name: str = Field(unique=True, index=True, max_length=100)
           base_url: str = Field(max_length=500)
           api_key_encrypted: str = Field(default="")  # Fernet ciphertext or ""
           models: str = Field(default="[]")            # JSON array as text e.g. '["gpt-4","gpt-3.5"]'
           is_default: bool = Field(default=False)
           created_at: datetime = Field(default_factory=_utcnow)
       ```
       - models is stored as a plain JSON string; serialize/deserialize in the API layer (not in the model).
       - api_key is NEVER stored in plain text.

    4. Update backend/app/models/__init__.py to export LLMProvider.

    5. Generate migration: run `cd backend && alembic revision --autogenerate -m "add_llm_provider_table"` then rename the output file to `0003_add_llm_provider_table.py`. Verify the migration uses `batch_alter_table` pattern consistent with existing migrations.

    6. Write tests in backend/app/tests/test_encryption.py (created here for TDD):
       - test_encrypt_decrypt_roundtrip
       - test_encrypt_produces_different_ciphertext_each_call
       - test_decrypt_invalid_raises
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/backend && uv run pytest app/tests/test_encryption.py -x -q && uv run alembic upgrade head && uv run alembic downgrade -1 && uv run alembic upgrade head</automated>
  </verify>
  <done>
    - Fernet encrypt/decrypt roundtrip tests pass
    - `alembic upgrade head` succeeds with llm_provider table created
    - `alembic downgrade -1` removes the table cleanly
    - LLMProvider importable from app.models
  </done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Provider CRUD endpoints and test-connection endpoint</name>
  <files>
    backend/app/api/v1/settings/__init__.py
    backend/app/api/v1/settings/providers.py
    backend/app/api/v1/router.py
  </files>
  <behavior>
    - GET /api/v1/settings/providers returns list of providers; api_key field is absent (never serialized out)
    - POST /api/v1/settings/providers with valid payload creates provider, returns 201 with provider object (no api_key)
    - POST with duplicate name returns 409
    - PUT /api/v1/settings/providers/{id} updates fields; omitted api_key field leaves existing encrypted value unchanged
    - DELETE /api/v1/settings/providers/{id} removes provider, returns 204
    - Setting is_default=true on a provider clears is_default on all others (only one default at a time)
    - POST /api/v1/settings/providers/test-connection with {base_url, api_key} calls the provider's GET /v1/models using AsyncOpenAI; returns {ok: true, latency_ms: int, model_count: int} on success or {ok: false, error: str} on failure
    - All endpoints require valid Bearer token (401 without)
  </behavior>
  <action>
    1. Create backend/app/api/v1/settings/__init__.py (empty).

    2. Create backend/app/api/v1/settings/providers.py with a FastAPI APIRouter:

       Schemas (define at top of file, do NOT use separate schema file for this plan):
       ```python
       class ProviderCreate(BaseModel):
           name: str
           base_url: str
           api_key: str = ""        # plain text on input; encrypted before storage
           models: list[str] = []
           is_default: bool = False

       class ProviderUpdate(BaseModel):
           name: str | None = None
           base_url: str | None = None
           api_key: str | None = None   # None means "don't change"
           models: list[str] | None = None
           is_default: bool | None = None

       class ProviderRead(BaseModel):
           id: int
           name: str
           base_url: str
           models: list[str]
           is_default: bool
           created_at: datetime
           # api_key intentionally absent

       class TestConnectionRequest(BaseModel):
           base_url: str
           api_key: str = ""

       class TestConnectionResponse(BaseModel):
           ok: bool
           latency_ms: int | None = None
           model_count: int | None = None
           error: str | None = None
       ```

       Endpoints:
       - `GET /` — select all LLMProvider rows, deserialize models JSON, return list[ProviderRead]
       - `POST /` — encrypt api_key with encrypt_value, handle is_default logic (UPDATE others to False if new provider is_default=True using a separate UPDATE statement), insert, return 201
       - `PUT /{provider_id}` — fetch or 404, patch fields, only re-encrypt api_key if api_key is not None in payload, handle is_default if changed, commit
       - `DELETE /{provider_id}` — fetch or 404, delete, return 204
       - `POST /test-connection` — create AsyncOpenAI(base_url=req.base_url, api_key=req.api_key or "ollama"), call `await client.models.list()` inside `asyncio.wait_for(..., timeout=10)`, measure latency with time.perf_counter(), return TestConnectionResponse. Catch any exception → return ok=False with error message.

       Use `Depends(get_current_user)` on the router (not per-endpoint) so all routes are protected.
       Use `Depends(get_session)` per endpoint.

    3. Update backend/app/api/v1/router.py:
       - Import and include the settings providers router:
         ```python
         from app.api.v1.settings.providers import router as providers_router
         api_router.include_router(providers_router, prefix="/settings/providers", tags=["settings"])
         ```

    4. Add `openai>=2.29.0` to backend/pyproject.toml if not already present (run `uv add openai`).
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/backend && uv run pytest app/tests/test_settings_providers.py -x -q 2>/dev/null || echo "Test file created in 03-03; verify router loads" && uv run python -c "from app.api.v1.settings.providers import router; print('router OK')"</automated>
  </verify>
  <done>
    - Router imports without error
    - All CRUD and test-connection routes are registered under /api/v1/settings/providers
    - api_key never appears in ProviderRead response
    - is_default logic enforces single default
    - test-connection uses openai AsyncOpenAI client with 10s timeout
  </done>
</task>

</tasks>

<verification>
```bash
cd /Users/przbadu/dev/claude-clone/backend
uv run alembic upgrade head
uv run python -c "from app.models.llm_provider import LLMProvider; from app.core.encryption import encrypt_value, decrypt_value; print('models OK')"
uv run python -c "from app.api.v1.router import api_router; routes = [r.path for r in api_router.routes]; assert any('settings/providers' in r for r in routes), routes; print('router OK')"
uv run pytest app/tests/test_encryption.py -x -q
```
</verification>

<success_criteria>
- LLMProvider table exists in SQLite after `alembic upgrade head`
- Fernet encryption roundtrip tests pass
- All five endpoints (GET, POST, PUT, DELETE providers; POST test-connection) registered
- openai added to dependencies
- api_key stored encrypted, never returned
</success_criteria>

<output>
After completion, create `.planning/phases/03-llm-provider-settings/03-01-SUMMARY.md`
</output>

---

<!-- ============================================================
     PLAN 03-02  (Wave 2)  Settings Frontend
     ============================================================ -->

# Plan 03-02: Settings Frontend

<objective>
Build the Settings page shell with a Providers section (list, add, edit, delete, test-connection)
and a Theme section (Light/Dark/System switcher via next-themes). The page uses tab/section
navigation so future phases can add MCP, Skills, and Embedding sections without restructuring.

Purpose: Users need to configure at least one LLM provider before Phase 4 (streaming chat) is
useful. Theme support also lands here (UX-01).

Output: /settings route, provider CRUD UI, test-connection UI, theme switcher.
</objective>

<execution_context>
@/Users/przbadu/.claude/get-shit-done/workflows/execute-plan.md
@/Users/przbadu/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/phases/03-llm-provider-settings/03-01-SUMMARY.md

<interfaces>
<!-- Contracts the executor must build against. -->

From frontend/src/lib/api.ts:
```typescript
export async function apiFetch(
  path: string,
  token: string,
  options: RequestInit = {}
): Promise<Response>
```

From frontend/src/context/auth-context.tsx:
```typescript
export function useAuth(): {
  token: string | null;
  user: UserResponse | null;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}
```

Backend API contracts (from 03-01):
```
GET    /api/v1/settings/providers         -> ProviderRead[]
POST   /api/v1/settings/providers         -> ProviderRead (201)
PUT    /api/v1/settings/providers/{id}    -> ProviderRead
DELETE /api/v1/settings/providers/{id}    -> 204
POST   /api/v1/settings/providers/test-connection
  body: { base_url: string, api_key: string }
  -> { ok: boolean, latency_ms?: number, model_count?: number, error?: string }

ProviderRead shape:
{
  id: number
  name: string
  base_url: string
  models: string[]
  is_default: boolean
  created_at: string
}
```

NOTE: Read frontend/AGENTS.md before writing any Next.js code. Check
`node_modules/next/dist/docs/` for current API patterns if uncertain.
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Install dependencies, shadcn components, ThemeProvider wiring</name>
  <files>
    frontend/package.json
    frontend/src/app/layout.tsx
    frontend/src/components/ui/card.tsx
    frontend/src/components/ui/input.tsx
    frontend/src/components/ui/label.tsx
    frontend/src/components/ui/switch.tsx
    frontend/src/components/ui/tabs.tsx
    frontend/src/components/ui/badge.tsx
  </files>
  <action>
    1. Install next-themes and @tanstack/react-query:
       ```bash
       cd /Users/przbadu/dev/claude-clone/frontend
       npm install next-themes @tanstack/react-query
       ```

    2. Add missing shadcn/ui components using the shadcn CLI (components are copy-pasted, not installed as npm packages):
       ```bash
       npx shadcn@latest add card input label switch tabs badge
       ```
       This writes component files into frontend/src/components/ui/. Do not hand-write these.

    3. Update frontend/src/app/layout.tsx:
       - Import ThemeProvider from next-themes and QueryClient/QueryClientProvider from @tanstack/react-query.
       - Create a client component `Providers` in `frontend/src/components/providers.tsx` that wraps children with:
         1. `<ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>`
         2. `<QueryClientProvider client={queryClient}>`
         3. `<AuthProvider>`
       - Use `"use client"` directive on the Providers component.
       - Root layout renders `<html suppressHydrationWarning>` (required by next-themes to prevent flash).
       - Replace current AuthProvider wrapping in layout.tsx with the new Providers component.

    NOTE: Read `node_modules/next/dist/docs/` for current App Router layout patterns before implementing.
    The `attribute="class"` prop tells next-themes to add `class="dark"` to `<html>`, which Tailwind's `dark:` variant reads.
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/frontend && npm run build 2>&1 | tail -5</automated>
  </verify>
  <done>
    - `npm run build` exits 0
    - next-themes and @tanstack/react-query in package.json
    - ThemeProvider wraps the app in layout.tsx
    - shadcn card, input, label, switch, tabs, badge components exist in src/components/ui/
  </done>
</task>

<task type="auto">
  <name>Task 2: API client, Settings page, Provider section, and Theme switcher</name>
  <files>
    frontend/src/lib/providers-api.ts
    frontend/src/app/settings/page.tsx
    frontend/src/app/settings/layout.tsx
    frontend/src/components/settings/providers-section.tsx
    frontend/src/components/settings/provider-form.tsx
    frontend/src/components/settings/provider-card.tsx
    frontend/src/components/settings/theme-switcher.tsx
  </files>
  <action>
    1. Create frontend/src/lib/providers-api.ts:
       ```typescript
       export interface ProviderRead {
         id: number
         name: string
         base_url: string
         models: string[]
         is_default: boolean
         created_at: string
       }
       export interface ProviderCreate {
         name: string
         base_url: string
         api_key?: string
         models: string[]
         is_default?: boolean
       }
       export interface TestConnectionResult {
         ok: boolean
         latency_ms?: number
         model_count?: number
         error?: string
       }
       export async function listProviders(token: string): Promise<ProviderRead[]>
       export async function createProvider(token: string, data: ProviderCreate): Promise<ProviderRead>
       export async function updateProvider(token: string, id: number, data: Partial<ProviderCreate>): Promise<ProviderRead>
       export async function deleteProvider(token: string, id: number): Promise<void>
       export async function testConnection(token: string, base_url: string, api_key: string): Promise<TestConnectionResult>
       ```
       All functions use apiFetch from @/lib/api. Throw on non-2xx responses (parse JSON error detail).

    2. Create frontend/src/app/settings/layout.tsx:
       - A simple layout that renders a page header ("Settings") and `{children}`.
       - This shell will gain a sidebar nav in later phases.

    3. Create frontend/src/app/settings/page.tsx:
       - `"use client"` directive.
       - Uses Tabs component (shadcn) with two tabs: "LLM Providers" and "Appearance".
       - "LLM Providers" tab renders `<ProvidersSection />`.
       - "Appearance" tab renders `<ThemeSwitcher />`.
       - Redirect to /login if token is null (use useAuth and useRouter).

    4. Create frontend/src/components/settings/theme-switcher.tsx:
       - `"use client"` directive.
       - Uses `useTheme` from next-themes.
       - Renders three buttons or a segmented control: "Light", "Dark", "System".
       - Active theme is highlighted.
       - Calls `setTheme("light" | "dark" | "system")` on click.
       - Uses shadcn Button variants for styling.

    5. Create frontend/src/components/settings/provider-card.tsx:
       - Displays a single ProviderRead as a shadcn Card.
       - Shows: name, base_url, model count badge, "Default" badge if is_default.
       - Action buttons: "Edit" (opens form), "Delete" (with confirm), "Test" (calls testConnection inline).
       - Test button shows loading spinner during call, then renders success (latency + model count) or error in a small status area below the card.
       - On delete: calls deleteProvider, then invalidates the providers query.
       - Edit opens a pre-filled provider-form dialog (use a simple controlled state toggle, not a route).

    6. Create frontend/src/components/settings/provider-form.tsx:
       - A form (shadcn Input, Label, Button) for creating or editing a provider.
       - Fields: Name, Base URL, API Key (password input, placeholder "Leave blank to keep existing"), Models (comma-separated string, split on save), Is Default (Switch).
       - On submit: calls createProvider or updateProvider, invalidates the providers query, closes form.
       - Inline validation: name and base_url required; show error text under field if empty on submit.
       - API key field: when editing, placeholder says "Leave blank to keep existing". Only sends api_key in payload if user types something.

    7. Create frontend/src/components/settings/providers-section.tsx:
       - `"use client"` directive.
       - Uses @tanstack/react-query `useQuery` with queryKey `["providers"]` to load providers.
       - Shows "Add Provider" button that toggles an inline provider-form for creation.
       - Renders a list of ProviderCard components.
       - Shows empty state ("No providers yet. Add one to start chatting.") when list is empty.
       - Uses `useMutation` + `queryClient.invalidateQueries` for create/update/delete.
       - Token from useAuth passed to all API functions.

    NOTE: All components are `"use client"`. Avoid server components for settings — they need auth token from context.
    Use lucide-react icons (Pencil, Trash2, Wifi, Check, X, Loader2) for action buttons.
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/frontend && npm run build 2>&1 | tail -10 && npm run lint 2>&1 | tail -5</automated>
  </verify>
  <done>
    - `npm run build` and `npm run lint` pass with zero errors
    - /settings route exists with LLM Providers and Appearance tabs
    - Provider form supports create and edit with validation
    - Test Connection button calls backend and shows result
    - Theme switcher calls setTheme and persists via next-themes localStorage
  </done>
</task>

<task type="checkpoint:human-verify" gate="blocking">
  <what-built>
    Settings page at /settings with:
    - LLM Providers tab: add/edit/delete providers, test-connection button
    - Appearance tab: Light/Dark/System theme switcher
    Backend endpoints: full CRUD + test-connection under /api/v1/settings/providers
  </what-built>
  <how-to-verify>
    1. Start backend: `cd backend && uv run uvicorn app.main:app --reload --port 8000`
    2. Start frontend: `cd frontend && npm run dev`
    3. Log in at http://localhost:3000/login
    4. Navigate to http://localhost:3000/settings
    5. Verify two tabs appear: "LLM Providers" and "Appearance"
    6. In LLM Providers tab: click "Add Provider", fill in a name (e.g. "Ollama"), base URL (http://localhost:11434/v1), leave API key blank, add model "llama3.2"
    7. Click Save — provider card should appear
    8. Click "Test" on the provider card — should show success (if Ollama running) or a clear error message (if not)
    9. Click Edit, change the name, save — card updates
    10. In Appearance tab: click Dark — page goes dark. Refresh — dark mode persists.
    11. Switch to System — theme matches OS preference.
    12. Click Delete on the provider — card disappears after confirm
  </how-to-verify>
  <resume-signal>Type "approved" or describe issues found</resume-signal>
</task>

</tasks>

<verification>
```bash
cd /Users/przbadu/dev/claude-clone/frontend
npm run build
npm run lint
npm run format:check
```
</verification>

<success_criteria>
- /settings page renders with Tabs
- Provider CRUD flow works end-to-end via the UI
- Test Connection returns a result from the backend
- Theme changes and persists across refresh
- Build and lint pass with zero errors
</success_criteria>

<output>
After completion, create `.planning/phases/03-llm-provider-settings/03-02-SUMMARY.md`
</output>

---

<!-- ============================================================
     PLAN 03-03  (Wave 3)  Settings Tests
     ============================================================ -->

# Plan 03-03: Settings Tests

<objective>
Write backend integration tests for provider CRUD + test-connection, and frontend component
tests for the providers section and theme switcher. Ensures Phase 3 features are regression-safe
before Phase 4 builds on top.

Purpose: Mandatory test coverage per project constraints; also validates that 03-01 and 03-02
behave correctly under edge cases.

Output: pytest test file for providers API, Vitest tests for providers section and theme switcher.
</objective>

<execution_context>
@/Users/przbadu/.claude/get-shit-done/workflows/execute-plan.md
@/Users/przbadu/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/phases/03-llm-provider-settings/03-01-SUMMARY.md
@.planning/phases/03-llm-provider-settings/03-02-SUMMARY.md

<interfaces>
<!-- What tests must cover. -->

Backend endpoints (from 03-01):
```
GET    /api/v1/settings/providers         bearer required
POST   /api/v1/settings/providers         body: ProviderCreate
PUT    /api/v1/settings/providers/{id}    body: ProviderUpdate
DELETE /api/v1/settings/providers/{id}    204
POST   /api/v1/settings/providers/test-connection  body: {base_url, api_key}
```

Frontend components (from 03-02):
```
ProvidersSection — renders provider list via useQuery, shows empty state
ProviderForm     — validates required fields, calls create/update API
ProviderCard     — shows provider data, delete with confirm, test-connection
ThemeSwitcher    — calls setTheme on button click
```
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Backend provider API integration tests</name>
  <files>
    backend/app/tests/test_settings_providers.py
  </files>
  <behavior>
    - Unauthenticated GET /settings/providers returns 401
    - POST creates a provider with encrypted api_key stored (verify by fetching from DB directly)
    - GET list returns providers without api_key field
    - POST with duplicate name returns 409
    - PUT updates fields; omitting api_key leaves encryption unchanged
    - DELETE removes the provider, returns 204
    - Setting is_default=true clears previous default
    - POST /test-connection with unreachable URL returns {ok: false, error: ...} (not a 500)
    - POST /test-connection with missing URL field returns 422
  </behavior>
  <action>
    Create backend/app/tests/test_settings_providers.py following the existing test pattern
    (AsyncClient + ASGITransport, async fixtures, pytest-asyncio auto mode).

    Test setup:
    - Use a test database (in-memory SQLite or temp file) — follow the pattern from existing auth tests.
    - Create a test user and obtain a bearer token via the /auth/login endpoint before each test or in a session fixture.
    - Use AsyncClient(transport=ASGITransport(app=app), base_url="http://test") for all requests.

    Test cases:
    1. test_list_providers_requires_auth — GET without token → 401
    2. test_create_provider — POST with valid payload → 201, response has no api_key field, id returned
    3. test_create_provider_duplicate_name — POST same name twice → 409 on second call
    4. test_list_providers_returns_created — after create, GET returns list with the provider
    5. test_update_provider — PUT with new name → 200, name updated
    6. test_update_provider_api_key_blank_preserves_encryption — PUT without api_key field → encrypted value in DB unchanged
    7. test_delete_provider — DELETE → 204, subsequent GET list excludes it
    8. test_is_default_exclusive — create two providers with second is_default=True → first is_default becomes False
    9. test_test_connection_unreachable — POST /test-connection {base_url: "http://localhost:9999/v1", api_key: ""} → 200 with ok=false and error string (not 500)
    10. test_test_connection_missing_base_url — POST /test-connection {} → 422

    Import LLMProvider model and encryption helpers directly in test to verify DB state:
    ```python
    from app.models.llm_provider import LLMProvider
    from app.core.encryption import decrypt_value
    ```
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/backend && uv run pytest app/tests/test_settings_providers.py -x -q</automated>
  </verify>
  <done>
    All 10 test cases pass. No auth bypass, no api_key leak, no 500 on unreachable provider.
  </done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Frontend component tests for providers section and theme switcher</name>
  <files>
    frontend/src/app/settings/__tests__/providers.test.tsx
    frontend/src/app/settings/__tests__/theme-switcher.test.tsx
  </files>
  <behavior>
    ProvidersSection:
    - Renders "No providers yet" empty state when API returns []
    - Renders a list of provider cards when API returns providers
    - "Add Provider" button shows the provider form
    - Submitting the form with valid data calls createProvider API function
    - Submitting with empty name shows inline validation error
    - Delete confirm calls deleteProvider API function

    ThemeSwitcher:
    - Renders three buttons: Light, Dark, System
    - Clicking "Dark" calls setTheme("dark")
    - Clicking "System" calls setTheme("system")
    - Active theme button has aria-pressed or a visual distinction
  </behavior>
  <action>
    Use Vitest + @testing-library/react + @testing-library/user-event.
    Mock API functions with vi.mock("@/lib/providers-api").
    Mock next-themes useTheme with vi.mock("next-themes").
    Mock useAuth context to return a fake token.
    Mock @tanstack/react-query at module level to provide a real QueryClient for render wrapping.

    frontend/src/app/settings/__tests__/providers.test.tsx:
    - test("shows empty state when no providers", ...)
    - test("renders provider cards when providers exist", ...)
    - test("shows add form on button click", ...)
    - test("calls createProvider on valid form submit", ...)
    - test("shows name required error on empty submit", ...)

    frontend/src/app/settings/__tests__/theme-switcher.test.tsx:
    - test("renders Light Dark System buttons", ...)
    - test("calls setTheme dark on Dark button click", ...)
    - test("calls setTheme system on System button click", ...)

    Each test file begins with `/// <reference types="vitest/globals" />` or uses import from vitest.
    Wrap renders in a helper that provides QueryClientProvider + mocked AuthContext.
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/frontend && npm test 2>&1 | tail -20</automated>
  </verify>
  <done>
    All Vitest tests pass. `npm test` exits 0. No "act" warnings.
  </done>
</task>

</tasks>

<verification>
```bash
# Backend
cd /Users/przbadu/dev/claude-clone/backend
uv run pytest app/tests/ -x -q

# Frontend
cd /Users/przbadu/dev/claude-clone/frontend
npm test
npm run build
```
</verification>

<success_criteria>
- Backend: 10 provider API tests pass including auth, CRUD, encryption, is_default exclusivity, test-connection failure path
- Frontend: 8 component tests pass for ProvidersSection and ThemeSwitcher
- All prior tests still pass (no regression)
- `npm run build` exits 0 after test additions
</success_criteria>

<output>
After completion, create `.planning/phases/03-llm-provider-settings/03-03-SUMMARY.md`
</output>
