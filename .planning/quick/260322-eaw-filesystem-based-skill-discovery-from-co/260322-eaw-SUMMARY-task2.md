---
phase: quick
plan: 260322-eaw
task: 2
subsystem: frontend
tags: [skills, crud, ui, settings]
key-files:
  created: []
  modified:
    - frontend/src/lib/skills-api.ts
    - frontend/src/components/settings/skills-section.tsx
    - frontend/src/components/settings/GeneralSection.tsx
    - frontend/src/types/chat.ts
    - frontend/src/__tests__/skills.test.tsx
    - frontend/src/__tests__/general-section.test.tsx
decisions:
  - "Inline add-skill form with name and description inputs (not a modal)"
  - "Delete confirmation uses inline Confirm/Cancel buttons per row"
  - "Sync message auto-dismisses after 4 seconds"
  - "Skill directories input lives in GeneralSection as textarea (one path per line)"
metrics:
  duration: "2min"
  completed: "2026-03-22T04:39:39Z"
---

# Task 2: Frontend -- Skill Directories Config, Scan Button, and CRUD UI

Skill CRUD UI with Add/Delete/Sync buttons and skill directories configuration in General settings.

## What Was Done

### skills-api.ts
- Added `source_path` and `instructions` fields to `SkillRead` interface
- Added `SkillCreate`, `SkillUpdate`, `SyncResult` interfaces
- Added `createSkill()`, `updateSkill()`, `deleteSkill()`, `syncSkills()` API functions

### skills-section.tsx
- Reworked `SkillRow` to include delete button with two-step confirmation
- Added source_path display for filesystem-discovered skills
- Added "Add Skill" button that reveals inline form (name + description inputs)
- Added "Scan Directories" button that calls POST /sync endpoint
- Added sync result message with auto-dismiss after 4 seconds
- Updated empty state text to mention scan directories option
- All mutations invalidate the `["skills"]` query key for cache refresh

### GeneralSection.tsx
- Added `skillDirectories` state (string, newline-separated paths)
- Added textarea field labeled "Skill Directories" with helper text
- On save, splits textarea by newlines, trims, filters empty, passes as `skill_directories` array

### chat.ts (types)
- Added `skill_directories: string[]` to `GeneralSettings` interface

### Test updates
- Updated `SAMPLE_SKILLS` in skills.test.tsx with `source_path: null, instructions: null`
- Added mock exports for `createSkill`, `deleteSkill`, `syncSkills` in skills test
- Added `skill_directories: []` to general-section test mocks

## Verification

- TypeScript compiles without errors (`npx tsc --noEmit` passes cleanly)

## Deviations from Plan

None -- plan executed as written. The Task 1 agent had already committed both backend and frontend files in a single commit (81bd096), so no separate frontend commit was needed.

## Commit

Commit `81bd096` contains all Task 2 frontend changes (combined with Task 1 backend changes by the parallel agent).
