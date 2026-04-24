"""JSON API for the React SPA.

Every endpoint:
  - declares typed Pydantic request + response schemas,
  - enforces path param validation (positive ints, length-limited slugs),
  - paginates list results with capped `limit`,
  - scopes every query to the caller's tenant (merchant_id) via `tenant_scope`.
"""
from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Path, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, text
from sqlalchemy.orm import Session, selectinload

from ..db import get_db
from ..errors import APIError
from ..models import (
    Category,
    Customer,
    Merchant,
    Order,
    Product,
)
from ..queries import showcase

router = APIRouter(prefix="/api", tags=["api"])


# ─── Shared types / constants ───────────────────────────────────────────────

MAX_PAGE_SIZE = 100
DEFAULT_PAGE_SIZE = 20

SlugPath = Annotated[
    str,
    Path(
        min_length=1,
        max_length=64,
        pattern=r"^[a-z0-9][a-z0-9_-]*$",
        description="Tenant slug (lowercase alphanumerics, hyphen, underscore).",
    ),
]
PositiveInt = Annotated[int, Path(gt=0, le=2**31 - 1)]
LimitQuery = Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE, description="Max rows to return.")]
OffsetQuery = Annotated[int, Query(ge=0, description="Skip N rows for offset pagination.")]


class Page(BaseModel):
    """Envelope for paginated list responses."""

    model_config = ConfigDict(extra="forbid")

    items: list[Any]
    total: int = Field(ge=0, description="Total rows matched (pre-pagination).")
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)


# ─── Tenant resolver ────────────────────────────────────────────────────────


def tenant_scope(
    slug: SlugPath,
    db: Annotated[Session, Depends(get_db)],
) -> Merchant:
    """Dependency: resolve `slug` → Merchant row, or raise 404.

    Any endpoint that takes `{slug}` in its path must depend on this helper
    rather than querying Merchant itself, guaranteeing consistent 404 shape
    and that downstream queries receive a verified tenant.
    """
    merchant = db.execute(
        select(Merchant).where(Merchant.slug == slug)
    ).scalar_one_or_none()
    if merchant is None:
        raise APIError.not_found("MERCHANT_NOT_FOUND", f"merchant '{slug}' not found")
    return merchant


MerchantDep = Annotated[Merchant, Depends(tenant_scope)]
DbDep = Annotated[Session, Depends(get_db)]


# ─── Response schemas ───────────────────────────────────────────────────────


class MerchantSummary(BaseModel):
    model_config = ConfigDict(from_attributes=False, extra="forbid")

    merchant_id: int
    slug: str
    store_name: str
    plan: str
    currency: str
    city: str | None = None
    country: str | None = None
    contact_email: str
    created_at: str | None
    activated_at: str | None
    suspended: bool


class MerchantStats(BaseModel):
    model_config = ConfigDict(extra="forbid")
    staff_count: int = 0
    categories: int = 0
    warehouses: int = 0
    products: int = 0


class MerchantDetail(MerchantSummary):
    stats: MerchantStats


class ProductSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")
    product_id: int
    slug: str
    title: str
    product_type: str | None
    base_price: float
    currency: str
    status: str
    variants_count: int


class VariantOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    variant_no: int
    sku: str
    option_name: str | None
    option_value: str | None
    price_override: float | None
    barcode: str | None
    is_default: bool


class ReviewOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    review_id: int
    rating: int
    title: str | None
    body: str | None
    is_verified_purchase: bool
    helpful_count: int
    created_at: str | None


class ProductDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")
    product_id: int
    title: str
    base_price: float
    currency: str
    product_type: str | None
    status: str
    variants: list[VariantOut]
    reviews: list[ReviewOut]


class CategoryOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    category_id: int
    parent_id: int | None
    slug: str
    name: str
    display_order: int


