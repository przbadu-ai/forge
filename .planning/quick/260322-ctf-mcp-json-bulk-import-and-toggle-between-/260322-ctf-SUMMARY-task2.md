---
phase: quick
plan: 260322-ctf
task: 2
title: "Frontend JSON editor and view toggle"
status: complete
completed: "2026-03-22"
duration: "2min"
key-files:
  created:
    - frontend/src/components/settings/mcp-json-editor.tsx
  modified:
    - frontend/src/lib/mcp-api.ts
    - frontend/src/components/settings/mcp-servers-section.tsx
decisions:
  - "Reused existing textarea styling from mcp-server-form.tsx for consistency"
  - "Form/JSON segmented toggle matches transport type toggle pattern (bg-primary active state)"
  - "Success message auto-clears after 2s and switches back to form view"
---

# Task 2: Frontend JSON editor and view toggle

**One-liner:** MCP JSON bulk import UI with form/JSON segmented toggle and McpJsonEditor component for pasting Cursor/Claude Desktop configs.

## What Was Done

### 1. mcp-api.ts -- Import API function

Added `McpBulkImportResponse` interface and `importMcpServers()` function that POSTs to `/api/v1/settings/mcp-servers/import` with the Cursor/Claude Desktop mcp.json format.

### 2. mcp-json-editor.tsx -- New component

Created `McpJsonEditor` component with:
- Monospace textarea (min-height 300px) with example JSON placeholder showing the mcpServers format
- Client-side JSON validation before API call (checks parse and mcpServers key)
- Error display (destructive styling) for parse errors and API failures
- Success display showing "Created N, Updated M servers" count
- Import Servers button with loading spinner
- Auto-clears textarea and calls `onImportSuccess` after 2s on success

### 3. mcp-servers-section.tsx -- View toggle

- Added `viewMode` state ("form" | "json") defaulting to "form"
- Added Form/JSON segmented toggle in header using `Code2` and `FormInput` icons from lucide-react
- Toggle styling matches existing transport type toggle pattern (`bg-primary text-primary-foreground` active, `hover:bg-muted text-muted-foreground` inactive)
- Form view: existing behavior (Add button, server cards, add form)
- JSON view: renders McpJsonEditor; on successful import, invalidates query cache and switches back to form view

## Verification

- TypeScript compiles without errors (`npx tsc --noEmit` clean)
- All three files created/modified as specified in plan

## Deviations from Plan

None -- all frontend changes were already committed by the Task 1 agent as part of commit `5344b0e`. This task verified the implementation matches the plan specification exactly (my edits produced identical output to what was committed).

## Commits

| Commit | Description |
|--------|-------------|
| 5344b0e | Frontend files committed as part of Task 1 docs commit (mcp-json-editor.tsx, mcp-servers-section.tsx, mcp-api.ts) |

## Self-Check: PASSED

- [x] `frontend/src/components/settings/mcp-json-editor.tsx` exists
- [x] `frontend/src/lib/mcp-api.ts` contains `importMcpServers`
- [x] `frontend/src/components/settings/mcp-servers-section.tsx` contains `viewMode` toggle
- [x] TypeScript compiles clean
- [x] Commit `5344b0e` exists with all frontend changes
