# COM2058 Project — Phase 1: Data Requirements

**Project:** StoreCraft — Multi-Tenant E-Commerce Platform SaaS
**Course:** COM2058 Database Management Systems, Ankara University
**Authors:** 
- Berk KIRIK -25812633 
- Atahan YILDIRIM -23291292 
- Melih Ozulu -21290142


---

## 1. Overview

StoreCraft is a multi-tenant SaaS platform  that lets independent merchants launch online stores. Each merchant (tenant) maintains its own catalog, customer base, orders, and inventory; data is isolated at the schema level. End-users are modeled globally via three binary **IS_A** (1:1) subtype relationships so one person can shop across many merchant stores with a single identity.

### 1.1 Scope of the Conceptual Design 
The conceptual data model presented in this document and refined in the Phase 2 ER diagram covers the full operational lifecycle of a multi-tenant e-commerce platform. The functional domains in scope are formalised as follows:

1. **Catalog management.** Products, product variants (modelled as a weak entity dependent on its parent product), and a recursive category hierarchy under each merchant.
2. **Warehouse and inventory control.** Per-merchant warehouses and stock levels modelled as a genuine ternary relationship `STOCKED_AT(PRODUCTS × PRODUCT_VARIANTS × WAREHOUSES)`, with derived availability quantities.
3. **Shopping workflow.** Customer shopping carts (including guest carts), finalised orders, and order line items (modelled as a second weak entity dependent on its order).
4. **Order fulfilment.** Payments and shipments associated with each order, with one-to-many cardinality on both legs to permit partial captures and split fulfilment.
5. **Customer engagement.** Product reviews authored by customers and merchant-issued discount codes redeemable on orders.
6. **Auditability.** An append-only activity log implementing a polymorphic association over the auditable entity set.

### Entity count
**17 entity types** in the ER diagram (4 Identity + 4 Tenant/Catalog + 1 Warehouses + 5 Commerce + 3 Engagement). **INVENTORY** -> **ternary relationship** `STOCKED_AT(PRODUCTS × PRODUCT_VARIANTS × WAREHOUSES)` with attributes, not a standalone entity. During Phase 3 relational mapping, the ternary becomes its own bridge table — yielding 18 total tables. Additional bridge tables (`merchant_staff`, `product_categories`, `cart_items`, `discount_usages`) also emerge then.

---

## 2. Tenant & Identity Model

### Tenancy
- **Tenant root:** `MERCHANTS` — each row = one store owner / shop
- **Tenant-scoped:** every catalog/commerce/inventory/audit table carries `merchant_id`
- **Tenant-free (global):** `USERS` and its three subtype entities (CUSTOMER, STAFF, PLATFORM_ADMIN)

### USERS subtypes — modelled as IS_A 
- **Subtypes:** CUSTOMER, STAFF, PLATFORM_ADMIN (3 separate entities)
- **Subtype rows may coexist:** one `USERS` row may simultaneously have a CUSTOMER row *and* a STAFF row (e.g., a merchant owner who also shops on other stores).
- **Subtype rows are optional:** a freshly-registered user may have no subtype row at all.
- **Notation:**  — three binary 1:1 `IS_A` relationships. The EER `◯d/◯o` specialization circle from Ch08 is **not** used.
  ```
   USERS ──(0,1)── IS_A_CUST  ──(1,1)── CUSTOMER
   USERS ──(0,1)── IS_A_STAFF ──(1,1)── STAFF
   USERS ──(0,1)── IS_A_PA    ──(1,1)── PLATFORM_ADMIN
  ```

### Staff roles
Stored as a plain string on the `merchant_staff` bridge (4 values): `owner`, `admin`, `staff`, `viewer`. RBAC/permission tables deferred to Phase 4+.

---

## 3. Entity Attribute Dictionary

### Group 1 — Identity (4 entities)

