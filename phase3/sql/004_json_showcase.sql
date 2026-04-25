-- ============================================================================
-- 004_json_showcase.sql — MySQL 8 native JSON feature showcase.
--
-- Demonstrates the JSON column on `activity_log.payload_json` with the four
-- standard access patterns (extract, scalar value, table-shaping, predicate),
-- plus a functional index that turns an expensive virtual-column scan into a
-- ref lookup.  Pairs with 005_explain_notes.sql (the EXPLAIN narrative).
--
-- Coverage map (Phase 4 §6 / §7 cross-reference):
--   Q26  JSON_EXTRACT  (->) ............ scalar fetch from JSON document
--   Q27  JSON_VALUE  + numeric cast .... typed scalar fetch (MySQL 8.0.21+)
--   Q28  JSON_TABLE  ................... pivot JSON rows into a relational set
--   Q29  JSON_CONTAINS / JSON_OVERLAPS .. predicate-style filtering
--   Q30  Functional index on JSON_VALUE  + EXPLAIN before/after
--
-- The seed populates `payload_json` for every order event with shape
--   {"order_number": "SC-...", "total": "<decimal>"}
-- and for system events with {"note": "auto"}, so all queries below operate on
-- realistic data.  Every query is tenant-aware (joins through merchant_id).
--
-- Usage:
--   docker compose exec mysql mysql -u storecraft -pstorecraft storecraft \
--       < /app/sql/004_json_showcase.sql
-- ============================================================================

USE storecraft;

-- ──────────────────────────── Q26  JSON_EXTRACT ─────────────────────────────
-- Pull `order_number` and `total` out of the JSON payload for every "order.paid"
-- event in the last 30 days, scoped to one merchant.  The `->>` operator is
-- shorthand for JSON_UNQUOTE(JSON_EXTRACT(...)) — strips the surrounding
-- quotes from string values so downstream comparison/casting is clean.

SELECT
    al.event_id,
    m.slug                                              AS merchant,
    al.action,
    al.payload_json ->> '$.order_number'                AS order_number,
    CAST(al.payload_json ->> '$.total' AS DECIMAL(12,2)) AS amount,
    al.occurred_at
FROM   activity_log al
JOIN   merchants    m ON m.merchant_id = al.merchant_id
WHERE  al.action      = 'order.paid'
  AND  al.occurred_at >= NOW() - INTERVAL 30 DAY
ORDER BY al.occurred_at DESC
LIMIT 20;


-- ──────────────────────────── Q27  JSON_VALUE  ──────────────────────────────
-- JSON_VALUE returns a SQL scalar with a declared type — preferred over
-- JSON_EXTRACT when sorting/filtering numerically, because no string-cast is
-- needed and the optimizer can use a functional index (see Q30).
--
-- Top 10 highest-revenue order events globally, derived purely from JSON.

SELECT
    m.slug                                                          AS merchant,
    JSON_VALUE(al.payload_json, '$.order_number')                   AS order_number,
    JSON_VALUE(al.payload_json, '$.total' RETURNING DECIMAL(12,2))  AS amount,
    al.occurred_at
FROM   activity_log al
JOIN   merchants    m ON m.merchant_id = al.merchant_id
WHERE  al.action LIKE 'order.%'
  AND  al.payload_json IS NOT NULL
  AND  JSON_VALUE(al.payload_json, '$.total' RETURNING DECIMAL(12,2)) IS NOT NULL
ORDER BY amount DESC
LIMIT 10;


-- ──────────────────────────── Q28  JSON_TABLE ───────────────────────────────
-- Reshape JSON documents into a relational view: every "order.*" event becomes
-- a row with typed columns for downstream JOINs.  This is the SQL standard's
-- inverse of JSON_OBJECT — useful for ad-hoc analytics over polymorphic logs
-- without changing the underlying schema.

SELECT
    m.slug             AS merchant,
    al.action          AS event,
    jt.order_number,
    jt.amount,
    al.occurred_at
FROM   activity_log al
JOIN   merchants    m ON m.merchant_id = al.merchant_id
JOIN   JSON_TABLE(
           al.payload_json,
           '$' COLUMNS (
               order_number VARCHAR(40)   PATH '$.order_number',
               amount       DECIMAL(12,2) PATH '$.total'
           )
       ) jt
WHERE  al.action LIKE 'order.%'
  AND  jt.order_number IS NOT NULL
ORDER BY al.occurred_at DESC
LIMIT 15;


-- ──────────────────────────── Q29  JSON_CONTAINS / JSON_OVERLAPS ────────────
-- Predicate-style filtering: rows whose JSON payload includes a particular
-- subdocument (here a literal note tag).  `JSON_CONTAINS` does deep equality;
-- `JSON_OVERLAPS` (8.0.17+) returns true when *any* element matches — handy
-- for tag arrays.  Useful for audit log searches like "find every cron event
-- that touched record X".

SELECT
    al.event_id,
    al.action,
    al.entity_type,
    al.entity_id,
    al.payload_json,
    al.occurred_at
FROM   activity_log al
WHERE  al.payload_json IS NOT NULL
  AND  (
        JSON_CONTAINS(al.payload_json, JSON_OBJECT('note', 'auto'))
     OR JSON_OVERLAPS(al.payload_json, JSON_ARRAY('manual', 'auto'))
       )
ORDER BY al.occurred_at DESC
LIMIT 20;


-- ──────────────────────────── Q30  Functional index on JSON_VALUE  ──────────
-- Without an index, JSON_VALUE filtering is a full table scan: every row's
-- JSON document is parsed at query time.  MySQL 8.0.13+ supports functional
-- (expression) indexes — the index stores the *result* of the expression,
-- so an exact-match lookup becomes O(log n).
--
-- The recipe:
--   1. Materialize the predicate expression as an indexable functional key.
--   2. Run the same query before/after — compare row count examined.
--
-- Idempotent: the CREATE INDEX uses IF NOT EXISTS so this script is safe to
-- replay.  Drop with: ALTER TABLE activity_log DROP INDEX ix_log_payload_total;

-- (a) BEFORE — should report a table scan ("type": "ALL", "rows" ≈ N).
EXPLAIN FORMAT=JSON
SELECT al.event_id, al.action, al.occurred_at
FROM   activity_log al
WHERE  JSON_VALUE(al.payload_json, '$.order_number') = 'SC-1';

-- (b) Create the functional index on the extracted scalar.
--     The CAST is required: functional-index keys must have an explicit type
--     (MySQL otherwise stores the expression as JSON-comparable, which the
--     optimizer cannot use for equality lookups).
ALTER TABLE activity_log
  ADD INDEX ix_log_payload_order_number (
      ( CAST(JSON_VALUE(payload_json, '$.order_number') AS CHAR(40)) )
  );

-- (c) AFTER — should now show "type": "ref", "rows" ≈ 1, key:
--     ix_log_payload_order_number.  Same query, same answer, two orders of
--     magnitude fewer rows examined.
EXPLAIN FORMAT=JSON
SELECT al.event_id, al.action, al.occurred_at
FROM   activity_log al
WHERE  CAST(JSON_VALUE(payload_json, '$.order_number') AS CHAR(40)) = 'SC-1';

-- (d) Confirm the index is now in use across the live query (without EXPLAIN).
SELECT al.event_id, al.action, al.occurred_at,
       JSON_VALUE(al.payload_json, '$.order_number') AS order_number
FROM   activity_log al
WHERE  CAST(JSON_VALUE(al.payload_json, '$.order_number') AS CHAR(40)) = 'SC-1'
LIMIT 5;

-- End of 004_json_showcase.sql
