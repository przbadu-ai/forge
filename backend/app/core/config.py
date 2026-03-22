from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Forge"
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:3000", "http://0.0.0.0:3000"]
    database_url: str = "sqlite+aiosqlite:///./forge.db"

    # Authentication
    secret_key: str = "change-me-in-production-32-chars-min"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    admin_username: str = "admin"
    admin_password: str = "changeme"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