#### 3.1 USERS (base entity)
Shared attributes every authenticated person carries. The three IS_A subtypes (CUSTOMER, STAFF, PLATFORM_ADMIN) reference this row.

| Attribute | Type | Key / Null | Notes |
|---|---|---|---|
| `user_id` | BIGINT | **PK** | Surrogate, auto-increment |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL | Login credential |
| `password_hash` | VARCHAR(255) | NOT NULL | Argon2id or bcrypt |
| `first_name` | VARCHAR(80) | NOT NULL | |
| `last_name` | VARCHAR(80) | NOT NULL | |
| `phone` | VARCHAR(20) | NULL | E.164 format |
| `email_verified_at` | DATETIME | NULL | Non-null = verified |
| `is_active` | BOOLEAN | NOT NULL, default TRUE | Soft-disable flag |
| `last_login_at` | DATETIME | NULL | |
| `created_at` | DATETIME | NOT NULL | |
| `updated_at` | DATETIME | NOT NULL | |

#### 3.2 CUSTOMER (IS_A subtype of USERS)
Subtype of USERS via the IS_A_CUST relationship — users who shop on any merchant's store.

| Attribute | Type | Key / Null | Notes |
|---|---|---|---|
| `user_id` | BIGINT | **PK, FK → USERS** | Shared PK — IS_A subtype reference |
| `default_shipping_address` | **COMPOSITE** | NULL | `{street, city, state, postal_code, country}`  |
| `date_of_birth` | DATE | NULL | |
| `loyalty_points` | INT | NOT NULL, default 0 | Across all merchants (global balance) |
| `accepts_marketing` | BOOLEAN | NOT NULL, default FALSE | Global opt-in |
| `referral_code` | VARCHAR(20) | UNIQUE, NULL | |

#### 3.3 STAFF (IS_A subtype of USERS)
Subtype of USERS via the IS_A_STAFF relationship — users employed at one or more merchants.

| Attribute | Type | Key / Null | Notes |
|---|---|---|---|
| `user_id` | BIGINT | **PK, FK → USERS** | Shared PK — IS_A subtype reference |
| `employment_type` | VARCHAR(20) | NOT NULL | `full_time` / `part_time` / `contractor` |
| `hired_at` | DATETIME | NOT NULL | First-employment date across StoreCraft |
| `title` | VARCHAR(80) | NOT NULL | e.g. "Store Manager", "Sales Assistant" |
| `commission_rate` | DECIMAL(5,2) | NULL | % of sales; null if salaried |
| `employment_status` | VARCHAR(20) | NOT NULL | `active` / `on_leave` / `terminated` |

#### 3.4 PLATFORM_ADMIN (IS_A subtype of USERS)
Subtype of USERS via the IS_A_PA relationship — StoreCraft platform employees (our own team).

| Attribute | Type | Key / Null | Notes |
|---|---|---|---|
| `user_id` | BIGINT | **PK, FK → USERS** | Shared PK — IS_A subtype reference |
| `admin_level` | VARCHAR(20) | NOT NULL | `super_admin` / `support` / `engineer` / `billing` |
| `department` | VARCHAR(50) | NOT NULL | e.g. "Customer Success", "Trust & Safety" |
| `hired_at` | DATETIME | NOT NULL | |

### Group 2 — Tenant + Catalog (4 entities)

#### 3.5 MERCHANTS (tenant root)
One row = one store = one tenant. All catalog/commerce data below carries `merchant_id`.

| Attribute | Type | Key / Null | Notes |
|---|---|---|---|
| `merchant_id` | BIGINT | **PK** | Tenant identifier |
| `slug` | VARCHAR(64) | UNIQUE, NOT NULL | URL slug (`storecraft.com/{slug}`) |
| `store_name` | VARCHAR(120) | NOT NULL | Public display name |
| `owner_user_id` | BIGINT | FK → STAFF, NOT NULL | Founding staff (owner) |
| `business_address` | **COMPOSITE** | NOT NULL | `{street, city, state, postal_code, country}` — |
| `contact_email` | VARCHAR(255) | NOT NULL | Support email |
| `currency` | CHAR(3) | NOT NULL | ISO 4217 (USD, TRY, EUR) |
| `plan` | VARCHAR(20) | NOT NULL | `starter` / `growth` / `enterprise` |
| `created_at` | DATETIME | NOT NULL | |
| `activated_at` | DATETIME | NULL | When plan payment confirmed |
| `suspended_at` | DATETIME | NULL | Non-null = suspended |

