from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import select

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import AsyncSessionFactory, create_db_and_tables
from app.core.security import hash_password
from app.models.user import User


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


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await create_db_and_tables()
    await seed_admin_user()
    yield


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )

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
