"""ASGI middleware: request-id tagging + structured access log.

Every request gets a UUID4 request-id (or the incoming `X-Request-ID` header
if the caller provides one), echoed back on the response. Each response is
logged as one key=value line with method, path, status, duration_ms, request-id.

NOTE: Rate limiting belongs here too — kept as a placeholder comment below so
the extension point is obvious.
"""
from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("storecraft.access")

REQUEST_ID_HEADER = "X-Request-ID"


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach `request.state.request_id`, emit access log, echo header."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        incoming = request.headers.get(REQUEST_ID_HEADER)
        request_id = incoming if incoming and len(incoming) <= 64 else uuid.uuid4().hex
        request.state.request_id = request_id

        # ─── rate limiting extension point ──────────────────────────────
        # A production deployment would slot a token-bucket / leaky-bucket
        # check here, keyed by client_ip or authenticated user. See
        # `slowapi` or `starlette-limiter` for off-the-shelf options.

        start = time.perf_counter()
        status_code = 500
        response: Response | None = None
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration_ms = (time.perf_counter() - start) * 1000.0
            extras: dict[str, Any] = {
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status": status_code,
                "duration_ms": f"{duration_ms:.1f}",
                "client": request.client.host if request.client else "-",
            }
            logger.info("http_request", extra=extras)
            if response is not None:
                response.headers[REQUEST_ID_HEADER] = request_id
