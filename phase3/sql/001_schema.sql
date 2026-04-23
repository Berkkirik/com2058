-- ============================================================================
-- StoreCraft — Relational Schema (MySQL 8.0+, InnoDB, utf8mb4)
-- Mapped from Phase 2 ER diagram (17 entity types + 1 ternary relationship)
--
-- Mapping rules applied (Elmasri & Navathe 6e, Chapter 9):
--   Step 1  Regular entities            → one relation each with PK
--   Step 2  Weak entities                → compound PK (owner_PK + discriminator)
--   Step 3  1:1 total/partial            → FK on partial side (OWNER_OF)
--   Step 4  1:N                          → FK on N side
--   Step 5  M:N                          → bridge table with composite PK
--   Step 6  Multivalued attributes       → (none in this model)
--   Step 7  N-ary (ternary)              → bridge with 3-part composite PK  (INVENTORY)
--   Step 8  IS-A / specialization        → separate relation per subclass with owner FK
--
-- Naming: snake_case tables, singular or plural as per Phase 1 convention.
-- Every non-global table carries merchant_id for tenant isolation.
-- ============================================================================

SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;
SET time_zone = '+00:00';
SET foreign_key_checks = 0;

-- ----------------------------------------------------------------------------
-- ZONE 1 · IDENTITY  (USERS supertype + 3 subtypes)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS users (
    user_id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    email             VARCHAR(255)    NOT NULL,
    password_hash     VARCHAR(255)    NOT NULL,
    first_name        VARCHAR(100)    NOT NULL,
    last_name         VARCHAR(100)    NOT NULL,
    phone             VARCHAR(32)     NULL,
    is_active         TINYINT(1)      NOT NULL DEFAULT 1,
    created_at        DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id),
    UNIQUE KEY ux_users_email (email),
    INDEX ix_users_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- R1: USERS → CUSTOMER (IS_A, 1:1 partial/total)
