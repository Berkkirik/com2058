"""Orders views — per-merchant order list + order detail."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..config import TEMPLATES_DIR
from ..db import get_db
from ..models import Merchant, Order

router = APIRouter(prefix="/dashboard/{slug}/orders", tags=["orders"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def orders_list(request: Request, slug: str, db: Session = Depends(get_db)):
    merchant = db.execute(select(Merchant).where(Merchant.slug == slug)).scalar_one_or_none()
    if merchant is None:
        raise HTTPException(status_code=404)
    orders = db.execute(
        select(Order)
        .where(Order.merchant_id == merchant.merchant_id)
        .options(selectinload(Order.customer), selectinload(Order.items))
        .order_by(Order.placed_at.desc())
        .limit(100)
    ).scalars().all()
    return templates.TemplateResponse(
        "orders_list.html",
        {"request": request, "merchant": merchant, "orders": orders},
    )


@router.get("/{order_id}", response_class=HTMLResponse)
def order_detail(request: Request, slug: str, order_id: int, db: Session = Depends(get_db)):
    merchant = db.execute(select(Merchant).where(Merchant.slug == slug)).scalar_one_or_none()
    if merchant is None:
        raise HTTPException(status_code=404)
    order = db.execute(
        select(Order)
        .where(Order.order_id == order_id, Order.merchant_id == merchant.merchant_id)
        .options(
            selectinload(Order.items),
            selectinload(Order.payments),
            selectinload(Order.shipments),
            selectinload(Order.customer),
            selectinload(Order.discount_usages),
        )
    ).scalar_one_or_none()
    if order is None:
        raise HTTPException(status_code=404, detail="order not found")
    return templates.TemplateResponse(
        "order_detail.html",
        {"request": request, "merchant": merchant, "order": order},
    )
