"""JSON API smoke tests — every endpoint returns well-formed data and honors tenant scoping."""
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
    """Minimum data for API tests: one merchant with one active product + variant + customer."""
    owner = User(email="owner@ex.com", password_hash="x", first_name="Owen", last_name="Wilson")
    db.add(owner)
    db.flush()
    db.add(Staff(user_id=owner.user_id, hired_at=date(2024, 1, 1), title="Owner"))
    db.flush()

    m = Merchant(
        slug="demo",
        store_name="Demo Store",
        owner_user_id=owner.user_id,
        contact_email="demo@demo.com",
        currency="USD",
        plan="pro",
        activated_at=datetime.utcnow(),
    )
    db.add(m)
    db.flush()

    db.add(Category(merchant_id=m.merchant_id, slug="gen", name="General"))
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

    cu_user = User(email="c@ex.com", password_hash="x", first_name="Cady", last_name="Heron")
    db.add(cu_user)
    db.flush()
    db.add(Customer(user_id=cu_user.user_id))
    db.commit()
    return {"merchant": m, "customer": cu_user, "product": p}


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_root_meta(client):
    r = client.get("/")
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "StoreCraft API"
    assert "frontend" in body


def test_merchants_list(client, seeded):
    r = client.get("/api/merchants")
    assert r.status_code == 200
    data = r.json()
    slugs = [m["slug"] for m in data]
    assert "demo" in slugs


def test_merchant_detail(client, seeded):
    r = client.get("/api/merchants/demo")
    assert r.status_code == 200
    data = r.json()
    assert data["slug"] == "demo"
    assert data["stats"]["products"] == 1
    assert data["stats"]["categories"] == 1


def test_merchant_404(client, seeded):
    r = client.get("/api/merchants/nope")
    assert r.status_code == 404


def test_products_list(client, seeded):
    r = client.get("/api/merchants/demo/products")
    assert r.status_code == 200
    products = r.json()
    assert len(products) == 1
    assert products[0]["title"] == "Widget"
    assert products[0]["variants_count"] == 1


def test_products_search_filter(client, seeded):
    r = client.get("/api/merchants/demo/products?q=widg")
    assert r.status_code == 200
    assert len(r.json()) == 1

    r = client.get("/api/merchants/demo/products?q=nothing")
    assert r.status_code == 200
    assert len(r.json()) == 0


def test_product_detail(client, seeded):
    p = seeded["product"]
    r = client.get(f"/api/merchants/demo/products/{p.product_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["title"] == "Widget"
    assert len(data["variants"]) == 1
    assert data["variants"][0]["sku"] == "SKU-W1"


def test_product_detail_404(client, seeded):
    r = client.get("/api/merchants/demo/products/999999")
    assert r.status_code == 404


def test_categories_list(client, seeded):
    r = client.get("/api/merchants/demo/categories")
    assert r.status_code == 200
    categories = r.json()
    assert any(c["name"] == "General" for c in categories)


def test_orders_list_empty(client, seeded):
    r = client.get("/api/merchants/demo/orders")
    assert r.status_code == 200
    assert r.json() == []


def test_cors_headers(client):
    """Pre-flight-ish check that CORS middleware is wired."""
    r = client.options("/api/merchants", headers={
        "Origin": "http://localhost:5173",
        "Access-Control-Request-Method": "GET",
    })
    # TestClient may not fully simulate CORS pre-flight; at minimum assert no 500.
    assert r.status_code in (200, 204, 400)


def test_tenant_isolation(client, db, seeded):
    """Products from merchant B must not leak into merchant A's response."""
    # Second merchant
    owner2 = User(email="o2@ex.com", password_hash="x", first_name="Olive", last_name="Other")
    db.add(owner2)
    db.flush()
    db.add(Staff(user_id=owner2.user_id, hired_at=date(2024, 1, 1), title="Owner"))
    db.flush()
    m2 = Merchant(
        slug="other",
        store_name="Other Store",
        owner_user_id=owner2.user_id,
        contact_email="o@o.com",
        currency="USD",
        plan="basic",
    )
    db.add(m2)
    db.flush()
    p2 = Product(
        merchant_id=m2.merchant_id,
        slug="leak",
        title="Secret Leak Product",
        base_price=Decimal("1.00"),
        status="active",
    )
    db.add(p2)
    db.commit()

    r = client.get("/api/merchants/demo/products")
    assert r.status_code == 200
    titles = [p["title"] for p in r.json()]
    assert "Secret Leak Product" not in titles
    assert titles == ["Widget"]
