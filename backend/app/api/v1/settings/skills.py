"""API endpoints for skill management (list and toggle)."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.core.database import get_session
from app.models.skill import Skill

router = APIRouter(dependencies=[Depends(get_current_user)])


# ---------- Schemas ----------


class SkillRead(BaseModel):
    id: int
    name: str
    description: str
    is_enabled: bool
    config: str | None
    created_at: datetime


# ---------- Helpers ----------


def _to_read(skill: Skill) -> SkillRead:
    return SkillRead(
        id=skill.id,
        name=skill.name,
        description=skill.description,
        is_enabled=skill.is_enabled,
        config=skill.config,
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


@router.get("/", response_model=list[SkillRead])
async def list_skills(
    session: AsyncSession = Depends(get_session),
) -> list[SkillRead]:
    result = await session.execute(select(Skill))
    skills = result.scalars().all()
    return [_to_read(s) for s in skills]


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
