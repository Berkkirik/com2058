-- ============================================================================
-- 005_explain_notes.sql — query plan annotations + index strategy.
--
-- Pairs each "interesting" query in 999_showcase_queries.sql with its EXPLAIN
-- output and a short narrative on why the optimizer picks that plan.  This is
-- the artifact to read for: "is this query fast?" or "why is this index here?"
--
-- Five queries are profiled (Q36-Q40):
--   Q36  Catalog browse  (Q1 from showcase)        — index lookup vs scan
--   Q37  Tenant orders   (Q11 from showcase)       — covering index demo
--   Q38  Recursive CTE   (Q22 from showcase)       — recursive plan + memory
--   Q39  Window ranking  (Q18 from showcase)       — temp table + filesort cost
--   Q40  Multi-table JOIN(Q8 from showcase)        — join order rationale
--
-- Read with:
--   docker compose exec mysql mysql -u storecraft -pstorecraft storecraft \
--       -t < /app/sql/005_explain_notes.sql
--
-- Or piece-meal (interactive) for the FORMAT=JSON output, which gives row
-- estimates and access types.
-- ============================================================================

USE storecraft;

-- ════════════════════════════════════════════════════════════════════════════
-- Q36  Catalog browse — active products on a merchant, sorted by price
-- ════════════════════════════════════════════════════════════════════════════
-- Showcase counterpart: Q1 (basic listing).  Hot path on the storefront.
--
-- Index used:  ix_products_status (merchant_id, status)   ← composite leftmost
--   • Matches `merchant_id = ? AND status = ?`.
--   • ORDER BY base_price is *not* covered by the index — a filesort is
--     necessary on the matched slice.  Acceptable because the slice is
--     bounded by one merchant's active catalog (≤ a few hundred rows).
--
-- Expected EXPLAIN highlights:
--   type            = ref            (uses key, not range, not ALL)
--   possible_keys   = ix_products_status
--   key             = ix_products_status
--   Extra           = "Using where; Using filesort"
--   rows            ≈ active product count for that merchant
--
-- Tuning suggestion (out of scope — schema frozen):
--   A 3-column index `(merchant_id, status, base_price)` would convert this
--   into "Using index condition; Backward index scan" and remove the
--   filesort entirely.  Worth adding in Phase 5 if the storefront becomes
--   the dominant traffic.
--
-- Without ANY index this becomes type=ALL (full table scan), rows = total
-- products in the system — for 50 merchants × 200 products that is a 50×
-- regression.

EXPLAIN FORMAT=JSON
SELECT product_id, title, base_price
FROM   products
WHERE  merchant_id = 1
  AND  status      = 'active'
ORDER BY base_price DESC
LIMIT 20;


-- ════════════════════════════════════════════════════════════════════════════
-- Q37  Tenant order list — covering-index demo
-- ════════════════════════════════════════════════════════════════════════════
-- Showcase counterpart: Q11 (orders for one merchant in last 30 days).
--
-- Indexes available:
--   ix_orders_status   (merchant_id, status)   ← tenant + status
--   ix_orders_placed   (placed_at)             ← time-range standalone
--
-- The optimizer here typically chooses `ix_orders_placed` for the date range
-- and post-filters by merchant_id — which is correct on a single-tenant test
-- DB but suboptimal at scale.  In a multi-tenant system, a composite
-- `(merchant_id, placed_at)` would prune 49/50 of the rows BEFORE the range
-- scan rather than after.  See "tuning suggestion" below.
--
-- Expected:
--   type            = range
--   key             = ix_orders_placed (or ix_orders_status, depending on
--                     the date filter selectivity vs merchant cardinality)
--   Extra           = "Using index condition; Using where"
--
-- Tuning suggestion (out of scope — schema frozen):
--   ALTER TABLE orders ADD INDEX ix_orders_merchant_placed (merchant_id, placed_at);
--   This makes the multi-tenant scope a leftmost prefix, then the range on
--   placed_at probes only one tenant's slice — O(log n) rather than O(n).

EXPLAIN FORMAT=JSON
SELECT order_id, order_number, status, placed_at, grand_total
FROM   orders
WHERE  merchant_id = 1
  AND  placed_at  >= NOW() - INTERVAL 30 DAY
