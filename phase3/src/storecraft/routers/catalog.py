"""Merchant storefront — product catalog + search (HTMX-powered)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from ..config import TEMPLATES_DIR
from ..db import get_db
from ..models import Category, Merchant, Product, ProductVariant

router = APIRouter(prefix="/m/{slug}", tags=["catalog"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _get_merchant(db: Session, slug: str) -> Merchant:
    merchant = db.execute(select(Merchant).where(Merchant.slug == slug)).scalar_one_or_none()
    if merchant is None:
        raise HTTPException(status_code=404, detail=f"merchant '{slug}' not found")
    return merchant


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def storefront(
    request: Request,
    slug: str,
    q: str = Query("", description="search text"),
    category: int | None = Query(None),
    db: Session = Depends(get_db),
):
    merchant = _get_merchant(db, slug)

    stmt = (
        select(Product)
        .where(Product.merchant_id == merchant.merchant_id, Product.status == "active")
        .options(selectinload(Product.variants))
    )
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Product.title.ilike(like), Product.slug.ilike(like)))
    if category:
        stmt = stmt.join(Product.category_links).where(
            Product.category_links.any()
        )  # simplified category filter

    products = db.execute(stmt.order_by(Product.title)).scalars().unique().all()

    categories = db.execute(
        select(Category).where(Category.merchant_id == merchant.merchant_id).order_by(Category.display_order)
    ).scalars().all()

    # HTMX partial: only return the product grid when the request header is set
    if request.headers.get("HX-Request") == "true":
        return templates.TemplateResponse(
            request=request,
            name="_product_grid.html",
            context={"products": products, "merchant": merchant},
        )

    return templates.TemplateResponse(
        request=request,
        name="storefront.html",
        context={
            "merchant": merchant,
            "products": products,
            "categories": categories,
            "query": q,
            "active_category": category,
        },
    )


@router.get("/product/{product_id}", response_class=HTMLResponse)
def product_detail(request: Request, slug: str, product_id: int, db: Session = Depends(get_db)):
    merchant = _get_merchant(db, slug)
    product = db.execute(
        select(Product)
        .where(Product.product_id == product_id, Product.merchant_id == merchant.merchant_id)
        .options(selectinload(Product.variants), selectinload(Product.reviews))
    ).scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail="product not found")
    return templates.TemplateResponse(
        request=request,
        name="product_detail.html",
        context={"merchant": merchant, "product": product},
    )
