---
phase: quick
plan: 260322-ctf
type: execute
wave: 1
depends_on: []
files_modified:
  - backend/app/api/v1/settings/mcp_servers.py
  - frontend/src/lib/mcp-api.ts
  - frontend/src/components/settings/mcp-servers-section.tsx
  - frontend/src/components/settings/mcp-json-editor.tsx
autonomous: true
requirements: [MCP-BULK-IMPORT, MCP-JSON-VIEW-TOGGLE]
must_haves:
  truths:
    - "User can paste a full mcp.json (Cursor/Claude Desktop format) and all servers are created in DB"
    - "User can toggle between Form view and JSON editor view on MCP settings page"
    - "Existing servers that match by name are updated (upsert), new ones are created"
    - "Import reports how many servers were created vs updated"
  artifacts:
    - path: "backend/app/api/v1/settings/mcp_servers.py"
      provides: "POST /import bulk endpoint"
      contains: "import_mcp_servers"
    - path: "frontend/src/components/settings/mcp-json-editor.tsx"
      provides: "JSON editor component with textarea and save button"
    - path: "frontend/src/lib/mcp-api.ts"
      provides: "importMcpServers API function"
      contains: "importMcpServers"
  key_links:
    - from: "frontend/src/components/settings/mcp-json-editor.tsx"
      to: "/api/v1/settings/mcp-servers/import"
      via: "importMcpServers in mcp-api.ts"
      pattern: "mcp-servers/import"
    - from: "frontend/src/components/settings/mcp-servers-section.tsx"
      to: "mcp-json-editor.tsx"
      via: "viewMode state toggle"
      pattern: "viewMode|McpJsonEditor"
---

<objective>
Add MCP JSON bulk import: a backend endpoint that accepts Cursor/Claude Desktop mcp.json format and creates/updates all servers, plus a frontend toggle between Form view and JSON editor view on the MCP settings page.

Purpose: Users with existing mcp.json configs can import all servers at once instead of adding them one by one.
Output: Working bulk import endpoint + JSON editor UI with form/JSON toggle.
</objective>

<execution_context>
@/Users/przbadu/.claude/get-shit-done/workflows/execute-plan.md
@/Users/przbadu/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@backend/app/api/v1/settings/mcp_servers.py
@frontend/src/lib/mcp-api.ts
@frontend/src/components/settings/mcp-servers-section.tsx
@frontend/src/components/settings/mcp-server-form.tsx
@frontend/src/components/settings/mcp-server-card.tsx

<interfaces>
<!-- Backend MCP server schemas and helpers already exist -->

From backend/app/api/v1/settings/mcp_servers.py:
```python
class McpServerCreate(BaseModel):
    name: str
    transport_type: str = "stdio"
    command: str | None = None
    url: str | None = None
    args: list[str] = []
    env_vars: dict[str, str] = {}
    is_enabled: bool = True

class McpServerRead(BaseModel):
    id: int
    name: str
    transport_type: str
    command: str | None
    url: str | None
    args: list[str]
    env_vars: dict[str, str]
    is_enabled: bool
    created_at: datetime
    updated_at: datetime

def _validate_transport_fields(transport_type, command, url) -> None: ...
def _to_read(server: McpServer) -> McpServerRead: ...
```

From frontend/src/lib/mcp-api.ts:
```typescript
export interface McpServerRead { id: number; name: string; command: string | null; args: string[]; env_vars: Record<string, string>; is_enabled: boolean; transport_type: McpTransportType; url: string | null; created_at: string; }
export interface McpServerCreate { name: string; command?: string | null; args?: string[]; env_vars?: Record<string, string>; is_enabled?: boolean; transport_type?: McpTransportType; url?: string | null; }
export async function listMcpServers(token: string): Promise<McpServerRead[]>
export async function createMcpServer(token: string, data: McpServerCreate): Promise<McpServerRead>
```

From frontend/src/components/settings/mcp-servers-section.tsx:
```typescript
// Uses useQuery with queryKey ["mcp-servers"], useAuth() for token
// Renders McpServerCard list + McpServerForm for adding
// Has showAddForm state toggle
```
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Backend bulk import endpoint</name>
  <files>backend/app/api/v1/settings/mcp_servers.py</files>
  <action>
Add a POST /import endpoint to the existing mcp_servers router. This endpoint accepts the Cursor/Claude Desktop mcp.json format and upserts all servers.

1. Add a new Pydantic schema `McpBulkImportRequest` with field `mcpServers: dict[str, McpServerEntry]` where `McpServerEntry` has: `command: str | None = None`, `args: list[str] = []`, `env: dict[str, str] = {}`, `url: str | None = None`. Note: the JSON format uses `env` not `env_vars`.

2. Add a response schema `McpBulkImportResponse` with fields: `created: int`, `updated: int`, `servers: list[McpServerRead]`.

