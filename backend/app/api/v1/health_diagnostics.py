"""Health diagnostics endpoint — checks connectivity of all configured integrations."""

import asyncio
import time

from fastapi import APIRouter, Depends
from openai import AsyncOpenAI
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.core.database import get_session
from app.core.encryption import decrypt_value
from app.models.llm_provider import LLMProvider
from app.models.settings import AppSettings

router = APIRouter(dependencies=[Depends(get_current_user)])


# ---------- Schemas ----------


class ServiceStatus(BaseModel):
    name: str
    status: str  # "ok" | "error" | "unconfigured"
    latency_ms: int | None = None
    error: str | None = None


class DiagnosticsResponse(BaseModel):
    services: list[ServiceStatus]


# ---------- Helpers ----------


async def _check_llm_provider(provider: LLMProvider) -> ServiceStatus:
    """Ping an LLM provider's /v1/models endpoint."""
    api_key = "ollama"
    if provider.api_key_encrypted:
        try:
            api_key = decrypt_value(provider.api_key_encrypted)
        except Exception:
            api_key = "ollama"

    client = AsyncOpenAI(base_url=provider.base_url, api_key=api_key)
    try:
        start = time.perf_counter()
        await asyncio.wait_for(client.models.list(), timeout=5)
        latency = int((time.perf_counter() - start) * 1000)
        return ServiceStatus(
            name=f"LLM: {provider.name}",
            status="ok",
            latency_ms=latency,
        )
    except Exception as exc:
        return ServiceStatus(
            name=f"LLM: {provider.name}",
            status="error",
            error=str(exc)[:200],
        )


async def _check_embedding(settings: AppSettings) -> ServiceStatus:
    """Check embedding endpoint connectivity."""
    if not settings.embedding_base_url:
        return ServiceStatus(name="Embedding Model", status="unconfigured")

    client = AsyncOpenAI(
        base_url=settings.embedding_base_url,
        api_key="ollama",
    )
    try:
        start = time.perf_counter()
        await asyncio.wait_for(client.models.list(), timeout=5)
        latency = int((time.perf_counter() - start) * 1000)
        return ServiceStatus(
            name="Embedding Model",
            status="ok",
            latency_ms=latency,
        )
    except Exception as exc:
        return ServiceStatus(
            name="Embedding Model",
            status="error",
            error=str(exc)[:200],
        )


async def _check_reranker(settings: AppSettings) -> ServiceStatus:
    """Check reranker endpoint connectivity."""
    if not settings.reranker_base_url:
        return ServiceStatus(name="Reranker", status="unconfigured")

    client = AsyncOpenAI(
        base_url=settings.reranker_base_url,
        api_key="ollama",
    )
    try:
        start = time.perf_counter()
        await asyncio.wait_for(client.models.list(), timeout=5)
        latency = int((time.perf_counter() - start) * 1000)
        return ServiceStatus(
            name="Reranker",
            status="ok",
            latency_ms=latency,
        )
    except Exception as exc:
        return ServiceStatus(
            name="Reranker",
            status="error",
            error=str(exc)[:200],
        )


async def _check_chromadb() -> ServiceStatus:
    """Check ChromaDB connectivity."""
    try:
        import httpx

        start = time.perf_counter()
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get("http://localhost:8100/api/v1/heartbeat")
            latency = int((time.perf_counter() - start) * 1000)
            if resp.status_code == 200:
                return ServiceStatus(
                    name="ChromaDB",
                    status="ok",
                    latency_ms=latency,
                )
            return ServiceStatus(
                name="ChromaDB",
                status="error",
                error=f"HTTP {resp.status_code}",
            )
    except Exception as exc:
        return ServiceStatus(
            name="ChromaDB",
            status="error",
            error=str(exc)[:200],
        )


async def _check_web_search(settings: AppSettings) -> list[ServiceStatus]:
    """Check web search provider connectivity."""
    results: list[ServiceStatus] = []

    if settings.searxng_base_url:
        try:
            import httpx

            start = time.perf_counter()
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{settings.searxng_base_url}/healthz")
                latency = int((time.perf_counter() - start) * 1000)
                if resp.status_code == 200:
                    results.append(
                        ServiceStatus(
                            name="SearXNG",
                            status="ok",
                            latency_ms=latency,
                        )
                    )
                else:
                    results.append(
                        ServiceStatus(
                            name="SearXNG",
                            status="error",
                            error=f"HTTP {resp.status_code}",
                        )
                    )
        except Exception as exc:
            results.append(
                ServiceStatus(
                    name="SearXNG",
                    status="error",
                    error=str(exc)[:200],
                )
            )
    else:
        results.append(ServiceStatus(name="SearXNG", status="unconfigured"))

    if settings.exa_api_key_encrypted:
        results.append(
            ServiceStatus(
                name="Exa Search",
                status="ok",
                error=None,
            )
        )
    else:
        results.append(ServiceStatus(name="Exa Search", status="unconfigured"))

    return results


# ---------- Endpoint ----------


@router.get("/", response_model=DiagnosticsResponse)
async def get_diagnostics(
    session: AsyncSession = Depends(get_session),
) -> DiagnosticsResponse:
    # Fetch all configured providers
    result = await session.execute(select(LLMProvider))
    providers = list(result.scalars().all())

    # Fetch app settings
    settings_result = await session.execute(select(AppSettings))
    settings = settings_result.scalars().first()
    if settings is None:
        settings = AppSettings()

    # Run all checks concurrently
    tasks: list[asyncio.Task[ServiceStatus | list[ServiceStatus]]] = []
    for p in providers:
        tasks.append(asyncio.create_task(_check_llm_provider(p)))
    tasks.append(asyncio.create_task(_check_embedding(settings)))
    tasks.append(asyncio.create_task(_check_reranker(settings)))
    tasks.append(asyncio.create_task(_check_chromadb()))
    tasks.append(asyncio.create_task(_check_web_search(settings)))

    results_raw = await asyncio.gather(*tasks)

    services: list[ServiceStatus] = []
    for r in results_raw:
        if isinstance(r, list):
            services.extend(r)
        else:
            services.append(r)

    return DiagnosticsResponse(services=services)
