"""FastAPI JSON API backend for StoreCraft.

Frontend is a separate React SPA (`phase3/frontend/`) served by Nginx in
production. During development the SPA hits this API at `/api/*` across
origins via CORS.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from .config import get_settings
from .db import engine
from .errors import envelope, register_exception_handlers
from .logging_config import configure_logging
from .middleware import RequestContextMiddleware

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger("storecraft.main")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Startup — verify DB reachability once at boot."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("startup_db_ok")
    except SQLAlchemyError as exc:  # pragma: no cover — boot-time only
        logger.warning("startup_db_unreachable error=%s", exc)
    yield
    logger.info("shutdown")


def create_app() -> FastAPI:
    app = FastAPI(
        title="StoreCraft API",
        description="Multi-tenant e-commerce platform · COM2058 Phase 3",
        version="0.2.0",
        lifespan=lifespan,
    )

    # ─── Middleware (order matters: CORS outermost, then request-id) ───────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list(),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
        max_age=600,
    )
    app.add_middleware(RequestContextMiddleware)

    # ─── Unified error envelope across every raised exception ──────────────
    register_exception_handlers(app)

    # ─── Routers ───────────────────────────────────────────────────────────
    from .routers import api
    app.include_router(api.router)

    # ─── Meta endpoints ────────────────────────────────────────────────────
    @app.get("/healthz", tags=["meta"])
    def liveness() -> dict[str, str]:
        """Liveness probe — always 200 if the process can respond."""
        return {"status": "ok"}

    @app.get("/readyz", tags=["meta"])
    def readiness() -> JSONResponse:
        """Readiness probe — checks DB reachability."""
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return JSONResponse({"status": "ready", "db": "up"})
        except SQLAlchemyError as exc:
            logger.error("readyz_db_down error=%s", exc)
            return JSONResponse(
                status_code=503,
                content=envelope("DB_UNAVAILABLE", "database unreachable"),
            )

    @app.get("/health", tags=["meta"])
    def health() -> JSONResponse:
        """Legacy combined liveness + DB probe — kept for existing callers."""
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return JSONResponse({"status": "ok", "db": "up"})
        except SQLAlchemyError as exc:
            logger.error("health_db_down error=%s", exc)
            return JSONResponse(
                {"status": "degraded", "db": "down"},
                status_code=503,
            )

    @app.get("/", tags=["meta"])
    def root() -> dict[str, str]:
        return {
            "name": "StoreCraft API",
            "version": "0.2.0",
            "docs": "/docs",
            "health": "/healthz",
            "frontend": "http://localhost:5173",
        }

    return app


app = create_app()
