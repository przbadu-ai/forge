---
status: awaiting_human_verify
trigger: "Fix streaming to be true token-by-token streaming"
created: 2026-03-22T00:00:00Z
updated: 2026-03-22T00:00:00Z
---

## Current Focus

hypothesis: CONFIRMED - Backend called create() without stream=True
test: Fix applied, awaiting human verification
expecting: Tokens appear progressively in UI
next_action: User verifies streaming behavior in browser

## Symptoms

expected: Tokens should appear one-by-one in the UI as they're generated (like ChatGPT)
actual: 10 second delay, then entire response appears at once
errors: None - it "works" but isn't actually streaming
reproduction: Send any message, e.g. "Say 'double bubble bath' ten times fast."
started: Has always been like this - backend was built with non-streaming LLM calls

## Eliminated

## Evidence

- timestamp: 2026-03-22
  checked: orchestrator.py _llm_call_with_retry method
  found: Line 80 calls client.chat.completions.create(**kwargs) without stream=True. Response is awaited in full, then line 243 yields entire content as single token SSE event.
  implication: This is the root cause - no streaming occurs at LLM level.

- timestamp: 2026-03-22
  checked: chat.py _token_generator and useChat.ts frontend
  found: Frontend SSE consumer already handles incremental "token" events correctly (accumulates delta, calls setStreamingContent). No frontend changes needed.
  implication: Fix is backend-only.

## Resolution

root_cause: Orchestrator._llm_call_with_retry called client.chat.completions.create() without stream=True. The entire LLM response was generated server-side before being sent as a single SSE "token" event containing the full text.
fix: Changed to stream=True. Iterate over async stream chunks, yielding each delta.content as a separate SSE "token" event. Tool call deltas are accumulated from the stream and dispatched after stream completes. Frontend already handles incremental token events.
verification: Syntax check passed, ruff linter passed. Awaiting human verification of streaming behavior.
files_changed: [backend/app/services/orchestrator.py]
