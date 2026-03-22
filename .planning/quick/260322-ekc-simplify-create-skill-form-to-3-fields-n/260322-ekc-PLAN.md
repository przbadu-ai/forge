---
phase: quick
plan: 260322-ekc
type: execute
wave: 1
depends_on: []
files_modified:
  - frontend/src/components/ui/dialog.tsx
  - frontend/src/components/ui/textarea.tsx
  - frontend/src/lib/skills-api.ts
  - frontend/src/components/settings/skills-section.tsx
autonomous: true
requirements: []
must_haves:
  truths:
    - "Clicking Add Skill opens a modal dialog titled 'Write skill instructions'"
    - "Dialog has three fields: Skill name (input), Description (textarea), Instructions (textarea)"
    - "Instructions field value is sent as `content` in the POST /api/v1/settings/skills/ payload"
    - "Cancel closes dialog without creating, Create submits and closes on success"
  artifacts:
    - path: "frontend/src/components/ui/dialog.tsx"
      provides: "Dialog primitive component from shadcn"
    - path: "frontend/src/components/ui/textarea.tsx"
      provides: "Textarea primitive component from shadcn"
    - path: "frontend/src/lib/skills-api.ts"
      provides: "SkillCreate with content field"
    - path: "frontend/src/components/settings/skills-section.tsx"
      provides: "Modal-based create skill form"
  key_links:
    - from: "skills-section.tsx"
      to: "skills-api.ts"
      via: "createSkill call with content field"
      pattern: "createSkill.*content"
---

<objective>
Replace the inline add-skill form with a modal dialog containing three fields: Skill name (text input), Description (textarea), and Instructions (textarea). The Instructions field maps to the `content` field on the backend SkillCreate schema.

Purpose: Match the design mockup -- clean modal with warm background, proper field labels, and Cancel/Create buttons.
Output: Working modal dialog for skill creation that sends all three fields to the API.
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-plan.md
@~/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@frontend/src/components/settings/skills-section.tsx
@frontend/src/lib/skills-api.ts
@frontend/components.json

NOTE: This project uses shadcn/ui v4 with base-ui primitives (style: "base-nova").
The backend SkillCreate schema already accepts `content: str | None = None`.
No backend changes are needed.
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add shadcn dialog and textarea components, update SkillCreate type</name>
  <files>frontend/src/components/ui/dialog.tsx, frontend/src/components/ui/textarea.tsx, frontend/src/lib/skills-api.ts</files>
  <action>
1. From the `frontend/` directory, run `npx shadcn@latest add dialog textarea` to install the shadcn dialog and textarea primitives. These use base-ui under the hood per the project's components.json config.

2. In `frontend/src/lib/skills-api.ts`, add `content?: string` to the `SkillCreate` interface (after `description`). This matches the backend `SkillCreate` schema which already has `content: str | None = None`. Also add `content?: string` to `SkillUpdate` for future use.
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/frontend && test -f src/components/ui/dialog.tsx && test -f src/components/ui/textarea.tsx && grep -q "content" src/lib/skills-api.ts && echo "PASS"</automated>
  </verify>
  <done>Dialog and Textarea UI components exist. SkillCreate and SkillUpdate interfaces include optional `content` field.</done>
</task>

<task type="auto">
  <name>Task 2: Replace inline form with modal dialog in skills-section</name>
  <files>frontend/src/components/settings/skills-section.tsx</files>
  <action>
Refactor `SkillsSection` in `frontend/src/components/settings/skills-section.tsx`:

1. **Import new components:** Add imports for `Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogClose` from `@/components/ui/dialog`, `Textarea` from `@/components/ui/textarea`, and `Label` from `@/components/ui/label`.

2. **Add state for instructions:** Add `const [newInstructions, setNewInstructions] = useState("")` alongside existing `newName` and `newDescription` state.

3. **Replace the inline form block** (the `{showAddForm && (...)}` section, lines ~214-264) with a `<Dialog open={showAddForm} onOpenChange={setShowAddForm}>` wrapping a `<DialogContent>`. The dialog should have:
   - `<DialogHeader>` with `<DialogTitle>Write skill instructions</DialogTitle>` and a close X button (DialogClose handles this automatically via shadcn).
   - A warm/cream-tinted background: add `className="sm:max-w-lg"` to DialogContent (keep it clean, not too wide).
   - Three labeled fields stacked vertically in a `<form>` with `onSubmit={handleCreate}`:
     - **Skill name**: `<Label htmlFor="skill-name">Skill name</Label>` + `<Input id="skill-name" ...>` bound to `newName`
     - **Description**: `<Label htmlFor="skill-desc">Description</Label>` + `<Textarea id="skill-desc" rows={3} ...>` bound to `newDescription`
     - **Instructions**: `<Label htmlFor="skill-instructions">Instructions</Label>` + `<Textarea id="skill-instructions" rows={6} placeholder="Enter detailed skill instructions..." ...>` bound to `newInstructions`
   - `<DialogFooter>` with Cancel (variant="outline") and Create (default variant) buttons. Cancel uses `<DialogClose asChild><Button variant="outline">Cancel</Button></DialogClose>`. Create is `type="submit"` with disabled state when `!newName.trim() || createMutation.isPending`.
   - Show error message below buttons if `createMutation.isError`.

4. **Update handleCreate** to include `content` in the mutation payload:
   ```
   createMutation.mutate({
     name: newName.trim(),
     description: newDescription.trim(),
     content: newInstructions.trim() || undefined,
   });
   ```

5. **Update createMutation onSuccess** to also reset `setNewInstructions("")`.

6. **Update the "Add Skill" button** to remain as-is (it already toggles `showAddForm`). The Dialog's `onOpenChange` will handle closing.

7. **Clean up**: Remove the old inline form JSX entirely. The `showAddForm` state now controls the Dialog's `open` prop.

IMPORTANT: Read the installed dialog.tsx and textarea.tsx files first to understand the exact export names and API (base-ui primitives may differ from standard shadcn). If DialogClose is not exported, use the `onOpenChange` callback approach instead.
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/frontend && npx next build 2>&1 | tail -5</automated>
  </verify>
  <done>Add Skill button opens a modal dialog with title "Write skill instructions", three labeled fields (Skill name, Description, Instructions), and Cancel/Create buttons. The `content` field is sent in the API call. Build passes with no errors.</done>
</task>

</tasks>

<verification>
- Click "Add Skill" on the Skills settings page -- modal dialog opens
- Dialog shows title "Write skill instructions" with close button
- Three fields visible: Skill name (input), Description (textarea), Instructions (textarea)
- Fill all fields, click Create -- skill appears in list, dialog closes
- Check browser DevTools Network tab: POST payload includes `content` field
- Click Cancel or X -- dialog closes without creating
- Empty name prevents submission (Create button disabled)
</verification>

<success_criteria>
- Modal dialog replaces inline form for skill creation
- All three fields (name, description, instructions/content) are sent to the API
- Dialog opens/closes cleanly with proper state reset
- Frontend builds without errors
</success_criteria>

<output>
After completion, create `.planning/quick/260322-ekc-simplify-create-skill-form-to-3-fields-n/260322-ekc-SUMMARY.md`
</output>
