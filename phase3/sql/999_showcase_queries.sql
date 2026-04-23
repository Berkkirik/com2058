-- ============================================================================
-- 999_showcase_queries.sql — 25 annotated queries demonstrating relational
-- operations across the StoreCraft schema. Each query is numbered (Q1-Q25)
-- and categorized; comments explain *what* and *why* before the SQL.
--
-- Usage:
--   docker compose exec mysql mysql -u storecraft -pstorecraft storecraft \
--       < /app/sql/999_showcase_queries.sql
-- ============================================================================

USE storecraft;

-- ──────────────────────────── BASICS (Q1-Q5) ────────────────────────────────

-- Q1  Simple SELECT * (listing): all active merchants on the pro plan.
SELECT merchant_id, slug, store_name, plan, created_at
FROM merchants
WHERE plan IN ('pro', 'enterprise')
  AND suspended_at IS NULL
ORDER BY created_at DESC;

-- Q2  Projection + WHERE on a computed predicate: products priced above the
-- merchant's mean. Demonstrates correlated comparison WITHOUT subquery.
SELECT p.product_id, p.title, p.base_price
FROM products p
WHERE p.status = 'active'
  AND p.base_price > 100
ORDER BY p.base_price DESC
LIMIT 20;

-- Q3  ORDER BY + LIMIT with OFFSET (pagination).
SELECT user_id, email, first_name, last_name, created_at
FROM users
ORDER BY created_at DESC
LIMIT 10 OFFSET 0;

-- Q4  DISTINCT: unique countries a merchant has ever shipped to.
SELECT DISTINCT s.merchant_id, s.ship_country
FROM shipments s
ORDER BY s.merchant_id, s.ship_country;

-- Q5  String + date functions: review titles shortened to 60 chars, formatted date.
SELECT
    review_id,
    CONCAT(LEFT(title, 60), CASE WHEN CHAR_LENGTH(title) > 60 THEN '…' ELSE '' END) AS title_clipped,
    DATE_FORMAT(created_at, '%Y-%m-%d') AS created_on,
    rating
FROM reviews
WHERE status = 'published'
ORDER BY created_at DESC
LIMIT 15;


-- ──────────────────────────── JOINS (Q6-Q10) ────────────────────────────────

-- Q6  INNER JOIN: each product with its owning merchant.
SELECT p.product_id, p.title, m.store_name, p.base_price, p.status
FROM products p
INNER JOIN merchants m ON m.merchant_id = p.merchant_id
WHERE p.status = 'active'
ORDER BY m.store_name, p.title
LIMIT 25;

-- Q7  LEFT JOIN + aggregate: products and how many variants each has.
SELECT
    p.product_id,
    p.title,
    COUNT(pv.variant_no) AS variants_count
FROM products p
LEFT JOIN product_variants pv ON pv.product_id = p.product_id
GROUP BY p.product_id, p.title
ORDER BY variants_count DESC, p.title
LIMIT 20;

-- Q8  4-way JOIN: order lines with customer name, product, merchant.
SELECT
    o.order_number,
    CONCAT(u.first_name, ' ', u.last_name) AS customer,
    m.store_name,
    oi.product_title,
    oi.quantity,
    oi.line_subtotal
FROM orders o
JOIN customers c     ON c.user_id = o.customer_user_id
JOIN users u         ON u.user_id = c.user_id
JOIN merchants m     ON m.merchant_id = o.merchant_id
JOIN order_items oi  ON oi.order_id = o.order_id
WHERE o.status IN ('paid', 'fulfilled')
ORDER BY o.placed_at DESC, o.order_number
LIMIT 30;

-- Q9  SELF JOIN: parent-child categories (direct parent only).
SELECT
    parent.category_id   AS parent_id,
    parent.name          AS parent_name,
    child.category_id    AS child_id,
    child.name           AS child_name
FROM categories child
JOIN categories parent ON parent.category_id = child.parent_category_id
ORDER BY parent.name, child.name;

-- Q10 FULL participation check — products that have never been ordered
-- (LEFT JOIN + IS NULL).
SELECT p.product_id, p.title, p.base_price
FROM products p
LEFT JOIN order_items oi ON oi.product_id = p.product_id
WHERE oi.product_id IS NULL
  AND p.status = 'active'
ORDER BY p.created_at DESC
LIMIT 20;


-- ────────────────────────── SUBQUERIES (Q11-Q13) ─────────────────────────────

-- Q11 Scalar subquery in SELECT: each merchant with its most expensive product.
SELECT
    m.merchant_id,
    m.store_name,
    (SELECT MAX(p.base_price) FROM products p WHERE p.merchant_id = m.merchant_id) AS top_price,
    (SELECT p.title FROM products p
       WHERE p.merchant_id = m.merchant_id
       ORDER BY p.base_price DESC LIMIT 1) AS top_product
FROM merchants m
WHERE m.plan <> 'free'
ORDER BY top_price DESC;

