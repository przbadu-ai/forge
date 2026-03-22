---
phase: quick
plan: 260322-ctf
tags: [mcp, bulk-import, json-editor, ui]
key-files:
  created:
    - frontend/src/components/settings/mcp-json-editor.tsx
  modified:
    - backend/app/api/v1/settings/mcp_servers.py
    - frontend/src/lib/mcp-api.ts
    - frontend/src/components/settings/mcp-servers-section.tsx
metrics:
  duration: 3min
  completed: "2026-03-22T03:35:00Z"
  tasks: 2
  files: 4
---

# Quick Task 260322-ctf: MCP JSON Bulk Import + Form/JSON Toggle

Users can paste their Cursor/Claude Desktop mcp.json and bulk import all MCP servers. Settings page has a Form/JSON toggle for choosing input method.

## Task 1: Backend -- Bulk Import Endpoint

- Added `POST /api/v1/settings/mcp-servers/import` accepting `{"mcpServers": {...}}` format
- Upsert-by-name: existing servers updated, new ones created
- Transport type inferred from fields (url present = sse, otherwise stdio)
- Single transaction with rollback on validation failure (422 with server name)
- Returns created/updated counts + full server list

## Task 2: Frontend -- JSON Editor + Toggle

- **McpJsonEditor** component: monospace textarea with placeholder example, client-side JSON validation, success/error display
- **Form/JSON toggle** in MCP settings header using segmented buttons (Code2/FormInput icons)
- Success auto-clears after 2s, invalidates query cache, switches back to form view

## Commits

| Commit | Description |
|--------|-------------|
| 4951141 | feat(260322-ctf): add bulk import endpoint for MCP servers |
| 5344b0e | Frontend files + docs |
| dd5bd7f | docs(260322-ctf): task 2 summary |