#### 3.6 PRODUCTS

| Attribute | Type | Key / Null | Notes |
|---|---|---|---|
| `product_id` | BIGINT | **PK** | |
| `merchant_id` | BIGINT | FK → MERCHANTS, NOT NULL | Tenant anchor |
| `slug` | VARCHAR(120) | NOT NULL | UNIQUE `(merchant_id, slug)` |
| `title` | VARCHAR(255) | NOT NULL | |
| `description` | TEXT | NULL | |
| `product_type` | VARCHAR(20) | NOT NULL | Enum kept as plain attribute: `physical` / `digital` / `subscription` (no subtype entities in Phase 2) |
| `base_price` | DECIMAL(12,2) | NOT NULL | Variants may override |
| `currency` | CHAR(3) | NOT NULL | |
| `status` | VARCHAR(20) | NOT NULL | `draft` / `active` / `archived` |
| `created_at` | DATETIME | NOT NULL | |
| `updated_at` | DATETIME | NOT NULL | |

#### 3.7 PRODUCT_VARIANTS (weak entity)
No standalone identity — a variant only exists under a product.

| Attribute | Type | Key / Null | Notes |
|---|---|---|---|
| `product_id` | BIGINT | **PK (part), FK → PRODUCTS** | Identifying relationship |
| `variant_no` | INT | **PK (part)** | **Partial key** — sequenced within a product |
| `sku` | VARCHAR(40) | UNIQUE `(merchant_id, sku)`, NOT NULL | Stock-keeping unit |
| `option1_name` | VARCHAR(40) | NULL | e.g. "Color" |
| `option1_value` | VARCHAR(40) | NULL | e.g. "Red" |
| `option2_name` | VARCHAR(40) | NULL | e.g. "Size" |
| `option2_value` | VARCHAR(40) | NULL | e.g. "L" |
| `price_override` | DECIMAL(12,2) | NULL | NULL = use product.base_price |
| `barcode` | VARCHAR(64) | NULL | EAN / UPC |
| `is_default` | BOOLEAN | NOT NULL, default FALSE | Default variant flag |

**Weak entity semantics:** Compound PK `(product_id, variant_no)`; 

#### 3.8 CATEGORIES (recursive hierarchy)

| Attribute | Type | Key / Null | Notes |
|---|---|---|---|
| `category_id` | BIGINT | **PK** | |
| `merchant_id` | BIGINT | FK → MERCHANTS, NOT NULL | Tenant anchor |
| `parent_category_id` | BIGINT | FK → CATEGORIES, NULL | **Recursive self-FK** |
| `slug` | VARCHAR(80) | NOT NULL | UNIQUE `(merchant_id, slug)` |
| `name` | VARCHAR(120) | NOT NULL | |
| `display_order` | SMALLINT | NOT NULL, default 0 | Sibling ordering |
| `created_at` | DATETIME | NOT NULL | |

**Recursive relationship:** `parent_category_id → category_id` creates a tree (e.g., Electronics → Phones → Smartphones).

### Group 3 — Inventory (1 entity + 1 ternary relationship)

#### 3.9 WAREHOUSES
Physical storage locations. Each warehouse belongs to one merchant.

