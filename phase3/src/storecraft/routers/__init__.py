"""FastAPI routers. JSON-only: only `api` is registered (HTML routers removed)."""

from . import api

__all__ = ["api"]
