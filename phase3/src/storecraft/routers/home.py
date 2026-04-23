"""Public home page — merchant directory."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import TEMPLATES_DIR
from ..db import get_db
from ..models import Merchant

router = APIRouter(tags=["public"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    merchants = db.execute(
        select(Merchant).where(Merchant.suspended_at.is_(None)).order_by(Merchant.created_at.desc())
    ).scalars().all()
    return templates.TemplateResponse(
        request=request, name="home.html", context={"merchants": merchants}
    )
