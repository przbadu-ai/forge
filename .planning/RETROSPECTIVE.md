# Retrospective

## Milestone: v1.0 — MVP

**Shipped:** 2026-03-22
**Phases:** 11 | **Plans:** 23 | **Commits:** 130

### What Was Built
- Full-stack AI assistant with streaming chat, execution traces, MCP integration, skills, file upload with RAG, and comprehensive settings
- 76 Python files (~7,800 LOC) + 78 TypeScript files (~7,500 LOC)
- 172 backend tests + 74 frontend tests + 3 Playwright E2E specs
- CI pipeline with lint, type-check, unit tests, E2E, and build

### What Worked
- Phase-based development kept scope focused and dependencies clear
- Pre-built code discovery saved massive effort in later phases (phases 10 and 11 were ~90-95% done)
- Split stack (FastAPI + Next.js) kept concerns separated cleanly
- SQLite WAL mode eliminated database lock issues under async
- Execution trace as JSON blob per message was the right simplicity tradeoff

### What Was Inefficient
- Phases 7 and 8 (Orchestration + MCP) had test failures that persisted as tech debt through to the end
- Several phases were completed before the verification system existed, creating tracking gaps
- Requirement checkbox sync fell behind — 8 requirements were unchecked despite being fully implemented
- Skill tool schemas not wired to Orchestrator — discovered only during integration audit

### Patterns Established
- EphemeralClient for ChromaDB in single-process dev
- pwdlib[bcrypt] as passlib replacement for modern Python
- Router-level Depends(get_current_user) for auth on all endpoints
- Fernet encryption for API keys with SHA-256 key derivation
- TraceEmitter dataclass pattern for structured event emission
- BaseExecutor as Protocol for structural typing

### Key Lessons
- Scout existing code BEFORE planning — phases 10-11 were mostly done and would have been over-planned without scouting
- Verification system should be established from phase 1, not added later
- Requirements tracking needs to be updated atomically with code changes
- Integration testing between phases (skills → orchestrator → LLM) catches wiring gaps that unit tests miss

### Cost Observations
- 11 phases completed in ~2 days of development
- Autonomous mode executed phases 10-11 end-to-end with minimal user intervention
- Gap-closing plans (source persistence, reranker wiring, CI E2E) were efficient single-plan phases

## Cross-Milestone Trends

| Metric | v1.0 |
|--------|------|
| Phases | 11 |
| Plans | 23 |
| Duration | 2 days |
| LOC | ~15,300 |
| Test count | 246+ |
| Tech debt items | 8 |
