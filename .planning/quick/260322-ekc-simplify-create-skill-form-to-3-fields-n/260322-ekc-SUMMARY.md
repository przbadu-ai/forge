---
plan: 260322-ekc
status: complete
---

# Quick Task 260322-ekc: Simplify create skill form

## One-liner
Replaced inline add-skill form with a modal dialog containing three labeled fields (name, description, instructions) matching the design mockup

## What changed
- **`frontend/src/lib/skills-api.ts`**: Added `content?: string` to `SkillCreate` and `SkillUpdate` interfaces
- **`frontend/src/components/settings/skills-section.tsx`**: Replaced inline form with `Dialog` modal containing:
  - "Write skill instructions" title with close button
  - Skill name (text input)
  - Description (multi-line textarea)
  - Instructions (large multi-line textarea, maps to `content` on backend)
  - Cancel + Create action buttons in dialog footer
- **`frontend/src/components/ui/dialog.tsx`**: Added shadcn dialog component (base-ui primitives)
- **`frontend/src/components/ui/textarea.tsx`**: Added shadcn textarea component

## Verification
- Frontend build passes with zero errors
- All 82 tests pass (15 test files)
- No backend changes needed — `content` field already existed in SkillCreate schema

## Commit
f78d599
