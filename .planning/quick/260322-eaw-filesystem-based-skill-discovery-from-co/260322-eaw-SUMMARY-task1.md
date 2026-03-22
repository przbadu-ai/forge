---
phase: quick
plan: 260322-eaw
scope: task-1-backend-only
completed: "2026-03-22T04:39:00Z"
duration: 2min
tasks_completed: 1
tasks_total: 2
key_files_created:
  - backend/app/services/skill_discovery.py
  - backend/alembic/versions/0011_add_skill_directories_and_skill_content.py
key_files_modified:
  - backend/app/models/settings.py
  - backend/app/models/skill.py
  - backend/app/api/v1/settings/general.py
  - backend/app/api/v1/settings/skills.py
decisions:
  - "Named field 'content' (not 'instructions') per user request to match Claude platform skill pattern"
  - "No-delete sync: POST /sync only creates/updates, never removes manually-created skills"
---

# Phase quick Plan 260322-eaw: Filesystem-based Skill Discovery (Task 1 - Backend)

Skill discovery service with SKILL.md parsing, content TEXT field on Skill model, and full CRUD + sync API endpoints.

## Task 1: Backend -- skill_directories setting, discovery service, and CRUD+sync endpoints

**Commit:** 81bd096

### Changes Made

1. **AppSettings model** -- Added `skill_directories` field (TEXT, stores JSON array of directory paths)

2. **Skill model** -- Added `content` (TEXT, full skill instructions/prompt) and `source_path` (TEXT, filesystem origin path)

3. **Alembic migration** (`0011_add_skill_directories_and_skill_content`) -- Adds columns to both `app_settings` and `skill` tables using batch_alter_table for SQLite compatibility

4. **General settings API** -- Updated GET/PUT to serialize `skill_directories` as JSON string in DB, expose as `list[str]` in API response

5. **SkillDiscoveryService** (`skill_discovery.py`) -- Scans configured directories for subdirectories containing SKILL.md, parses YAML frontmatter (name, description) and body content, returns list of DiscoveredSkill dataclass objects

6. **Skills API endpoints** -- Added:
   - `POST /` -- Create skill manually (409 on duplicate name)
   - `PUT /{skill_id}` -- Update skill fields
   - `DELETE /{skill_id}` -- Remove skill (204)
   - `POST /sync` -- Discover skills from configured directories and upsert by name
   - Updated `SkillRead` schema to include `content` and `source_path`

### Verification

- Discovery service imports and runs correctly (parse_skill_md, discover_skills)
- Alembic migration applies cleanly
- API module imports without errors
- GeneralSettingsRead defaults skill_directories to empty list

## Deviations from Plan

### Field Naming

**1. [User Override] Used 'content' instead of 'instructions'**
- Plan specified `instructions` as the field name
- User's additional context explicitly requested `content` to match the Claude platform skill pattern
- Applied `content` consistently across model, API schemas, and discovery service

## Remaining Work

Task 2 (Frontend) is handled by a separate agent.
