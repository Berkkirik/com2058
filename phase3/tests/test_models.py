"""Unit tests for SQLAlchemy ORM models — verifies schema, relationships, constraints."""
from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError

from storecraft.models import (
    Cart,
    CartItem,
    Category,
    Customer,
    Inventory,
    Merchant,
    Order,
    OrderItem,
    Product,
    ProductVariant,
    Staff,
    User,
    Warehouse,
)


def _make_user(db, **kw):
    u = User(
        email=kw.get("email", f"u{id(kw)}@example.com"),
        password_hash="hash",
        first_name=kw.get("first", "Ali"),
        last_name=kw.get("last", "Veli"),
    )
    db.add(u)
    db.flush()
    return u


def _make_merchant(db, slug="shop") -> Merchant:
    u = _make_user(db, email=f"{slug}-owner@ex.com")
    db.add(Staff(user_id=u.user_id, hired_at=date(2024, 1, 1), title="Owner"))
    db.flush()
    m = Merchant(
        slug=slug,
        store_name=slug.title(),
        owner_user_id=u.user_id,
        contact_email=f"contact@{slug}.com",
        currency="TRY",
        plan="basic",
    )
    db.add(m)
    db.flush()
    return m


def test_user_unique_email(db):
    db.add(User(email="dup@ex.com", password_hash="x", first_name="A", last_name="B"))
    db.commit()
    with pytest.raises(IntegrityError):
        db.add(User(email="dup@ex.com", password_hash="y", first_name="C", last_name="D"))
        db.commit()


def test_merchant_needs_owner_staff(db):
    """Without corresponding Staff row, merchant.owner_user_id FK should fail."""
    u = _make_user(db)
    # No Staff row created for u → FK violation
    m = Merchant(
        slug="noowner",
        store_name="X",
        owner_user_id=u.user_id,
        contact_email="x@x.com",
    )
    db.add(m)
    with pytest.raises(IntegrityError):
        db.commit()


def test_weak_entity_compound_pk(db):
    m = _make_merchant(db, slug="w1")
    p = Product(merchant_id=m.merchant_id, slug="p1", title="P", base_price=Decimal("10"))
    db.add(p)
    db.flush()
    v1 = ProductVariant(product_id=p.product_id, variant_no=1, sku="SKU-1", is_default=1)
    v2 = ProductVariant(product_id=p.product_id, variant_no=2, sku="SKU-2")
    db.add_all([v1, v2])
    db.commit()
    rows = db.query(ProductVariant).filter_by(product_id=p.product_id).all()
    assert len(rows) == 2
    assert (rows[0].product_id, rows[0].variant_no) != (rows[1].product_id, rows[1].variant_no)


def test_cascade_delete_weak_entities(db):
    m = _make_merchant(db, slug="w2")
    p = Product(merchant_id=m.merchant_id, slug="p-del", title="P2", base_price=Decimal("5"))
    db.add(p)
    db.flush()
    db.add(ProductVariant(product_id=p.product_id, variant_no=1, sku="SKU-del"))
    db.commit()

    db.delete(p)
    db.commit()
    assert db.query(ProductVariant).filter_by(product_id=p.product_id).count() == 0


def test_cart_guest_and_customer(db):
    m = _make_merchant(db, slug="w3")
    # Guest cart
    g = Cart(
        merchant_id=m.merchant_id,
        session_token="guest-1",
        expires_at=datetime.utcnow() + timedelta(days=1),
    )
    db.add(g)
    # Customer cart
    cu = _make_user(db, email="cust@ex.com")
    db.add(Customer(user_id=cu.user_id))
    db.flush()
    c = Cart(
        merchant_id=m.merchant_id,
        customer_user_id=cu.user_id,
        session_token="cust-1",
        expires_at=datetime.utcnow() + timedelta(days=1),
    )
    db.add(c)
    db.commit()

    all_carts = db.query(Cart).filter_by(merchant_id=m.merchant_id).all()
    assert len(all_carts) == 2
    assert any(cart.customer_user_id is None for cart in all_carts)


def test_inventory_ternary_pk(db):
    m = _make_merchant(db, slug="w4")
    p = Product(merchant_id=m.merchant_id, slug="p", title="P", base_price=Decimal("1"))
    db.add(p)
    db.flush()
    db.add(ProductVariant(product_id=p.product_id, variant_no=1, sku="X"))
    db.flush()
    w = Warehouse(
        merchant_id=m.merchant_id,
        name="WH",
        addr_line1="a",
        addr_city="A",
        addr_country="TR",
        addr_zip="06000",
    )
    db.add(w)
    db.flush()
    inv = Inventory(
        product_id=p.product_id,
        variant_no=1,
        warehouse_id=w.warehouse_id,
        qty_on_hand=10,
        qty_reserved=2,
        reorder_level=5,
    )
    db.add(inv)
    db.commit()
    assert inv.qty_available == 8


def test_category_recursive_fk(db):
    m = _make_merchant(db, slug="w5")
    root = Category(merchant_id=m.merchant_id, slug="root", name="Root")
    db.add(root)
    db.flush()
    child = Category(
        merchant_id=m.merchant_id,
        slug="child",
        name="Child",
        parent_category_id=root.category_id,
    )
    db.add(child)
    db.commit()

    # Back-populated relationships
    db.refresh(root)
    assert len(root.children) == 1
    assert root.children[0].name == "Child"


def test_tenant_isolation_products(db):
    m1 = _make_merchant(db, slug="tA")
    m2 = _make_merchant(db, slug="tB")
    db.add_all(
        [
            Product(merchant_id=m1.merchant_id, slug="sharedslug", title="X", base_price=Decimal("1")),
            Product(merchant_id=m2.merchant_id, slug="sharedslug", title="Y", base_price=Decimal("2")),
        ]
    )
    db.commit()
    # Same slug allowed across tenants; isolation works
    m1_products = db.query(Product).filter_by(merchant_id=m1.merchant_id).all()
    m2_products = db.query(Product).filter_by(merchant_id=m2.merchant_id).all()
    assert len(m1_products) == 1
    assert len(m2_products) == 1
    assert m1_products[0].slug == m2_products[0].slug == "sharedslug"
