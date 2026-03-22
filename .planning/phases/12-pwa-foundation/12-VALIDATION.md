---
phase: 12
slug: pwa-foundation
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-03-22
updated: 2026-03-22
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
| 12-00-01 | 00 | 0 | PWA-01,02,04 | scaffold | `test -f src/__tests__/manifest.test.ts` | Plan 00 creates | pending |
| 12-00-02 | 00 | 0 | PWA-02 | scaffold | `test -f tests/pwa.spec.ts` | Plan 00 creates | pending |
| 12-01-01 | 01 | 1 | PWA-01 | unit | `npx vitest run src/__tests__/manifest.test.ts` | Created in 12-00 | pending |
| 12-01-2a | 01 | 1 | PWA-02,05 | unit | `npx vitest run --reporter=verbose` | Created in 12-00 | pending |
| 12-01-2b | 01 | 1 | PWA-02,03 | unit | `npx vitest run src/__tests__/sw-registration.test.tsx` | Created in 12-00 | pending |
| 12-02-01 | 02 | 2 | PWA-04 | unit+E2E | `npx vitest run src/__tests__/offline-page.test.tsx` | Created in 12-00 | pending |
| 12-02-02 | 02 | 2 | PWA-02,05 | E2E | `npx playwright test tests/pwa.spec.ts` | Created in 12-00 | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [x] `src/__tests__/manifest.test.ts` — test manifest.ts returns valid PWA manifest (Plan 12-00, Task 1)
- [x] `src/__tests__/sw-registration.test.tsx` — test SW registration component renders (Plan 12-00, Task 1)
- [x] `src/__tests__/offline-page.test.tsx` — test offline page renders with retry button (Plan 12-00, Task 1)
- [x] `tests/pwa.spec.ts` — Playwright E2E for manifest, SW, API bypass, offline page (Plan 12-00, Task 2)

*All Wave 0 test files are created by Plan 12-00 before implementation begins.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Browser install prompt appears | PWA-01 | Requires real browser install UI | Open in Chrome, verify install icon in address bar |
| SSE streaming works with SW | PWA-02 | Requires live LLM endpoint | Send chat message, verify streaming tokens arrive without buffering |
| Offline fallback displays | PWA-04 | Requires network disconnect | Disable network in DevTools, navigate to app |
| Lighthouse PWA audit passes | PWA-01 | Requires Lighthouse runner | Run Lighthouse in Chrome DevTools, verify PWA category |

NOTE: SSE bypass also has an automated E2E test (`tests/pwa.spec.ts` - "SW uses NetworkOnly for /api/* routes") that verifies the compiled SW source contains the API bypass pattern. The manual check above tests end-to-end with a real LLM call.

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved (revision 2026-03-22)
