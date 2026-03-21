"""Tests for skill settings API and SkillExecutor."""

from typing import Any

import pytest
from httpx import AsyncClient

from app.services.executors.skill_executor import SkillExecutor
from app.services.trace_emitter import TraceEmitter

SKILLS_BASE = "/api/v1/settings/skills"
SKILLS_URL = f"{SKILLS_BASE}/"  # trailing slash for collection endpoints


# ---------- 1. List skills (seeded by lifespan) ----------


async def test_list_skills(auth_client: AsyncClient) -> None:
    """GET /settings/skills returns seeded skills."""
    resp = await auth_client.get(SKILLS_URL)
    assert resp.status_code == 200
    skills = resp.json()
    names = [s["name"] for s in skills]
    assert "web_search" in names
    assert "code_execution" in names
    assert len(skills) >= 2
    # Each skill should have expected fields
    for skill in skills:
        assert "id" in skill
        assert "description" in skill
        assert "is_enabled" in skill
        assert "created_at" in skill


# ---------- 2. Toggle skill ----------


async def test_toggle_skill(auth_client: AsyncClient) -> None:
    """PATCH /{id}/toggle flips is_enabled."""
    # Get skills to find ID
    resp = await auth_client.get(SKILLS_URL)
    skills = resp.json()
    skill = skills[0]
    sid = skill["id"]
    original_enabled = skill["is_enabled"]

    # Toggle off
    resp = await auth_client.patch(f"{SKILLS_BASE}/{sid}/toggle")
    assert resp.status_code == 200
    assert resp.json()["is_enabled"] is not original_enabled

    # Toggle back
    resp2 = await auth_client.patch(f"{SKILLS_BASE}/{sid}/toggle")
    assert resp2.status_code == 200
    assert resp2.json()["is_enabled"] is original_enabled


# ---------- 3. Auth required ----------


async def test_skills_requires_auth(client: AsyncClient) -> None:
    """GET /settings/skills without token returns 401."""
    resp = await client.get(SKILLS_URL)
    assert resp.status_code in (401, 403)


# ---------- 4. Toggle not found ----------


async def test_toggle_skill_not_found(auth_client: AsyncClient) -> None:
    """PATCH toggle on non-existent skill returns 404."""
    resp = await auth_client.patch(f"{SKILLS_BASE}/99999/toggle")
    assert resp.status_code == 404


# ---------- 5. SkillExecutor unit tests ----------


@pytest.mark.asyncio
async def test_skill_executor_with_default_handlers() -> None:
    """SkillExecutor calls default placeholder handlers correctly."""
    executor = SkillExecutor()

    result = await executor.execute("web_search", {"query": "test query"})
    assert result.error is None
    assert "not yet configured" in result.output.lower()
    assert "test query" in result.output

    result2 = await executor.execute("code_execution", {"code": "print('hello')"})
    assert result2.error is None
    assert "not yet configured" in result2.output.lower()


@pytest.mark.asyncio
async def test_skill_executor_unknown_skill() -> None:
    """SkillExecutor returns error for unregistered skill."""
    executor = SkillExecutor()
    result = await executor.execute("unknown_skill", {})
    assert result.error is not None
    assert "no handler" in result.error.lower()


@pytest.mark.asyncio
async def test_skill_executor_with_custom_handler() -> None:
    """SkillExecutor works with custom handler functions."""

    async def custom_handler(input: dict[str, Any]) -> str:
        return f"Custom result: {input.get('data', '')}"

    executor = SkillExecutor(handlers={"custom": custom_handler})
    result = await executor.execute("custom", {"data": "hello"})
    assert result.error is None
    assert result.output == "Custom result: hello"


@pytest.mark.asyncio
async def test_skill_executor_emits_trace_events() -> None:
    """SkillExecutor emits trace events when a tracer is provided."""
    tracer = TraceEmitter()
    executor = SkillExecutor(tracer=tracer)

    await executor.execute("web_search", {"query": "test"})

    events = tracer.events
    # Should have tool_start and tool_end events
    assert len(events) == 2
    assert events[0].type == "tool_call"
    assert events[0].status == "running"
    assert events[0].name == "web_search"
    assert events[1].type == "tool_call"
    assert events[1].status == "completed"
    assert events[1].name == "web_search"


@pytest.mark.asyncio
async def test_skill_executor_handler_error() -> None:
    """SkillExecutor handles handler exceptions gracefully."""

    async def failing_handler(input: dict[str, Any]) -> str:
        raise RuntimeError("Something broke")

    tracer = TraceEmitter()
    executor = SkillExecutor(handlers={"broken": failing_handler}, tracer=tracer)
    result = await executor.execute("broken", {})

    assert result.error is not None
    assert "failed" in result.error.lower()
    # Trace should show error
    events = tracer.events
    assert events[-1].status == "error"
