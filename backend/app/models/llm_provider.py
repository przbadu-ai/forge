from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(UTC)


class LLMProvider(SQLModel, table=True):
    __tablename__ = "llm_provider"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True, max_length=100)
    base_url: str = Field(max_length=500)
    api_key_encrypted: str = Field(default="")
    models: str = Field(default="[]")  # JSON array as text
    is_default: bool = Field(default=False)
    created_at: datetime = Field(default_factory=_utcnow)
