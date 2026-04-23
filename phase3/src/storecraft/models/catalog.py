"""Catalog zone: MERCHANTS (tenant root), PRODUCTS, PRODUCT_VARIANTS (weak),
CATEGORIES (recursive), plus bridges MERCHANT_STAFF (R4) and PRODUCT_CATEGORIES (R10)."""
from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base

if TYPE_CHECKING:
    from .commerce import Cart, Order, Shipment, Payment
    from .engagement import Discount, Review, ActivityLog
    from .identity import Staff
    from .inventory import Warehouse, Inventory


class Merchant(Base):
    """Tenant root. Every other entity in the 5 non-identity zones scopes via merchant_id."""

    __tablename__ = "merchants"

    merchant_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    store_name: Mapped[str] = mapped_column(String(150), nullable=False)
    owner_user_id: Mapped[int] = mapped_column(
        ForeignKey("staff.user_id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    business_line1: Mapped[Optional[str]] = mapped_column(String(255))
    business_line2: Mapped[Optional[str]] = mapped_column(String(255))
    business_city: Mapped[Optional[str]] = mapped_column(String(100))
    business_country: Mapped[Optional[str]] = mapped_column(String(2))
    business_zip: Mapped[Optional[str]] = mapped_column(String(20))
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="TRY")
    plan: Mapped[str] = mapped_column(
        SAEnum("free", "basic", "pro", "enterprise", name="plan_enum"),
        nullable=False,
        default="basic",
    )
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )
    activated_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime)
    suspended_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime)

    # R5 owner link
    owner: Mapped["Staff"] = relationship(back_populates="owned_merchants")
    # R4 bridge
    staff_memberships: Mapped[list["MerchantStaff"]] = relationship(
        back_populates="merchant", cascade="all, delete-orphan"
    )
    # R6/R7/R8
    products: Mapped[list["Product"]] = relationship(back_populates="merchant", cascade="all, delete-orphan")
    categories: Mapped[list["Category"]] = relationship(back_populates="merchant", cascade="all, delete-orphan")
    warehouses: Mapped[list["Warehouse"]] = relationship(back_populates="merchant", cascade="all, delete-orphan")
    # R13/R16/R20/R21
    carts: Mapped[list["Cart"]] = relationship(back_populates="merchant", cascade="all, delete-orphan")
    orders: Mapped[list["Order"]] = relationship(back_populates="merchant")
    payments: Mapped[list["Payment"]] = relationship(back_populates="merchant")
    shipments: Mapped[list["Shipment"]] = relationship(back_populates="merchant")
    # engagement
    reviews: Mapped[list["Review"]] = relationship(back_populates="merchant", cascade="all, delete-orphan")
    discounts: Mapped[list["Discount"]] = relationship(back_populates="merchant", cascade="all, delete-orphan")
    activity_events: Mapped[list["ActivityLog"]] = relationship(
        back_populates="merchant", cascade="all, delete-orphan"
    )


class MerchantStaff(Base):
    """R4: STAFF ⟷ MERCHANTS bridge with {role} attribute."""

    __tablename__ = "merchant_staff"

    merchant_id: Mapped[int] = mapped_column(
        ForeignKey("merchants.merchant_id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("staff.user_id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
    role: Mapped[str] = mapped_column(
        SAEnum("owner", "admin", "staff", "viewer", name="merchant_role_enum"),
        nullable=False,
        default="staff",
    )
    joined_at: Mapped[dt.datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )

    merchant: Mapped["Merchant"] = relationship(back_populates="staff_memberships")
    staff_member: Mapped["Staff"] = relationship(back_populates="memberships")


class Product(Base):
    """R6: MERCHANTS → PRODUCTS (1:N total on products side)."""

    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("merchant_id", "slug", name="ux_products_merchant_slug"),
        CheckConstraint("base_price >= 0", name="ck_products_price"),
    )

    product_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    merchant_id: Mapped[int] = mapped_column(
        ForeignKey("merchants.merchant_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(String(120), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    product_type: Mapped[str] = mapped_column(
        SAEnum("physical", "digital", "service", name="product_type_enum"),
        nullable=False,
        default="physical",
    )
    base_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="TRY")
    status: Mapped[str] = mapped_column(
        SAEnum("draft", "active", "archived", name="product_status_enum"),
        nullable=False,
        default="draft",
    )
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp()
    )

    merchant: Mapped["Merchant"] = relationship(back_populates="products")
    # R11 weak
    variants: Mapped[list["ProductVariant"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
    # R10 bridge
    category_links: Mapped[list["ProductCategory"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
    reviews: Mapped[list["Review"]] = relationship(back_populates="product", cascade="all, delete-orphan")


class ProductVariant(Base):
    """R11: PRODUCTS → PV (weak entity, compound PK, identifying relationship)."""

    __tablename__ = "product_variants"
    __table_args__ = (
        UniqueConstraint("sku", name="ux_pv_sku"),
        CheckConstraint("price_override IS NULL OR price_override >= 0", name="ck_pv_price"),
    )

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.product_id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
    variant_no: Mapped[int] = mapped_column(Integer, primary_key=True)
    sku: Mapped[str] = mapped_column(String(80), nullable=False)
    option1_name: Mapped[str] = mapped_column(String(40), nullable=False, default="default")
    option1_value: Mapped[str] = mapped_column(String(80), nullable=False, default="default")
    price_override: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2))
    barcode: Mapped[Optional[str]] = mapped_column(String(64))
    is_default: Mapped[int] = mapped_column(TINYINT(1), nullable=False, default=0)

    product: Mapped["Product"] = relationship(back_populates="variants")
    inventory_rows: Mapped[list["Inventory"]] = relationship(
        back_populates="variant", cascade="all, delete-orphan"
    )


class Category(Base):
    """R7 + R9: merchant-scoped category tree (nullable self-FK for root)."""

    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint("merchant_id", "slug", name="ux_categories_merchant_slug"),
    )

    category_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    merchant_id: Mapped[int] = mapped_column(
        ForeignKey("merchants.merchant_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    parent_category_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("categories.category_id", ondelete="SET NULL", onupdate="CASCADE")
    )
    slug: Mapped[str] = mapped_column(String(120), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )

    merchant: Mapped["Merchant"] = relationship(back_populates="categories")
    # R9 recursive
    parent: Mapped[Optional["Category"]] = relationship(remote_side="Category.category_id", back_populates="children")
    children: Mapped[list["Category"]] = relationship(back_populates="parent")
    # R10 bridge
    product_links: Mapped[list["ProductCategory"]] = relationship(
        back_populates="category", cascade="all, delete-orphan"
    )


class ProductCategory(Base):
    """R10: PRODUCTS ⟷ CATEGORIES (M:N bridge)."""

    __tablename__ = "product_categories"

    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.product_id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.category_id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
    assigned_at: Mapped[dt.datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )

    product: Mapped["Product"] = relationship(back_populates="category_links")
    category: Mapped["Category"] = relationship(back_populates="product_links")
