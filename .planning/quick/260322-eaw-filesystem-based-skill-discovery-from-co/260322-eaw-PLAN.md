---
phase: quick
plan: 260322-eaw
type: execute
wave: 1
depends_on: []
files_modified:
  - backend/app/models/settings.py
  - backend/alembic/versions/0011_add_skill_directories_to_settings.py
  - backend/app/api/v1/settings/general.py
  - backend/app/services/skill_discovery.py
  - backend/app/api/v1/settings/skills.py
  - backend/app/models/skill.py
  - frontend/src/lib/skills-api.ts
  - frontend/src/components/settings/skills-section.tsx
autonomous: true
requirements: []
must_haves:
  truths:
    - "User can configure skill directory paths in General settings"
    - "User can scan directories and discover skills from SKILL.md files"
    - "User can manually create, update, and delete skills"
    - "Discovered skills are upserted into the database"
  artifacts:
    - path: "backend/app/services/skill_discovery.py"
      provides: "Filesystem skill scanning service"
    - path: "backend/alembic/versions/0011_add_skill_directories_to_settings.py"
      provides: "Migration for skill_directories column"
  key_links:
    - from: "frontend skills-section.tsx"
      to: "POST /api/v1/settings/skills/sync"
      via: "syncSkills API call"
    - from: "backend skill_discovery.py"
      to: "filesystem SKILL.md files"
      via: "os.scandir + yaml frontmatter parsing"
---

<objective>
Add filesystem-based skill discovery: scan configured directories for SKILL.md files, sync discovered skills to DB, and provide full CRUD + sync UI for skills management.

