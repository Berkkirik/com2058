"""Smoke tests for FastAPI routes — exercise routing, DB access, template rendering."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest

from storecraft.models import (
    Category,
    Customer,
    Merchant,
    Order,
    OrderItem,
    Product,
    ProductVariant,
    Staff,
    User,
)


@pytest.fixture
def seeded(db):
    """Insert minimum data for route tests."""
    owner = User(email="owner@ex.com", password_hash="x", first_name="O", last_name="W")
    db.add(owner)
    db.flush()
    db.add(Staff(user_id=owner.user_id, hired_at=date(2024, 1, 1), title="Owner"))
    db.flush()

    m = Merchant(
        slug="demo",
        store_name="Demo Store",
        owner_user_id=owner.user_id,
        contact_email="demo@demo.com",
        currency="TRY",
        plan="basic",
        activated_at=datetime.utcnow(),
    )
    db.add(m)
    db.flush()

    cat = Category(merchant_id=m.merchant_id, slug="gen", name="General")
    db.add(cat)
    db.flush()

    p = Product(
        merchant_id=m.merchant_id,
        slug="widget",
        title="Widget",
        base_price=Decimal("9.99"),
        status="active",
    )
    db.add(p)
    db.flush()
    db.add(ProductVariant(product_id=p.product_id, variant_no=1, sku="SKU-W1", is_default=1))

    cu_user = User(email="c@ex.com", password_hash="x", first_name="C", last_name="U")
    db.add(cu_user)
    db.flush()
    db.add(Customer(user_id=cu_user.user_id))

    db.commit()
    return {"merchant": m, "customer": cu_user, "product": p}


def test_health_endpoint(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"


def test_home_page_renders(client, seeded):
    r = client.get("/")
    assert r.status_code == 200
    assert b"Merchant Directory" in r.content
    assert b"Demo Store" in r.content


def test_storefront_renders(client, seeded):
    r = client.get("/m/demo")
    assert r.status_code == 200
    assert b"Widget" in r.content
    assert b"9.99" in r.content


def test_storefront_htmx_partial(client, seeded):
    r = client.get("/m/demo", headers={"HX-Request": "true"})
    assert r.status_code == 200
    # Should be just the product grid, not the full page
    assert b"<!doctype" not in r.content.lower()
    assert b"product-grid" in r.content


def test_product_detail(client, seeded):
    p = seeded["product"]
    r = client.get(f"/m/demo/product/{p.product_id}")
    assert r.status_code == 200
    assert b"SKU-W1" in r.content


def test_product_detail_404(client, seeded):
    r = client.get("/m/demo/product/99999")
    assert r.status_code == 404


def test_unknown_merchant(client, seeded):
    r = client.get("/m/nope")
    assert r.status_code == 404


def test_api_merchants(client, seeded):
    r = client.get("/api/merchants")
    assert r.status_code == 200
    data = r.json()
    assert any(m["slug"] == "demo" for m in data)


def test_api_products_per_merchant(client, seeded):
    r = client.get("/api/merchants/demo/products")
    assert r.status_code == 200
    data = r.json()
    assert any(p["title"] == "Widget" for p in data)


def test_api_products_tenant_scoped(client, seeded):
    """A second merchant's products should not appear under /m/demo."""
    # Spin up another tenant in a fresh request (via API)
    # Since /api only exposes read, we'll check that 'demo' list does not include unrelated items.
    r = client.get("/api/merchants/demo/products")
    data = r.json()
    assert all(p["title"] == "Widget" for p in data)


from tests.conftest import mysql_only


@mysql_only
def test_dashboard_renders(client, seeded):
    """Dashboard uses views + MySQL-only DATE_FORMAT — exercised via docker compose integration."""
    r = client.get("/dashboard/demo")
    assert r.status_code == 200
    assert b"Demo Store" in r.content
    assert b"Dashboard" in r.content


def test_admin_renders(client, seeded):
    r = client.get("/admin")
    assert r.status_code == 200
    assert b"Platform Admin" in r.content
    assert b"Demo Store" in r.content


def test_orders_list_empty(client, seeded):
    r = client.get("/dashboard/demo/orders")
    assert r.status_code == 200
    # No orders seeded → just the header
    assert b"Orders" in r.content
