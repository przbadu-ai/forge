from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Conversation(SQLModel, table=True):
    __tablename__ = "conversation"

    id: int | None = Field(default=None, primary_key=True)
    title: str = Field(default="New Conversation", max_length=200)
    user_id: int = Field(foreign_key="user.id", index=True)
    system_prompt: str | None = Field(default=None)
    temperature: float | None = Field(default=None)
    max_tokens: int | None = Field(default=None)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
