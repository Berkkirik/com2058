"""Inventory zone: WAREHOUSES + INVENTORY (ternary STOCKED_AT as its own relation)."""
from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    func,
)
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db import Base

if TYPE_CHECKING:
    from .catalog import Merchant, ProductVariant
    from .commerce import Shipment


class Warehouse(Base):
    """R8: MERCHANTS → WAREHOUSES (1:N partial/total)."""

    __tablename__ = "warehouses"

    warehouse_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    merchant_id: Mapped[int] = mapped_column(
        ForeignKey("merchants.merchant_id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    addr_line1: Mapped[str] = mapped_column(String(255), nullable=False)
    addr_line2: Mapped[Optional[str]] = mapped_column(String(255))
    addr_city: Mapped[str] = mapped_column(String(100), nullable=False)
    addr_country: Mapped[str] = mapped_column(String(2), nullable=False)
    addr_zip: Mapped[str] = mapped_column(String(20), nullable=False)
    is_active: Mapped[int] = mapped_column(TINYINT(1), nullable=False, default=1)
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp()
    )

    merchant: Mapped["Merchant"] = relationship(back_populates="warehouses")
    inventory_rows: Mapped[list["Inventory"]] = relationship(
        back_populates="warehouse", cascade="all, delete-orphan"
    )
    shipments: Mapped[list["Shipment"]] = relationship(back_populates="warehouse")


class Inventory(Base):
    """R12: STOCKED_AT ternary (PRODUCTS × PRODUCT_VARIANTS × WAREHOUSES).

    Composite PK = (product_id, variant_no, warehouse_id). Compound FK to
    product_variants (product_id, variant_no).
    """

    __tablename__ = "inventory"
    __table_args__ = (
        ForeignKeyConstraint(
            ["product_id", "variant_no"],
            ["product_variants.product_id", "product_variants.variant_no"],
            name="fk_inv_variant",
            ondelete="CASCADE",
            onupdate="CASCADE",
        ),
        CheckConstraint(
            "qty_on_hand >= 0 AND qty_reserved >= 0 AND reorder_level >= 0",
            name="ck_inv_nonneg",
        ),
        CheckConstraint("qty_reserved <= qty_on_hand", name="ck_inv_reserved_le_onhand"),
    )

    product_id: Mapped[int] = mapped_column(primary_key=True)
    variant_no: Mapped[int] = mapped_column(primary_key=True)
    warehouse_id: Mapped[int] = mapped_column(
        ForeignKey("warehouses.warehouse_id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
    qty_on_hand: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    qty_reserved: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reorder_level: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp()
    )

    variant: Mapped["ProductVariant"] = relationship(back_populates="inventory_rows")
    warehouse: Mapped["Warehouse"] = relationship(back_populates="inventory_rows")

    @property
    def qty_available(self) -> int:
        """Derived attribute (‡qty_available) from Phase 1."""
        return self.qty_on_hand - self.qty_reserved
