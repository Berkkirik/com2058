"""SQLAlchemy ORM models — one module per ER diagram zone.

Every model inherits from `storecraft.db.Base` so `Base.metadata` contains the
full catalog for test harnesses and tools that need to introspect the schema.

Import order matters for back-populates resolution; keep this file as the
single public surface so tests can do `from storecraft.models import *`.
"""

from .identity import User, Customer, Staff, PlatformAdmin
from .catalog import (
    Merchant,
    MerchantStaff,
    Product,
    ProductVariant,
    Category,
    ProductCategory,
)
from .inventory import Warehouse, Inventory
from .commerce import (
    Cart,
    CartItem,
    Order,
    OrderItem,
    Payment,
    Shipment,
)
from .engagement import (
    Review,
    Discount,
    DiscountUsage,
    ActivityLog,
)

__all__ = [
    "User", "Customer", "Staff", "PlatformAdmin",
    "Merchant", "MerchantStaff", "Product", "ProductVariant",
    "Category", "ProductCategory",
    "Warehouse", "Inventory",
    "Cart", "CartItem", "Order", "OrderItem", "Payment", "Shipment",
    "Review", "Discount", "DiscountUsage", "ActivityLog",
]
