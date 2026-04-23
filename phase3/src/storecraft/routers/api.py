"""Small JSON API surface for tests and external clients."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Merchant, Product
from ..queries import showcase

router = APIRouter(prefix="/api", tags=["api"])


@router.get("/merchants")
def list_merchants(db: Session = Depends(get_db)):
    rows = db.execute(select(Merchant).order_by(Merchant.merchant_id)).scalars().all()
    return [
        {"merchant_id": m.merchant_id, "slug": m.slug, "store_name": m.store_name, "plan": m.plan}
        for m in rows
    ]


@router.get("/merchants/{slug}/products")
def list_products(slug: str, db: Session = Depends(get_db)):
    merchant = db.execute(select(Merchant).where(Merchant.slug == slug)).scalar_one_or_none()
    if merchant is None:
        raise HTTPException(404, "merchant not found")
    rows = db.execute(
        select(Product).where(
            Product.merchant_id == merchant.merchant_id,
            Product.status == "active",
        )
    ).scalars().all()
    return [
        {
            "product_id": p.product_id,
            "title": p.title,
            "base_price": float(p.base_price),
            "currency": p.currency,
        }
        for p in rows
    ]


@router.get("/queries/kpi")
def api_merchant_kpi(db: Session = Depends(get_db)):
    """Showcase Q14 — per-merchant sales KPIs."""
    return showcase.q14_merchant_sales_kpi(db)


@router.get("/queries/this-month")
def api_this_month(db: Session = Depends(get_db)):
    """Showcase Q21 — this-month CTE KPI."""
    return showcase.q21_this_month_kpis(db)


@router.get("/queries/top-customers/{slug}")
def api_top_customers(slug: str, db: Session = Depends(get_db)):
    """Showcase Q18 — window-function ranking of customers within a merchant."""
    merchant = db.execute(select(Merchant).where(Merchant.slug == slug)).scalar_one_or_none()
    if merchant is None:
        raise HTTPException(404, "merchant not found")
    return showcase.q18_top_customers_per_merchant(db, merchant.merchant_id)


@router.get("/queries/category-tree/{slug}")
def api_category_tree(slug: str, db: Session = Depends(get_db)):
    """Showcase Q22 — recursive CTE for the category tree."""
    merchant = db.execute(select(Merchant).where(Merchant.slug == slug)).scalar_one_or_none()
    if merchant is None:
        raise HTTPException(404, "merchant not found")
    return showcase.q22_category_tree(db, merchant.merchant_id)


@router.get("/queries/low-stock/{slug}")
def api_low_stock(slug: str, db: Session = Depends(get_db)):
    merchant = db.execute(select(Merchant).where(Merchant.slug == slug)).scalar_one_or_none()
    if merchant is None:
        raise HTTPException(404)
    return showcase.low_stock_alerts(db, merchant.merchant_id)