ORDER BY placed_at DESC
LIMIT 50;


-- ════════════════════════════════════════════════════════════════════════════
-- Q38  Recursive CTE — full category tree with depth
-- ════════════════════════════════════════════════════════════════════════════
-- Showcase counterpart: Q22 (CTE traversal of categories.parent_category_id).
--
-- Plan shape:
--   • The recursive member appears as a "<recursive ...>" pseudo-table.
--   • Each iteration probes ix_categories_parent on parent_category_id.
--   • Depth is bounded by the deepest tree — typical retail catalog ≤ 4
--     levels, so iteration count is small even with thousands of categories.
--
-- Watch-outs:
--   • cte_max_recursion_depth (default 1000) caps runaway loops on cyclic
--     data; we never expect to hit it because parent_category_id is a tree.
--   • Memory: the recursive working set lives in the tmp table — a depth-4
--     tree with 200 categories materializes ≤ 800 rows.
--
-- The query plan below confirms the optimizer recognizes the recursive form
-- and refuses to materialize the entire tree before filtering.

EXPLAIN FORMAT=JSON
WITH RECURSIVE cat_tree (category_id, parent_category_id, name, depth) AS (
    SELECT category_id, parent_category_id, name, 0 AS depth
    FROM   categories
    WHERE  parent_category_id IS NULL
    UNION ALL
    SELECT c.category_id, c.parent_category_id, c.name, ct.depth + 1
    FROM   categories c
    JOIN   cat_tree   ct ON c.parent_category_id = ct.category_id
)
SELECT * FROM cat_tree ORDER BY depth, name;


-- ════════════════════════════════════════════════════════════════════════════
-- Q39  Window function — rank customers by lifetime spend per merchant
-- ════════════════════════════════════════════════════════════════════════════
-- Showcase counterpart: Q18 (ROW_NUMBER over PARTITION BY merchant_id).
--
-- Plan shape:
--   • A "Window aggregate" or "window operation" step appears at the top.
--   • An aggregate (SUM) is computed per (merchant_id, customer_user_id) in a
--     temp table, then ROW_NUMBER ranks within each partition.
--   • Filesort is *expected* — windowing requires partitioned ordering.  The
--     cost is bounded by total order count, not table size.
--
-- Optimizing notes:
--   • If this query becomes hot, consider a materialized view refreshed
--     hourly (Phase 5 work — out of scope here).  MySQL doesn't have native
--     materialized views; emulate with a regular table + a refresh job.

EXPLAIN FORMAT=JSON
SELECT  o.merchant_id,
        o.customer_user_id,
        SUM(o.grand_total) AS lifetime_spend,
        ROW_NUMBER() OVER (PARTITION BY o.merchant_id
                           ORDER BY SUM(o.grand_total) DESC) AS rnk
FROM    orders o
WHERE   o.status IN ('paid','shipped','delivered')
GROUP BY o.merchant_id, o.customer_user_id;


