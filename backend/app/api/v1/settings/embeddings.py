"""Embedding and reranker settings endpoints."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.core.database import get_session
from app.models.settings import AppSettings

router = APIRouter(dependencies=[Depends(get_current_user)])


# ---------- Schemas ----------


class EmbeddingSettingsRead(BaseModel):
    embedding_base_url: str | None = None
    embedding_model: str | None = None
    reranker_base_url: str | None = None
    reranker_model: str | None = None


class EmbeddingSettingsUpdate(BaseModel):
    embedding_base_url: str | None = None
    embedding_model: str | None = None
    reranker_base_url: str | None = None
    reranker_model: str | None = None


# ---------- Endpoints ----------


@router.get("", response_model=EmbeddingSettingsRead)
async def get_embedding_settings(
    session: AsyncSession = Depends(get_session),
) -> EmbeddingSettingsRead:
    result = await session.execute(select(AppSettings))
    settings = result.scalars().first()
    if settings is None:
        return EmbeddingSettingsRead()
    return EmbeddingSettingsRead(
        embedding_base_url=settings.embedding_base_url,
        embedding_model=settings.embedding_model,
        reranker_base_url=settings.reranker_base_url,
        reranker_model=settings.reranker_model,
    )


@router.put("", response_model=EmbeddingSettingsRead)
async def update_embedding_settings(
    data: EmbeddingSettingsUpdate,
    session: AsyncSession = Depends(get_session),
) -> EmbeddingSettingsRead:
    result = await session.execute(select(AppSettings))
    settings = result.scalars().first()

    if settings is None:
        settings = AppSettings(id=1)
        session.add(settings)

    if data.embedding_base_url is not None:
        settings.embedding_base_url = data.embedding_base_url or None
    if data.embedding_model is not None:
        settings.embedding_model = data.embedding_model or None
    if data.reranker_base_url is not None:
        settings.reranker_base_url = data.reranker_base_url or None
    if data.reranker_model is not None:
        settings.reranker_model = data.reranker_model or None

    session.add(settings)
    await session.commit()
    await session.refresh(settings)

    return EmbeddingSettingsRead(
        embedding_base_url=settings.embedding_base_url,
        embedding_model=settings.embedding_model,
        reranker_base_url=settings.reranker_base_url,
        reranker_model=settings.reranker_model,
    )
