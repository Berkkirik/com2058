"""Showcase queries — Python API mirroring sql/999_showcase_queries.sql.

Each function corresponds to one of the 25 numbered queries. Callers receive
plain dicts (or SQLAlchemy rows) ready to feed into Jinja2 templates or return
as JSON.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


# ── BASICS ───────────────────────────────────────────────────────────────────

def q1_active_pro_merchants(session: Session) -> list[dict[str, Any]]:
    """Q1: simple SELECT — pro/enterprise merchants not suspended."""
    rows = session.execute(
        text(
            """
            SELECT merchant_id, slug, store_name, plan, created_at
            FROM merchants
            WHERE plan IN ('pro','enterprise') AND suspended_at IS NULL
            ORDER BY created_at DESC
            """
        )
    ).mappings().all()
    return [dict(r) for r in rows]


def q14_merchant_sales_kpi(session: Session) -> list[dict[str, Any]]:
    """Q14: GROUP BY + aggregates — per-merchant KPIs."""
    rows = session.execute(
        text(
            """
            SELECT
                m.merchant_id,
                m.store_name,
                COUNT(DISTINCT o.order_id) AS orders_count,
                COALESCE(SUM(o.grand_total), 0) AS gross_sales,
                COALESCE(AVG(o.grand_total), 0) AS avg_order_value,
                MIN(o.placed_at) AS first_order,
                MAX(o.placed_at) AS last_order
            FROM merchants m
            LEFT JOIN orders o
              ON o.merchant_id = m.merchant_id
             AND o.status IN ('paid','fulfilled')
            GROUP BY m.merchant_id, m.store_name
            ORDER BY gross_sales DESC
            """
        )
    ).mappings().all()
    return [dict(r) for r in rows]


def q18_top_customers_per_merchant(session: Session, merchant_id: int | None = None) -> list[dict[str, Any]]:
    """Q18: window function — ROW_NUMBER() per merchant."""
    sql = """
        SELECT merchant_id, customer_name, lifetime_spend,
               ROW_NUMBER() OVER (PARTITION BY merchant_id ORDER BY lifetime_spend DESC) AS rank_in_store
        FROM v_customer_lifetime_value
        WHERE lifetime_spend > 0
        { merchant_filter }
        ORDER BY merchant_id, rank_in_store
        LIMIT 50
    """
    mf = "AND merchant_id = :mid" if merchant_id else ""
    rows = session.execute(
        text(sql.replace("{ merchant_filter }", mf)),
        {"mid": merchant_id} if merchant_id else {},
    ).mappings().all()
    return [dict(r) for r in rows]


def q21_this_month_kpis(session: Session) -> list[dict[str, Any]]:
    """Q21: CTE — current-month KPIs per merchant with plan overlay."""
    rows = session.execute(
        text(
            """
            WITH month_kpi AS (
                SELECT merchant_id,
                       SUM(grand_total) AS rev,
                       COUNT(*) AS orders_cnt
                  FROM orders
                 WHERE placed_at >= DATE_FORMAT(CURDATE(), '%Y-%m-01')
                   AND status IN ('paid','fulfilled')
                GROUP BY merchant_id
            )
            SELECT m.merchant_id, m.store_name, m.plan,
                   COALESCE(k.rev, 0) AS this_month_rev,
                   COALESCE(k.orders_cnt, 0) AS this_month_orders
              FROM merchants m
              LEFT JOIN month_kpi k ON k.merchant_id = m.merchant_id
             ORDER BY this_month_rev DESC
            """
        )
    ).mappings().all()
    return [dict(r) for r in rows]


def q22_category_tree(session: Session, merchant_id: int) -> list[dict[str, Any]]:
    """Q22: recursive CTE for category tree."""
    rows = session.execute(
        text(
            """
            WITH RECURSIVE category_tree (category_id, merchant_id, name, parent_category_id, depth, path) AS (
                SELECT category_id, merchant_id, name, parent_category_id, 0, name
                  FROM categories
                 WHERE parent_category_id IS NULL AND merchant_id = :mid
                UNION ALL
                SELECT c.category_id, c.merchant_id, c.name, c.parent_category_id,
                       t.depth + 1, CONCAT(t.path, ' > ', c.name)
                  FROM categories c
                  JOIN category_tree t ON c.parent_category_id = t.category_id
            )
            SELECT category_id, depth, path
              FROM category_tree
             ORDER BY path
            """
        ),
        {"mid": merchant_id},
    ).mappings().all()
    return [dict(r) for r in rows]


def low_stock_alerts(session: Session, merchant_id: int) -> list[dict[str, Any]]:
    """Helper for dashboard — uses the v_low_stock_alerts view (Q23)."""
    rows = session.execute(
        text(
            """
            SELECT warehouse_name, product_id, sku,
                   qty_on_hand, qty_reserved, qty_available, reorder_level
              FROM v_low_stock_alerts
             WHERE merchant_id = :mid
             ORDER BY qty_available ASC
             LIMIT 20
            """
        ),
        {"mid": merchant_id},
    ).mappings().all()
    return [dict(r) for r in rows]


def top_products(session: Session, merchant_id: int, limit: int = 10) -> list[dict[str, Any]]:
    """Top products by unit sales using v_top_products_by_merchant view."""
    rows = session.execute(
        text(
            """
            SELECT product_id, title, units_sold, gross_revenue
              FROM v_top_products_by_merchant
             WHERE merchant_id = :mid
             ORDER BY units_sold DESC
             LIMIT :limit
            """
        ),
        {"mid": merchant_id, "limit": limit},
    ).mappings().all()
    return [dict(r) for r in rows]
