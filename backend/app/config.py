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

    @field_validator("app_env", mode="before")
    @classmethod
    def normalize_app_env(cls, value: str) -> str:
        """Normalize environment aliases (e.g. 'prod' -> 'production', 'dev' -> 'development')."""
        if isinstance(value, str):
            val = value.strip().lower()
            if val in ("prod", "production"):
                return "production"
            if val in ("dev", "development"):
                return "development"
            if val in ("stage", "staging", "test", "testing"):
                return "staging"
        return value
    frontend_url: str = "http://localhost"
    backend_url: str = "http://localhost/api"
    redirect_base_url: str = "http://localhost"  # base URL for dynamic QR redirects (e.g. https://qr.domain.com)
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
    mail_host: str = "mailpit"
    mail_port: int = 1025
    mail_from: str = "noreply@pointqr.dev"
    mail_username: str = ""
    mail_password: str = ""
    mail_tls: bool = False
    mail_ssl: bool = False

    # ---- Email verification -------------------------------------------------
    email_verification_required: bool = False

    # ---- Admin user (seeded on startup) -------------------------------------
    admin_email: str = "admin@pointqr.dev"
    admin_password: str = "ChangeMe!123"

    # ---- Registration -------------------------------------------------------
    registration_enabled: bool = True

    # ---- Cleanup / Storage Lifecycle ----------------------------------------
    # Number of days to keep completed/failed export files and their BatchJob rows.
    export_retention_days: int = 7
    # Grace period (days) before logo files are removed from soft-deleted QR codes.
    logo_orphan_grace_days: int = 7
    # Scan event retention per tier (days).  Set to -1 to keep events forever.
    scan_event_retention_days_free: int = 90
    scan_event_retention_days_pro: int = 365
    scan_event_retention_days_enterprise: int = 730
    # Jobs stuck in PENDING / PROCESSING longer than this are marked FAILED.
    stale_job_timeout_hours: int = 2

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS_ORIGINS comma-separated string into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
