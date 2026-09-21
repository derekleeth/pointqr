"""Application configuration loaded from environment variables via Pydantic Settings."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- Application --------------------------------------------------------
    app_env: Literal["development", "staging", "production"] = "development"
    app_debug: bool = False
    frontend_url: str = "http://localhost"
    backend_url: str = "http://localhost/api"
    cors_origins: str = "http://localhost,http://localhost:5173"

    # ---- Database -----------------------------------------------------------
    database_url: str = "postgresql+asyncpg://pointqr:pointqr_dev_password@postgres:5432/pointqr"

    # ---- Celery / RabbitMQ --------------------------------------------------
    celery_broker_url: str = "amqp://pointqr:pointqr_dev_password@rabbitmq:5672//"

    # ---- JWT ----------------------------------------------------------------
    secret_key: str = "CHANGE_ME_GENERATE_A_STRONG_SECRET_KEY_HERE"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # ---- Storage ------------------------------------------------------------
    storage_path: str = "/app/storage"

    # ---- Mail ---------------------------------------------------------------
    mail_host: str = "mailhog"
    mail_port: int = 1025
    mail_from: str = "noreply@pointqr.dev"

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS_ORIGINS comma-separated string into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
