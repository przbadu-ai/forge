"""McpServer model — stores MCP server configuration for tool discovery."""

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(UTC)


class McpServer(SQLModel, table=True):
    """Represents a registered MCP server that provides tools."""

    __tablename__ = "mcp_server"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True, max_length=100)
    command: str = Field(max_length=500)  # e.g. "uvx" or "/usr/local/bin/mcp-server"
    args: str = Field(default="[]")  # JSON array: ["--flag", "value"]
    env_vars: str = Field(default="{}")  # JSON object: {"KEY": "VALUE"}
    is_enabled: bool = Field(default=True)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
