from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Message(SQLModel, table=True):
    __tablename__ = "message"

    id: int | None = Field(default=None, primary_key=True)
    conversation_id: int = Field(foreign_key="conversation.id", index=True)
    role: str = Field(max_length=20)  # "user" | "assistant" | "system"
    content: str = Field(default="")
    trace_data: str | None = Field(default=None, sa_column_kwargs={"nullable": True})
    source_data: str | None = Field(default=None, sa_column_kwargs={"nullable": True})
    created_at: datetime = Field(default_factory=_utcnow)
