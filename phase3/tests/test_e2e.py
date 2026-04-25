"""End-to-end API tests: exercises the full FastAPI app over TestClient.

Covers what the narrower `test_api.py` smoke suite does not:
  - Unified error envelope across APIError, HTTPException, validation.
  - Tenant isolation across every tenant-scoped endpoint.
  - Pagination (default limit, limit cap, offset, ordering).
  - Path parameter validation (slug pattern, positive int).
  - Request-ID middleware echoes header, CORS responds to allowed origin,
    rejects unknown origin.
  - Showcase / query endpoints return 200 against stub views.
  - /healthz, /readyz, /health meta endpoints all respond.
  - Unhandled exception path returns opaque envelope (no traceback leak).
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from storecraft.main import create_app
from storecraft.models import (
    Category,
    Customer,
    Merchant,
    Product,
    ProductVariant,
    Staff,
    User,
)


# ─── Shared seed fixture ──────────────────────────────────────────────────────


@pytest.fixture
def two_tenants(db):
    """Seed two merchants ('alpha' / 'beta') with distinct products + customers."""
    a_owner = User(email="a@ex.com", password_hash="x", first_name="A", last_name="Owner")
    b_owner = User(email="b@ex.com", password_hash="x", first_name="B", last_name="Owner")
    db.add_all([a_owner, b_owner])
    db.flush()
    db.add_all(
        [
            Staff(user_id=a_owner.user_id, hired_at=date(2024, 1, 1), title="Owner"),
            Staff(user_id=b_owner.user_id, hired_at=date(2024, 1, 1), title="Owner"),
        ]
    )
    db.flush()

    alpha = Merchant(
        slug="alpha",
        store_name="Alpha Store",
        owner_user_id=a_owner.user_id,
        contact_email="a@a.com",
        currency="USD",
        plan="pro",
        activated_at=datetime.utcnow(),
    )
    beta = Merchant(
        slug="beta",
        store_name="Beta Store",
        owner_user_id=b_owner.user_id,
        contact_email="b@b.com",
        currency="USD",
        plan="basic",
    )
    db.add_all([alpha, beta])
    db.flush()

    db.add_all(
        [
            Category(merchant_id=alpha.merchant_id, slug="cat-a", name="Alpha Cat"),
            Category(merchant_id=beta.merchant_id, slug="cat-b", name="Beta Cat"),
        ]
    )

    # Seed 25 alpha products so we can exercise pagination defaults.
    for i in range(25):
        p = Product(
            merchant_id=alpha.merchant_id,
            slug=f"alpha-{i:02d}",
            title=f"Alpha Product {i:02d}",
            base_price=Decimal("1.00") + Decimal(i),
            status="active",
        )
        db.add(p)
        db.flush()
        db.add(ProductVariant(product_id=p.product_id, variant_no=1, sku=f"A-{i:02d}", is_default=1))

    beta_p = Product(
        merchant_id=beta.merchant_id,
        slug="beta-secret",
        title="Beta Secret",
        base_price=Decimal("5.00"),
        status="active",
    )
    db.add(beta_p)
    db.flush()
    db.add(ProductVariant(product_id=beta_p.product_id, variant_no=1, sku="B-01", is_default=1))

    cu_user = User(email="cust@ex.com", password_hash="x", first_name="Cust", last_name="O'Mer")
    db.add(cu_user)
    db.flush()
    db.add(Customer(user_id=cu_user.user_id))
    db.commit()
    return {"alpha": alpha, "beta": beta, "customer": cu_user}


# ─── Error envelope ───────────────────────────────────────────────────────────


def test_error_envelope_not_found(client, two_tenants):
    r = client.get("/api/merchants/does-not-exist")
    assert r.status_code == 404
    body = r.json()
    assert body["error"]["code"] == "MERCHANT_NOT_FOUND"
    assert "does-not-exist" in body["error"]["message"]
    assert body["error"]["details"] == []


def test_error_envelope_validation_path(client, two_tenants):
    # Slug pattern disallows uppercase → 422 VALIDATION_ERROR.
    r = client.get("/api/merchants/UPPER")
    assert r.status_code == 422
    body = r.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert len(body["error"]["details"]) >= 1


def test_error_envelope_negative_product_id(client, two_tenants):
    r = client.get("/api/merchants/alpha/products/-1")
    # Path constraint gt=0 → validation error, not a 404.
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


def test_error_envelope_limit_over_cap(client, two_tenants):
    r = client.get("/api/merchants/alpha/products?limit=5000")
    assert r.status_code == 422


def test_product_not_found_under_existing_merchant(client, two_tenants):
    r = client.get("/api/merchants/alpha/products/99999")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "PRODUCT_NOT_FOUND"


def test_order_not_found(client, two_tenants):
    r = client.get("/api/merchants/alpha/orders/99999")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "ORDER_NOT_FOUND"


# ─── Tenant isolation (every tenant-scoped endpoint) ─────────────────────────


def test_tenant_isolation_products(client, two_tenants):
    r = client.get("/api/merchants/alpha/products?limit=50")
    titles = {p["title"] for p in r.json()}
    assert "Beta Secret" not in titles


def test_tenant_isolation_categories(client, two_tenants):
    r = client.get("/api/merchants/alpha/categories")
    names = [c["name"] for c in r.json()]
    assert "Beta Cat" not in names
    assert "Alpha Cat" in names


def test_tenant_isolation_product_detail(client, two_tenants):
    """A product from beta must not be readable via alpha's URL."""
    r = client.get("/api/merchants/beta/products")
    beta_pid = r.json()[0]["product_id"]
    r2 = client.get(f"/api/merchants/alpha/products/{beta_pid}")
    assert r2.status_code == 404


