"""FastAPI routers. Registered in storecraft.main via include_router calls."""

from . import admin, api, catalog, dashboard, home, orders

__all__ = ["admin", "api", "catalog", "dashboard", "home", "orders"]
