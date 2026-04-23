"""Platform-admin views — merchant directory, activity log, low-stock across tenants."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from ..config import TEMPLATES_DIR
from ..db import get_db
from ..models import Merchant

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def admin_home(request: Request, db: Session = Depends(get_db)):
    merchants = db.execute(select(Merchant).order_by(Merchant.created_at.desc())).scalars().all()
    recent = db.execute(
        text(
            """
            SELECT event_id, actor_label, entity_type, entity_id, action, occurred_at
              FROM v_recent_activity
             ORDER BY occurred_at DESC
             LIMIT 30
            """
        )
    ).mappings().all()
    return templates.TemplateResponse(
        request=request,
        name="admin.html",
        context={"merchants": merchants, "recent_activity": list(recent)},
    )