Purpose: Allow users to define skills as filesystem directories (like Claude Code's .claude/skills/) and have them automatically discovered and synced.
Output: Backend discovery service + migration + API endpoints + frontend UI with scan/create/edit/delete.
</objective>

<execution_context>
@/Users/przbadu/.claude/get-shit-done/workflows/execute-plan.md
@/Users/przbadu/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@backend/app/models/settings.py
@backend/app/models/skill.py
@backend/app/api/v1/settings/skills.py
@backend/app/api/v1/settings/general.py
@backend/app/services/executors/skill_executor.py
@frontend/src/lib/skills-api.ts
@frontend/src/components/settings/skills-section.tsx
@frontend/src/lib/api.ts
@frontend/src/hooks/useGeneralSettings.ts
@frontend/src/lib/settings-api.ts
@backend/app/main.py

<interfaces>
<!-- Existing patterns the executor needs -->

From backend/app/models/settings.py:
```python
class AppSettings(SQLModel, table=True):
    __tablename__ = "app_settings"
    id: int | None = Field(default=None, primary_key=True)
    system_prompt: str | None = Field(default=None)
    temperature: float = Field(default=0.7)
    max_tokens: int = Field(default=2048)
    # ... other fields
```

From backend/app/models/skill.py:
```python
class Skill(SQLModel, table=True):
    __tablename__ = "skill"
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True, max_length=100)
    description: str = Field(max_length=500, default="")
    is_enabled: bool = Field(default=True)
    config: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=_utcnow)
```

From backend/app/api/v1/settings/skills.py:
```python
router = APIRouter(dependencies=[Depends(get_current_user)])
class SkillRead(BaseModel):
    id: int; name: str; description: str; is_enabled: bool; config: str | None; created_at: datetime
```

From frontend/src/lib/skills-api.ts:
```typescript
export interface SkillRead { id: number; name: string; description: string; is_enabled: boolean; config: string | null; created_at: string; }
export async function listSkills(token: string): Promise<SkillRead[]>
export async function toggleSkill(token: string, id: number): Promise<SkillRead>
```

From frontend/src/lib/api.ts:
```typescript
export async function apiFetch(path: string, token: string, options?: RequestInit): Promise<Response>
```

Migration pattern (batch_alter_table for SQLite):
```python
with op.batch_alter_table('app_settings', schema=None) as batch_op:
    batch_op.add_column(sa.Column('col_name', sa.TEXT(), nullable=True))
```

General settings API pattern: single-row upsert (id=1), GET returns defaults if no row, PUT creates or updates.

Seed skills in backend/app/main.py: DEFAULT_SKILLS list seeded in lifespan. The discovery/sync feature supplements this.
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Backend — skill_directories setting, discovery service, and CRUD+sync endpoints</name>
  <files>
    backend/app/models/settings.py,
    backend/alembic/versions/0011_add_skill_directories_to_settings.py,
    backend/app/api/v1/settings/general.py,
    backend/app/services/skill_discovery.py,
    backend/app/api/v1/settings/skills.py,
    backend/app/models/skill.py
  </files>
  <action>
    **1. Add skill_directories to AppSettings model** (`backend/app/models/settings.py`):
    - Add field: `skill_directories: str | None = Field(default=None)` — stores JSON array of directory paths as TEXT (e.g., `'["/path/to/skills", "/other/path"]'`)

    **2. Create Alembic migration** (`backend/alembic/versions/0011_add_skill_directories_to_settings.py`):
    - Follow existing pattern: `down_revision` = `"0bdc60677f9a"` (the web search settings migration)
    - Use `batch_alter_table('app_settings')` to add `skill_directories` column as `sa.TEXT(), nullable=True`
    - Use revision ID format matching project convention (short descriptive name)

    **3. Update General settings API** (`backend/app/api/v1/settings/general.py`):
    - Add `skill_directories: list[str] = []` to `GeneralSettingsRead` schema
    - Add `skill_directories: list[str] | None = None` to `GeneralSettingsUpdate` schema
    - In `get_general_settings`: parse `settings.skill_directories` from JSON string to list (use `json.loads`, default to `[]` if None)
    - In `update_general_settings`: if `data.skill_directories is not None`, serialize to JSON string with `json.dumps` before storing

    **4. Create SkillDiscoveryService** (`backend/app/services/skill_discovery.py`):
    ```python
    import json
    import logging
    import os
    from dataclasses import dataclass
    from pathlib import Path

    logger = logging.getLogger(__name__)

    @dataclass
    class DiscoveredSkill:
        name: str
        description: str
        source_path: str  # absolute path to the skill directory
        instructions: str  # full content of SKILL.md after frontmatter

    def parse_skill_md(filepath: Path) -> DiscoveredSkill | None:
        """Parse a SKILL.md file. Expects YAML frontmatter with name and description."""
        try:
            content = filepath.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            logger.warning("Cannot read %s", filepath)
            return None

        # Parse simple YAML frontmatter between --- delimiters
        if not content.startswith("---"):
            return None
        parts = content.split("---", 2)
        if len(parts) < 3:
            return None

        frontmatter_text = parts[1].strip()
        body = parts[2].strip()

        # Simple key: value parsing (no need for PyYAML dependency)
        meta: dict[str, str] = {}
        for line in frontmatter_text.splitlines():
            if ":" in line:
                key, _, value = line.partition(":")
                meta[key.strip()] = value.strip()

        name = meta.get("name", "")
        description = meta.get("description", "")
        if not name:
            name = filepath.parent.name  # use directory name as fallback

        return DiscoveredSkill(
            name=name,
            description=description,
            source_path=str(filepath.parent),
            instructions=body,
        )

    def discover_skills(directories: list[str]) -> list[DiscoveredSkill]:
        """Scan directories for subdirectories containing SKILL.md."""
        discovered: list[DiscoveredSkill] = []
        for dir_path_str in directories:
            dir_path = Path(dir_path_str).expanduser().resolve()
            if not dir_path.is_dir():
                logger.warning("Skill directory does not exist: %s", dir_path)
                continue
            # Each subdirectory is a potential skill
            try:
                for entry in sorted(dir_path.iterdir()):
                    if entry.is_dir():
                        skill_md = entry / "SKILL.md"
                        if skill_md.is_file():
                            skill = parse_skill_md(skill_md)
                            if skill:
                                discovered.append(skill)
            except OSError:
                logger.warning("Cannot scan directory: %s", dir_path)
        return discovered
    ```

    **5. Add source_path and instructions fields to Skill model** (`backend/app/models/skill.py`):
    - Add `source_path: str | None = Field(default=None)` — filesystem path where skill was discovered
    - Add `instructions: str | None = Field(default=None)` — content from SKILL.md body
    - These nullable fields are backward-compatible (no migration needed for existing rows — but add columns in the migration from step 2)
    - UPDATE the migration in step 2 to ALSO add `source_path` and `instructions` columns to the `skill` table using `batch_alter_table('skill')`

    **6. Add CRUD + sync endpoints** (`backend/app/api/v1/settings/skills.py`):

    Add schemas:
    ```python
    class SkillCreate(BaseModel):
        name: str
        description: str = ""
        is_enabled: bool = True
        config: str | None = None

    class SkillUpdate(BaseModel):
        name: str | None = None
        description: str | None = None
        is_enabled: bool | None = None
        config: str | None = None

    class SyncResult(BaseModel):
        created: int
        updated: int
        total_discovered: int
    ```

    Update `SkillRead` to include `source_path: str | None` and `instructions: str | None`.
    Update `_to_read` helper accordingly.

    Add endpoints:

    - `POST /` — create skill manually. Accept `SkillCreate`, create `Skill` row, return `SkillRead`. Raise 409 if name already exists.

    - `PUT /{skill_id}` — update skill. Accept `SkillUpdate`, update only non-None fields, return `SkillRead`.

    - `DELETE /{skill_id}` — delete skill. Return 204 no content.

    - `POST /sync` — sync from filesystem:
      1. Read `AppSettings` (id=1) to get `skill_directories` JSON string
      2. Parse to `list[str]`, call `discover_skills(directories)`
      3. For each discovered skill: upsert by name (if exists update description/source_path/instructions, if not create new)
      4. Return `SyncResult` with counts

    The sync endpoint does NOT delete skills missing from filesystem (skills may be manually created). Only creates/updates.
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/backend && python -c "
import asyncio, json
from app.services.skill_discovery import discover_skills, parse_skill_md, DiscoveredSkill
from pathlib import Path
# Test parse returns None for empty
assert parse_skill_md(Path('/nonexistent/SKILL.md')) is None
print('Discovery service imports OK')
# Test discover on empty list
assert discover_skills([]) == []
print('All checks passed')
"</automated>
  </verify>
  <done>
    - AppSettings has skill_directories field, migration runs cleanly
    - General settings GET/PUT includes skill_directories as list of strings
    - Skill model has source_path and instructions fields
    - SkillDiscoveryService scans directories and parses SKILL.md frontmatter
    - POST /sync discovers and upserts skills from configured directories
    - POST / creates skill, PUT /{id} updates skill, DELETE /{id} removes skill
    - All new endpoints require authentication (router-level dependency already handles this)
  </done>
</task>

<task type="auto">
  <name>Task 2: Frontend — skill directories config, scan button, and CRUD UI</name>
  <files>
    frontend/src/lib/skills-api.ts,
    frontend/src/components/settings/skills-section.tsx
  </files>
  <action>
    **1. Update skills-api.ts** (`frontend/src/lib/skills-api.ts`):

    Update `SkillRead` interface to include new fields:
    ```typescript
    export interface SkillRead {
      id: number;
      name: string;
      description: string;
      is_enabled: boolean;
      config: string | null;
      source_path: string | null;
      instructions: string | null;
      created_at: string;
    }
    ```

    Add new interfaces and functions:
    ```typescript
    export interface SkillCreate {
      name: string;
      description: string;
      is_enabled?: boolean;
    }

    export interface SkillUpdate {
      name?: string;
      description?: string;
      is_enabled?: boolean;
    }

    export interface SyncResult {
      created: number;
      updated: number;
      total_discovered: number;
    }

    export async function createSkill(token: string, data: SkillCreate): Promise<SkillRead> {
      const res = await apiFetch("/api/v1/settings/skills/", token, {
        method: "POST",
        body: JSON.stringify(data),
      });
      return handleResponse<SkillRead>(res);
    }

    export async function updateSkill(token: string, id: number, data: SkillUpdate): Promise<SkillRead> {
      const res = await apiFetch(`/api/v1/settings/skills/${id}`, token, {
        method: "PUT",
        body: JSON.stringify(data),
      });
      return handleResponse<SkillRead>(res);
    }

    export async function deleteSkill(token: string, id: number): Promise<void> {
      const res = await apiFetch(`/api/v1/settings/skills/${id}`, token, {
        method: "DELETE",
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(body.detail ?? `Request failed (${res.status})`);
      }
    }

    export async function syncSkills(token: string): Promise<SyncResult> {
      const res = await apiFetch("/api/v1/settings/skills/sync", token, {
        method: "POST",
      });
      return handleResponse<SyncResult>(res);
    }
    ```

    **2. Update skills-section.tsx** (`frontend/src/components/settings/skills-section.tsx`):

    Major rework of the component:

    - Import new API functions: `createSkill`, `deleteSkill`, `syncSkills` from skills-api
    - Import additional icons: `Plus`, `Trash2`, `FolderSync` (or `RefreshCw`) from lucide-react
    - Import `Button` from `@/components/ui/button`
    - Import `Input` from `@/components/ui/input`
    - Import `useState` from react

    **SkillRow component** — update to include:
    - A delete button (Trash2 icon) on the right side, before the toggle Switch
    - Show `skill.source_path` as small muted text if present (indicates filesystem-discovered skill)
    - Delete button calls `onDelete(skill.id)`

    **Add skill form** — inline form that appears when user clicks "Add Skill":
    - Two inputs: name (required) and description
    - Submit button calls `createSkill` mutation
    - On success, invalidate skills query, reset form, hide form

    **Sync button** — at the top of the skills list:
    - Button labeled "Scan Directories" with FolderSync/RefreshCw icon
    - Calls `syncSkills` mutation
    - Shows loading spinner while syncing
    - On success: show brief toast-like message with "Created X, Updated Y" (can be simple state-based text that disappears after 3 seconds)
    - Invalidates skills query on success

    **Mutations setup:**
    ```typescript
    const deleteMutation = useMutation({
      mutationFn: (id: number) => deleteSkill(token!, id),
      onSuccess: () => queryClient.invalidateQueries({ queryKey: ["skills"] }),
    });

    const syncMutation = useMutation({
      mutationFn: () => syncSkills(token!),
      onSuccess: () => queryClient.invalidateQueries({ queryKey: ["skills"] }),
    });

    const createMutation = useMutation({
      mutationFn: (data: { name: string; description: string }) => createSkill(token!, data),
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ["skills"] });
        setShowAddForm(false);
        setNewName("");
        setNewDescription("");
      },
    });
    ```

    **Layout structure:**
    ```
    <description text>
    <div flex row: "Add Skill" button + "Scan Directories" button + sync result text>
    {showAddForm && <inline form with name/description inputs + Save/Cancel>}
    <skill list with SkillRow items>
    {empty state if no skills}
    ```

    Note: The skill_directories configuration is handled in the General settings section via the existing `useGeneralSettings` hook. The GeneralSection.tsx already manages AppSettings fields — the `skill_directories` field will appear there automatically once the backend returns it. However, since GeneralSection.tsx only renders system_prompt/temperature/max_tokens explicitly, you need to ADD a skill_directories textarea to GeneralSection.tsx as well.

    **3. Update GeneralSection.tsx** (`frontend/src/components/settings/GeneralSection.tsx`):
    - Add `skill_directories` state as a string (one path per line)
    - Initialize from `settings.skill_directories` (join array with newlines)
    - Add a textarea labeled "Skill Directories" with placeholder "One directory path per line\n/path/to/skills\n~/.claude/skills"
    - On save, split by newlines, trim, filter empty lines, pass as `skill_directories` array to `updateSettings`
    - Update the `useGeneralSettings` hook types if needed — the `GeneralSettings` type in `@/types/chat` needs `skill_directories: string[]`
  </action>
  <verify>
    <automated>cd /Users/przbadu/dev/claude-clone/frontend && npx tsc --noEmit 2>&1 | head -30</automated>
  </verify>
  <done>
    - skills-api.ts exports createSkill, updateSkill, deleteSkill, syncSkills functions
    - SkillsSection shows "Add Skill" button that opens inline name/description form
    - SkillsSection shows "Scan Directories" button that triggers POST /sync
    - Each skill row has a delete button
    - Sync results (created/updated count) shown briefly after scan
    - GeneralSection includes "Skill Directories" textarea (one path per line)
    - Saving general settings persists skill_directories to backend
    - TypeScript compiles without errors
  </done>
</task>

</tasks>

<verification>
1. Backend: `cd backend && alembic upgrade head` runs without error
2. Backend: General settings GET returns `skill_directories: []` by default
3. Backend: PUT general settings with `skill_directories: ["/tmp/test-skills"]` persists and returns correctly
4. Backend: POST /sync returns `{ created: 0, updated: 0, total_discovered: 0 }` when no skills in configured dirs
5. Backend: POST / creates a new skill, DELETE /{id} removes it
6. Frontend: Skills page shows Add Skill button, Scan Directories button, and delete buttons on each row
7. Frontend: General settings page shows Skill Directories textarea
</verification>

<success_criteria>
- Users can configure skill directory paths in General settings (one path per line)
- Users can click "Scan Directories" to discover and sync skills from filesystem
- Discovered skills appear in the skills list with source_path indicator
- Users can manually create and delete skills
- All existing skill functionality (list, toggle) continues to work
</success_criteria>

<output>
After completion, create `.planning/quick/260322-eaw-filesystem-based-skill-discovery-from-co/260322-eaw-SUMMARY.md`
</output>
