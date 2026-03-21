from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(UTC)


class UploadedFile(SQLModel, table=True):
    __tablename__ = "uploaded_file"

    id: int | None = Field(default=None, primary_key=True)
    filename: str = Field(max_length=255)  # stored name (UUID-based)
    original_name: str = Field(max_length=255)
    content_type: str = Field(max_length=100)
    size_bytes: int = Field(default=0)
    status: str = Field(default="pending", max_length=20)  # pending/processing/ready/failed
    chunk_count: int = Field(default=0)
    user_id: int = Field(foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=_utcnow)
