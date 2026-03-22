"""Skill model — stores agent skill configuration (pre-seeded, enable/disable only)."""

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Skill(SQLModel, table=True):
    """Represents a pre-seeded agent skill that the LLM can invoke."""

    __tablename__ = "skill"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True, max_length=100)
    description: str = Field(max_length=500, default="")
    is_enabled: bool = Field(default=True)
    config: str | None = Field(default=None)  # JSON config, nullable
    content: str | None = Field(default=None)  # Full skill instructions/prompt
    source_path: str | None = Field(default=None)  # Filesystem path where skill was discovered
    created_at: datetime = Field(default_factory=_utcnow)