| Attribute | Type | Key / Null | Notes |
|---|---|---|---|
| `warehouse_id` | BIGINT | **PK** | |
| `merchant_id` | BIGINT | FK → MERCHANTS, NOT NULL | Tenant anchor |
| `name` | VARCHAR(80) | NOT NULL | e.g., "Ankara Main Warehouse" |
| `address` | **COMPOSITE** | NOT NULL | `{street, city, state, postal_code, country}` |
| `is_active` | BOOLEAN | NOT NULL, default TRUE | Operational flag |
| `created_at` | DATETIME | NOT NULL | |

#### 3.10 INVENTORY (ternary relationship: PRODUCT × VARIANT × WAREHOUSE)
Genuine ternary — quantity is defined only by the triple of (product, variant, warehouse). Binary decomposition loses information.

| Attribute | Type | Key / Null | Notes |
|---|---|---|---|
| `product_id` | BIGINT | **PK (part), FK → PRODUCTS** | Ternary participant 1 |
| `variant_no` | INT | **PK (part), FK → PRODUCT_VARIANTS** (composite) | Ternary participant 2 |
| `warehouse_id` | BIGINT | **PK (part), FK → WAREHOUSES** | Ternary participant 3 |
| `merchant_id` | BIGINT | FK → MERCHANTS, NOT NULL | Tenant anchor (composite-FK enforcement) |
| `quantity_on_hand` | INT | NOT NULL, default 0 | Physical stock |
| `quantity_reserved` | INT | NOT NULL, default 0 | Reserved by carts/orders |
| `quantity_available` | INT | **DERIVED** | `= on_hand − reserved`  |
| `reorder_level` | INT | NULL | Low-stock threshold |
| `last_restocked_at` | DATETIME | NULL | |
| `updated_at` | DATETIME | NOT NULL | |

**Compound PK:** `(product_id, variant_no, warehouse_id)`.

```
    PRODUCTS           VARIANTS            WAREHOUSES
        \                  |                  /
         \                 |                 /
          \________◇ STOCKED_AT ◇___________/
                  {qty_on_hand, qty_reserved, reorder_level}
```

**Why genuine ternary (vs. binary decomposition):** a binary `variant⟷warehouse` paired with `variant⟷product` cannot express "variant X in warehouse Y has N units" — the count depends on all three. This argument is expanded in the Phase 4 report.

### Group 4 — Commerce (5 entities)

#### 3.11 CARTS
Active shopping carts. A cart lives under one merchant's storefront.

| Attribute | Type | Key / Null | Notes |
|---|---|---|---|
| `cart_id` | BIGINT | **PK** | |
| `merchant_id` | BIGINT | FK → MERCHANTS, NOT NULL | Tenant anchor |
| `customer_user_id` | BIGINT | FK → CUSTOMER, NULL | NULL for guest carts |
| `session_token` | VARCHAR(64) | NULL | Guest-cart identifier |
| `currency` | CHAR(3) | NOT NULL | Frozen at cart creation |
| `status` | VARCHAR(20) | NOT NULL | `active` / `abandoned` / `converted` |
| `expires_at` | DATETIME | NULL | GC for abandoned carts |
| `created_at` | DATETIME | NOT NULL | |
| `updated_at` | DATETIME | NOT NULL | |

Cart-line data will surface in Phase 2 as the `cart_items` bridge (M:N: carts ↔ product_variants, with `quantity` attribute).

#### 3.12 ORDERS
Finalized purchases. Immutable once placed (revisions are handled via refund/cancel).

