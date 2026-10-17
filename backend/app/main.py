"""Sentinel Forge — FastAPI application factory."""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import analysis as analysis_router
from app.api import auth as auth_router
from app.core.config import settings
from app.services.database import Database


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application lifecycle: init DB on startup, dispose on shutdown."""
    db: Database = app.state.db
    db.create_tables()
    yield
    db.dispose()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Sentinel Forge",
        description="Static analysis toolkit for Claude Code mods (function hooks).",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

    # Store in app.state for dependency injection
    app.state.settings = settings
    app.state.db = Database(settings.database_url)

    app.include_router(analysis_router.router)
    app.include_router(auth_router.router)

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok", "service": "sentinel-forge"}

    return app


app = create_app()