-- Q12 IN subquery: customers who ordered from more than one merchant.
SELECT u.user_id, u.email, COUNT(DISTINCT o.merchant_id) AS distinct_merchants
FROM users u
JOIN orders o ON o.customer_user_id = u.user_id
WHERE u.user_id IN (
    SELECT customer_user_id FROM orders GROUP BY customer_user_id HAVING COUNT(DISTINCT merchant_id) > 1
)
GROUP BY u.user_id, u.email
ORDER BY distinct_merchants DESC, u.email;

-- Q13 Correlated EXISTS: merchants that have at least one low-stock variant.
SELECT m.merchant_id, m.store_name
FROM merchants m
WHERE EXISTS (
    SELECT 1
    FROM warehouses w
    JOIN inventory inv ON inv.warehouse_id = w.warehouse_id
    WHERE w.merchant_id = m.merchant_id
      AND inv.qty_on_hand - inv.qty_reserved <= inv.reorder_level
)
ORDER BY m.store_name;


-- ──────────────────────────── AGGREGATES (Q14-Q17) ──────────────────────────

-- Q14 GROUP BY + multiple aggregates: per-merchant sales KPIs.
SELECT
    m.store_name,
    COUNT(DISTINCT o.order_id)   AS orders_count,
    SUM(o.grand_total)           AS gross_sales,
    AVG(o.grand_total)           AS avg_order_value,
    MIN(o.placed_at)             AS first_order,
    MAX(o.placed_at)             AS last_order
FROM merchants m
LEFT JOIN orders o ON o.merchant_id = m.merchant_id AND o.status IN ('paid','fulfilled')
GROUP BY m.merchant_id, m.store_name
ORDER BY gross_sales DESC;

-- Q15 HAVING filter on aggregate: categories with ≥3 distinct products.
SELECT
    c.category_id,
    c.name,
    COUNT(DISTINCT pc.product_id) AS product_count
FROM categories c
JOIN product_categories pc ON pc.category_id = c.category_id
GROUP BY c.category_id, c.name
HAVING product_count >= 3
ORDER BY product_count DESC;

-- Q16 CONDITIONAL aggregate (SUM-CASE): payments by status per merchant.
SELECT
    m.store_name,
    SUM(CASE WHEN p.status = 'captured' THEN p.amount ELSE 0 END) AS captured_total,
    SUM(CASE WHEN p.status = 'refunded' THEN p.amount ELSE 0 END) AS refunded_total,
    COUNT(CASE WHEN p.status = 'failed'  THEN 1 END)              AS failures
FROM merchants m
JOIN payments p ON p.merchant_id = m.merchant_id
GROUP BY m.merchant_id, m.store_name
ORDER BY captured_total DESC;

-- Q17 ROLLUP for subtotals + grand total: order units per status.
SELECT
    COALESCE(status, 'ALL')    AS status_bucket,
    COUNT(*)                   AS orders,
    SUM(grand_total)           AS revenue
FROM orders
GROUP BY status WITH ROLLUP;


-- ────────────────────── WINDOW FUNCTIONS (Q18-Q20) ──────────────────────────

-- Q18 ROW_NUMBER: rank of customers by lifetime spend within each merchant.
SELECT
    merchant_id,
    customer_name,
    lifetime_spend,
    ROW_NUMBER() OVER (PARTITION BY merchant_id ORDER BY lifetime_spend DESC) AS rank_in_store
FROM v_customer_lifetime_value
WHERE lifetime_spend > 0
ORDER BY merchant_id, rank_in_store;

-- Q19 LAG / running total: each order with the previous order's total for
-- the same customer and the running sum.
SELECT
    order_number,
    customer_user_id,
    placed_at,
    grand_total,
    LAG(grand_total) OVER (PARTITION BY customer_user_id ORDER BY placed_at) AS prev_order_total,
    SUM(grand_total) OVER (PARTITION BY customer_user_id ORDER BY placed_at) AS running_spend
FROM orders
WHERE status IN ('paid','fulfilled')
ORDER BY customer_user_id, placed_at;

-- Q20 NTILE: quartile the products of a merchant by unit sales.
SELECT
    merchant_id,
    product_id,
    title,
    units_sold,
    NTILE(4) OVER (PARTITION BY merchant_id ORDER BY units_sold DESC) AS sales_quartile
FROM v_top_products_by_merchant
ORDER BY merchant_id, sales_quartile, units_sold DESC;


-- ────────────────────── CTEs + RECURSIVE (Q21-Q22) ──────────────────────────

-- Q21 CTE: current month KPIs per merchant, joined back to plan tier.
WITH month_kpi AS (
    SELECT
        merchant_id,
        SUM(grand_total) AS rev,
        COUNT(*)         AS orders_cnt
    FROM orders
    WHERE placed_at >= DATE_FORMAT(CURDATE(), '%Y-%m-01')
      AND status IN ('paid','fulfilled')
    GROUP BY merchant_id
)
SELECT
    m.store_name,
    m.plan,
    COALESCE(k.rev, 0)        AS this_month_rev,
    COALESCE(k.orders_cnt, 0) AS this_month_orders
