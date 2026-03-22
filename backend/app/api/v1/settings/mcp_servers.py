"""CRUD endpoints for MCP server management."""

import json
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.core.database import get_session
from app.models.mcp_server import McpServer

router = APIRouter(dependencies=[Depends(get_current_user)])

VALID_TRANSPORT_TYPES = {"stdio", "sse", "streamable_http"}


# ---------- Schemas ----------


class McpServerCreate(BaseModel):
    name: str
    transport_type: str = "stdio"
    command: str | None = None
    url: str | None = None
    args: list[str] = []
    env_vars: dict[str, str] = {}
    is_enabled: bool = True


class McpServerUpdate(BaseModel):
    name: str | None = None
    transport_type: str | None = None
    command: str | None = None
    url: str | None = None
    args: list[str] | None = None
    env_vars: dict[str, str] | None = None
    is_enabled: bool | None = None


class McpServerRead(BaseModel):
    id: int
    name: str
    transport_type: str
    command: str | None
    url: str | None
    args: list[str]
    env_vars: dict[str, str]
    is_enabled: bool
    created_at: datetime
    updated_at: datetime


# ---------- Helpers ----------


def _validate_transport_fields(transport_type: str, command: str | None, url: str | None) -> None:
    """Validate that required fields are present for the given transport type."""
    if transport_type not in VALID_TRANSPORT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Invalid transport_type '{transport_type}'. Must be one of: {', '.join(sorted(VALID_TRANSPORT_TYPES))}",
        )
    if transport_type == "stdio" and not command:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="'command' is required for stdio transport type",
        )
    if transport_type in ("sse", "streamable_http") and not url:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="'url' is required for sse and streamable_http transport types",
        )


def _to_read(server: McpServer) -> McpServerRead:
    return McpServerRead(
        id=server.id,
        name=server.name,
        transport_type=server.transport_type,
        command=server.command,
        url=server.url,
        args=json.loads(server.args),
        env_vars=json.loads(server.env_vars),
        is_enabled=server.is_enabled,
        created_at=server.created_at,
        updated_at=server.updated_at,
    )


async def _get_server(server_id: int, session: AsyncSession) -> McpServer:
    result = await session.execute(
        select(McpServer).where(McpServer.id == server_id)  # type: ignore[arg-type]
    )
    server = result.scalars().first()
    if server is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MCP server not found")
    return server


# ---------- Endpoints ----------


@router.get("/", response_model=list[McpServerRead])
async def list_mcp_servers(
    session: AsyncSession = Depends(get_session),
) -> list[McpServerRead]:
    result = await session.execute(select(McpServer))
    servers = result.scalars().all()
    return [_to_read(s) for s in servers]


@router.post("/", response_model=McpServerRead, status_code=status.HTTP_201_CREATED)
async def create_mcp_server(
    data: McpServerCreate,
    session: AsyncSession = Depends(get_session),
) -> McpServerRead:
    _validate_transport_fields(data.transport_type, data.command, data.url)

    server = McpServer(
        name=data.name,
        transport_type=data.transport_type,
        command=data.command,
        url=data.url,
        args=json.dumps(data.args),
        env_vars=json.dumps(data.env_vars),
        is_enabled=data.is_enabled,
    )
    session.add(server)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"MCP server with name '{data.name}' already exists",
        ) from exc
    await session.refresh(server)
    return _to_read(server)


@router.put("/{server_id}", response_model=McpServerRead)
async def update_mcp_server(
    server_id: int,
    data: McpServerUpdate,
    session: AsyncSession = Depends(get_session),
) -> McpServerRead:
    server = await _get_server(server_id, session)

    if data.name is not None:
        server.name = data.name
    if data.transport_type is not None:
        server.transport_type = data.transport_type
    if data.command is not None:
        server.command = data.command
    if data.url is not None:
        server.url = data.url
    if data.args is not None:
        server.args = json.dumps(data.args)
    if data.env_vars is not None:
        server.env_vars = json.dumps(data.env_vars)
    if data.is_enabled is not None:
        server.is_enabled = data.is_enabled

    # Validate the final state of the server
    _validate_transport_fields(server.transport_type, server.command, server.url)

    server.updated_at = datetime.now(UTC)
    session.add(server)
    await session.commit()
    await session.refresh(server)
    return _to_read(server)


@router.delete("/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mcp_server(
    server_id: int,
    session: AsyncSession = Depends(get_session),
) -> None:
    server = await _get_server(server_id, session)
    await session.delete(server)
    await session.commit()


@router.patch("/{server_id}/toggle", response_model=McpServerRead)
async def toggle_mcp_server(
    server_id: int,
    session: AsyncSession = Depends(get_session),
) -> McpServerRead:
    server = await _get_server(server_id, session)
    server.is_enabled = not server.is_enabled
    server.updated_at = datetime.now(UTC)
    session.add(server)
    await session.commit()
    await session.refresh(server)
    return _to_read(server)
