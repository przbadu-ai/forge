# Phase 11: Settings Completion + Quality Gate - Context

**Gathered:** 2026-03-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Complete all remaining settings (web search providers), ensure health diagnostics cover all integrations, and establish quality gates: all backend tests pass (pytest), all frontend tests pass (vitest), E2E tests pass (Playwright), and CI pipeline runs all checks green.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion
All implementation choices are at Claude's discretion — infrastructure/quality phase. Most functionality is already implemented:

- Web search settings (SearXNG + Exa): backend API, frontend UI, encryption, tests all exist
- Health diagnostics: 6-service concurrent checks with latency, frontend panel exists
- Backend tests: 27 test files (~3,541 lines)
- Frontend tests: 14 vitest test files
- E2E: Playwright configured, 3 spec files (auth, settings, conversation)
- CI: GitHub Actions with lint + type-check + unit tests for both stacks

Primary gap: Playwright E2E tests not yet in CI pipeline.

</decisions>

<canonical_refs>
## Canonical References

No external specs — requirements fully captured in decisions above and REQUIREMENTS.md (SET-04, SET-06, TEST-01, TEST-02, TEST-03).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- backend/app/api/v1/settings/web_search.py — complete web search settings API
- backend/app/api/v1/health_diagnostics.py — 6-service health check with concurrent checks
- frontend/src/components/settings/web-search-section.tsx — full web search UI
- frontend/src/components/settings/health-diagnostics.tsx — diagnostics panel UI
- .github/workflows/ci.yml — existing CI pipeline (backend + frontend quality + tests + build)
- Makefile — comprehensive targets for dev, test, lint, type-check, build

### Established Patterns
- Vitest + Testing Library for frontend component tests
- pytest + httpx + pytest-asyncio for backend tests
- Playwright for E2E with webServer config

### Integration Points
- CI pipeline needs Playwright E2E job added
- All test suites need to pass without failures

</code_context>

<specifics>
## Specific Ideas

No specific requirements — infrastructure phase.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 11-settings-quality-gate*
*Context gathered: 2026-03-22*