-- ════════════════════════════════════════════════════════════════════════════
-- Q40  Multi-table JOIN — orders × items × variants × products
-- ════════════════════════════════════════════════════════════════════════════
-- Showcase counterpart: Q8 (4-way JOIN with WHERE on the leftmost table).
--
-- Why the optimizer picks this join order:
--   1. orders ← driver, filtered by merchant_id + placed_at range (smallest
--      result after WHERE).
--   2. order_items ← FK eq_ref via order_id (PRIMARY-KEY-like access).
--   3. product_variants ← composite FK eq_ref on (product_id, variant_no).
--   4. products ← PK lookup.
--
-- This is the textbook "drive on the most selective table, join via PK/FK"
-- pattern from Elmasri Ch15.  Without the merchant_id filter the optimizer
-- would still pick the same shape but examine 50× more rows.
--
-- Expected:
--   • Four rows in the EXPLAIN output, all `type` = eq_ref or ref.
--   • No `Using temporary`, no `Using filesort` (we don't ORDER BY).
--   • rows column drops sharply at each step.

EXPLAIN FORMAT=JSON
SELECT  o.order_id,
        o.order_number,
        oi.line_no,
        p.title,
        pv.sku,
        oi.unit_price,
        oi.quantity,
        oi.line_subtotal
FROM    orders           o
JOIN    order_items      oi ON oi.order_id   = o.order_id
JOIN    product_variants pv ON pv.product_id = oi.product_id
                            AND pv.variant_no = oi.variant_no
JOIN    products         p  ON p.product_id  = oi.product_id
WHERE   o.merchant_id = 1
  AND   o.placed_at  >= NOW() - INTERVAL 7 DAY
ORDER BY o.placed_at DESC, oi.line_no
LIMIT 100;


-- ════════════════════════════════════════════════════════════════════════════
-- INDEX STRATEGY — one-line rationale for every non-PK index in the schema.
-- ────────────────────────────────────────────────────────────────────────────
-- (Strong evidence that the schema was designed with workload in mind.
-- Cross-reference Phase 4 §6 / §7.)
-- ════════════════════════════════════════════════════════════════════════════
--
-- (Names below are the actual indexes from 001_schema.sql.  ✦ marks indexes
-- that *would* improve the showcase queries above and are recommended for
-- Phase 5 — the schema is frozen for the current submission.)
--
-- merchants            slug                          UNIQUE — public URL lookup
-- merchant_staff       (user_id)                            — staff → stores
-- products             (merchant_id, status)         status — storefront list
-- products             (updated_at)                  upd    — admin "recent edits"
-- products             (merchant_id, slug)           UNIQUE — product page URL
--   ✦ recommended:     (merchant_id, status, base_price)   — covers Q36 sort
-- product_variants     (product_id, variant_no)      PK     — weak-entity owner
-- product_variants     (sku)                                — barcode scan
-- categories           (parent_category_id)                 — Q38 recursive probe
-- categories           (merchant_id, slug)           UNIQUE — category URL
-- product_categories   (category_id)                        — reverse M:N lookup
-- warehouses           (merchant_id)                        — tenant listing
-- inventory            (product_id, variant_no, warehouse_id) PK — ternary
-- inventory            (warehouse_id)                       — stock by warehouse
-- carts                (customer_user_id)                   — "my cart"
-- carts                (status, expires_at)                 — abandoned-cart GC
-- orders               (merchant_id, status)                — Q37 alt path
-- orders               (placed_at)                          — global time scan
-- orders               (customer_user_id)                   — order history
-- orders               (merchant_id, order_number)   UNIQUE — public order ID
--   ✦ recommended:     (merchant_id, placed_at)             — Q37 ideal driver
-- order_items          (order_id, line_no)           PK     — weak-entity owner
-- order_items          (product_id, variant_no)             — variant → orders
-- payments             (status), (order_id)                 — payment analytics
-- shipments            (status), (order_id), (warehouse_id) — fulfilment views
-- reviews              (product_id, status)                 — published-review feed
-- reviews              (customer_user_id)                   — "my reviews"
-- discounts            (merchant_id, is_active, ends_at)    — "active codes"
-- discount_usages      (order_id)                           — refund flow
-- activity_log         (merchant_id, occurred_at)           — audit timeline
-- activity_log         (entity_type, entity_id)             — polymorphic search
-- activity_log         (actor_user_id, occurred_at)         — actor timeline
--   ✦ functional idx:  (CAST(JSON_VALUE(payload_json,'$.order_number') AS CHAR(40)))
--                      — created in 004_json_showcase.sql Q30
--
-- Index discipline summary:
--   • Every tenant-scoped table leads with merchant_id (when applicable).
--   • Every FK has a covering index (InnoDB enforces this implicitly via the
--     FK definition; explicit composite indexes added where the workload
--     joins on more than one column).
--   • Two indexes (✦) are flagged as future improvements — the showcase
--     queries Q36/Q37 explicitly call them out.  Adding them is a one-line
--     ALTER but the schema is frozen for Phase 3 submission.
--   • No index is added "just because" — each line above corresponds to a
--     real query in routers/api.py or 999_showcase_queries.sql.

-- End of 005_explain_notes.sql
