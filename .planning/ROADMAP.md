# Roadmap: Forge

## Milestones

- ✅ **v1.0 MVP** -- Phases 1-11 (shipped 2026-03-22)
- 🚧 **v2.1 PWA** -- Phases 12-14 (in progress)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-11) -- SHIPPED 2026-03-22</summary>

- [x] Phase 1: Infrastructure Foundation (4 plans) -- completed 2026-03-21
- [x] Phase 2: Authentication (3 plans) -- completed 2026-03-21
- [x] Phase 3: LLM Provider Settings (2 plans) -- completed 2026-03-21
- [x] Phase 4: Core Streaming Chat (2 plans) -- completed 2026-03-21
- [x] Phase 5: Chat Completions (1 plan) -- completed 2026-03-22
- [x] Phase 6: Execution Trace System (3 plans) -- completed 2026-03-21
- [x] Phase 7: Orchestration Loop (2 plans) -- completed 2026-03-21
- [x] Phase 8: MCP Integration (2 plans) -- completed 2026-03-21
- [x] Phase 9: Skills Integration (1 plan) -- completed 2026-03-22
- [x] Phase 10: File Upload + RAG (1 plan) -- completed 2026-03-22
- [x] Phase 11: Settings Completion + Quality Gate (2 plans) -- completed 2026-03-22

Full details: `.planning/milestones/v1.0-ROADMAP.md`

</details>

### 🚧 v2.1 PWA (In Progress)

**Milestone Goal:** Make Forge a fully installable Progressive Web App with responsive UI, service worker, offline shell, and app manifest -- usable as a desktop and mobile app.

- [ ] **Phase 12: PWA Foundation** - Service worker, manifest, icons, offline fallback, and Docker build support
- [ ] **Phase 13: Install UX and Offline Experience** - Install prompt, iOS instructions, offline indicator, and update notifications
- [ ] **Phase 14: Responsive Layout** - Mobile navigation, tablet sidebar, chat/settings adaptation, and touch targets

## Phase Details

### Phase 12: PWA Foundation
**Goal**: Forge is a valid, installable PWA that passes Lighthouse PWA audit with cached app shell and graceful offline fallback
**Depends on**: Phase 11 (v1.0 complete)
**Requirements**: PWA-01, PWA-02, PWA-03, PWA-04, PWA-05
**Success Criteria** (what must be TRUE):
  1. Browser recognizes Forge as installable (Lighthouse PWA audit passes with no critical failures)
  2. App shell loads instantly from service worker cache on repeat visits (no network waterfall for static assets)
  3. SSE streaming for chat continues to work correctly with service worker registered (no buffering or corruption)
  4. User sees a branded offline fallback page (not browser error) when backend is unreachable
  5. Docker standalone build serves the service worker and manifest correctly (curl /sw.js returns 200)
**Plans**: 3 plans

Plans:
- [x] 12-00-PLAN.md -- Wave 0 test scaffolds (manifest, SW registration, offline page, E2E)
- [ ] 12-01-PLAN.md -- Serwist integration, manifest, icons, SW source, and config wiring
- [ ] 12-02-PLAN.md -- Offline fallback page and PWA browser verification

### Phase 13: Install UX and Offline Experience
**Goal**: Users can discover, install, and manage the Forge PWA with clear offline state communication and seamless update lifecycle
**Depends on**: Phase 12
**Requirements**: INST-01, INST-02, INST-03, INST-04
**Success Criteria** (what must be TRUE):
  1. Chrome/Edge users see a custom install banner prompting them to install Forge as an app
  2. iOS/Safari users see clear instructions for manually adding Forge to their home screen
  3. User sees a visible offline indicator banner when network connection is lost
  4. User is notified when a new version of Forge is available and can tap to refresh and get the update
**Plans**: TBD

Plans:
- [ ] 13-01: TBD

### Phase 14: Responsive Layout
**Goal**: Forge is fully usable on mobile and tablet devices with no horizontal scroll, proper navigation, and touch-friendly interactions
**Depends on**: Phase 12
**Requirements**: RESP-01, RESP-02, RESP-03, RESP-04, RESP-05
**Success Criteria** (what must be TRUE):
  1. On mobile screens (<768px), a bottom navigation bar replaces the sidebar for primary navigation
  2. On tablet screens (768px+), the existing sidebar layout renders correctly without changes
  3. Chat messages, input area, and markdown blocks adapt to narrow widths without horizontal scroll
  4. Settings pages stack vertically on mobile with no truncated or overlapping content
  5. All interactive elements (buttons, links, toggles) meet the 44px minimum touch target size
**Plans**: TBD

Plans:
- [ ] 14-01: TBD
- [ ] 14-02: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 12 -> 13 -> 14

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Infrastructure Foundation | v1.0 | 4/4 | Complete | 2026-03-21 |
| 2. Authentication | v1.0 | 3/3 | Complete | 2026-03-21 |
| 3. LLM Provider Settings | v1.0 | 2/2 | Complete | 2026-03-21 |
| 4. Core Streaming Chat | v1.0 | 2/2 | Complete | 2026-03-21 |
| 5. Chat Completions | v1.0 | 1/1 | Complete | 2026-03-22 |
| 6. Execution Trace System | v1.0 | 3/3 | Complete | 2026-03-21 |
| 7. Orchestration Loop | v1.0 | 2/2 | Complete | 2026-03-21 |
| 8. MCP Integration | v1.0 | 2/2 | Complete | 2026-03-21 |
| 9. Skills Integration | v1.0 | 1/1 | Complete | 2026-03-22 |
| 10. File Upload + RAG | v1.0 | 1/1 | Complete | 2026-03-22 |
| 11. Settings + Quality Gate | v1.0 | 2/2 | Complete | 2026-03-22 |
| 12. PWA Foundation | v2.1 | 1/3 | In Progress|  |
| 13. Install UX + Offline | v2.1 | 0/? | Not started | - |
| 14. Responsive Layout | v2.1 | 0/? | Not started | - |
