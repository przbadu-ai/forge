from sqlmodel import Field, SQLModel


class AppSettings(SQLModel, table=True):
    __tablename__ = "app_settings"

    id: int | None = Field(default=None, primary_key=True)
    system_prompt: str | None = Field(default=None)
    temperature: float = Field(default=0.7)
    max_tokens: int = Field(default=2048)

    # Embedding settings
    embedding_base_url: str | None = Field(default=None)
    embedding_model: str | None = Field(default=None)

    # Reranker settings
    reranker_base_url: str | None = Field(default=None)
    reranker_model: str | None = Field(default=None)
