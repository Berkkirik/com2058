"""FastAPI JSON API backend for StoreCraft.

Frontend is a separate React SPA (`phase3/frontend/`) served by Nginx in
production. During development the SPA hits this API at `/api/*` across
origins via CORS.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from .config import get_settings
from .db import engine

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Startup — verify DB reachability once at boot."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:  # pragma: no cover — boot-time only
        print(f"[startup] DB not reachable yet: {exc}")
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="StoreCraft API",
        description="Multi-tenant e-commerce platform · COM2058 Phase 3",
        version="0.2.0",
        lifespan=lifespan,
    )

    # CORS for the React dev server (Vite defaults to 5173) and production origin.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # dev-friendly; tighten in production deploy
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Only the JSON API router is registered — all HTML routers are gone.
    from .routers import api
    app.include_router(api.router)

    @app.get("/health", tags=["meta"])
    def health() -> JSONResponse:
        """Liveness + DB probe."""
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return JSONResponse({"status": "ok", "db": "up"})
        except Exception as exc:
            return JSONResponse({"status": "degraded", "db": "down", "error": str(exc)}, status_code=503)

    @app.get("/", tags=["meta"])
    def root() -> dict[str, str]:
        return {
            "name": "StoreCraft API",
            "version": "0.2.0",
            "docs": "/docs",
            "health": "/health",
            "frontend": "http://localhost:5173",
        }

    return app


app = create_app()
