"""FastAPI application factory with lifespan, CORS, static files, and router registration."""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

from app.api.v1.redirect import router as redirect_router
from app.api.v1.router import api_v1_router
from app.config import get_settings
from app.core.security import hash_password, verify_password
from app.database import AsyncSessionLocal
from app.models.user import User, UserRole
from app.services.site_settings import KEY_REGISTRATION_ENABLED, get_setting, set_setting

logger = logging.getLogger(__name__)
settings = get_settings()


async def _seed_admin() -> None:
    """Create or synchronize the admin user from environment variables."""
    if not settings.admin_email or not settings.admin_password:
        logger.info("ADMIN_EMAIL or ADMIN_PASSWORD not configured; skipping admin seed.")
        return

    try:
        async with AsyncSessionLocal() as session:
            async with session.begin():
                result = await session.execute(
                    select(User).where(User.email == settings.admin_email)
                )
                user = result.scalar_one_or_none()

                if user is None:
                    admin = User(
                        email=settings.admin_email,
                        hashed_password=hash_password(settings.admin_password),
                        role=UserRole.admin,
                        is_active=True,
                        is_verified=True,
                    )
                    session.add(admin)
                    logger.info("Successfully created admin user: %s", settings.admin_email)
                else:
                    changed = False
                    if user.role != UserRole.admin:
                        user.role = UserRole.admin
                        changed = True
                    if not user.is_active:
                        user.is_active = True
                        changed = True
                    if not user.is_verified:
                        user.is_verified = True
                        changed = True
                    if not verify_password(settings.admin_password, user.hashed_password):
                        user.hashed_password = hash_password(settings.admin_password)
                        changed = True

                    if changed:
                        logger.info("Synchronized admin credentials/role for: %s", settings.admin_email)
                    else:
                        logger.info("Admin user already verified and up to date: %s", settings.admin_email)
    except Exception:
        logger.exception("Failed to seed admin user on startup")


async def _seed_site_settings() -> None:
    """Seed the site_settings table from .env on first startup only.

    If a row already exists (set via the admin UI) it is left untouched so
    that an admin-toggled value is never silently overwritten by a restart.
    """
    try:
        async with AsyncSessionLocal() as session:
            async with session.begin():
                env_default = "true" if settings.registration_enabled else "false"
                existing = await get_setting(
                    KEY_REGISTRATION_ENABLED, default="__missing__", db=session
                )
                if existing == "__missing__":
                    await set_setting(KEY_REGISTRATION_ENABLED, env_default, db=session)
                    logger.info(
                        "Seeded site setting %s=%s from .env",
                        KEY_REGISTRATION_ENABLED,
                        env_default,
                    )
    except Exception:
        logger.exception("Failed to seed site settings on startup")


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan – startup and shutdown hooks."""
    # Ensure storage directories exist on startup
    storage = Path(settings.storage_path)
    (storage / "logos").mkdir(parents=True, exist_ok=True)
    (storage / "exports").mkdir(parents=True, exist_ok=True)

    # Seed or synchronize the admin user
    await _seed_admin()

    # Initialise site settings from .env if not already in the DB
    await _seed_site_settings()

    yield
    # Shutdown: SQLAlchemy disposes connection pool automatically


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title="PointQR API",
        description="QR Code Generation Platform – REST API",
        version="0.2.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        root_path="/api",
        lifespan=lifespan,
    )

    # CORS middleware – allow the Vue frontend origin(s)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Static file serving for uploaded logos and generated exports
    # Served at /static/* from the shared Docker volume
    storage_path = Path(settings.storage_path)
    storage_path.mkdir(parents=True, exist_ok=True)
    application.mount(
        "/static",
        StaticFiles(directory=str(storage_path)),
        name="static",
    )

    # API routers – prefix="/v1" is already declared on api_v1_router itself
    application.include_router(api_v1_router)

    # Redirect service – mounted at app root so /r/{short_code} has no API prefix
    application.include_router(redirect_router)

    @application.get("/health", tags=["health"], summary="Health check")
    async def health_check() -> dict:
        return {"status": "ok", "version": "0.2.0"}

    return application


app = create_app()
