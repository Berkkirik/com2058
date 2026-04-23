"""JSON API for the React SPA.

Every endpoint returns JSON. Tenant scoping via `merchant_id` (path param) or
resolved from `slug`.
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session, selectinload

from ..db import get_db
from ..models import (
    ActivityLog,
    Category,
    Customer,
    Discount,
    Merchant,
    Order,
    OrderItem,
    Payment,
    Product,
    ProductVariant,
    Review,
    Shipment,
    User,
    Warehouse,
)
from ..queries import showcase

router = APIRouter(prefix="/api", tags=["api"])


# ── Merchant directory ──────────────────────────────────────────────────────

@router.get("/merchants")
def list_merchants(db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    rows = db.execute(select(Merchant).order_by(Merchant.merchant_id)).scalars().all()
    return [
        {
            "merchant_id": m.merchant_id,
            "slug": m.slug,
            "store_name": m.store_name,
            "plan": m.plan,
            "currency": m.currency,
            "city": m.business_city,
            "country": m.business_country,
            "contact_email": m.contact_email,
            "created_at": m.created_at.isoformat() if m.created_at else None,
            "activated_at": m.activated_at.isoformat() if m.activated_at else None,
            "suspended": m.suspended_at is not None,
        }
        for m in rows
    ]


def _merchant_or_404(db: Session, slug: str) -> Merchant:
    m = db.execute(select(Merchant).where(Merchant.slug == slug)).scalar_one_or_none()
    if m is None:
        raise HTTPException(404, f"merchant '{slug}' not found")
    return m


@router.get("/merchants/{slug}")
def get_merchant(slug: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    m = _merchant_or_404(db, slug)
    staff_count = db.execute(
        text("SELECT COUNT(*) FROM merchant_staff WHERE merchant_id = :m"),
        {"m": m.merchant_id},
    ).scalar()
    category_count = db.execute(
        text("SELECT COUNT(*) FROM categories WHERE merchant_id = :m"),
        {"m": m.merchant_id},
    ).scalar()
    warehouse_count = db.execute(
        text("SELECT COUNT(*) FROM warehouses WHERE merchant_id = :m"),
        {"m": m.merchant_id},
    ).scalar()
    product_count = db.execute(
        text("SELECT COUNT(*) FROM products WHERE merchant_id = :m"),
        {"m": m.merchant_id},
    ).scalar()
    return {
        "merchant_id": m.merchant_id,
        "slug": m.slug,
        "store_name": m.store_name,
        "plan": m.plan,
        "currency": m.currency,
        "city": m.business_city,
        "country": m.business_country,
        "contact_email": m.contact_email,
        "created_at": m.created_at.isoformat() if m.created_at else None,
        "activated_at": m.activated_at.isoformat() if m.activated_at else None,
        "suspended": m.suspended_at is not None,
        "stats": {
            "staff_count": int(staff_count or 0),
            "categories": int(category_count or 0),
            "warehouses": int(warehouse_count or 0),
            "products": int(product_count or 0),
        },
    }


# ── Catalog ────────────────────────────────────────────────────────────────

@router.get("/merchants/{slug}/products")
def list_products(
    slug: str,
    q: str = Query("", description="search text"),
    category_id: int | None = Query(None),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    m = _merchant_or_404(db, slug)
    stmt = (
        select(Product)
        .where(Product.merchant_id == m.merchant_id, Product.status == "active")
        .options(selectinload(Product.variants))
        .order_by(Product.title)
    )
    if q:
        like = f"%{q}%"
        stmt = stmt.where(Product.title.ilike(like))
    products = db.execute(stmt).scalars().unique().all()
    return [
        {
            "product_id": p.product_id,
            "slug": p.slug,
            "title": p.title,
            "product_type": p.product_type,
            "base_price": float(p.base_price),
            "currency": p.currency,
            "status": p.status,
            "variants_count": len(p.variants),
        }
        for p in products
    ]


@router.get("/merchants/{slug}/products/{product_id}")
def get_product(slug: str, product_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    m = _merchant_or_404(db, slug)
    p = db.execute(
        select(Product)
        .where(Product.product_id == product_id, Product.merchant_id == m.merchant_id)
        .options(selectinload(Product.variants), selectinload(Product.reviews))
    ).scalar_one_or_none()
    if p is None:
        raise HTTPException(404, "product not found")
    return {
        "product_id": p.product_id,
        "title": p.title,
        "base_price": float(p.base_price),
        "currency": p.currency,
        "product_type": p.product_type,
        "status": p.status,
        "variants": [
            {
                "variant_no": v.variant_no,
                "sku": v.sku,
                "option_name": v.option1_name,
                "option_value": v.option1_value,
                "price_override": float(v.price_override) if v.price_override else None,
                "barcode": v.barcode,
                "is_default": bool(v.is_default),
            }
            for v in p.variants
        ],
        "reviews": [
            {
                "review_id": r.review_id,
                "rating": r.rating,
                "title": r.title,
                "body": r.body,
                "is_verified_purchase": bool(r.is_verified_purchase),
                "helpful_count": r.helpful_count,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in p.reviews
        ],
    }


@router.get("/merchants/{slug}/categories")
def list_categories(slug: str, db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    m = _merchant_or_404(db, slug)
    rows = db.execute(
        select(Category).where(Category.merchant_id == m.merchant_id).order_by(Category.display_order)
    ).scalars().all()
    return [
        {
            "category_id": c.category_id,
            "parent_id": c.parent_category_id,
            "slug": c.slug,
            "name": c.name,
            "display_order": c.display_order,
        }
        for c in rows
    ]


# ── Orders ─────────────────────────────────────────────────────────────────

@router.get("/merchants/{slug}/orders")
def list_orders(slug: str, db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    m = _merchant_or_404(db, slug)
    orders = db.execute(
        select(Order)
        .where(Order.merchant_id == m.merchant_id)
        .options(selectinload(Order.items), selectinload(Order.customer).selectinload(Customer.user))
        .order_by(Order.placed_at.desc())
        .limit(200)
    ).scalars().unique().all()
    return [
        {
            "order_id": o.order_id,
            "order_number": o.order_number,
            "status": o.status,
            "subtotal": float(o.subtotal),
            "discount_total": float(o.discount_total),
            "tax_total": float(o.tax_total),
            "grand_total": float(o.grand_total) if o.grand_total is not None else 0.0,
            "currency": o.currency,
            "placed_at": o.placed_at.isoformat() if o.placed_at else None,
            "line_count": len(o.items),
            "customer": {
                "user_id": o.customer.user_id if o.customer else None,
                "full_name": (
                    f"{o.customer.user.first_name} {o.customer.user.last_name}"
                    if o.customer and o.customer.user
                    else None
                ),
            },
        }
        for o in orders
    ]


@router.get("/merchants/{slug}/orders/{order_id}")
def get_order(slug: str, order_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    m = _merchant_or_404(db, slug)
    o = db.execute(
        select(Order)
        .where(Order.order_id == order_id, Order.merchant_id == m.merchant_id)
        .options(
            selectinload(Order.items),
            selectinload(Order.payments),
            selectinload(Order.shipments),
            selectinload(Order.discount_usages),
            selectinload(Order.customer).selectinload(Customer.user),
        )
    ).scalar_one_or_none()
    if o is None:
        raise HTTPException(404, "order not found")
    return {
        "order_id": o.order_id,
        "order_number": o.order_number,
        "status": o.status,
        "subtotal": float(o.subtotal),
        "discount_total": float(o.discount_total),
        "tax_total": float(o.tax_total),
        "grand_total": float(o.grand_total) if o.grand_total is not None else 0.0,
        "currency": o.currency,
        "placed_at": o.placed_at.isoformat() if o.placed_at else None,
        "canceled_at": o.canceled_at.isoformat() if o.canceled_at else None,
        "ship_address": {"line1": o.ship_line1, "city": o.ship_city, "country": o.ship_country, "zip": o.ship_zip},
        "bill_address": {"line1": o.bill_line1, "city": o.bill_city, "country": o.bill_country, "zip": o.bill_zip},
        "customer": {
            "user_id": o.customer.user_id if o.customer else None,
            "email": o.customer.user.email if o.customer and o.customer.user else None,
            "full_name": (
                f"{o.customer.user.first_name} {o.customer.user.last_name}"
                if o.customer and o.customer.user
                else None
            ),
        },
        "items": [
            {
                "line_no": it.line_no,
                "product_id": it.product_id,
                "variant_no": it.variant_no,
                "product_title": it.product_title,
                "variant_label": it.variant_label,
                "sku": it.sku,
                "unit_price": float(it.unit_price),
                "quantity": it.quantity,
                "line_subtotal": float(it.line_subtotal) if it.line_subtotal is not None else 0.0,
            }
            for it in o.items
        ],
        "payments": [
            {
                "payment_id": p.payment_id,
                "method": p.payment_method,
                "amount": float(p.amount),
                "status": p.status,
                "gateway_reference": p.gateway_reference,
                "processed_at": p.processed_at.isoformat() if p.processed_at else None,
            }
            for p in o.payments
        ],
        "shipments": [
            {
                "shipment_id": s.shipment_id,
                "carrier": s.carrier,
                "tracking_number": s.tracking_number,
                "status": s.status,
                "shipped_at": s.shipped_at.isoformat() if s.shipped_at else None,
                "delivered_at": s.delivered_at.isoformat() if s.delivered_at else None,
            }
            for s in o.shipments
        ],
        "discount_usages": [
            {
                "discount_id": du.discount_id,
                "amount_applied": float(du.amount_applied),
                "used_at": du.used_at.isoformat() if du.used_at else None,
            }
            for du in o.discount_usages
        ],
    }


# ── Admin (cross-tenant) ────────────────────────────────────────────────────

@router.get("/admin/activity")
def admin_activity(limit: int = Query(50, ge=1, le=500), db: Session = Depends(get_db)):
    rows = db.execute(
        text(
            """
            SELECT event_id, merchant_id, actor_label, entity_type, entity_id, action, occurred_at
              FROM v_recent_activity
             ORDER BY occurred_at DESC
             LIMIT :lim
            """
        ),
        {"lim": limit},
    ).mappings().all()
    return [dict(r) for r in rows]


# ── Showcase queries (exposed as JSON for the React dashboard) ──────────────

@router.get("/queries/kpi")
def api_kpi(db: Session = Depends(get_db)):
    """Q14 — per-merchant KPI aggregate."""
    return showcase.q14_merchant_sales_kpi(db)


@router.get("/queries/this-month")
def api_this_month(db: Session = Depends(get_db)):
    """Q21 — this-month CTE KPI per merchant."""
    return showcase.q21_this_month_kpis(db)


@router.get("/queries/active-pro-merchants")
def api_active_pro(db: Session = Depends(get_db)):
    """Q1 — active pro/enterprise merchants."""
    return showcase.q1_active_pro_merchants(db)


@router.get("/queries/top-customers/{slug}")
def api_top_customers(slug: str, db: Session = Depends(get_db)):
    """Q18 — window-function ranking per merchant."""
    m = _merchant_or_404(db, slug)
    return showcase.q18_top_customers_per_merchant(db, m.merchant_id)


@router.get("/queries/category-tree/{slug}")
def api_category_tree(slug: str, db: Session = Depends(get_db)):
    """Q22 — recursive CTE for the category tree."""
    m = _merchant_or_404(db, slug)
    return showcase.q22_category_tree(db, m.merchant_id)


@router.get("/queries/low-stock/{slug}")
def api_low_stock(slug: str, db: Session = Depends(get_db)):
    """View: v_low_stock_alerts filtered by merchant."""
    m = _merchant_or_404(db, slug)
    return showcase.low_stock_alerts(db, m.merchant_id)


@router.get("/queries/top-products/{slug}")
def api_top_products(slug: str, limit: int = Query(10, ge=1, le=100), db: Session = Depends(get_db)):
    """View: v_top_products_by_merchant filtered by merchant."""
    m = _merchant_or_404(db, slug)
    return showcase.top_products(db, m.merchant_id, limit=limit)
