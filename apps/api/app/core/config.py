from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="MR9_", extra="ignore")

    secret_key: str = "dev-only-change-me-please-use-bootstrap"
    database_url: str = "sqlite+pysqlite:////tmp/mr9-dev.db"
    cors_origins: str = "http://localhost:3000"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    access_token_minutes: int = 60
    refresh_token_days: int = 14
    genieacs_timeout_seconds: float = 15.0
    genieacs_max_concurrency: int = 12
    firmware_storage_dir: str = "/tmp/mr9-firmwares"
    environment: str = "development"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
