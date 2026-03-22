# Requirements: Forge

**Defined:** 2026-03-22
**Core Value:** Every AI interaction -- chat, tool call, MCP action, skill execution -- is visible, persisted, and reviewable.

## v2.1 Requirements

Requirements for PWA milestone. Each maps to roadmap phases.

### PWA Foundation

- [ ] **PWA-01**: App serves a valid web app manifest with name, icons, theme color, display: standalone, and start_url
- [ ] **PWA-02**: Service worker registers on app load with Serwist, caches app shell assets, and bypasses /api/* routes (preserving SSE streaming)
- [ ] **PWA-03**: App provides PWA icons (192x192, 512x512 PNG) and Apple touch icon
- [ ] **PWA-04**: Offline fallback page displays when user has no network connection
- [ ] **PWA-05**: Docker standalone build includes service worker and manifest in output

### Install UX

- [ ] **INST-01**: User sees a custom install prompt banner on Chrome/Edge (via beforeinstallprompt)
- [ ] **INST-02**: iOS/Safari users see manual "Add to Home Screen" instructions
- [ ] **INST-03**: User sees a visual offline indicator (banner) when network is unavailable
- [ ] **INST-04**: User is notified when a new app version is available and can refresh to update

### Responsive Layout

- [ ] **RESP-01**: Mobile screens (<768px) show bottom navigation bar instead of sidebar
- [ ] **RESP-02**: Tablet/iPad screens (768px+) show the existing sidebar layout
- [ ] **RESP-03**: Chat messages, input area, and markdown rendering adapt to mobile widths
- [ ] **RESP-04**: Settings pages use stacked layout on mobile screens
- [ ] **RESP-05**: Touch targets meet 44px minimum, spacing is mobile-friendly throughout

## Future Requirements

### Push Notifications

- **NOTF-01**: User receives push notification when LLM response completes (background)
- **NOTF-02**: User can configure push notification preferences

### Offline Data

- **OFFL-01**: Conversation list cached in IndexedDB for offline browsing
- **OFFL-02**: Pending messages queued offline and sent when reconnected

## Out of Scope

| Feature | Reason |
|---------|--------|
| Full offline chat | LLM calls require live backend -- offline chat is impossible |
| Push notifications | Single-user self-hosted tool -- user is always present |
| Background sync | Forge is not a messaging app; no queue needed |
| Native app (React Native/Capacitor) | PWA achieves installability without native complexity |
| OAuth/social login | Single-user tool, JWT sufficient |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| PWA-01 | Phase 12 | Pending |
| PWA-02 | Phase 12 | Pending |
| PWA-03 | Phase 12 | Pending |
| PWA-04 | Phase 12 | Pending |
| PWA-05 | Phase 12 | Pending |
| INST-01 | Phase 13 | Pending |
| INST-02 | Phase 13 | Pending |
| INST-03 | Phase 13 | Pending |
| INST-04 | Phase 13 | Pending |
| RESP-01 | Phase 14 | Pending |
| RESP-02 | Phase 14 | Pending |
| RESP-03 | Phase 14 | Pending |
| RESP-04 | Phase 14 | Pending |
| RESP-05 | Phase 14 | Pending |

**Coverage:**
- v2.1 requirements: 14 total
- Mapped to phases: 14
- Unmapped: 0

---
*Requirements defined: 2026-03-22*
*Last updated: 2026-03-22 after roadmap creation*