| Attribute | Type | Key / Null | Notes |
|---|---|---|---|
| `order_id` | BIGINT | **PK** | |
| `merchant_id` | BIGINT | FK → MERCHANTS, NOT NULL | Tenant anchor |
| `customer_user_id` | BIGINT | FK → CUSTOMER, NOT NULL | Registered customer required |
| `order_number` | VARCHAR(20) | UNIQUE `(merchant_id, order_number)`, NOT NULL | Public ID (`SC-10001`) |
| `status` | VARCHAR(20) | NOT NULL | `pending` / `paid` / `shipped` / `delivered` / `canceled` / `refunded` |
| `shipping_address` | **COMPOSITE** | NOT NULL | Snapshot of customer address |
| `billing_address` | **COMPOSITE** | NOT NULL | May differ from shipping |
| `subtotal` | DECIMAL(12,2) | NOT NULL | Sum of line items |
| `discount_total` | DECIMAL(12,2) | NOT NULL, default 0 | Applied coupons |
| `tax_total` | DECIMAL(12,2) | NOT NULL, default 0 | |
| `shipping_total` | DECIMAL(12,2) | NOT NULL, default 0 | Carrier fees |
| `grand_total` | DECIMAL(12,2) | **DERIVED** | `subtotal − discount_total + tax_total + shipping_total` |
| `currency` | CHAR(3) | NOT NULL | |
| `placed_at` | DATETIME | NOT NULL | |
| `canceled_at` | DATETIME | NULL | |

**Address snapshots:** customer addresses can change over time; orders freeze them for accounting immutability.

#### 3.13 ORDER_ITEMS (weak entity — #2)
Line items exist only under their order.

| Attribute | Type | Key / Null | Notes |
|---|---|---|---|
| `order_id` | BIGINT | **PK (part), FK → ORDERS** | Identifying relationship |
| `line_no` | INT | **PK (part)** | **Partial key** — 1, 2, 3... within order |
| `product_id` | BIGINT | FK → PRODUCTS, NOT NULL | |
| `variant_no` | INT | FK → PRODUCT_VARIANTS (composite), NOT NULL | |
| `merchant_id` | BIGINT | FK → MERCHANTS, NOT NULL | Tenant anchor |
| `product_title` | VARCHAR(255) | NOT NULL | **Snapshot** — frozen at order time |
| `variant_label` | VARCHAR(120) | NOT NULL | **Snapshot** — e.g., "Red / L" |
| `sku` | VARCHAR(40) | NOT NULL | **Snapshot** |
| `unit_price` | DECIMAL(12,2) | NOT NULL | **Snapshot** |
| `quantity` | INT | NOT NULL | |
| `line_subtotal` | DECIMAL(12,2) | **DERIVED** | `unit_price × quantity` |
| `discount_amount` | DECIMAL(12,2) | NOT NULL, default 0 | Line-level discount |

**Snapshot pattern:** `product_title`, `variant_label`, `sku`, `unit_price` freeze values — if the catalog later changes, order history stays intact. Phase 4 report discusses this controlled denormalization.

#### 3.14 PAYMENTS
One order may have several payments (partial, retries, post-refund re-charge) → 1:N.

| Attribute | Type | Key / Null | Notes |
|---|---|---|---|
| `payment_id` | BIGINT | **PK** | |
| `order_id` | BIGINT | FK → ORDERS, NOT NULL | |
| `merchant_id` | BIGINT | FK → MERCHANTS, NOT NULL | Tenant anchor |
| `payment_method` | VARCHAR(20) | NOT NULL | `credit_card` / `debit_card` / `bank_transfer` / `cash_on_delivery` / `wallet` |
| `amount` | DECIMAL(12,2) | NOT NULL | |
| `currency` | CHAR(3) | NOT NULL | |
| `status` | VARCHAR(20) | NOT NULL | `pending` / `authorized` / `captured` / `failed` / `refunded` |
| `gateway_reference` | VARCHAR(120) | NULL | Stripe / iyzico transaction ID |
| `processed_at` | DATETIME | NULL | Gateway confirmation time |
| `created_at` | DATETIME | NOT NULL | |

#### 3.15 SHIPMENTS
One order may be split across warehouses → 1:N.