def test_tenant_isolation_orders_empty(client, two_tenants):
    r = client.get("/api/merchants/alpha/orders")
    assert r.status_code == 200
    assert r.json() == []


# ─── Pagination ──────────────────────────────────────────────────────────────


def test_products_default_limit_20(client, two_tenants):
    r = client.get("/api/merchants/alpha/products")
    assert r.status_code == 200
    assert len(r.json()) == 20  # DEFAULT_PAGE_SIZE


def test_products_limit_caps_at_100(client, two_tenants):
    r = client.get("/api/merchants/alpha/products?limit=100")
    assert r.status_code == 200
    # Only 25 seeded, so we don't get 100, but request is accepted.
    assert len(r.json()) == 25


def test_products_offset_skips_rows(client, two_tenants):
    r_all = client.get("/api/merchants/alpha/products?limit=100").json()
    r_skip = client.get("/api/merchants/alpha/products?limit=100&offset=10").json()
    assert len(r_skip) == len(r_all) - 10
    assert r_skip[0]["product_id"] != r_all[0]["product_id"]


def test_merchants_list_pagination(client, two_tenants):
    r = client.get("/api/merchants?limit=1")
    assert r.status_code == 200
    assert len(r.json()) == 1


# ─── Product search ──────────────────────────────────────────────────────────


def test_product_search_case_insensitive(client, two_tenants):
    r = client.get("/api/merchants/alpha/products?q=alpha&limit=100")
    assert len(r.json()) == 25


def test_product_search_no_match(client, two_tenants):
    r = client.get("/api/merchants/alpha/products?q=nothing-exists")
    assert r.status_code == 200
    assert r.json() == []


def test_product_search_sanitizes_like_metachar(client, two_tenants):
    """A `%` in the query must not become a wildcard — no results."""
    r = client.get("/api/merchants/alpha/products?q=%25")
    assert r.status_code == 200
    # Safely escaped: 0 matches because we search literal "%".
    assert r.json() == []


# ─── Showcase / query endpoints ──────────────────────────────────────────────


def test_queries_active_pro(client, two_tenants):
    r = client.get("/api/queries/active-pro-merchants")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_queries_kpi(client, two_tenants):
    r = client.get("/api/queries/kpi")
    assert r.status_code == 200


def test_queries_category_tree_unknown_merchant_404(client, two_tenants):
    r = client.get("/api/queries/category-tree/unknown")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "MERCHANT_NOT_FOUND"


def test_queries_low_stock_returns_list(client, two_tenants):
    r = client.get("/api/queries/low-stock/alpha")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_queries_top_products_limit_cap(client, two_tenants):
    r = client.get("/api/queries/top-products/alpha?limit=5")
    assert r.status_code == 200


def test_queries_top_products_bad_limit(client, two_tenants):
    r = client.get("/api/queries/top-products/alpha?limit=500")
    assert r.status_code == 422


def test_admin_activity(client, two_tenants):
    r = client.get("/api/admin/activity?limit=10")
    assert r.status_code == 200


# ─── Meta endpoints ──────────────────────────────────────────────────────────


def test_healthz_liveness(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_readyz_readiness(client):
    r = client.get("/readyz")
    assert r.status_code == 200
    assert r.json()["status"] == "ready"


def test_legacy_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_root_meta_points_at_new_healthz(client):
    body = client.get("/").json()
    assert body["health"] == "/healthz"


# ─── Request-ID / CORS ───────────────────────────────────────────────────────


def test_request_id_is_generated(client):
    r = client.get("/healthz")
    assert "x-request-id" in {k.lower() for k in r.headers.keys()}


def test_request_id_echoed(client):
    custom = "abc123-custom-id"
    r = client.get("/healthz", headers={"X-Request-ID": custom})
    assert r.headers.get("x-request-id", "") == custom


def test_cors_allowed_origin(client):
    r = client.get("/api/merchants", headers={"Origin": "http://localhost:5173"})
    # Allowed origin echoes in header
    assert r.status_code == 200
    assert r.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_cors_disallowed_origin(client):
    r = client.get("/api/merchants", headers={"Origin": "http://evil.example.com"})
    # Request itself may succeed (simple GET isn't preflighted) but the CORS
    # ack header must not be present for a disallowed origin.
    assert r.headers.get("access-control-allow-origin") != "http://evil.example.com"


# ─── Unhandled exception path (never leak traceback) ─────────────────────────


def test_unhandled_exception_returns_opaque_envelope():
    """Add a route that raises an unexpected exception; handler must mask it."""
    app = create_app()

    @app.get("/__explode__")
    def _boom() -> dict[str, str]:
        raise RuntimeError("sensitive-internals-should-not-leak")

    with TestClient(app, raise_server_exceptions=False) as c:
        r = c.get("/__explode__")
    assert r.status_code == 500
    body = r.json()
    assert body["error"]["code"] == "INTERNAL_ERROR"
    assert "sensitive-internals-should-not-leak" not in body["error"]["message"]
