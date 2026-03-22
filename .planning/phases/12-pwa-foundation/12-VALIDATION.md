---
phase: 12
slug: pwa-foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-22
---

# Phase 12 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Vitest 4.x (frontend), Playwright (E2E) |
| **Config file** | `frontend/vitest.config.ts`, `frontend/playwright.config.ts` |
| **Quick run command** | `cd frontend && npx vitest run --reporter=verbose` |
| **Full suite command** | `cd frontend && npx vitest run && npx playwright test` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd frontend && npx vitest run --reporter=verbose`
- **After every plan wave:** Run `cd frontend && npx vitest run && npx playwright test`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 12-01-01 | 01 | 1 | PWA-01 | unit | `npx vitest run --reporter=verbose` | ❌ W0 | ⬜ pending |
| 12-01-02 | 01 | 1 | PWA-02 | unit | `npx vitest run --reporter=verbose` | ❌ W0 | ⬜ pending |
| 12-01-03 | 01 | 1 | PWA-03 | unit | `npx vitest run --reporter=verbose` | ❌ W0 | ⬜ pending |
| 12-02-01 | 02 | 2 | PWA-04 | E2E | `npx playwright test` | ❌ W0 | ⬜ pending |
| 12-02-02 | 02 | 2 | PWA-05 | E2E | `npx playwright test` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `src/__tests__/manifest.test.ts` — test manifest.ts returns valid PWA manifest
- [ ] `src/__tests__/sw-registration.test.tsx` — test SW registration component renders
- [ ] `src/__tests__/offline-page.test.tsx` — test offline page renders with retry button

*Existing Vitest + Playwright infrastructure covers framework needs.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Browser install prompt appears | PWA-01 | Requires real browser install UI | Open in Chrome, verify install icon in address bar |
| SSE streaming works with SW | PWA-02 | Requires live LLM endpoint | Send chat message, verify streaming tokens arrive without buffering |
| Offline fallback displays | PWA-04 | Requires network disconnect | Disable network in DevTools, navigate to app |
| Lighthouse PWA audit passes | PWA-01 | Requires Lighthouse runner | Run Lighthouse in Chrome DevTools, verify PWA category |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
