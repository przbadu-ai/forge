"""Web search provider settings endpoints (SearXNG, Exa)."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.core.database import get_session
from app.core.encryption import encrypt_value
from app.models.settings import AppSettings

router = APIRouter(dependencies=[Depends(get_current_user)])


# ---------- Schemas ----------


class WebSearchSettingsRead(BaseModel):
    searxng_base_url: str | None = None
    exa_api_key_set: bool = False


class WebSearchSettingsUpdate(BaseModel):
    searxng_base_url: str | None = None
    exa_api_key: str | None = None


# ---------- Helpers ----------


def _to_read(settings: AppSettings) -> WebSearchSettingsRead:
    has_exa = bool(settings.exa_api_key_encrypted)
    return WebSearchSettingsRead(
        searxng_base_url=settings.searxng_base_url,
        exa_api_key_set=has_exa,
    )


# ---------- Endpoints ----------


@router.get("", response_model=WebSearchSettingsRead)
async def get_web_search_settings(
    session: AsyncSession = Depends(get_session),
) -> WebSearchSettingsRead:
    result = await session.execute(select(AppSettings))
    settings = result.scalars().first()
    if settings is None:
        return WebSearchSettingsRead()
    return _to_read(settings)


@router.put("", response_model=WebSearchSettingsRead)
async def update_web_search_settings(
    data: WebSearchSettingsUpdate,
    session: AsyncSession = Depends(get_session),
) -> WebSearchSettingsRead:
    result = await session.execute(select(AppSettings))
    settings = result.scalars().first()

    if settings is None:
        settings = AppSettings(id=1)
        session.add(settings)

    if data.searxng_base_url is not None:
        settings.searxng_base_url = data.searxng_base_url or None
    if data.exa_api_key is not None:
        settings.exa_api_key_encrypted = (
            encrypt_value(data.exa_api_key) if data.exa_api_key else None
        )

    session.add(settings)
    await session.commit()
    await session.refresh(settings)

    return _to_read(settings)
