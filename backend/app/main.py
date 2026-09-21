"""FastAPI application factory with lifespan, CORS, static files, and router registration."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_v1_router
from app.config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan – startup and shutdown hooks."""
    # Ensure storage directories exist on startup
    storage = Path(settings.storage_path)
    (storage / "logos").mkdir(parents=True, exist_ok=True)
    (storage / "exports").mkdir(parents=True, exist_ok=True)
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

    @application.get("/health", tags=["health"], summary="Health check")
    async def health_check() -> dict:
        return {"status": "ok", "version": "0.2.0"}

    return application


app = create_app()
