"""Engagement + Audit zone: REVIEWS, DISCOUNTS, DISCOUNT_USAGES, ACTIVITY_LOG."""
from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base

if TYPE_CHECKING:
    from .catalog import Merchant, Product
    from .commerce import Order
    from .identity import Customer, Staff, User


class Review(Base):
    """R23: PRODUCTS ← REVIEWED_AS → REVIEWS ← WRITTEN_BY → CUSTOMER.
    Modeled as a full entity (not a bridge); FKs to product + customer are NOT NULL."""

    __tablename__ = "reviews"
    __table_args__ = (
        CheckConstraint("rating BETWEEN 1 AND 5", name="ck_reviews_rating"),
    )

    review_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.product_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    customer_user_id: Mapped[int] = mapped_column(
        ForeignKey("customers.user_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    merchant_id: Mapped[int] = mapped_column(
        ForeignKey("merchants.merchant_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    order_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("orders.order_id", ondelete="SET NULL", onupdate="CASCADE")
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    is_verified_purchase: Mapped[int] = mapped_column(TINYINT(1), nullable=False, default=0)
    helpful_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(
        SAEnum("pending", "published", "rejected", name="review_status_enum"),
        nullable=False,
        default="published",
    )
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )

    product: Mapped["Product"] = relationship(back_populates="reviews")
    customer: Mapped["Customer"] = relationship(back_populates="reviews")
    merchant: Mapped["Merchant"] = relationship(back_populates="reviews")
    order: Mapped[Optional["Order"]] = relationship()


class Discount(Base):
    """R24 source-side entity: merchant-scoped promo codes."""

    __tablename__ = "discounts"
    __table_args__ = (
        UniqueConstraint("merchant_id", "code", name="ux_discounts_code"),
        CheckConstraint("value >= 0", name="ck_discounts_value"),
        CheckConstraint("ends_at IS NULL OR ends_at > starts_at", name="ck_discounts_window"),
    )

    discount_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    merchant_id: Mapped[int] = mapped_column(
        ForeignKey("merchants.merchant_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    discount_type: Mapped[str] = mapped_column(
        SAEnum("percentage", "fixed_amount", "free_shipping", name="discount_type_enum"),
        nullable=False,
    )
    value: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    min_order_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, default=Decimal("0.00")
    )
    max_uses: Mapped[Optional[int]] = mapped_column(Integer)
    max_uses_per_customer: Mapped[Optional[int]] = mapped_column(Integer)
    used_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    starts_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False)
    ends_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime)
    is_active: Mapped[int] = mapped_column(TINYINT(1), nullable=False, default=1)
    created_by: Mapped[int] = mapped_column(
        ForeignKey("staff.user_id", ondelete="RESTRICT", onupdate="CASCADE"),
        nullable=False,
    )

    merchant: Mapped["Merchant"] = relationship(back_populates="discounts")
    usages: Mapped[list["DiscountUsage"]] = relationship(
        back_populates="discount", cascade="all, delete-orphan"
    )


class DiscountUsage(Base):
    """R24: DISCOUNTS ⟷ ORDERS bridge (M:N)."""

    __tablename__ = "discount_usages"

    discount_id: Mapped[int] = mapped_column(
        ForeignKey("discounts.discount_id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.order_id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
    used_at: Mapped[dt.datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )
    amount_applied: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    discount: Mapped["Discount"] = relationship(back_populates="usages")
    order: Mapped["Order"] = relationship(back_populates="discount_usages")


class ActivityLog(Base):
    """R25: USERS → ACTIVITY_LOG (1:N, partial/partial).
    Polymorphic association: entity_type + entity_id without FK.
    """

    __tablename__ = "activity_log"

    event_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    merchant_id: Mapped[int] = mapped_column(
        ForeignKey("merchants.merchant_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    actor_user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.user_id", ondelete="SET NULL", onupdate="CASCADE")
    )
    actor_type: Mapped[str] = mapped_column(
        SAEnum("user", "system", "webhook", "cron", name="actor_type_enum"),
        nullable=False,
        default="user",
    )
    entity_type: Mapped[str] = mapped_column(String(40), nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    action: Mapped[str] = mapped_column(String(60), nullable=False)
    payload_json: Mapped[Optional[dict]] = mapped_column(JSON)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45))
    occurred_at: Mapped[dt.datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )

    merchant: Mapped["Merchant"] = relationship(back_populates="activity_events")
    actor: Mapped[Optional["User"]] = relationship(back_populates="activity_events")
