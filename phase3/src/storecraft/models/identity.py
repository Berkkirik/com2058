"""Identity zone models: USERS (supertype) + CUSTOMER / STAFF / PLATFORM_ADMIN (IS_A subtypes)."""
from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    func,
)
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base

if TYPE_CHECKING:
    from .catalog import MerchantStaff
    from .commerce import Cart, Order
    from .engagement import ActivityLog, Review


class User(Base):
    """Global user identity — supertype; specializes into Customer/Staff/PlatformAdmin via IS_A."""

    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(32))
    is_active: Mapped[int] = mapped_column(TINYINT(1), nullable=False, default=1)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )

    # Subtypes
    customer: Mapped[Optional["Customer"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    staff: Mapped[Optional["Staff"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    platform_admin: Mapped[Optional["PlatformAdmin"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )

    # R25: USERS → ACTIVITY_LOG (1:N, partial on both sides)
    activity_events: Mapped[list["ActivityLog"]] = relationship(
        back_populates="actor",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User #{self.user_id} {self.email}>"


class Customer(Base):
    """R1: USERS IS_A CUSTOMER (1:1 partial/total). Customer-specific attributes."""

    __tablename__ = "customers"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
    default_shipping_line1: Mapped[Optional[str]] = mapped_column(String(255))
    default_shipping_line2: Mapped[Optional[str]] = mapped_column(String(255))
    default_shipping_city: Mapped[Optional[str]] = mapped_column(String(100))
    default_shipping_country: Mapped[Optional[str]] = mapped_column(String(2))
    default_shipping_zip: Mapped[Optional[str]] = mapped_column(String(20))
    date_of_birth: Mapped[Optional[dt.date]] = mapped_column(Date)
    loyalty_points: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    accepts_marketing: Mapped[int] = mapped_column(TINYINT(1), nullable=False, default=0)

    # Back to supertype
    user: Mapped["User"] = relationship(back_populates="customer")

    # R14: CUSTOMER → CARTS (1:N, partial/partial at-most-1)
    carts: Mapped[list["Cart"]] = relationship(back_populates="customer")

    # R17: CUSTOMER → ORDERS (1:N, partial/total)
    orders: Mapped[list["Order"]] = relationship(back_populates="customer")

    # R23b: CUSTOMER → REVIEWS (WRITTEN_BY, 1:N)
    reviews: Mapped[list["Review"]] = relationship(
        back_populates="customer", cascade="all, delete-orphan"
    )


class Staff(Base):
    """R2: USERS IS_A STAFF (1:1 partial/total). Employment record for merchant staff members."""

    __tablename__ = "staff"
    __table_args__ = (
        CheckConstraint("commission_rate >= 0 AND commission_rate <= 1", name="ck_staff_commission"),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
    employment_type: Mapped[str] = mapped_column(
        SAEnum("full_time", "part_time", "contractor", name="employment_type_enum"),
        nullable=False,
        default="full_time",
    )
    hired_at: Mapped[dt.date] = mapped_column(Date, nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    commission_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, default=Decimal("0.0000")
    )
    employment_status: Mapped[str] = mapped_column(
        SAEnum("active", "suspended", "terminated", name="employment_status_enum"),
        nullable=False,
        default="active",
    )

    user: Mapped["User"] = relationship(back_populates="staff")

    # R5: MERCHANTS owner_user_id → STAFF (1:1, total on MERCHANTS side)
    owned_merchants: Mapped[list["Merchant"]] = relationship(back_populates="owner")

    # R4: STAFF ⟷ MERCHANTS (M:N via merchant_staff bridge)
    memberships: Mapped[list["MerchantStaff"]] = relationship(
        back_populates="staff_member", cascade="all, delete-orphan"
    )


class PlatformAdmin(Base):
    """R3: USERS IS_A PLATFORM_ADMIN (1:1 partial/total). Internal support/moderation role."""

    __tablename__ = "platform_admins"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.user_id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
    admin_level: Mapped[str] = mapped_column(
        SAEnum("support", "moderator", "superadmin", name="admin_level_enum"),
        nullable=False,
        default="support",
    )
    department: Mapped[str] = mapped_column(String(80), nullable=False)
    hired_at: Mapped[dt.date] = mapped_column(Date, nullable=False)

    user: Mapped["User"] = relationship(back_populates="platform_admin")


# Late import — Merchant referenced in Staff.owned_merchants.back_populates
from .catalog import Merchant  # noqa: E402,F401
