from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.main import create_app


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    app = create_app()
    # Manually run the lifespan so DB tables are created and admin is seeded
    async with (
        app.router.lifespan_context(app),
        AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as ac,
    ):
        yield ac


@pytest_asyncio.fixture
async def auth_client(client: AsyncClient) -> AsyncGenerator[AsyncClient, None]:
    """Client with admin credentials pre-logged-in; Authorization header set."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={
            "username": settings.admin_username,
            "password": settings.admin_password,
        },
    )
    token = resp.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    yield client
