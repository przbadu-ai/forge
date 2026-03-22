"""API endpoints for skill management (list, toggle, CRUD, and filesystem sync)."""

import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.core.database import get_session
from app.models.settings import AppSettings
from app.models.skill import Skill
from app.services.skill_discovery import discover_skills

router = APIRouter(dependencies=[Depends(get_current_user)])


# ---------- Schemas ----------


class SkillRead(BaseModel):
    id: int
    name: str
    description: str
    is_enabled: bool
    config: str | None
    content: str | None
    source_path: str | None
    created_at: datetime


class SkillCreate(BaseModel):
    name: str
    description: str = ""
    is_enabled: bool = True
    config: str | None = None
    content: str | None = None


class SkillUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    is_enabled: bool | None = None
    config: str | None = None
    content: str | None = None


class SyncResult(BaseModel):
    created: int
    updated: int
    total_discovered: int


# ---------- Helpers ----------


def _to_read(skill: Skill) -> SkillRead:
    return SkillRead(
        id=skill.id,
        name=skill.name,
        description=skill.description,
        is_enabled=skill.is_enabled,
        config=skill.config,
        content=skill.content,
        source_path=skill.source_path,
        created_at=skill.created_at,
    )


async def _get_skill(skill_id: int, session: AsyncSession) -> Skill:
    result = await session.execute(
        select(Skill).where(Skill.id == skill_id)  # type: ignore[arg-type]
    )
    skill = result.scalars().first()
    if skill is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Skill not found")
    return skill


# ---------- Endpoints ----------


@router.get("", response_model=list[SkillRead])
async def list_skills(
    session: AsyncSession = Depends(get_session),
) -> list[SkillRead]:
    result = await session.execute(select(Skill))
    skills = result.scalars().all()
    return [_to_read(s) for s in skills]


@router.post("", response_model=SkillRead, status_code=status.HTTP_201_CREATED)
async def create_skill(
    data: SkillCreate,
    session: AsyncSession = Depends(get_session),
) -> SkillRead:
    # Check for duplicate name
    result = await session.execute(
        select(Skill).where(Skill.name == data.name)  # type: ignore[arg-type]
    )
    if result.scalars().first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Skill with name '{data.name}' already exists",
        )

    skill = Skill(
        name=data.name,
        description=data.description,
        is_enabled=data.is_enabled,
        config=data.config,
        content=data.content,
    )
    session.add(skill)
    await session.commit()
    await session.refresh(skill)
    return _to_read(skill)


@router.put("/{skill_id}", response_model=SkillRead)
async def update_skill(
    skill_id: int,
    data: SkillUpdate,
    session: AsyncSession = Depends(get_session),
) -> SkillRead:
    skill = await _get_skill(skill_id, session)

    if data.name is not None:
        skill.name = data.name
    if data.description is not None:
        skill.description = data.description
    if data.is_enabled is not None:
        skill.is_enabled = data.is_enabled
    if data.config is not None:
        skill.config = data.config
    if data.content is not None:
        skill.content = data.content

    session.add(skill)
    await session.commit()
    await session.refresh(skill)
    return _to_read(skill)


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill(
    skill_id: int,
    session: AsyncSession = Depends(get_session),
) -> None:
    skill = await _get_skill(skill_id, session)
    await session.delete(skill)
    await session.commit()


@router.patch("/{skill_id}/toggle", response_model=SkillRead)
async def toggle_skill(
    skill_id: int,
    session: AsyncSession = Depends(get_session),
) -> SkillRead:
    skill = await _get_skill(skill_id, session)
    skill.is_enabled = not skill.is_enabled
    session.add(skill)
    await session.commit()
    await session.refresh(skill)
    return _to_read(skill)


@router.post("/sync", response_model=SyncResult)
async def sync_skills(
    session: AsyncSession = Depends(get_session),
) -> SyncResult:
    """Sync skills from configured filesystem directories."""
    # Read skill_directories from AppSettings
    result = await session.execute(select(AppSettings))
    settings = result.scalars().first()

    directories: list[str] = []
    if settings and settings.skill_directories:
        try:
            directories = json.loads(settings.skill_directories)
        except (json.JSONDecodeError, TypeError):
            directories = []

    # Discover skills from filesystem
    discovered = discover_skills(directories)

    created = 0
    updated = 0

    for disc in discovered:
        # Check if skill with this name already exists
        result = await session.execute(
            select(Skill).where(Skill.name == disc.name)  # type: ignore[arg-type]
        )
        existing = result.scalars().first()

        if existing:
            existing.description = disc.description
            existing.source_path = disc.source_path
            existing.content = disc.content
            session.add(existing)
            updated += 1
        else:
            skill = Skill(
                name=disc.name,
                description=disc.description,
                source_path=disc.source_path,
                content=disc.content,
            )
            session.add(skill)
            created += 1

    await session.commit()

    return SyncResult(
        created=created,
        updated=updated,
        total_discovered=len(discovered),
    )
