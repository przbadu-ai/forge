from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import select
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import AsyncSessionFactory, create_db_and_tables
from app.core.security import hash_password
from app.models.skill import Skill
from app.models.user import User
from app.services.mcp_process_manager import McpProcessManager

# Module-level singleton for MCP process management
mcp_process_manager = McpProcessManager()


DEFAULT_SKILLS = [
    {
        "name": "web_search",
        "description": "Search the web for current information",
    },
    {
        "name": "code_execution",
        "description": "Execute code snippets in a sandboxed environment",
    },
]


async def seed_admin_user() -> None:
    async with AsyncSessionFactory() as session:
        result = await session.execute(select(User))
        existing = result.scalars().first()
        if existing is None:
            user = User(
                username=settings.admin_username,
                hashed_password=hash_password(settings.admin_password),
            )
            session.add(user)
            await session.commit()


async def seed_default_skills() -> None:
    """Seed pre-defined skills if they don't exist yet."""
    async with AsyncSessionFactory() as session:
        for skill_data in DEFAULT_SKILLS:
            result = await session.execute(select(Skill).where(Skill.name == skill_data["name"]))
            if result.scalars().first() is None:
                skill = Skill(**skill_data)
                session.add(skill)
        await session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await create_db_and_tables()
    await seed_admin_user()
    await seed_default_skills()
    await mcp_process_manager.cleanup_orphans()
    yield
    await mcp_process_manager.stop_all()


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )

    # Fix redirect URLs when behind a reverse proxy (e.g., Next.js rewrites).
    # FastAPI's trailing-slash redirects use the internal Host header (backend:8000),
    # which leaks to the browser and causes mixed-content errors on HTTPS.
    class FixRedirectMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):  # type: ignore[override]
            response = await call_next(request)
            if response.status_code in (307, 308):
                location = response.headers.get("location", "")
                if "backend:8000" in location:
                    # Strip the internal origin — return a relative redirect
                    response.headers["location"] = location.replace(
                        "http://backend:8000", ""
                    )
            return response

    application.add_middleware(FixRedirectMiddleware)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Content-Type", "Cache-Control"],
    )

    application.include_router(api_router, prefix="/api/v1")

    return application


app = create_app()
