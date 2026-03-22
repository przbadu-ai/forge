"""Filesystem-based skill discovery service.

Scans configured directories for subdirectories containing SKILL.md files
and parses them into DiscoveredSkill objects for upserting into the database.
"""

import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class DiscoveredSkill:
    name: str
    description: str
    source_path: str  # absolute path to the skill directory
    content: str  # full content of SKILL.md after frontmatter


def parse_skill_md(filepath: Path) -> DiscoveredSkill | None:
    """Parse a SKILL.md file. Expects YAML frontmatter with name and description."""
    try:
        raw = filepath.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        logger.warning("Cannot read %s", filepath)
        return None

    # Parse simple YAML frontmatter between --- delimiters
    if not raw.startswith("---"):
        # No frontmatter — treat entire file as content, use directory name
        return DiscoveredSkill(
            name=filepath.parent.name,
            description="",
            source_path=str(filepath.parent),
            content=raw.strip(),
        )

    parts = raw.split("---", 2)
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
        content=body,
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
