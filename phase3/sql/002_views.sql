-- ============================================================================
-- 002_views.sql — reporting and analytics views.
-- These views are referenced by the FastAPI dashboard and by Q23 of the
-- showcase query library.
-- ============================================================================

-- v_merchant_revenue_monthly: per-merchant per-month revenue from captured
-- payments (fulfilled or in-flight orders count; refunds subtract).
CREATE OR REPLACE VIEW v_merchant_revenue_monthly AS
SELECT
    m.merchant_id,
    m.store_name,
    DATE_FORMAT(p.processed_at, '%Y-%m-01') AS month_start,
    SUM(CASE WHEN p.status = 'captured' THEN p.amount ELSE 0 END)
        - SUM(CASE WHEN p.status = 'refunded' THEN p.amount ELSE 0 END) AS net_revenue,
    COUNT(DISTINCT p.order_id) AS orders_count
FROM merchants m
JOIN payments p ON p.merchant_id = m.merchant_id
WHERE p.processed_at IS NOT NULL
GROUP BY m.merchant_id, m.store_name, month_start;


-- v_top_products_by_merchant: aggregates units sold and revenue per product.
CREATE OR REPLACE VIEW v_top_products_by_merchant AS
SELECT
    o.merchant_id,
    p.product_id,
    p.title,
    SUM(oi.quantity)       AS units_sold,
    SUM(oi.line_subtotal)  AS gross_revenue
FROM orders o
JOIN order_items oi ON oi.order_id = o.order_id
JOIN products p     ON p.product_id = oi.product_id
WHERE o.status IN ('paid', 'fulfilled')
GROUP BY o.merchant_id, p.product_id, p.title;


-- v_low_stock_alerts: inventory rows where available stock is at/below reorder.
CREATE OR REPLACE VIEW v_low_stock_alerts AS
SELECT
    w.merchant_id,
    w.warehouse_id,
    w.name                 AS warehouse_name,
    inv.product_id,
    inv.variant_no,
    pv.sku,
    inv.qty_on_hand,
    inv.qty_reserved,
    inv.qty_on_hand - inv.qty_reserved AS qty_available,
    inv.reorder_level
FROM inventory inv
JOIN warehouses w       ON w.warehouse_id = inv.warehouse_id
JOIN product_variants pv ON pv.product_id = inv.product_id AND pv.variant_no = inv.variant_no
WHERE (inv.qty_on_hand - inv.qty_reserved) <= inv.reorder_level;


-- v_customer_lifetime_value: sum of captured payments per customer per merchant.
CREATE OR REPLACE VIEW v_customer_lifetime_value AS
SELECT
    o.merchant_id,
    u.user_id,
    CONCAT(u.first_name, ' ', u.last_name) AS customer_name,
    COUNT(DISTINCT o.order_id)              AS orders_count,
    SUM(o.grand_total)                      AS lifetime_spend,
    MAX(o.placed_at)                        AS last_order_at
FROM orders o
JOIN users u ON u.user_id = o.customer_user_id
WHERE o.status IN ('paid', 'fulfilled')
GROUP BY o.merchant_id, u.user_id, customer_name;


-- v_recent_activity: last 7 days of actions with actor name resolved.
CREATE OR REPLACE VIEW v_recent_activity AS
SELECT
    a.event_id,
    a.merchant_id,
    a.actor_type,
    CASE
        WHEN a.actor_user_id IS NULL THEN CONCAT('system:', a.actor_type)
        ELSE CONCAT(u.first_name, ' ', u.last_name)
    END AS actor_label,
    a.entity_type,
    a.entity_id,
    a.action,
    a.occurred_at
FROM activity_log a
LEFT JOIN users u ON u.user_id = a.actor_user_id
WHERE a.occurred_at >= (NOW() - INTERVAL 7 DAY);

-- End of 002_views.sql