| Attribute | Type | Key / Null | Notes |
|---|---|---|---|
| `shipment_id` | BIGINT | **PK** | |
| `order_id` | BIGINT | FK → ORDERS, NOT NULL | |
| `merchant_id` | BIGINT | FK → MERCHANTS, NOT NULL | Tenant anchor |
| `warehouse_id` | BIGINT | FK → WAREHOUSES, NOT NULL | Origin warehouse |
| `carrier` | VARCHAR(40) | NOT NULL | "PTT", "Yurtiçi", "Aras", "DHL", ... |
| `tracking_number` | VARCHAR(80) | NULL | |
| `status` | VARCHAR(20) | NOT NULL | `preparing` / `shipped` / `in_transit` / `delivered` / `returned` |
| `shipping_address` | **COMPOSITE** | NOT NULL | Snapshot |
| `shipped_at` | DATETIME | NULL | |
| `delivered_at` | DATETIME | NULL | |
| `created_at` | DATETIME | NOT NULL | |

### Group 5 — Engagement + Audit (3 entities)

#### 3.16 REVIEWS

| Attribute | Type | Key / Null | Notes |
|---|---|---|---|
| `review_id` | BIGINT | **PK** | |
| `product_id` | BIGINT | FK → PRODUCTS, NOT NULL | |
| `customer_user_id` | BIGINT | FK → CUSTOMER, NOT NULL | |
| `merchant_id` | BIGINT | FK → MERCHANTS, NOT NULL | Tenant anchor |
| `order_id` | BIGINT | FK → ORDERS, NULL | Non-null = verified purchase |
| `rating` | SMALLINT | NOT NULL | CHECK `BETWEEN 1 AND 5` |
| `title` | VARCHAR(120) | NULL | Optional headline |
| `body` | TEXT | NULL | Review text |
| `is_verified_purchase` | BOOLEAN | NOT NULL, default FALSE | TRUE iff `order_id IS NOT NULL` |
| `helpful_count` | INT | NOT NULL, default 0 | Community vote tally |
| `status` | VARCHAR(20) | NOT NULL | `pending` / `published` / `rejected` |
| `created_at` | DATETIME | NOT NULL | |
| `moderated_at` | DATETIME | NULL | |
| `moderated_by` | BIGINT | FK → STAFF, NULL | Reviewer (self-reference to staff) |

**Business rule:** One customer can review a product at most once → `UNIQUE (product_id, customer_user_id)`.

#### 3.17 DISCOUNTS

| Attribute | Type | Key / Null | Notes |
|---|---|---|---|
| `discount_id` | BIGINT | **PK** | |
| `merchant_id` | BIGINT | FK → MERCHANTS, NOT NULL | Tenant anchor |
| `code` | VARCHAR(40) | UNIQUE `(merchant_id, code)`, NOT NULL | e.g., "SUMMER20" |
| `discount_type` | VARCHAR(20) | NOT NULL | `percentage` / `fixed_amount` / `free_shipping` |
| `value` | DECIMAL(12,2) | NOT NULL | `20` → 20% or 20 TL (depending on type) |
| `min_order_amount` | DECIMAL(12,2) | NULL | Minimum cart subtotal |
| `max_uses` | INT | NULL | NULL = unlimited |
| `max_uses_per_customer` | INT | NULL, default 1 | Per-customer cap |
| `used_count` | INT | NOT NULL, default 0 | Increments as redeemed |
| `starts_at` | DATETIME | NOT NULL | |
| `ends_at` | DATETIME | NULL | NULL = open-ended |
| `is_active` | BOOLEAN | NOT NULL, default TRUE | Manual kill-switch |
| `created_at` | DATETIME | NOT NULL | |
| `created_by` | BIGINT | FK → STAFF, NOT NULL | Author |

Phase 2 will surface the `discount_usages(discount_id, order_id, used_at)` bridge (M:N: which orders used which coupon).

#### 3.18 ACTIVITY_LOG (polymorphic audit)

