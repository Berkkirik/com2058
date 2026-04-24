"""Unified API error envelope + FastAPI exception handlers.

All error responses conform to:

    {"error": {"code": "SNAKE_CASE_CODE", "message": "...", "details": [...]}}

Usage:
    raise APIError("MERCHANT_NOT_FOUND", "merchant 'x' not found", status_code=404)

or for inline validation:
    raise APIError.bad_request("LIMIT_TOO_HIGH", "limit must be <= 100")

FastAPI's built-in HTTPException and Pydantic's RequestValidationError are both
remapped to the same envelope by the registered handlers.
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError

logger = logging.getLogger("storecraft.errors")


# ─── Error envelope ────────────────────────────────────────────────────────────


def envelope(
    code: str,
    message: str,
    details: list[Any] | None = None,
) -> dict[str, dict[str, Any]]:
    """Build the canonical error envelope body."""
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or [],
        }
    }


# ─── Exception class ───────────────────────────────────────────────────────────


class APIError(Exception):
    """Raise from any router to produce a consistent error envelope."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        status_code: int = 400,
        details: list[Any] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or []
        super().__init__(message)

    # Convenience constructors ------------------------------------------------
    @classmethod
    def not_found(cls, code: str, message: str) -> "APIError":
        return cls(code, message, status_code=404)

    @classmethod
    def bad_request(cls, code: str, message: str, details: list[Any] | None = None) -> "APIError":
        return cls(code, message, status_code=400, details=details)

    @classmethod
    def conflict(cls, code: str, message: str) -> "APIError":
        return cls(code, message, status_code=409)

    @classmethod
    def unauthorized(cls, code: str = "UNAUTHORIZED", message: str = "authentication required") -> "APIError":
        return cls(code, message, status_code=401)

    @classmethod
    def forbidden(cls, code: str = "FORBIDDEN", message: str = "insufficient permissions") -> "APIError":
        return cls(code, message, status_code=403)


# ─── Status code → code-string fallback ────────────────────────────────────────


_STATUS_CODE_MAP: dict[int, str] = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    422: "UNPROCESSABLE_ENTITY",
    429: "RATE_LIMITED",
    500: "INTERNAL_ERROR",
    503: "SERVICE_UNAVAILABLE",
}


def _code_for(status: int) -> str:
    return _STATUS_CODE_MAP.get(status, f"HTTP_{status}")


# ─── Handlers ──────────────────────────────────────────────────────────────────


async def _api_error_handler(_request: Request, exc: APIError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=envelope(exc.code, exc.message, exc.details),
    )


async def _http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    # Allow routers to still use HTTPException — we normalize it.
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content=envelope(_code_for(exc.status_code), detail or _code_for(exc.status_code).lower()),
    )


async def _validation_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    # Flatten Pydantic errors into the `details` array — never leak raw ValueError objects.
    details: list[dict[str, Any]] = []
    for err in exc.errors():
        details.append(
            {
                "loc": [str(p) for p in err.get("loc", [])],
                "msg": err.get("msg", ""),
                "type": err.get("type", ""),
            }
        )
    return JSONResponse(
        status_code=422,
        content=envelope("VALIDATION_ERROR", "request validation failed", details),
    )


async def _integrity_handler(_request: Request, exc: IntegrityError) -> JSONResponse:
    logger.warning("integrity_error: %s", exc.orig, exc_info=False)
    return JSONResponse(
        status_code=409,
        content=envelope("INTEGRITY_ERROR", "database integrity constraint violated"),
    )


async def _operational_handler(_request: Request, exc: OperationalError) -> JSONResponse:
    logger.error("operational_error: %s", exc.orig, exc_info=False)
    return JSONResponse(
        status_code=503,
        content=envelope("DB_UNAVAILABLE", "database temporarily unavailable"),
    )


async def _sqlalchemy_handler(_request: Request, exc: SQLAlchemyError) -> JSONResponse:
    logger.error("sqlalchemy_error: %s", exc, exc_info=False)
    return JSONResponse(
        status_code=500,
        content=envelope("DB_ERROR", "database error"),
    )


async def _unhandled_handler(_request: Request, exc: Exception) -> JSONResponse:
    # Never leak a stack trace to the client — log with traceback, return generic envelope.
    logger.exception("unhandled_exception: %s", exc)
    return JSONResponse(
        status_code=500,
        content=envelope("INTERNAL_ERROR", "internal server error"),
    )


# ─── Wiring ────────────────────────────────────────────────────────────────────


def register_exception_handlers(app: FastAPI) -> None:
    """Attach every handler — call once from main.create_app()."""
    app.add_exception_handler(APIError, _api_error_handler)
    app.add_exception_handler(HTTPException, _http_exception_handler)
    app.add_exception_handler(RequestValidationError, _validation_handler)
    app.add_exception_handler(IntegrityError, _integrity_handler)
    app.add_exception_handler(OperationalError, _operational_handler)
    app.add_exception_handler(SQLAlchemyError, _sqlalchemy_handler)
    app.add_exception_handler(Exception, _unhandled_handler)
