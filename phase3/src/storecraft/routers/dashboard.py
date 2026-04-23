"""Merchant dashboard — KPIs from showcase queries + low-stock alerts."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import TEMPLATES_DIR
from ..db import get_db
from ..models import Merchant
from ..queries import showcase

router = APIRouter(prefix="/dashboard/{slug}", tags=["dashboard"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, slug: str, db: Session = Depends(get_db)):
    merchant = db.execute(select(Merchant).where(Merchant.slug == slug)).scalar_one_or_none()
    if merchant is None:
        raise HTTPException(status_code=404, detail="merchant not found")

    kpis = {row["merchant_id"]: row for row in showcase.q14_merchant_sales_kpi(db)}.get(
        merchant.merchant_id, {}
    )
    top = showcase.top_products(db, merchant.merchant_id, limit=10)
    low = showcase.low_stock_alerts(db, merchant.merchant_id)
    month = {row["merchant_id"]: row for row in showcase.q21_this_month_kpis(db)}.get(
        merchant.merchant_id, {}
    )
    top_customers = showcase.q18_top_customers_per_merchant(db, merchant_id=merchant.merchant_id)

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "merchant": merchant,
            "kpis": kpis,
            "month_kpis": month,
            "top_products": top,
            "low_stock": low,
            "top_customers": top_customers,
        },
    )