| Attribute | Type | Key / Null | Notes |
|---|---|---|---|
| `event_id` | BIGINT | **PK** | |
| `merchant_id` | BIGINT | FK → MERCHANTS, NOT NULL | Tenant anchor |
| `actor_user_id` | BIGINT | FK → USERS, NULL | NULL for system events |
| `actor_type` | VARCHAR(20) | NOT NULL | `staff` / `customer` / `platform_admin` / `system` |
| `entity_type` | VARCHAR(40) | NOT NULL | Polymorphic discriminator |
| `entity_id` | BIGINT | NOT NULL | **No FK** — entity_id targets vary by entity_type |
| `action` | VARCHAR(40) | NOT NULL | `created` / `updated` / `deleted` / `status_changed` / `logged_in` / … |
| `payload_json` | JSON | NULL | Before/after diff or action details |
| `ip_address` | VARCHAR(45) | NULL | IPv4 or IPv6 |
| `user_agent` | VARCHAR(255) | NULL | Client info |
| `occurred_at` | DATETIME | NOT NULL | |

**Polymorphic association:** `(entity_type, entity_id)` references different tables at runtime; no DB-level FK. This is a **controlled denormalization** — single uniform audit table at the cost of referential integrity. Phase 4 report discusses the trade-off.

---

## 4. Relationships (Summary)

The ER diagram (Phase 2) draws **26 relationships** (R1-R25 + R23b — REVIEWS participates in two binary relationships, one with PRODUCTS and one with CUSTOMER). Quick inventory:

| # | Relationship | Cardinality | Participation (L / R) | Notes |
|---|---|---|---|---|
| R1  | `USERS — IS_A — CUSTOMER` | 1:1 IS_A | (0,1) / (1,1) | Ch07 ER binary; R1/R2/R3 may coexist for one USERS row |
| R2  | `USERS — IS_A — STAFF` | 1:1 IS_A | (0,1) / (1,1) | Ch07 ER binary |
| R3  | `USERS — IS_A — PLATFORM_ADMIN` | 1:1 IS_A | (0,1) / (1,1) | Ch07 ER binary |
| R4  | `STAFF — WORKS_FOR — MERCHANTS` (via `merchant_staff`) | M:N | (0,N) partial / (1,N) **total** (≥1 owner) | Carries `role` attribute |
| R5  | `STAFF — OWNER_OF — MERCHANTS` | 1:1 (via `merchants.owner_user_id`) | (0,1) partial / (1,1) **total** | Founding owner — every merchant must have one staff owner |
| R6  | `MERCHANTS — HAS — PRODUCTS` | 1:N | (0,N) partial / (1,1) **total** | |
| R7  | `MERCHANTS — HAS — CATEGORIES` | 1:N | (0,N) partial / (1,1) **total** | |
| R8  | `MERCHANTS — HAS — WAREHOUSES` | 1:N | (0,N) partial / (1,1) **total** | |
| R9  | `CATEGORIES — PARENT_OF — CATEGORIES` | 1:N recursive | (0,N) partial / (0,1) partial | Tree |
| R10 | `PRODUCTS — CATEGORIZED_IN — CATEGORIES` (bridge `product_categories`) | M:N | (0,N) partial / (0,N) partial | |
| R11 | `PRODUCTS — HAS_VARIANT — PRODUCT_VARIANTS` (weak/identifying) | 1:N identifying | (0,N) partial / (1,1) **total** | |
| R12 | `STOCKED_AT (PRODUCTS × PRODUCT_VARIANTS × WAREHOUSES)` | **Ternary M:N:N** | all (0,N) partial | Genuine ternary |
| R13 | `MERCHANTS — HAS — CARTS` | 1:N | (0,N) partial / (1,1) **total** | |
| R14 | `CUSTOMER — SHOPS_AT — CARTS` | 1:N | (0,N) partial / (0,1) partial | CART side (0,1): guest cart has null `customer_user_id` |
| R15 | `CARTS — CART_ITEMS — PRODUCT_VARIANTS` (bridge `cart_items`) | M:N | (0,N) partial / (0,N) partial | `quantity` attribute |
| R16 | `MERCHANTS — HAS — ORDERS` | 1:N | (0,N) partial / (1,1) **total** | |
| R17 | `CUSTOMER — PLACES — ORDERS` | 1:N | (0,N) partial / (1,1) **total** | |
| R18 | `ORDERS — HAS_ITEM — ORDER_ITEMS` (weak/identifying) | 1:N identifying | (0,N) partial / (1,1) **total** | |
| R19 | `PRODUCT_VARIANTS — REFERENCES — ORDER_ITEMS` | 1:N | (0,N) partial / (1,1) **total** | |
| R20 | `ORDERS — HAS_PAYMENT — PAYMENTS` | 1:N | (0,N) partial / (1,1) **total** | |
| R21 | `ORDERS — HAS_SHIPMENT — SHIPMENTS` | 1:N | (0,N) partial / (1,1) **total** | `shipments.order_id` NOT NULL — every shipment must belong to an order |
| R22 | `WAREHOUSES — SHIPS_FROM — SHIPMENTS` | 1:N | (0,N) partial / (1,1) **total** | |
| R23  | `PRODUCTS — REVIEWED_AS — REVIEWS` | 1:N | (0,N) partial / (1,1) **total** | REVIEWS is a full entity (not bridge); `product_id` NOT NULL |
| R23b | `CUSTOMER — WRITTEN_BY — REVIEWS` | 1:N | (0,N) partial / (1,1) **total** | `customer_user_id` NOT NULL — every review has an author |
| R24 | `DISCOUNTS — APPLIED_TO — ORDERS` (bridge `discount_usages`) | M:N | (0,N) partial / (0,N) partial | |
| R25 | `USERS — ACTOR_OF — ACTIVITY_LOG` | 1:N | (0,N) partial / (0,1) partial | LOG side (0,1): system events have null `actor_user_id` |

