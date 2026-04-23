"""Shared pytest fixtures.

Tests exercise the ORM against SQLite for portability; live-MySQL integration
is verified via docker compose + the seed script. MySQL-specific schema
features (Computed columns) are stripped from the ORM metadata at test time.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event, text

from storecraft.db import Base, engine, SessionLocal
from storecraft.main import create_app


@pytest.fixture(scope="session", autouse=True)
def _enable_sqlite_fks():
    if engine.url.get_backend_name() == "sqlite":
        @event.listens_for(engine, "connect")
        def _fk_on(dbapi_conn, _):
            cur = dbapi_conn.cursor()
            cur.execute("PRAGMA foreign_keys=ON")
            cur.close()


@pytest.fixture(scope="session")
def _schema():
    if engine.url.get_backend_name() == "sqlite":
        # Strip Computed columns (MySQL-only)
        for tbl, col in [("orders", "grand_total"), ("order_items", "line_subtotal")]:
            table = Base.metadata.tables[tbl]
            col_obj = table.c[col]
            col_obj.computed = None
        # Replace MySQL TINYINT(1) with generic Boolean/Integer for SQLite
        from sqlalchemy import Integer as SAInteger
        from sqlalchemy.dialects.mysql.types import TINYINT as MySQLTINYINT
        for table in Base.metadata.tables.values():
            for col in table.columns:
                if isinstance(col.type, MySQLTINYINT):
                    col.type = SAInteger()
    Base.metadata.create_all(engine)
    # Emit stub versions of the SQL views so dashboard/admin routes don't fail
    # in SQLite-backed tests. Production uses 002_views.sql applied by MySQL.
    if engine.url.get_backend_name() == "sqlite":
        with engine.begin() as conn:
            conn.execute(text("CREATE VIEW v_merchant_revenue_monthly AS SELECT 0 AS merchant_id, '' AS store_name, DATE('now') AS month_start, 0.0 AS net_revenue, 0 AS orders_count WHERE 1=0"))
            conn.execute(text("CREATE VIEW v_top_products_by_merchant AS SELECT 0 AS merchant_id, 0 AS product_id, '' AS title, 0 AS units_sold, 0.0 AS gross_revenue WHERE 1=0"))
            conn.execute(text("CREATE VIEW v_low_stock_alerts AS SELECT 0 AS merchant_id, 0 AS warehouse_id, '' AS warehouse_name, 0 AS product_id, 0 AS variant_no, '' AS sku, 0 AS qty_on_hand, 0 AS qty_reserved, 0 AS qty_available, 0 AS reorder_level WHERE 1=0"))
            conn.execute(text("CREATE VIEW v_customer_lifetime_value AS SELECT 0 AS merchant_id, 0 AS user_id, '' AS customer_name, 0 AS orders_count, 0.0 AS lifetime_spend, DATE('now') AS last_order_at WHERE 1=0"))
            conn.execute(text("CREATE VIEW v_recent_activity AS SELECT 0 AS event_id, 0 AS merchant_id, '' AS actor_type, '' AS actor_label, '' AS entity_type, 0 AS entity_id, '' AS action, DATE('now') AS occurred_at WHERE 1=0"))
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def db(_schema):
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        with engine.begin() as conn:
            for tbl in reversed(Base.metadata.sorted_tables):
                conn.execute(text(f"DELETE FROM {tbl.name}"))
        session.close()


@pytest.fixture
def client(_schema) -> TestClient:
    return TestClient(create_app())


def is_mysql() -> bool:
    return engine.url.get_backend_name() == "mysql"


mysql_only = pytest.mark.skipif(
    not is_mysql(),
    reason="Query uses MySQL-specific functions (DATE_FORMAT, WITH RECURSIVE, views populated by 002_views.sql) — runs in docker-compose integration suite.",
)