3. Add endpoint `@router.post("/import", response_model=McpBulkImportResponse)` that:
   - Iterates over each key-value pair in mcpServers
   - The dict key is the server name
   - Determines transport_type: if entry has `url` field set, use "sse"; otherwise "stdio"
   - For each server, check if a McpServer with that name already exists (SELECT by name)
   - If exists: update its command, args (json.dumps), env_vars (json.dumps from entry.env), url, transport_type, updated_at
   - If not exists: create new McpServer with is_enabled=True
   - Validate transport fields using existing `_validate_transport_fields`
   - Commit all changes in a single transaction
   - Return count of created/updated and the full list of imported servers

4. Handle errors: if any server fails validation, rollback and return 422 with detail indicating which server name failed.
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone && curl -s -X POST http://localhost:8000/api/v1/settings/mcp-servers/import -H "Content-Type: application/json" -H "Authorization: Bearer TEST" -d '{"mcpServers":{"test-server":{"command":"echo","args":["hello"]}}}' | python3 -m json.tool || echo "Verify endpoint exists by checking route registration: grep -n 'import' backend/app/api/v1/settings/mcp_servers.py"</automated>
  </verify>
  <done>POST /api/v1/settings/mcp-servers/import accepts mcp.json format, upserts servers, returns created/updated counts. Existing servers matched by name are updated, new ones created.</done>
</task>

<task type="auto">
  <name>Task 2: Frontend JSON editor and view toggle</name>
  <files>frontend/src/lib/mcp-api.ts, frontend/src/components/settings/mcp-json-editor.tsx, frontend/src/components/settings/mcp-servers-section.tsx</files>
  <action>
1. **mcp-api.ts** - Add import API function and response type:
   ```typescript
   export interface McpBulkImportResponse {
     created: number;
     updated: number;
     servers: McpServerRead[];
   }

   export async function importMcpServers(
     token: string,
     data: { mcpServers: Record<string, { command?: string; args?: string[]; env?: Record<string, string>; url?: string }> }
   ): Promise<McpBulkImportResponse> {
     const res = await apiFetch("/api/v1/settings/mcp-servers/import", token, {
       method: "POST",
       body: JSON.stringify(data),
     });
     return handleResponse<McpBulkImportResponse>(res);
   }
   ```

2. **mcp-json-editor.tsx** - Create new component:
   - Accept props: `onImportSuccess: () => void` (to trigger query invalidation)
   - State: `jsonText` (string, initialized with example template showing the mcpServers format), `error` (string | null), `result` (McpBulkImportResponse | null), `isImporting` (boolean)
   - Render a Card with CardHeader "Import from JSON" and CardContent containing:
     - A `<textarea>` with monospace font (font-mono), min-height 300px, full width, styled with the same textarea classes used in mcp-server-form.tsx
     - Placeholder text showing the example JSON format from the description
     - Error display (text-destructive) if parsing or import fails
     - Success display showing "Created N, Updated M servers" after successful import
     - A "Import Servers" Button that:
       a. Tries JSON.parse on the textarea value
       b. Validates that parsed object has `mcpServers` key and it's an object
       c. Calls importMcpServers with the parsed data
       d. On success: shows result, calls onImportSuccess, clears textarea after 2s
       e. On error: shows error message
   - Use useAuth() for the token

3. **mcp-servers-section.tsx** - Add view toggle:
   - Add state: `viewMode: "form" | "json"` defaulting to "form"
   - In the header area (next to "Add MCP Server" button), add a segmented toggle (two buttons styled like the transport type toggle in mcp-server-form.tsx) with options "Form" and "JSON"
   - Use cn() for active/inactive styling, matching the existing transport toggle pattern: active gets `bg-primary text-primary-foreground`, inactive gets `hover:bg-muted text-muted-foreground`
   - When viewMode is "form": show existing UI (showAddForm toggle, McpServerCard list) -- current behavior
   - When viewMode is "json": show McpJsonEditor component instead of the form/card list. Pass `onImportSuccess` that calls `queryClient.invalidateQueries({ queryKey: ["mcp-servers"] })` and switches viewMode back to "form"
   - Import McpJsonEditor and the new view toggle icons (Code2 and FormInput from lucide-react) for the toggle buttons
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/frontend && npx tsc --noEmit 2>&1 | head -20</automated>
  </verify>
  <done>MCP settings page has a Form/JSON toggle. JSON view shows a textarea where users paste mcp.json content and click Import. Successful import creates/updates servers and switches back to form view showing the imported servers.</done>
</task>

</tasks>

<verification>
1. Backend: POST /api/v1/settings/mcp-servers/import accepts `{"mcpServers": {"name": {"command": "...", "args": [...]}}}` and returns `{"created": N, "updated": M, "servers": [...]}`
2. Frontend: MCP settings page shows Form/JSON toggle buttons in the header
3. JSON view: textarea with placeholder example, Import button, error/success feedback
4. After successful import, view switches to Form showing all imported servers as cards
5. TypeScript compiles without errors
</verification>

<success_criteria>
- Pasting a valid mcp.json with 2+ servers creates all of them in the database
- Re-importing the same JSON updates existing servers (matched by name) rather than creating duplicates
- The Form/JSON toggle works and preserves state correctly
- Invalid JSON shows a clear error message in the UI
</success_criteria>

<output>
After completion, create `.planning/quick/260322-ctf-mcp-json-bulk-import-and-toggle-between-/260322-ctf-SUMMARY.md`
</output>
