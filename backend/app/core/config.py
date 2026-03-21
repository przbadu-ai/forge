from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Forge"
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:3000"]
    database_url: str = "sqlite+aiosqlite:///./forge.db"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
