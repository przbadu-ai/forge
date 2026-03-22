import asyncio
import json
import time
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from openai import AsyncOpenAI
from pydantic import BaseModel
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.core.database import get_session
from app.core.encryption import encrypt_value
from app.models.llm_provider import LLMProvider

router = APIRouter(dependencies=[Depends(get_current_user)])


# ---------- Schemas ----------


class ProviderCreate(BaseModel):
    name: str
    base_url: str
    api_key: str = ""
    models: list[str] = []
    is_default: bool = False


class ProviderUpdate(BaseModel):
    name: str | None = None
    base_url: str | None = None
    api_key: str | None = None
    models: list[str] | None = None
    is_default: bool | None = None


class ProviderRead(BaseModel):
    id: int
    name: str
    base_url: str
    models: list[str]
    is_default: bool
    created_at: datetime


class TestConnectionRequest(BaseModel):
    base_url: str
    api_key: str = ""


class TestConnectionResponse(BaseModel):
    ok: bool
    latency_ms: int | None = None
    model_count: int | None = None
    error: str | None = None


# ---------- Helpers ----------


def _to_read(provider: LLMProvider) -> ProviderRead:
    return ProviderRead(
        id=provider.id,
        name=provider.name,
        base_url=provider.base_url,
        models=json.loads(provider.models),
        is_default=provider.is_default,
        created_at=provider.created_at,
    )


async def _clear_other_defaults(session: AsyncSession, *, exclude_id: int | None = None) -> None:
    """Set is_default=False on all providers except exclude_id."""
    stmt = (
        update(LLMProvider)
        .where(LLMProvider.is_default == True)  # type: ignore[arg-type]  # noqa: E712
        .values(is_default=False)
    )
    if exclude_id is not None:
        stmt = stmt.where(LLMProvider.id != exclude_id)  # type: ignore[arg-type]
    await session.execute(stmt)


# ---------- Endpoints ----------


@router.get("", response_model=list[ProviderRead])
async def list_providers(
    session: AsyncSession = Depends(get_session),
) -> list[ProviderRead]:
    result = await session.execute(select(LLMProvider))
    providers = result.scalars().all()
    return [_to_read(p) for p in providers]


@router.post("", response_model=ProviderRead, status_code=status.HTTP_201_CREATED)
async def create_provider(
    data: ProviderCreate,
    session: AsyncSession = Depends(get_session),
) -> ProviderRead:
    provider = LLMProvider(
        name=data.name,
        base_url=data.base_url,
        api_key_encrypted=encrypt_value(data.api_key) if data.api_key else "",
        models=json.dumps(data.models),
        is_default=data.is_default,
    )

    if data.is_default:
        await _clear_other_defaults(session)

    session.add(provider)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Provider with name '{data.name}' already exists",
        ) from exc

    await session.refresh(provider)
    return _to_read(provider)


@router.put("/{provider_id}", response_model=ProviderRead)
async def update_provider(
    provider_id: int,
    data: ProviderUpdate,
    session: AsyncSession = Depends(get_session),
) -> ProviderRead:
    provider = await session.get(LLMProvider, provider_id)
    if provider is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")

    if data.name is not None:
        provider.name = data.name
    if data.base_url is not None:
        provider.base_url = data.base_url
    if data.api_key is not None:
        provider.api_key_encrypted = encrypt_value(data.api_key) if data.api_key else ""
    if data.models is not None:
        provider.models = json.dumps(data.models)
    if data.is_default is not None:
        provider.is_default = data.is_default
        if data.is_default:
            await _clear_other_defaults(session, exclude_id=provider.id)

    session.add(provider)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Provider with name '{data.name}' already exists",
        ) from exc

    await session.refresh(provider)
    return _to_read(provider)


@router.delete("/{provider_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_provider(
    provider_id: int,
    session: AsyncSession = Depends(get_session),
) -> None:
    provider = await session.get(LLMProvider, provider_id)
    if provider is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")
    await session.delete(provider)
    await session.commit()


@router.post("/test-connection", response_model=TestConnectionResponse)
async def test_connection(
    data: TestConnectionRequest,
) -> TestConnectionResponse:
    client = AsyncOpenAI(
        base_url=data.base_url,
        api_key=data.api_key or "ollama",
    )
    try:
        start = time.perf_counter()
        models_page = await asyncio.wait_for(client.models.list(), timeout=10)
        latency_ms = int((time.perf_counter() - start) * 1000)
        model_list = list(models_page)
        return TestConnectionResponse(
            ok=True,
            latency_ms=latency_ms,
            model_count=len(model_list),
        )
    except Exception as exc:
        return TestConnectionResponse(ok=False, error=str(exc))
