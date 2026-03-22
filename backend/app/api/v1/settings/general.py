import json

from fastapi import APIRouter, Depends
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.core.database import get_session
from app.models.settings import AppSettings

router = APIRouter(dependencies=[Depends(get_current_user)])


# ---------- Schemas ----------


class GeneralSettingsRead(BaseModel):
    system_prompt: str | None = None
    temperature: float = 0.7
    max_tokens: int = 2048
    skill_directories: list[str] = []


class GeneralSettingsUpdate(BaseModel):
    system_prompt: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    skill_directories: list[str] | None = None

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v: float | None) -> float | None:
        if v is not None and (v < 0.0 or v > 2.0):
            raise ValueError("temperature must be between 0.0 and 2.0")
        return v

    @field_validator("max_tokens")
    @classmethod
    def validate_max_tokens(cls, v: int | None) -> int | None:
        if v is not None and v < 1:
            raise ValueError("max_tokens must be >= 1")
        return v


# ---------- Endpoints ----------


@router.get("", response_model=GeneralSettingsRead)
async def get_general_settings(
    session: AsyncSession = Depends(get_session),
) -> GeneralSettingsRead:
    result = await session.execute(select(AppSettings))
    settings = result.scalars().first()
    if settings is None:
        return GeneralSettingsRead()

    skill_dirs: list[str] = []
    if settings.skill_directories:
        try:
            skill_dirs = json.loads(settings.skill_directories)
        except (json.JSONDecodeError, TypeError):
            skill_dirs = []

    return GeneralSettingsRead(
        system_prompt=settings.system_prompt,
        temperature=settings.temperature,
        max_tokens=settings.max_tokens,
        skill_directories=skill_dirs,
    )


@router.put("", response_model=GeneralSettingsRead)
async def update_general_settings(
    data: GeneralSettingsUpdate,
    session: AsyncSession = Depends(get_session),
) -> GeneralSettingsRead:
    result = await session.execute(select(AppSettings))
    settings = result.scalars().first()

    if settings is None:
        settings = AppSettings(id=1)
        session.add(settings)

    if data.system_prompt is not None:
        settings.system_prompt = data.system_prompt
    # Allow explicitly setting system_prompt to empty string to clear it
    # But None means "don't change"

    if data.temperature is not None:
        settings.temperature = data.temperature
    if data.max_tokens is not None:
        settings.max_tokens = data.max_tokens
    if data.skill_directories is not None:
        settings.skill_directories = json.dumps(data.skill_directories)

    session.add(settings)
    await session.commit()
    await session.refresh(settings)

    skill_dirs: list[str] = []
    if settings.skill_directories:
        try:
            skill_dirs = json.loads(settings.skill_directories)
        except (json.JSONDecodeError, TypeError):
            skill_dirs = []

    return GeneralSettingsRead(
        system_prompt=settings.system_prompt,
        temperature=settings.temperature,
        max_tokens=settings.max_tokens,
        skill_directories=skill_dirs,
    )
