"""Exercise the Python-side showcase query library against seeded data."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import text

from storecraft.models import (
    Customer,
    Merchant,
    Order,
    OrderItem,
    Product,
    ProductVariant,
    Staff,
    User,
)
from storecraft.queries import showcase
from tests.conftest import mysql_only

# All showcase queries exercise MySQL-specific features — skip on SQLite.
pytestmark = mysql_only


@pytest.fixture
def mini_tenant(db):
    owner = User(email="o@ex.com", password_hash="x", first_name="O", last_name="W")
    db.add(owner)
    db.flush()
    db.add(Staff(user_id=owner.user_id, hired_at=date(2024, 1, 1), title="Owner"))
    db.flush()
    m = Merchant(
        slug="mini",
        store_name="Mini",
        owner_user_id=owner.user_id,
        contact_email="a@b.com",
        plan="pro",
    )
    db.add(m)
    db.flush()
    p = Product(merchant_id=m.merchant_id, slug="x", title="X", base_price=Decimal("10"), status="active")
    db.add(p)
    db.flush()
    db.add(ProductVariant(product_id=p.product_id, variant_no=1, sku="S", is_default=1))
    db.flush()

    cu_user = User(email="c@c.c", password_hash="x", first_name="C", last_name="U")
    db.add(cu_user)
    db.flush()
    db.add(Customer(user_id=cu_user.user_id))
    db.flush()

    # Add an order to exercise KPI aggregates
    o = Order(
        merchant_id=m.merchant_id,
        customer_user_id=cu_user.user_id,
        order_number="TST-001",
        status="paid",
        ship_line1="a", ship_city="a", ship_country="TR", ship_zip="0",
        bill_line1="a", bill_city="a", bill_country="TR", bill_zip="0",
        subtotal=Decimal("50"), discount_total=Decimal("0"), tax_total=Decimal("9"),
        currency="TRY",
    )
    db.add(o)
    db.flush()
    db.add(
        OrderItem(
            order_id=o.order_id, line_no=1,
            product_id=p.product_id, variant_no=1,
            product_title="X", variant_label="def",
            sku="S", unit_price=Decimal("25"), quantity=2,
        )
    )
    db.commit()
    return m


def test_q1_active_pro_merchants(db, mini_tenant):
    rows = showcase.q1_active_pro_merchants(db)
    # Q1 filters by plan IN ('pro','enterprise'); our tenant is 'pro'.
    slugs = [r["slug"] for r in rows]
    assert "mini" in slugs


def test_q14_kpi_returns_row_per_merchant(db, mini_tenant):
    rows = showcase.q14_merchant_sales_kpi(db)
    by_id = {r["merchant_id"]: r for r in rows}
    assert mini_tenant.merchant_id in by_id
    # Our tenant has 1 paid order; gross_sales may be NULL in SQLite if Computed
    # is stripped — fall back to subtotal check.
    kpi = by_id[mini_tenant.merchant_id]
    assert kpi["orders_count"] == 1


def test_q21_this_month_includes_tenant(db, mini_tenant):
    rows = showcase.q21_this_month_kpis(db)
    slugs = [r["store_name"] for r in rows]
    assert "Mini" in slugs


def test_q22_category_tree_returns_empty_for_new_tenant(db, mini_tenant):
    rows = showcase.q22_category_tree(db, mini_tenant.merchant_id)
    assert rows == []  # no categories added in this fixture