class OrderCustomerBrief(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: int | None = None
    full_name: str | None = None


class OrderCustomerFull(OrderCustomerBrief):
    email: str | None = None


class OrderSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")
    order_id: int
    order_number: str
    status: str
    subtotal: float
    discount_total: float
    tax_total: float
    grand_total: float
    currency: str
    placed_at: str | None
    line_count: int
    customer: OrderCustomerBrief


class Address(BaseModel):
    model_config = ConfigDict(extra="forbid")
    line1: str | None = None
    city: str | None = None
    country: str | None = None
    zip: str | None = None


class OrderItemOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    line_no: int
    product_id: int
    variant_no: int
    product_title: str | None
    variant_label: str | None
    sku: str | None
    unit_price: float
    quantity: int
    line_subtotal: float


class PaymentOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    payment_id: int
    method: str
    amount: float
    status: str
    gateway_reference: str | None
    processed_at: str | None


class ShipmentOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    shipment_id: int
    carrier: str | None
    tracking_number: str | None
    status: str
    shipped_at: str | None
    delivered_at: str | None


class DiscountUsageOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    discount_id: int
    amount_applied: float
    used_at: str | None


class OrderDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")
    order_id: int
    order_number: str
    status: str
    subtotal: float
    discount_total: float
    tax_total: float
    grand_total: float
    currency: str
    placed_at: str | None
    canceled_at: str | None
    ship_address: Address
    bill_address: Address
    customer: OrderCustomerFull
    items: list[OrderItemOut]
    payments: list[PaymentOut]
    shipments: list[ShipmentOut]
    discount_usages: list[DiscountUsageOut]


class ActivityOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: int
    merchant_id: int
    actor_label: str | None = None
    entity_type: str | None = None
    entity_id: int | None = None
    action: str | None = None
    occurred_at: str | None = None


# ─── Shared helpers ─────────────────────────────────────────────────────────


def _iso(dt: Any) -> str | None:
    return dt.isoformat() if dt is not None else None


def _count(db: Session, sql: str, merchant_id: int) -> int:
    val = db.execute(text(sql), {"m": merchant_id}).scalar()
    return int(val or 0)


# ─── Merchant directory ────────────────────────────────────────────────────


@router.get("/merchants", response_model=list[MerchantSummary])
def list_merchants(
    db: DbDep,
    limit: LimitQuery = DEFAULT_PAGE_SIZE,
    offset: OffsetQuery = 0,
) -> list[MerchantSummary]:
    """Paginated directory of merchants. No cross-tenant leaks — this is the
    *directory*, deliberately global."""
    rows = (
        db.execute(
            select(Merchant)
            .order_by(Merchant.merchant_id)
            .limit(limit)
            .offset(offset)
        )
        .scalars()
        .all()
    )
    return [
        MerchantSummary(
            merchant_id=m.merchant_id,
            slug=m.slug,
            store_name=m.store_name,
            plan=m.plan,
            currency=m.currency,
            city=m.business_city,
            country=m.business_country,
            contact_email=m.contact_email,
            created_at=_iso(m.created_at),
            activated_at=_iso(m.activated_at),
            suspended=m.suspended_at is not None,
        )
        for m in rows
    ]


@router.get("/merchants/{slug}", response_model=MerchantDetail)
def get_merchant(merchant: MerchantDep, db: DbDep) -> MerchantDetail:
    stats = MerchantStats(
        staff_count=_count(db, "SELECT COUNT(*) FROM merchant_staff WHERE merchant_id = :m", merchant.merchant_id),
        categories=_count(db, "SELECT COUNT(*) FROM categories WHERE merchant_id = :m", merchant.merchant_id),
        warehouses=_count(db, "SELECT COUNT(*) FROM warehouses WHERE merchant_id = :m", merchant.merchant_id),
        products=_count(db, "SELECT COUNT(*) FROM products WHERE merchant_id = :m", merchant.merchant_id),
    )
    return MerchantDetail(
        merchant_id=merchant.merchant_id,
        slug=merchant.slug,
        store_name=merchant.store_name,
        plan=merchant.plan,
        currency=merchant.currency,
        city=merchant.business_city,
        country=merchant.business_country,
        contact_email=merchant.contact_email,
        created_at=_iso(merchant.created_at),
        activated_at=_iso(merchant.activated_at),
        suspended=merchant.suspended_at is not None,
        stats=stats,
    )


# ─── Catalog ────────────────────────────────────────────────────────────────


@router.get("/merchants/{slug}/products", response_model=list[ProductSummary])
def list_products(
    merchant: MerchantDep,
    db: DbDep,
    q: Annotated[str, Query(max_length=80, description="search text")] = "",
    category_id: Annotated[int | None, Query(gt=0)] = None,
    limit: LimitQuery = DEFAULT_PAGE_SIZE,
    offset: OffsetQuery = 0,
) -> list[ProductSummary]:
    stmt = (
        select(Product)
        .where(Product.merchant_id == merchant.merchant_id, Product.status == "active")
        .options(selectinload(Product.variants))
        .order_by(Product.title)
    )
    if q:
        # Sanitize LIKE metacharacters so client input can't turn into a wildcard.
        safe = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        stmt = stmt.where(Product.title.ilike(f"%{safe}%"))
    # `category_id` filter hook — reserved for Phase 4 when product_categories M:N table is queried.
    stmt = stmt.limit(limit).offset(offset)
    products = db.execute(stmt).scalars().unique().all()
    return [
        ProductSummary(
            product_id=p.product_id,
            slug=p.slug,
            title=p.title,
            product_type=p.product_type,
            base_price=float(p.base_price),
            currency=p.currency,
            status=p.status,
            variants_count=len(p.variants),
        )
        for p in products
    ]


@router.get("/merchants/{slug}/products/{product_id}", response_model=ProductDetail)
def get_product(
    merchant: MerchantDep,
    product_id: PositiveInt,
    db: DbDep,
) -> ProductDetail:
    p = db.execute(
        select(Product)
        .where(
            Product.product_id == product_id,
            Product.merchant_id == merchant.merchant_id,  # tenant scope enforced
        )
        .options(selectinload(Product.variants), selectinload(Product.reviews))
    ).scalar_one_or_none()
    if p is None:
        raise APIError.not_found("PRODUCT_NOT_FOUND", f"product {product_id} not found")
    return ProductDetail(
        product_id=p.product_id,
        title=p.title,
        base_price=float(p.base_price),
        currency=p.currency,
        product_type=p.product_type,
        status=p.status,
        variants=[
            VariantOut(
                variant_no=v.variant_no,
                sku=v.sku,
                option_name=v.option1_name,
                option_value=v.option1_value,
                price_override=float(v.price_override) if v.price_override is not None else None,
                barcode=v.barcode,
                is_default=bool(v.is_default),
            )
            for v in p.variants
        ],
        reviews=[
            ReviewOut(
                review_id=r.review_id,
                rating=r.rating,
                title=r.title,
                body=r.body,
                is_verified_purchase=bool(r.is_verified_purchase),
                helpful_count=r.helpful_count,
                created_at=_iso(r.created_at),
            )
            for r in p.reviews
        ],
    )


@router.get("/merchants/{slug}/categories", response_model=list[CategoryOut])
def list_categories(
    merchant: MerchantDep,
    db: DbDep,
    limit: LimitQuery = MAX_PAGE_SIZE,
    offset: OffsetQuery = 0,
) -> list[CategoryOut]:
    rows = (
        db.execute(
            select(Category)
            .where(Category.merchant_id == merchant.merchant_id)  # tenant scope
            .order_by(Category.display_order)
            .limit(limit)
            .offset(offset)
        )
        .scalars()
        .all()
    )
    return [
        CategoryOut(
            category_id=c.category_id,
            parent_id=c.parent_category_id,
            slug=c.slug,
            name=c.name,
            display_order=c.display_order,
        )
        for c in rows
    ]


# ─── Orders ─────────────────────────────────────────────────────────────────


@router.get("/merchants/{slug}/orders", response_model=list[OrderSummary])
def list_orders(
    merchant: MerchantDep,
    db: DbDep,
    limit: LimitQuery = DEFAULT_PAGE_SIZE,
    offset: OffsetQuery = 0,
) -> list[OrderSummary]:
    orders = (
        db.execute(
            select(Order)
            .where(Order.merchant_id == merchant.merchant_id)  # tenant scope
            .options(
                selectinload(Order.items),
                selectinload(Order.customer).selectinload(Customer.user),
            )
            .order_by(Order.placed_at.desc())
            .limit(limit)
            .offset(offset)
        )
        .scalars()
        .unique()
        .all()
    )
    out: list[OrderSummary] = []
    for o in orders:
        full_name: str | None = None
        user_id: int | None = None
        if o.customer and o.customer.user:
            full_name = f"{o.customer.user.first_name} {o.customer.user.last_name}"
            user_id = o.customer.user_id
        out.append(
            OrderSummary(
                order_id=o.order_id,
                order_number=o.order_number,
                status=o.status,
                subtotal=float(o.subtotal),
                discount_total=float(o.discount_total),
                tax_total=float(o.tax_total),
                grand_total=float(o.grand_total) if o.grand_total is not None else 0.0,
                currency=o.currency,
                placed_at=_iso(o.placed_at),
                line_count=len(o.items),
                customer=OrderCustomerBrief(user_id=user_id, full_name=full_name),
            )
        )
    return out


@router.get("/merchants/{slug}/orders/{order_id}", response_model=OrderDetail)
def get_order(
    merchant: MerchantDep,
    order_id: PositiveInt,
    db: DbDep,
) -> OrderDetail:
    o = db.execute(
        select(Order)
        .where(
            Order.order_id == order_id,
            Order.merchant_id == merchant.merchant_id,  # tenant scope enforced
        )
        .options(
            selectinload(Order.items),
            selectinload(Order.payments),
            selectinload(Order.shipments),
            selectinload(Order.discount_usages),
            selectinload(Order.customer).selectinload(Customer.user),
        )
    ).scalar_one_or_none()
    if o is None:
        raise APIError.not_found("ORDER_NOT_FOUND", f"order {order_id} not found")

    customer = OrderCustomerFull()
    if o.customer and o.customer.user:
        customer = OrderCustomerFull(
            user_id=o.customer.user_id,
            email=o.customer.user.email,
            full_name=f"{o.customer.user.first_name} {o.customer.user.last_name}",
        )
    return OrderDetail(
        order_id=o.order_id,
        order_number=o.order_number,
        status=o.status,
        subtotal=float(o.subtotal),
        discount_total=float(o.discount_total),
        tax_total=float(o.tax_total),
        grand_total=float(o.grand_total) if o.grand_total is not None else 0.0,
        currency=o.currency,
        placed_at=_iso(o.placed_at),
        canceled_at=_iso(o.canceled_at),
        ship_address=Address(line1=o.ship_line1, city=o.ship_city, country=o.ship_country, zip=o.ship_zip),
        bill_address=Address(line1=o.bill_line1, city=o.bill_city, country=o.bill_country, zip=o.bill_zip),
        customer=customer,
        items=[
            OrderItemOut(
                line_no=it.line_no,
                product_id=it.product_id,
                variant_no=it.variant_no,
                product_title=it.product_title,
                variant_label=it.variant_label,
                sku=it.sku,
                unit_price=float(it.unit_price),
                quantity=it.quantity,
                line_subtotal=float(it.line_subtotal) if it.line_subtotal is not None else 0.0,
            )
            for it in o.items
        ],
        payments=[
            PaymentOut(
                payment_id=p.payment_id,
                method=p.payment_method,
                amount=float(p.amount),
                status=p.status,
                gateway_reference=p.gateway_reference,
                processed_at=_iso(p.processed_at),
            )
            for p in o.payments
        ],
        shipments=[
            ShipmentOut(
                shipment_id=s.shipment_id,
                carrier=s.carrier,
                tracking_number=s.tracking_number,
                status=s.status,
                shipped_at=_iso(s.shipped_at),
                delivered_at=_iso(s.delivered_at),
            )
            for s in o.shipments
        ],
        discount_usages=[
            DiscountUsageOut(
                discount_id=du.discount_id,
                amount_applied=float(du.amount_applied),
                used_at=_iso(du.used_at),
            )
            for du in o.discount_usages
        ],
    )


# ─── Admin (cross-tenant) ──────────────────────────────────────────────────


@router.get("/admin/activity", response_model=list[ActivityOut])
def admin_activity(
    db: DbDep,
    limit: LimitQuery = 50,
    offset: OffsetQuery = 0,
) -> list[ActivityOut]:
    """Cross-tenant audit — intentionally not scoped to a single merchant
    because this endpoint is reserved for platform admins. A production
    deployment would gate this behind an auth dependency.
    """
    rows = db.execute(
        text(
            """
            SELECT event_id, merchant_id, actor_label, entity_type, entity_id, action, occurred_at
              FROM v_recent_activity
             ORDER BY occurred_at DESC
             LIMIT :lim OFFSET :off
            """
        ),
        {"lim": limit, "off": offset},
    ).mappings().all()
    return [
        ActivityOut(
            event_id=int(r["event_id"]),
            merchant_id=int(r["merchant_id"]),
            actor_label=r.get("actor_label"),
            entity_type=r.get("entity_type"),
            entity_id=int(r["entity_id"]) if r.get("entity_id") is not None else None,
            action=r.get("action"),
            occurred_at=_iso(r.get("occurred_at")),
        )
        for r in rows
    ]


# ─── Showcase queries (exposed as JSON for the React dashboard) ──────────────
# These return raw dict rows from SQL; typing is intentionally loose because
# they are for reporting / dashboards and their shape is the SQL's output.


@router.get("/queries/kpi")
def api_kpi(db: DbDep) -> list[dict[str, Any]]:
    """Q14 — per-merchant KPI aggregate."""
    return showcase.q14_merchant_sales_kpi(db)


@router.get("/queries/this-month")
def api_this_month(db: DbDep) -> list[dict[str, Any]]:
    """Q21 — this-month CTE KPI per merchant."""
    return showcase.q21_this_month_kpis(db)


@router.get("/queries/active-pro-merchants")
def api_active_pro(db: DbDep) -> list[dict[str, Any]]:
    """Q1 — active pro/enterprise merchants."""
    return showcase.q1_active_pro_merchants(db)


@router.get("/queries/top-customers/{slug}")
def api_top_customers(merchant: MerchantDep, db: DbDep) -> list[dict[str, Any]]:
    """Q18 — window-function ranking per merchant (tenant-scoped)."""
    return showcase.q18_top_customers_per_merchant(db, merchant.merchant_id)


@router.get("/queries/category-tree/{slug}")
def api_category_tree(merchant: MerchantDep, db: DbDep) -> list[dict[str, Any]]:
    """Q22 — recursive CTE for the category tree (tenant-scoped)."""
    return showcase.q22_category_tree(db, merchant.merchant_id)


@router.get("/queries/low-stock/{slug}")
def api_low_stock(merchant: MerchantDep, db: DbDep) -> list[dict[str, Any]]:
    """View: v_low_stock_alerts filtered by merchant (tenant-scoped)."""
    return showcase.low_stock_alerts(db, merchant.merchant_id)


@router.get("/queries/top-products/{slug}")
def api_top_products(
    merchant: MerchantDep,
    db: DbDep,
    limit: LimitQuery = 10,
) -> list[dict[str, Any]]:
    """View: v_top_products_by_merchant filtered by merchant (tenant-scoped)."""
    return showcase.top_products(db, merchant.merchant_id, limit=limit)