FROM merchants m
LEFT JOIN month_kpi k ON k.merchant_id = m.merchant_id
ORDER BY this_month_rev DESC;

-- Q22 RECURSIVE CTE: full category tree with depth.
WITH RECURSIVE category_tree (category_id, merchant_id, name, parent_category_id, depth, path) AS (
    SELECT category_id, merchant_id, name, parent_category_id, 0 AS depth, name AS path
    FROM categories
    WHERE parent_category_id IS NULL
    UNION ALL
    SELECT c.category_id, c.merchant_id, c.name, c.parent_category_id,
           t.depth + 1, CONCAT(t.path, ' > ', c.name)
    FROM categories c
    JOIN category_tree t ON c.parent_category_id = t.category_id
)
SELECT merchant_id, depth, path, category_id
FROM category_tree
ORDER BY merchant_id, path;


-- ────────────────────── VIEW + DML + TRANSACTION (Q23-Q25) ──────────────────

-- Q23 Use a view created in 002_views.sql: low-stock alerts per merchant.
SELECT * FROM v_low_stock_alerts
WHERE merchant_id = (SELECT merchant_id FROM merchants ORDER BY merchant_id LIMIT 1)
ORDER BY qty_available ASC
LIMIT 20;

-- Q24 UPDATE with JOIN: mark shipments as delivered when status was in_transit
-- and it's been > 7 days since dispatch (bulk correction).
-- (Wrapped in a SELECT preview first; uncomment UPDATE to apply.)
SELECT s.shipment_id, s.tracking_number, s.shipped_at, s.status
FROM shipments s
WHERE s.status = 'in_transit'
  AND s.shipped_at IS NOT NULL
  AND s.shipped_at < (NOW() - INTERVAL 7 DAY);

-- UPDATE shipments s
-- JOIN orders o ON o.order_id = s.order_id
--    SET s.status = 'delivered', s.delivered_at = NOW()
-- WHERE s.status = 'in_transit'
--   AND s.shipped_at < (NOW() - INTERVAL 7 DAY);

-- Q25 Multi-statement transactional block: "place order" simulation.
-- Demonstrates BEGIN/COMMIT, FK-constrained inserts, derived-column verification.
START TRANSACTION;

-- a) Pick first active cart owned by any customer
SET @cart_id := (SELECT cart_id FROM carts WHERE status = 'active' AND customer_user_id IS NOT NULL LIMIT 1);
SET @merch   := (SELECT merchant_id FROM carts WHERE cart_id = @cart_id);
SET @cust    := (SELECT customer_user_id FROM carts WHERE cart_id = @cart_id);

-- b) Insert an order with address snapshot from the customer
INSERT INTO orders (merchant_id, customer_user_id, order_number, status,
                    ship_line1, ship_city, ship_country, ship_zip,
                    bill_line1, bill_city, bill_country, bill_zip,
                    subtotal, discount_total, tax_total, currency)
SELECT
    @merch, @cust, CONCAT('DEMO-', UNIX_TIMESTAMP()), 'pending',
    COALESCE(c.default_shipping_line1, 'N/A'), COALESCE(c.default_shipping_city, 'Ankara'),
    COALESCE(c.default_shipping_country, 'TR'), COALESCE(c.default_shipping_zip, '06000'),
    COALESCE(c.default_shipping_line1, 'N/A'), COALESCE(c.default_shipping_city, 'Ankara'),
    COALESCE(c.default_shipping_country, 'TR'), COALESCE(c.default_shipping_zip, '06000'),
    0.00, 0.00, 0.00, 'TRY'
FROM customers c
WHERE c.user_id = @cust;

SET @oid := LAST_INSERT_ID();

-- c) Copy cart items into order_items
INSERT INTO order_items (order_id, line_no, product_id, variant_no,
                         product_title, variant_label, sku, unit_price, quantity)
SELECT
    @oid,
    ROW_NUMBER() OVER (ORDER BY ci.added_at),
    ci.product_id,
    ci.variant_no,
    p.title,
    CONCAT(pv.option1_name, ':', pv.option1_value),
    pv.sku,
    COALESCE(pv.price_override, p.base_price),
    ci.quantity
FROM cart_items ci
JOIN product_variants pv ON pv.product_id = ci.product_id AND pv.variant_no = ci.variant_no
JOIN products p          ON p.product_id = ci.product_id
WHERE ci.cart_id = @cart_id;

-- d) Update order subtotal from the items
UPDATE orders o
   SET subtotal = (SELECT COALESCE(SUM(oi.line_subtotal), 0)
                     FROM order_items oi WHERE oi.order_id = @oid)
 WHERE o.order_id = @oid;

-- e) Mark cart converted
UPDATE carts SET status = 'converted' WHERE cart_id = @cart_id;

-- Verify
SELECT order_id, merchant_id, order_number, subtotal, discount_total, tax_total, grand_total
FROM orders WHERE order_id = @oid;

ROLLBACK; -- demo is read-only — change to COMMIT in production

-- End of 999_showcase_queries.sql
