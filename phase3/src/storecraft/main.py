"""FastAPI application factory.

Currently wires only the health endpoint and static/template handlers;
feature routers are registered in follow-up iterations.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import text

from .config import STATIC_DIR, TEMPLATES_DIR, get_settings
from .db import engine

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Startup/shutdown hooks — verifies DB reachability at boot."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:  # pragma: no cover — surfaced in logs only
        print(f"[startup] DB not reachable yet: {exc}")
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="StoreCraft",
        description="Multi-tenant e-commerce platform · COM2058 Phase 3",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Static + templates
    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    # Register routers (lazy imports to avoid circularity at module load)
    from .routers import admin, api, catalog, dashboard, home, orders
    app.include_router(home.router)
    app.include_router(catalog.router)
    app.include_router(dashboard.router)
    app.include_router(orders.router)
    app.include_router(admin.router)
    app.include_router(api.router)

    @app.get("/health", tags=["meta"])
    def health() -> JSONResponse:
        """Liveness probe — checks DB connectivity too."""
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return JSONResponse({"status": "ok", "db": "up"})
        except Exception as exc:
            return JSONResponse({"status": "degraded", "db": "down", "error": str(exc)}, status_code=503)

    return app


app = create_app()