CREATE TABLE IF NOT EXISTS customers (
    user_id                     BIGINT UNSIGNED NOT NULL,
    default_shipping_line1      VARCHAR(255)    NULL,
    default_shipping_line2      VARCHAR(255)    NULL,
    default_shipping_city       VARCHAR(100)    NULL,
    default_shipping_country    CHAR(2)         NULL,
    default_shipping_zip        VARCHAR(20)     NULL,
    date_of_birth               DATE            NULL,
    loyalty_points              INT UNSIGNED    NOT NULL DEFAULT 0,
    accepts_marketing           TINYINT(1)      NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id),
    CONSTRAINT fk_customers_user FOREIGN KEY (user_id)
        REFERENCES users (user_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- R2: USERS → STAFF (IS_A, 1:1 partial/total)
CREATE TABLE IF NOT EXISTS staff (
    user_id               BIGINT UNSIGNED NOT NULL,
    employment_type       ENUM('full_time','part_time','contractor') NOT NULL DEFAULT 'full_time',
    hired_at              DATE            NOT NULL,
    title                 VARCHAR(100)    NOT NULL,
    commission_rate       DECIMAL(5,4)    NOT NULL DEFAULT 0.0000,
    employment_status     ENUM('active','suspended','terminated') NOT NULL DEFAULT 'active',
    PRIMARY KEY (user_id),
    CONSTRAINT fk_staff_user FOREIGN KEY (user_id)
        REFERENCES users (user_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT ck_staff_commission CHECK (commission_rate >= 0 AND commission_rate <= 1)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- R3: USERS → PLATFORM_ADMIN (IS_A, 1:1 partial/total)
CREATE TABLE IF NOT EXISTS platform_admins (
    user_id        BIGINT UNSIGNED NOT NULL,
    admin_level    ENUM('support','moderator','superadmin') NOT NULL DEFAULT 'support',
    department     VARCHAR(80)     NOT NULL,
    hired_at       DATE            NOT NULL,
    PRIMARY KEY (user_id),
    CONSTRAINT fk_platform_admins_user FOREIGN KEY (user_id)
        REFERENCES users (user_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ----------------------------------------------------------------------------
-- ZONE 2 · TENANT ROOT + CATALOG
-- ----------------------------------------------------------------------------

-- R5 (OWNER_OF, 1:1 total): owner_user_id FK → staff
-- R4 (WORKS_FOR, M:N): via merchant_staff bridge
CREATE TABLE IF NOT EXISTS merchants (
    merchant_id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    slug                VARCHAR(80)     NOT NULL,
    store_name          VARCHAR(150)    NOT NULL,
    owner_user_id       BIGINT UNSIGNED NOT NULL,
    business_line1      VARCHAR(255)    NULL,
    business_line2      VARCHAR(255)    NULL,
    business_city       VARCHAR(100)    NULL,
    business_country    CHAR(2)         NULL,
    business_zip        VARCHAR(20)     NULL,
    contact_email       VARCHAR(255)    NOT NULL,
    currency            CHAR(3)         NOT NULL DEFAULT 'TRY',
    plan                ENUM('free','basic','pro','enterprise') NOT NULL DEFAULT 'basic',
    created_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    activated_at        DATETIME        NULL,
    suspended_at        DATETIME        NULL,
    PRIMARY KEY (merchant_id),
    UNIQUE KEY ux_merchants_slug (slug),
    CONSTRAINT fk_merchants_owner FOREIGN KEY (owner_user_id)
        REFERENCES staff (user_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    INDEX ix_merchants_plan (plan),
    INDEX ix_merchants_activated (activated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- R4: STAFF ⟷ MERCHANTS bridge (M:N, WORKS_FOR with {role} attribute)
CREATE TABLE IF NOT EXISTS merchant_staff (
    merchant_id   BIGINT UNSIGNED NOT NULL,
    user_id       BIGINT UNSIGNED NOT NULL,
    role          ENUM('owner','admin','staff','viewer') NOT NULL DEFAULT 'staff',
    joined_at     DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (merchant_id, user_id),
    CONSTRAINT fk_ms_merchant FOREIGN KEY (merchant_id)
        REFERENCES merchants (merchant_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_ms_user FOREIGN KEY (user_id)
        REFERENCES staff (user_id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX ix_ms_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- R6: MERCHANTS → PRODUCTS (1:N)
CREATE TABLE IF NOT EXISTS products (
    product_id      BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    merchant_id     BIGINT UNSIGNED NOT NULL,
    slug            VARCHAR(120)    NOT NULL,
    title           VARCHAR(255)    NOT NULL,
    product_type    ENUM('physical','digital','service') NOT NULL DEFAULT 'physical',
    base_price      DECIMAL(12,2)   NOT NULL,
    currency        CHAR(3)         NOT NULL DEFAULT 'TRY',
    status          ENUM('draft','active','archived') NOT NULL DEFAULT 'draft',
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (product_id),
    UNIQUE KEY ux_products_merchant_slug (merchant_id, slug),
    CONSTRAINT fk_products_merchant FOREIGN KEY (merchant_id)
        REFERENCES merchants (merchant_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT ck_products_price CHECK (base_price >= 0),
    INDEX ix_products_status (merchant_id, status),
    INDEX ix_products_updated (updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- R11: PRODUCTS → PRODUCT_VARIANTS (weak entity, compound PK)
CREATE TABLE IF NOT EXISTS product_variants (
    product_id       BIGINT UNSIGNED NOT NULL,
    variant_no       INT UNSIGNED    NOT NULL,
    sku              VARCHAR(80)     NOT NULL,
    option1_name     VARCHAR(40)     NOT NULL DEFAULT 'default',
    option1_value    VARCHAR(80)     NOT NULL DEFAULT 'default',
    price_override   DECIMAL(12,2)   NULL,
    barcode          VARCHAR(64)     NULL,
    is_default       TINYINT(1)      NOT NULL DEFAULT 0,
    PRIMARY KEY (product_id, variant_no),
    UNIQUE KEY ux_pv_sku (sku),
    CONSTRAINT fk_pv_product FOREIGN KEY (product_id)
        REFERENCES products (product_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT ck_pv_price CHECK (price_override IS NULL OR price_override >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- R7: MERCHANTS → CATEGORIES (1:N)  +  R9: CATEGORIES → CATEGORIES (recursive 1:N)
CREATE TABLE IF NOT EXISTS categories (
    category_id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    merchant_id           BIGINT UNSIGNED NOT NULL,
    parent_category_id    BIGINT UNSIGNED NULL,
    slug                  VARCHAR(120)    NOT NULL,
    name                  VARCHAR(150)    NOT NULL,
    display_order         INT             NOT NULL DEFAULT 0,
    created_at            DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (category_id),
    UNIQUE KEY ux_categories_merchant_slug (merchant_id, slug),
    CONSTRAINT fk_categories_merchant FOREIGN KEY (merchant_id)
        REFERENCES merchants (merchant_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_categories_parent FOREIGN KEY (parent_category_id)
        REFERENCES categories (category_id) ON DELETE SET NULL ON UPDATE CASCADE,
    INDEX ix_categories_parent (parent_category_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- R10: PRODUCTS ⟷ CATEGORIES (M:N bridge)
CREATE TABLE IF NOT EXISTS product_categories (
    product_id     BIGINT UNSIGNED NOT NULL,
    category_id    BIGINT UNSIGNED NOT NULL,
    assigned_at    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (product_id, category_id),
    CONSTRAINT fk_pc_product FOREIGN KEY (product_id)
        REFERENCES products (product_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_pc_category FOREIGN KEY (category_id)
        REFERENCES categories (category_id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX ix_pc_category (category_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ----------------------------------------------------------------------------
-- ZONE 3 · INVENTORY
-- ----------------------------------------------------------------------------

-- R8: MERCHANTS → WAREHOUSES (1:N)
CREATE TABLE IF NOT EXISTS warehouses (
    warehouse_id     BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    merchant_id      BIGINT UNSIGNED NOT NULL,
    name             VARCHAR(120)    NOT NULL,
    addr_line1       VARCHAR(255)    NOT NULL,
    addr_line2       VARCHAR(255)    NULL,
    addr_city        VARCHAR(100)    NOT NULL,
    addr_country     CHAR(2)         NOT NULL,
    addr_zip         VARCHAR(20)     NOT NULL,
    is_active        TINYINT(1)      NOT NULL DEFAULT 1,
    created_at       DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (warehouse_id),
    CONSTRAINT fk_warehouses_merchant FOREIGN KEY (merchant_id)
        REFERENCES merchants (merchant_id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX ix_warehouses_merchant_active (merchant_id, is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- R12: STOCKED_AT ternary (PRODUCTS × PRODUCT_VARIANTS × WAREHOUSES, M:N:N)
-- Mapping step 7: n-ary relationship → bridge table with composite PK of all 3 participants.
CREATE TABLE IF NOT EXISTS inventory (
    product_id       BIGINT UNSIGNED NOT NULL,
    variant_no       INT UNSIGNED    NOT NULL,
    warehouse_id     BIGINT UNSIGNED NOT NULL,
    qty_on_hand      INT             NOT NULL DEFAULT 0,
    qty_reserved     INT             NOT NULL DEFAULT 0,
    reorder_level    INT             NOT NULL DEFAULT 0,
    updated_at       DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (product_id, variant_no, warehouse_id),
    CONSTRAINT fk_inv_variant FOREIGN KEY (product_id, variant_no)
        REFERENCES product_variants (product_id, variant_no) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_inv_warehouse FOREIGN KEY (warehouse_id)
        REFERENCES warehouses (warehouse_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT ck_inv_nonneg CHECK (qty_on_hand >= 0 AND qty_reserved >= 0 AND reorder_level >= 0),
    CONSTRAINT ck_inv_reserved_le_onhand CHECK (qty_reserved <= qty_on_hand),
    INDEX ix_inv_warehouse (warehouse_id),
    INDEX ix_inv_low_stock (reorder_level, qty_on_hand)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ----------------------------------------------------------------------------
-- ZONE 4 · COMMERCE
-- ----------------------------------------------------------------------------

-- R13: MERCHANTS → CARTS (1:N)  +  R14: CUSTOMER → CARTS (1:N, 0..1 on cart)
CREATE TABLE IF NOT EXISTS carts (
    cart_id             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    merchant_id         BIGINT UNSIGNED NOT NULL,
    customer_user_id    BIGINT UNSIGNED NULL,    -- NULL = guest cart
    session_token       VARCHAR(64)     NOT NULL,
    currency            CHAR(3)         NOT NULL DEFAULT 'TRY',
    status              ENUM('active','abandoned','converted') NOT NULL DEFAULT 'active',
    expires_at          DATETIME        NOT NULL,
    created_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (cart_id),
    UNIQUE KEY ux_carts_session (merchant_id, session_token),
    CONSTRAINT fk_carts_merchant FOREIGN KEY (merchant_id)
        REFERENCES merchants (merchant_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_carts_customer FOREIGN KEY (customer_user_id)
        REFERENCES customers (user_id) ON DELETE SET NULL ON UPDATE CASCADE,
    INDEX ix_carts_status (merchant_id, status),
    INDEX ix_carts_customer (customer_user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- R15: CARTS ⟷ PRODUCT_VARIANTS (M:N bridge) with {quantity}
CREATE TABLE IF NOT EXISTS cart_items (
    cart_id       BIGINT UNSIGNED NOT NULL,
    product_id    BIGINT UNSIGNED NOT NULL,
    variant_no    INT UNSIGNED    NOT NULL,
    quantity      INT UNSIGNED    NOT NULL DEFAULT 1,
    added_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (cart_id, product_id, variant_no),
    CONSTRAINT fk_ci_cart FOREIGN KEY (cart_id)
        REFERENCES carts (cart_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_ci_variant FOREIGN KEY (product_id, variant_no)
        REFERENCES product_variants (product_id, variant_no) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT ck_ci_qty CHECK (quantity >= 1)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- R16: MERCHANTS → ORDERS (1:N)  +  R17: CUSTOMER → ORDERS (1:N total)
CREATE TABLE IF NOT EXISTS orders (
    order_id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    merchant_id         BIGINT UNSIGNED NOT NULL,
    customer_user_id    BIGINT UNSIGNED NOT NULL,
    order_number        VARCHAR(32)     NOT NULL,
    status              ENUM('pending','paid','fulfilled','canceled','refunded') NOT NULL DEFAULT 'pending',
    ship_line1          VARCHAR(255)    NOT NULL,
    ship_line2          VARCHAR(255)    NULL,
    ship_city           VARCHAR(100)    NOT NULL,
    ship_country        CHAR(2)         NOT NULL,
    ship_zip            VARCHAR(20)     NOT NULL,
    bill_line1          VARCHAR(255)    NOT NULL,
    bill_line2          VARCHAR(255)    NULL,
    bill_city           VARCHAR(100)    NOT NULL,
    bill_country        CHAR(2)         NOT NULL,
    bill_zip            VARCHAR(20)     NOT NULL,
    subtotal            DECIMAL(12,2)   NOT NULL,
    discount_total      DECIMAL(12,2)   NOT NULL DEFAULT 0.00,
    tax_total           DECIMAL(12,2)   NOT NULL DEFAULT 0.00,
    -- grand_total is derived: stored for reporting perf (MySQL generated column enforces consistency)
    grand_total         DECIMAL(12,2)   AS (subtotal - discount_total + tax_total) STORED,
    currency            CHAR(3)         NOT NULL DEFAULT 'TRY',
    placed_at           DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    canceled_at         DATETIME        NULL,
    PRIMARY KEY (order_id),
    UNIQUE KEY ux_orders_number (merchant_id, order_number),
    CONSTRAINT fk_orders_merchant FOREIGN KEY (merchant_id)
        REFERENCES merchants (merchant_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_orders_customer FOREIGN KEY (customer_user_id)
        REFERENCES customers (user_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT ck_orders_amounts CHECK (subtotal >= 0 AND discount_total >= 0 AND tax_total >= 0),
    INDEX ix_orders_status (merchant_id, status),
    INDEX ix_orders_placed (placed_at),
    INDEX ix_orders_customer (customer_user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- R18: ORDERS → ORDER_ITEMS (weak identifying, compound PK)
-- R19: PRODUCT_VARIANTS → ORDER_ITEMS (FK reference, snapshot preserves variant at time of sale)
CREATE TABLE IF NOT EXISTS order_items (
    order_id        BIGINT UNSIGNED NOT NULL,
    line_no         INT UNSIGNED    NOT NULL,
    product_id      BIGINT UNSIGNED NOT NULL,
    variant_no      INT UNSIGNED    NOT NULL,
    product_title   VARCHAR(255)    NOT NULL,   -- snapshot
    variant_label   VARCHAR(160)    NOT NULL,   -- snapshot
    sku             VARCHAR(80)     NOT NULL,
    unit_price      DECIMAL(12,2)   NOT NULL,
    quantity        INT UNSIGNED    NOT NULL,
    line_subtotal   DECIMAL(12,2)   AS (unit_price * quantity) STORED,
    PRIMARY KEY (order_id, line_no),
    CONSTRAINT fk_oi_order FOREIGN KEY (order_id)
        REFERENCES orders (order_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_oi_variant FOREIGN KEY (product_id, variant_no)
        REFERENCES product_variants (product_id, variant_no) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT ck_oi_amounts CHECK (unit_price >= 0 AND quantity >= 1),
    INDEX ix_oi_variant (product_id, variant_no)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- R20: ORDERS → PAYMENTS (1:N total)
CREATE TABLE IF NOT EXISTS payments (
    payment_id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    order_id             BIGINT UNSIGNED NOT NULL,
    merchant_id          BIGINT UNSIGNED NOT NULL,
    payment_method       ENUM('card','bank_transfer','cash_on_delivery','wallet') NOT NULL,
    amount               DECIMAL(12,2)   NOT NULL,
    currency             CHAR(3)         NOT NULL DEFAULT 'TRY',
    status               ENUM('initiated','authorized','captured','failed','refunded') NOT NULL DEFAULT 'initiated',
    gateway_reference    VARCHAR(120)    NULL,
    processed_at         DATETIME        NULL,
    created_at           DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (payment_id),
    CONSTRAINT fk_payments_order FOREIGN KEY (order_id)
        REFERENCES orders (order_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_payments_merchant FOREIGN KEY (merchant_id)
        REFERENCES merchants (merchant_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT ck_payments_amount CHECK (amount > 0),
    INDEX ix_payments_status (status),
    INDEX ix_payments_order (order_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- R21: ORDERS → SHIPMENTS (1:N total)  +  R22: WAREHOUSES → SHIPMENTS (1:N total)
CREATE TABLE IF NOT EXISTS shipments (
    shipment_id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    order_id            BIGINT UNSIGNED NOT NULL,
    merchant_id         BIGINT UNSIGNED NOT NULL,
    warehouse_id        BIGINT UNSIGNED NOT NULL,
    carrier             VARCHAR(80)     NOT NULL,
    tracking_number     VARCHAR(120)    NULL,
    status              ENUM('preparing','dispatched','in_transit','delivered','failed','returned') NOT NULL DEFAULT 'preparing',
    ship_line1          VARCHAR(255)    NOT NULL,
    ship_line2          VARCHAR(255)    NULL,
    ship_city           VARCHAR(100)    NOT NULL,
    ship_country        CHAR(2)         NOT NULL,
    ship_zip            VARCHAR(20)     NOT NULL,
    shipped_at          DATETIME        NULL,
    delivered_at        DATETIME        NULL,
    created_at          DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (shipment_id),
    CONSTRAINT fk_shipments_order FOREIGN KEY (order_id)
        REFERENCES orders (order_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_shipments_merchant FOREIGN KEY (merchant_id)
        REFERENCES merchants (merchant_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_shipments_warehouse FOREIGN KEY (warehouse_id)
        REFERENCES warehouses (warehouse_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    INDEX ix_shipments_status (status),
    INDEX ix_shipments_order (order_id),
    INDEX ix_shipments_warehouse (warehouse_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- ----------------------------------------------------------------------------
-- ZONE 5 · ENGAGEMENT + AUDIT
-- ----------------------------------------------------------------------------

-- R23: PRODUCTS ← REVIEWED_AS → REVIEWS ← WRITTEN_BY → CUSTOMER
CREATE TABLE IF NOT EXISTS reviews (
    review_id                BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    product_id               BIGINT UNSIGNED NOT NULL,
    customer_user_id         BIGINT UNSIGNED NOT NULL,
    merchant_id              BIGINT UNSIGNED NOT NULL,
    order_id                 BIGINT UNSIGNED NULL,
    rating                   TINYINT UNSIGNED NOT NULL,
    title                    VARCHAR(150)    NOT NULL,
    body                     TEXT            NOT NULL,
    is_verified_purchase     TINYINT(1)      NOT NULL DEFAULT 0,
    helpful_count            INT UNSIGNED    NOT NULL DEFAULT 0,
    status                   ENUM('pending','published','rejected') NOT NULL DEFAULT 'published',
    created_at               DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (review_id),
    CONSTRAINT fk_reviews_product FOREIGN KEY (product_id)
        REFERENCES products (product_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_reviews_customer FOREIGN KEY (customer_user_id)
        REFERENCES customers (user_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_reviews_merchant FOREIGN KEY (merchant_id)
        REFERENCES merchants (merchant_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_reviews_order FOREIGN KEY (order_id)
        REFERENCES orders (order_id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT ck_reviews_rating CHECK (rating BETWEEN 1 AND 5),
    INDEX ix_reviews_product (product_id, status),
    INDEX ix_reviews_customer (customer_user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- R24: DISCOUNTS ⟷ ORDERS (M:N via discount_usages)
CREATE TABLE IF NOT EXISTS discounts (
    discount_id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    merchant_id              BIGINT UNSIGNED NOT NULL,
    code                     VARCHAR(40)     NOT NULL,
    discount_type            ENUM('percentage','fixed_amount','free_shipping') NOT NULL,
    value                    DECIMAL(12,2)   NOT NULL,
    min_order_amount         DECIMAL(12,2)   NOT NULL DEFAULT 0.00,
    max_uses                 INT UNSIGNED    NULL,
    max_uses_per_customer    INT UNSIGNED    NULL,
    used_count               INT UNSIGNED    NOT NULL DEFAULT 0,
    starts_at                DATETIME        NOT NULL,
    ends_at                  DATETIME        NULL,
    is_active                TINYINT(1)      NOT NULL DEFAULT 1,
    created_by               BIGINT UNSIGNED NOT NULL,
    PRIMARY KEY (discount_id),
    UNIQUE KEY ux_discounts_code (merchant_id, code),
    CONSTRAINT fk_discounts_merchant FOREIGN KEY (merchant_id)
        REFERENCES merchants (merchant_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_discounts_staff FOREIGN KEY (created_by)
        REFERENCES staff (user_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT ck_discounts_value CHECK (value >= 0),
    CONSTRAINT ck_discounts_window CHECK (ends_at IS NULL OR ends_at > starts_at),
    INDEX ix_discounts_active (merchant_id, is_active, ends_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


CREATE TABLE IF NOT EXISTS discount_usages (
    discount_id     BIGINT UNSIGNED NOT NULL,
    order_id        BIGINT UNSIGNED NOT NULL,
    used_at         DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    amount_applied  DECIMAL(12,2)   NOT NULL,
    PRIMARY KEY (discount_id, order_id),
    CONSTRAINT fk_du_discount FOREIGN KEY (discount_id)
        REFERENCES discounts (discount_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_du_order FOREIGN KEY (order_id)
        REFERENCES orders (order_id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX ix_du_order (order_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- R25: USERS → ACTIVITY_LOG (1:N; partial/partial with system events)
-- Polymorphic association: entity_type + entity_id without an FK (single audit table design)
CREATE TABLE IF NOT EXISTS activity_log (
    event_id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    merchant_id       BIGINT UNSIGNED NOT NULL,
    actor_user_id     BIGINT UNSIGNED NULL,
    actor_type        ENUM('user','system','webhook','cron') NOT NULL DEFAULT 'user',
    entity_type       VARCHAR(40)     NOT NULL,
    entity_id         BIGINT UNSIGNED NOT NULL,
    action            VARCHAR(60)     NOT NULL,
    payload_json      JSON            NULL,
    ip_address        VARCHAR(45)     NULL,
    occurred_at       DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (event_id),
    CONSTRAINT fk_log_merchant FOREIGN KEY (merchant_id)
        REFERENCES merchants (merchant_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_log_user FOREIGN KEY (actor_user_id)
        REFERENCES users (user_id) ON DELETE SET NULL ON UPDATE CASCADE,
    INDEX ix_log_merchant_time (merchant_id, occurred_at),
    INDEX ix_log_entity (entity_type, entity_id),
    INDEX ix_log_actor (actor_user_id, occurred_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


SET foreign_key_checks = 1;

-- End of 001_schema.sql
