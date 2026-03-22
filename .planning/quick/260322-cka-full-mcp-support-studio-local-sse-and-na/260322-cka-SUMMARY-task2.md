---
phase: quick
plan: 260322-cka
task: 2
subsystem: frontend
tags: [mcp, transport-types, navigation, ui]
key-files:
  created:
    - frontend/src/components/layout/app-header.tsx
  modified:
    - frontend/src/lib/mcp-api.ts
    - frontend/src/components/settings/mcp-server-form.tsx
    - frontend/src/components/settings/mcp-server-card.tsx
    - frontend/src/app/(protected)/layout.tsx
    - frontend/src/app/(protected)/chat/layout.tsx
    - frontend/src/__tests__/mcp-servers.test.tsx
decisions:
  - Segmented button group (role=radiogroup) for transport type selector instead of native select
  - AppHeader uses usePathname for active link highlighting with startsWith matching
  - Chat layout changed from h-screen to h-full since protected layout now owns viewport height
metrics:
  duration: 3min
  completed: "2026-03-22T03:24:12Z"
---

# Quick Task 260322-cka Task 2: Frontend -- MCP Transport Types + Navigation Header

MCP form supports stdio/SSE/streamable_http with conditional field visibility; global AppHeader with Chat/Settings navigation and logout.

## What Was Done

### 1. Updated MCP API types (mcp-api.ts)
- Added `McpTransportType` union type: "stdio" | "sse" | "streamable_http"
- Added `transport_type` and `url` fields to McpServerRead, McpServerCreate, McpServerUpdate
- Made `command` nullable (`string | null`) to support remote transports

### 2. Updated McpServerForm (mcp-server-form.tsx)
- Added segmented transport type selector with three buttons: Local (stdio), SSE, Streamable HTTP
- Conditional field visibility: stdio shows command+args, sse/streamable_http shows URL
- Updated validation: stdio requires command, remote transports require URL
- Submit data includes transport_type and conditionally nulls command/url

### 3. Updated McpServerCard (mcp-server-card.tsx)
- Added transport type badge (stdio/SSE/HTTP) next to enabled/disabled badge
- Remote transports display URL in monospace instead of command preview
- Handles nullable command field gracefully

### 4. Created AppHeader (app-header.tsx)
- Compact h-12 header with app name "Forge" linking to /chat
- Chat and Settings navigation links with lucide icons (MessageSquare, Settings)
- Active state highlighting using usePathname with startsWith matching
- Logout button on far right using useAuth().logout

### 5. Wired AppHeader into protected layout
- Protected layout now wraps children in flex column with AppHeader on top
- Content area uses flex-1 overflow-hidden for proper scrolling

### 6. Adjusted chat layout
- Changed h-screen to h-full since protected layout now controls viewport height

### 7. Updated tests
- Added transport_type and url fields to SAMPLE_SERVERS mock data
- Added test: transport type badge renders on server cards
- Added test: form shows URL field when SSE transport selected, hides command field

## Verification

- TypeScript: `npx tsc --noEmit` -- zero errors
- Lint: `npm run lint` -- zero errors (3 pre-existing warnings in unrelated files)
- Tests: `npm test` -- 15 test files, 82 tests passed

## Deviations from Plan

None - plan executed exactly as written.

## Commits

| Commit | Description |
|--------|-------------|
| d171e4c | feat(260322-cka): add transport type support to MCP form and global navigation header |
