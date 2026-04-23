"""Commerce zone: CARTS, CART_ITEMS, ORDERS, ORDER_ITEMS (weak), PAYMENTS, SHIPMENTS."""
from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    CheckConstraint,
    Computed,
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
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base

if TYPE_CHECKING:
    from .catalog import Merchant, ProductVariant
    from .engagement import DiscountUsage, Review
    from .identity import Customer
    from .inventory import Warehouse


class Cart(Base):
    """R13 + R14: merchant-scoped cart, nullable customer (guest cart)."""

    __tablename__ = "carts"
    __table_args__ = (
        UniqueConstraint("merchant_id", "session_token", name="ux_carts_session"),
    )

    cart_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    merchant_id: Mapped[int] = mapped_column(
        ForeignKey("merchants.merchant_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    customer_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("customers.user_id", ondelete="SET NULL", onupdate="CASCADE")
    )
    session_token: Mapped[str] = mapped_column(String(64), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="TRY")
    status: Mapped[str] = mapped_column(
        SAEnum("active", "abandoned", "converted", name="cart_status_enum"),
        nullable=False,
        default="active",
    )
    expires_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )

    merchant: Mapped["Merchant"] = relationship(back_populates="carts")
    customer: Mapped[Optional["Customer"]] = relationship(back_populates="carts")
    items: Mapped[list["CartItem"]] = relationship(
        back_populates="cart", cascade="all, delete-orphan"
    )


class CartItem(Base):
    """R15: CARTS ⟷ PV bridge (M:N) with {quantity}."""

    __tablename__ = "cart_items"
    __table_args__ = (
        ForeignKeyConstraint(
            ["product_id", "variant_no"],
            ["product_variants.product_id", "product_variants.variant_no"],
            name="fk_ci_variant",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        CheckConstraint("quantity >= 1", name="ck_ci_qty"),
    )

    cart_id: Mapped[int] = mapped_column(
        ForeignKey("carts.cart_id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
    product_id: Mapped[int] = mapped_column(primary_key=True)
    variant_no: Mapped[int] = mapped_column(primary_key=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    added_at: Mapped[dt.datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )

    cart: Mapped["Cart"] = relationship(back_populates="items")
    variant: Mapped["ProductVariant"] = relationship()


class Order(Base):
    """R16 + R17: merchant-scoped order placed by a customer. Generated grand_total."""

    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("merchant_id", "order_number", name="ux_orders_number"),
        CheckConstraint("subtotal >= 0 AND discount_total >= 0 AND tax_total >= 0", name="ck_orders_amounts"),
    )

    order_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    merchant_id: Mapped[int] = mapped_column(
        ForeignKey("merchants.merchant_id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    customer_user_id: Mapped[int] = mapped_column(
        ForeignKey("customers.user_id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    order_number: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(
        SAEnum("pending", "paid", "fulfilled", "canceled", "refunded", name="order_status_enum"),
        nullable=False,
        default="pending",
    )
    ship_line1: Mapped[str] = mapped_column(String(255), nullable=False)
    ship_line2: Mapped[Optional[str]] = mapped_column(String(255))
    ship_city: Mapped[str] = mapped_column(String(100), nullable=False)
    ship_country: Mapped[str] = mapped_column(String(2), nullable=False)
    ship_zip: Mapped[str] = mapped_column(String(20), nullable=False)
    bill_line1: Mapped[str] = mapped_column(String(255), nullable=False)
    bill_line2: Mapped[Optional[str]] = mapped_column(String(255))
    bill_city: Mapped[str] = mapped_column(String(100), nullable=False)
    bill_country: Mapped[str] = mapped_column(String(2), nullable=False)
    bill_zip: Mapped[str] = mapped_column(String(20), nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discount_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    tax_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    grand_total: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        Computed("subtotal - discount_total + tax_total", persisted=True),
    )
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="TRY")
    placed_at: Mapped[dt.datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )
    canceled_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime)

    merchant: Mapped["Merchant"] = relationship(back_populates="orders")
    customer: Mapped["Customer"] = relationship(back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
    payments: Mapped[list["Payment"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
    shipments: Mapped[list["Shipment"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )
    discount_usages: Mapped[list["DiscountUsage"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )


class OrderItem(Base):
    """R18: ORDERS → ORDER_ITEMS (weak, compound PK, identifying).
    R19: FK to PRODUCT_VARIANTS preserves reference at time of sale.
    """

    __tablename__ = "order_items"
    __table_args__ = (
        ForeignKeyConstraint(
            ["product_id", "variant_no"],
            ["product_variants.product_id", "product_variants.variant_no"],
            name="fk_oi_variant",
            ondelete="RESTRICT",
            onupdate="CASCADE",
        ),
        CheckConstraint("unit_price >= 0 AND quantity >= 1", name="ck_oi_amounts"),
    )

    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.order_id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
    line_no: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(Integer, nullable=False)
    variant_no: Mapped[int] = mapped_column(Integer, nullable=False)
    product_title: Mapped[str] = mapped_column(String(255), nullable=False)
    variant_label: Mapped[str] = mapped_column(String(160), nullable=False)
    sku: Mapped[str] = mapped_column(String(80), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    line_subtotal: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        Computed("unit_price * quantity", persisted=True),
    )

    order: Mapped["Order"] = relationship(back_populates="items")
    variant: Mapped["ProductVariant"] = relationship()


class Payment(Base):
    """R20: ORDERS → PAYMENTS (1:N, partial/total)."""

    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_payments_amount"),
    )

    payment_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.order_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    merchant_id: Mapped[int] = mapped_column(
        ForeignKey("merchants.merchant_id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    payment_method: Mapped[str] = mapped_column(
        SAEnum("card", "bank_transfer", "cash_on_delivery", "wallet", name="payment_method_enum"),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="TRY")
    status: Mapped[str] = mapped_column(
        SAEnum("initiated", "authorized", "captured", "failed", "refunded", name="payment_status_enum"),
        nullable=False,
        default="initiated",
    )
    gateway_reference: Mapped[Optional[str]] = mapped_column(String(120))
    processed_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )

    order: Mapped["Order"] = relationship(back_populates="payments")
    merchant: Mapped["Merchant"] = relationship(back_populates="payments")


class Shipment(Base):
    """R21: ORDERS → SHIPMENTS (1:N, partial/total) + R22: WAREHOUSES → SHIPMENTS (1:N)."""

    __tablename__ = "shipments"

    shipment_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.order_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    merchant_id: Mapped[int] = mapped_column(
        ForeignKey("merchants.merchant_id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    warehouse_id: Mapped[int] = mapped_column(
        ForeignKey("warehouses.warehouse_id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )
    carrier: Mapped[str] = mapped_column(String(80), nullable=False)
    tracking_number: Mapped[Optional[str]] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(
        SAEnum(
            "preparing", "dispatched", "in_transit", "delivered", "failed", "returned",
            name="shipment_status_enum",
        ),
        nullable=False,
        default="preparing",
    )
    ship_line1: Mapped[str] = mapped_column(String(255), nullable=False)
    ship_line2: Mapped[Optional[str]] = mapped_column(String(255))
    ship_city: Mapped[str] = mapped_column(String(100), nullable=False)
    ship_country: Mapped[str] = mapped_column(String(2), nullable=False)
    ship_zip: Mapped[str] = mapped_column(String(20), nullable=False)
    shipped_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime)
    delivered_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )

    order: Mapped["Order"] = relationship(back_populates="shipments")
    merchant: Mapped["Merchant"] = relationship(back_populates="shipments")
    warehouse: Mapped["Warehouse"] = relationship(back_populates="shipments")