---

## 5. Business Rules & Constraints

1. **Tenant isolation** — every non-global table carries `merchant_id`; composite FKs `(merchant_id, X)` prevent cross-tenant references.
2. **Global user identity** — one `users` row per person; membership in merchants is via `merchant_staff`, shopping is via `orders` keyed on `customer_user_id`.
3. **Weak-entity identity** — `PRODUCT_VARIANTS`, `ORDER_ITEMS` share identity with their owner; cannot exist without it.
4. **Every merchant has an owner** — `MERCHANTS.owner_user_id` NOT NULL at creation; enforced via `merchant_staff` with `role='owner'`.
5. **One owner transition** — changing owner requires demoting previous owner to admin (app-level check in Phase 4).
6. **Review uniqueness** — `UNIQUE (product_id, customer_user_id)` on `reviews`.
7. **Rating range** — `CHECK (rating BETWEEN 1 AND 5)` on `reviews`.
8. **Verified-purchase flag coherence** — `is_verified_purchase` TRUE iff `order_id IS NOT NULL`.
9. **Order immutability** — once `orders.status` reaches `paid`, financial fields (`subtotal`, `tax_total`, etc.) are immutable; changes go through refund/cancel flow.
10. **Line-item snapshot** — `order_items.product_title/sku/unit_price` frozen at order placement.
11. **Inventory reservation** — before an order transitions to `paid`, `inventory.quantity_reserved` must have sufficient headroom; on cancel, reservation decremented.
12. **Discount validity** — enforced at order placement: `NOW() BETWEEN starts_at AND COALESCE(ends_at, NOW())`, `is_active = TRUE`, `used_count < max_uses`.
13. **Recursive category depth** — no enforced max, but Phase 5 report notes convention of ≤ 4 levels.
14. **Audit immutability** — `activity_log` is append-only (app-level); no UPDATE/DELETE after insertion.
15. **Currency consistency** — an order's `currency` must match `merchants.currency` for that tenant.
16. **Cart → order transition** — on successful checkout, cart status set to `converted`; cart rows retained for analytics (not deleted).


*End of Phase 1*

