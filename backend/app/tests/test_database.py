"""Tests verifying SQLite WAL mode, busy_timeout, and concurrent access safety."""

import asyncio

import pytest
from sqlalchemy import text

from app.core.database import AsyncSessionFactory, engine


@pytest.mark.asyncio
async def test_wal_mode_enabled() -> None:
    async with engine.connect() as conn:
        result = await conn.execute(text("PRAGMA journal_mode"))
        mode = result.scalar()
    assert mode == "wal", f"Expected WAL mode but got: {mode}"


@pytest.mark.asyncio
async def test_busy_timeout_set() -> None:
    async with engine.connect() as conn:
        result = await conn.execute(text("PRAGMA busy_timeout"))
        timeout = result.scalar()
    assert timeout == 5000, f"Expected busy_timeout=5000 but got: {timeout}"


@pytest.mark.asyncio
async def test_concurrent_sessions_no_lock_error() -> None:
    async def read_session() -> str:
        async with AsyncSessionFactory() as session:
            result = await session.execute(text("SELECT 1"))
            return str(result.scalar())

    results = await asyncio.gather(*[read_session() for _ in range(5)])
    assert all(r == "1" for r in results)
