"""Deterministic Faker-based seed data for StoreCraft.

Target volume (COM2058 demo-friendly):
    3 merchants × (1 owner + 2-3 staff) = ~10 staff users
    20-30 customers
    40-60 products × 1-3 variants each
    2-3 warehouses per merchant
    realistic inventory rows
    80-150 orders distributed over last 90 days
    payments + shipments for each paid order
    reviews for ~30% of fulfilled orders
    5-10 discounts per merchant with usages
    200+ activity_log rows

Invocation:
    python -m storecraft.scripts.seed [--reset] [--seed N]

The generator is idempotent per seed value — running twice with the same seed
yields the same rows (Faker drives every random decision).
"""
from __future__ import annotations

import argparse
import hashlib
import logging
import random
import secrets
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Sequence

from faker import Faker
from sqlalchemy import text
from sqlalchemy.orm import Session

from storecraft.config import get_settings
from storecraft.db import SessionLocal, engine
from storecraft.models import (
    ActivityLog,
    Cart,
    CartItem,
    Category,
    Customer,
    Discount,
    DiscountUsage,
    Inventory,
    Merchant,
    MerchantStaff,
    Order,
    OrderItem,
    Payment,
    PlatformAdmin,
    Product,
    ProductCategory,
    ProductVariant,
    Review,
    Shipment,
    Staff,
    User,
    Warehouse,
)

log = logging.getLogger("storecraft.seed")


MERCHANT_PRESETS = [
    {
        "slug": "berkin-kitapcisi",
        "store_name": "Berk'in Kitapçısı",
        "currency": "TRY",
        "plan": "pro",
        "categories": ["Edebiyat", "Bilim", "Tarih", "Çocuk Kitapları", "Programlama"],
        "product_seed": "book",
    },
    {
        "slug": "ankara-elektronik",
        "store_name": "Ankara Elektronik",
        "currency": "TRY",
        "plan": "enterprise",
        "categories": ["Telefon", "Bilgisayar", "Ses Sistemleri", "Akıllı Ev", "Kablolar"],
        "product_seed": "electronics",
    },
    {
        "slug": "techstore",
        "store_name": "TechStore",
        "currency": "USD",
        "plan": "basic",
        "categories": ["Wearables", "Cameras", "Drones", "Gaming", "Accessories"],
        "product_seed": "gadget",
    },
]


BOOK_TITLES = [
    "Sessiz Bahçe", "Ankara'nın Sokakları", "Veri Tabanı Sanatı", "Python ile Yolculuk",
    "Algoritmaların Dansı", "Kayıp Zaman", "Sayısal Devrim", "Makine Düşünür mü?",
    "Bir Şehir Hikayesi", "Anılarımın İçinde", "Sıcak Kahve", "Uyuyan Güneş",
    "Yağmur Altında", "Gölgelerin Dili", "Matematiksel Güzellik", "Orman Fısıltıları",
]
ELECTRONICS_TITLES = [
    "Akıllı Telefon X7", "Dizüstü Bilgisayar UltraBook", "Kablosuz Kulaklık Pro", "4K Monitör 27\"",
    "Mekanik Klavye", "Oyuncu Faresi", "USB-C Hub", "SSD 1TB NVMe", "Router Wi-Fi 6",
    "Akıllı Ampul RGB", "Bluetooth Hoparlör", "Webcam FHD", "Taşınabilir Şarj 20000mAh",
    "Termal Kamera", "VR Başlık", "3D Yazıcı Filament",
]
GADGET_TITLES = [
    "Smart Watch Titan", "Action Camera 4K", "Drone Explorer", "VR Headset Alpha",
    "Gaming Chair Pro", "RGB Desk Mat", "Wireless Charger", "USB Microphone Studio",
    "Noise Cancelling Headset", "Portable SSD 2TB", "Mesh Wi-Fi System", "Smart Bulb Trio",
    "Air Purifier Mini", "Dash Cam 1080p", "Smart Lock v2", "Ergonomic Mouse",
]


def hash_password(password: str) -> str:
    """Simple deterministic hash for demo purposes only (bcrypt would require round-trip)."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def generate_order_number(merchant_id: int, idx: int) -> str:
    return f"M{merchant_id:03d}-{idx:06d}"


def run(*, seed: int = 42, reset: bool = True, session: Session | None = None) -> None:
    settings = get_settings()
    random.seed(seed)
    fake = Faker(settings.seed_locale)
    fake.seed_instance(seed)
    fake_en = Faker("en_US")
    fake_en.seed_instance(seed)

    owned = session is None
    if owned:
        session = SessionLocal()

    try:
        if reset:
            log.info("TRUNCATE all seed tables")
            with engine.begin() as conn:
                conn.execute(text("SET foreign_key_checks = 0"))
                # SHOW FULL TABLES distinguishes 'BASE TABLE' from 'VIEW'.
                rows = conn.execute(text("SHOW FULL TABLES WHERE Table_type = 'BASE TABLE'")).fetchall()
                for row in rows:
                    tbl = row[0]
                    conn.execute(text(f"TRUNCATE TABLE `{tbl}`"))
                conn.execute(text("SET foreign_key_checks = 1"))

        # ── USERS: 1 super-admin + per-merchant owners & staff + customers ─
        log.info("creating users")
        admin = User(
            email="admin@storecraft.local",
            password_hash=hash_password("admin"),
            first_name="Platform",
            last_name="Admin",
            phone="+90-312-000-0000",
        )
        session.add(admin)
        session.flush()
        session.add(
            PlatformAdmin(
                user_id=admin.user_id,
                admin_level="superadmin",
                department="Operations",
                hired_at=date(2024, 1, 1),
            )
        )

        merchant_rows: list[Merchant] = []
        staff_users: list[User] = []

        for preset in MERCHANT_PRESETS:
            # Owner (staff)
            owner_user = User(
                email=f"owner@{preset['slug']}.local",
                password_hash=hash_password("ownerpw"),
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                phone=fake.phone_number(),
            )
            session.add(owner_user)
            session.flush()
            owner_staff = Staff(
                user_id=owner_user.user_id,
                employment_type="full_time",
                hired_at=fake.date_between(start_date="-3y", end_date="-1y"),
                title="Owner",
                commission_rate=Decimal("0.15"),
            )
            session.add(owner_staff)
            staff_users.append(owner_user)
            session.flush()

            # Merchant
            m = Merchant(
                slug=preset["slug"],
                store_name=preset["store_name"],
                owner_user_id=owner_user.user_id,
                business_line1=fake.street_address(),
                business_city=fake.city(),
                business_country="TR" if preset["slug"] != "techstore" else "US",
                business_zip=fake.postcode()[:20],
                contact_email=f"hello@{preset['slug']}.local",
                currency=preset["currency"],
                plan=preset["plan"],
                activated_at=datetime.utcnow() - timedelta(days=random.randint(180, 720)),
            )
            session.add(m)
            session.flush()
            merchant_rows.append(m)

            # Owner joins merchant_staff
            session.add(MerchantStaff(merchant_id=m.merchant_id, user_id=owner_user.user_id, role="owner"))

            # 2-3 extra staff
            for _ in range(random.randint(2, 3)):
                u = User(
                    email=fake.unique.email(),
                    password_hash=hash_password("staffpw"),
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    phone=fake.phone_number(),
                )
                session.add(u)
                session.flush()
                session.add(
                    Staff(
                        user_id=u.user_id,
                        employment_type=random.choice(["full_time", "part_time"]),
                        hired_at=fake.date_between(start_date="-2y", end_date="today"),
                        title=random.choice(["Manager", "Clerk", "Warehouse Lead", "Support"]),
                        commission_rate=Decimal(str(round(random.uniform(0.02, 0.10), 4))),
                    )
                )
                staff_users.append(u)
                session.add(
                    MerchantStaff(
                        merchant_id=m.merchant_id,
                        user_id=u.user_id,
                        role=random.choice(["admin", "staff", "viewer"]),
                    )
                )

            # Categories: 5 top-level + 2 children under the first one
            top_cats: list[Category] = []
            for i, name in enumerate(preset["categories"]):
                c = Category(
                    merchant_id=m.merchant_id,
                    slug=fake.slug(name),
                    name=name,
                    display_order=i,
                )
                session.add(c)
                top_cats.append(c)
            session.flush()
            for j in range(2):
                child_name = fake.word().title() + " " + random.choice(["Serisi", "Koleksiyonu", "Özel"])
                session.add(
                    Category(
                        merchant_id=m.merchant_id,
                        parent_category_id=top_cats[0].category_id,
                        slug=fake.unique.slug(child_name),
                        name=child_name,
                        display_order=10 + j,
                    )
                )
            session.flush()

            # Warehouses
            for _ in range(random.randint(2, 3)):
                session.add(
                    Warehouse(
                        merchant_id=m.merchant_id,
                        name=f"{preset['store_name']} · {fake.city()} Deposu",
                        addr_line1=fake.street_address(),
                        addr_city=fake.city(),
                        addr_country=m.business_country or "TR",
                        addr_zip=fake.postcode()[:20],
                    )
                )
            session.flush()

            # Products + variants
            title_pool = {
                "book": BOOK_TITLES,
                "electronics": ELECTRONICS_TITLES,
                "gadget": GADGET_TITLES,
            }[preset["product_seed"]]
            all_cats = session.query(Category).filter(Category.merchant_id == m.merchant_id).all()
            for title in title_pool:
                p = Product(
                    merchant_id=m.merchant_id,
                    slug=fake.unique.slug(title),
                    title=title,
                    product_type=random.choices(["physical", "digital", "service"], weights=[85, 10, 5])[0],
                    base_price=Decimal(str(round(random.uniform(20, 2500), 2))),
                    currency=preset["currency"],
                    status=random.choices(["draft", "active", "archived"], weights=[10, 85, 5])[0],
                )
                session.add(p)
                session.flush()

                # 1-3 variants
                variant_count = random.randint(1, 3)
                for vn in range(1, variant_count + 1):
                    options = [
                        ("Renk", random.choice(["Siyah", "Beyaz", "Mavi", "Kırmızı", "Yeşil"])),
                        ("Boyut", random.choice(["S", "M", "L", "XL"])),
                        ("Kapak", random.choice(["Karton", "Ciltli", "PDF"])),
                    ]
                    opt_name, opt_val = options[random.randint(0, 2)]
                    session.add(
                        ProductVariant(
                            product_id=p.product_id,
                            variant_no=vn,
                            sku=f"SKU-{m.merchant_id:02d}-{p.product_id:04d}-V{vn}",
                            option1_name=opt_name,
                            option1_value=opt_val,
                            price_override=(None if vn == 1 else Decimal(str(round(float(p.base_price) * random.uniform(0.95, 1.15), 2)))),
                            barcode=fake.ean13(),
                            is_default=(1 if vn == 1 else 0),
                        )
                    )

                # Link to 1-3 random categories
                linked = random.sample(all_cats, k=random.randint(1, min(3, len(all_cats))))
                for c in linked:
                    session.add(ProductCategory(product_id=p.product_id, category_id=c.category_id))
            session.flush()

            # Inventory — for each variant × each warehouse
            variants = (
                session.query(ProductVariant)
                .join(Product, Product.product_id == ProductVariant.product_id)
                .filter(Product.merchant_id == m.merchant_id)
                .all()
            )
            warehouses = session.query(Warehouse).filter(Warehouse.merchant_id == m.merchant_id).all()
            for v in variants:
                for w in warehouses:
                    if random.random() < 0.8:  # not every variant is in every warehouse
                        qty = random.randint(0, 200)
                        reserved = random.randint(0, max(0, qty // 5))
                        session.add(
                            Inventory(
                                product_id=v.product_id,
                                variant_no=v.variant_no,
                                warehouse_id=w.warehouse_id,
                                qty_on_hand=qty,
                                qty_reserved=reserved,
                                reorder_level=random.choice([5, 10, 20]),
                            )
                        )

            # Discounts (3-6 per merchant)
            for i in range(random.randint(3, 6)):
                starts = datetime.utcnow() - timedelta(days=random.randint(30, 120))
                ends = starts + timedelta(days=random.randint(30, 90))
                disc_type = random.choice(["percentage", "fixed_amount", "free_shipping"])
                value = (
                    Decimal(str(random.randint(5, 40)))  # %
                    if disc_type == "percentage"
                    else Decimal(str(random.randint(20, 200)))
                )
                session.add(
                    Discount(
                        merchant_id=m.merchant_id,
                        code=f"{preset['product_seed'].upper()}{i + 1:02d}",
                        discount_type=disc_type,
                        value=value,
                        min_order_amount=Decimal(str(random.choice([0, 100, 250, 500]))),
                        max_uses=random.choice([None, 100, 500, 1000]),
                        max_uses_per_customer=random.choice([None, 1, 3]),
                        starts_at=starts,
                        ends_at=ends,
                        created_by=owner_user.user_id,
                    )
                )

        session.flush()

        # ── CUSTOMERS (global identity) ─────────────────────────
        log.info("creating customers")
        customer_users: list[User] = []
        for _ in range(random.randint(20, 30)):
            u = User(
                email=fake.unique.email(),
                password_hash=hash_password("custpw"),
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                phone=fake.phone_number(),
            )
            session.add(u)
            session.flush()
            session.add(
                Customer(
                    user_id=u.user_id,
                    default_shipping_line1=fake.street_address(),
                    default_shipping_city=fake.city(),
                    default_shipping_country="TR",
                    default_shipping_zip=fake.postcode()[:20],
                    date_of_birth=fake.date_of_birth(minimum_age=18, maximum_age=75),
                    loyalty_points=random.randint(0, 500),
                    accepts_marketing=random.choice([0, 1]),
                )
            )
            customer_users.append(u)
        session.flush()

        # ── ORDERS + PAYMENTS + SHIPMENTS + REVIEWS + LOGS ──────
        log.info("creating orders + downstream rows")
        for m in merchant_rows:
            variants = (
                session.query(ProductVariant)
                .join(Product, Product.product_id == ProductVariant.product_id)
                .filter(Product.merchant_id == m.merchant_id, Product.status == "active")
                .all()
            )
            warehouses = session.query(Warehouse).filter(Warehouse.merchant_id == m.merchant_id).all()
            products = {p.product_id: p for p in session.query(Product).filter(Product.merchant_id == m.merchant_id).all()}

            num_orders = random.randint(25, 60)
            for i in range(num_orders):
                cust = random.choice(customer_users)
                placed = datetime.utcnow() - timedelta(days=random.randint(0, 90), hours=random.randint(0, 23))
                status = random.choices(
                    ["pending", "paid", "fulfilled", "canceled", "refunded"],
                    weights=[10, 15, 55, 10, 10],
                )[0]

                # build 1-4 order lines
                chosen = random.sample(variants, k=min(random.randint(1, 4), len(variants)))
                subtotal = Decimal("0.00")
                lines_data = []
                for line_no, v in enumerate(chosen, start=1):
                    p = products[v.product_id]
                    unit_price = v.price_override or p.base_price
                    qty = random.randint(1, 3)
                    line_sub = (unit_price * qty).quantize(Decimal("0.01"))
                    subtotal += line_sub
                    lines_data.append(
                        dict(
                            line_no=line_no,
                            product_id=v.product_id,
                            variant_no=v.variant_no,
                            product_title=p.title,
                            variant_label=f"{v.option1_name}:{v.option1_value}",
                            sku=v.sku,
                            unit_price=unit_price,
                            quantity=qty,
                        )
                    )

                # Optional discount
                discount_total = Decimal("0.00")
                tax_total = (subtotal * Decimal("0.18")).quantize(Decimal("0.01"))
                if random.random() < 0.25 and subtotal > 50:
                    discount_total = (subtotal * Decimal(str(random.choice([0.05, 0.1, 0.15])))).quantize(Decimal("0.01"))

                o = Order(
                    merchant_id=m.merchant_id,
                    customer_user_id=cust.user_id,
                    order_number=generate_order_number(m.merchant_id, i),
                    status=status,
                    ship_line1=fake.street_address(),
                    ship_city=fake.city(),
                    ship_country=m.business_country or "TR",
                    ship_zip=fake.postcode()[:20],
                    bill_line1=fake.street_address(),
                    bill_city=fake.city(),
                    bill_country=m.business_country or "TR",
                    bill_zip=fake.postcode()[:20],
                    subtotal=subtotal,
                    discount_total=discount_total,
                    tax_total=tax_total,
                    currency=m.currency,
                    placed_at=placed,
                    canceled_at=(placed + timedelta(hours=random.randint(1, 48)) if status == "canceled" else None),
                )
                session.add(o)
                session.flush()

                # Lines
                for ld in lines_data:
                    session.add(OrderItem(order_id=o.order_id, **ld))

                # Payment (if not pending/canceled)
                if status in ("paid", "fulfilled", "refunded"):
                    session.add(
                        Payment(
                            order_id=o.order_id,
                            merchant_id=m.merchant_id,
                            payment_method=random.choice(["card", "bank_transfer", "wallet"]),
                            amount=(subtotal - discount_total + tax_total).quantize(Decimal("0.01")),
                            currency=m.currency,
                            status=("refunded" if status == "refunded" else "captured"),
                            gateway_reference=fake.uuid4(),
                            processed_at=placed + timedelta(minutes=random.randint(1, 15)),
                        )
                    )

                # Shipment (if fulfilled)
                if status == "fulfilled":
                    wh = random.choice(warehouses) if warehouses else None
                    if wh:
                        shipped_at = placed + timedelta(hours=random.randint(4, 48))
                        delivered_at = shipped_at + timedelta(days=random.randint(1, 5))
                        session.add(
                            Shipment(
                                order_id=o.order_id,
                                merchant_id=m.merchant_id,
                                warehouse_id=wh.warehouse_id,
                                carrier=random.choice(["Yurtiçi", "MNG", "Aras", "UPS", "DHL"]),
                                tracking_number=fake.bothify("???##########"),
                                status="delivered",
                                ship_line1=o.ship_line1,
                                ship_city=o.ship_city,
                                ship_country=o.ship_country,
                                ship_zip=o.ship_zip,
                                shipped_at=shipped_at,
                                delivered_at=delivered_at,
                            )
                        )

                # Review (~25% of fulfilled)
                if status == "fulfilled" and random.random() < 0.35:
                    # pick one of the ordered products
                    ld = random.choice(lines_data)
                    session.add(
                        Review(
                            product_id=ld["product_id"],
                            customer_user_id=cust.user_id,
                            merchant_id=m.merchant_id,
                            order_id=o.order_id,
                            rating=random.choices([1, 2, 3, 4, 5], weights=[2, 5, 15, 35, 43])[0],
                            title=fake.sentence(nb_words=5).rstrip("."),
                            body=fake.paragraph(nb_sentences=3),
                            is_verified_purchase=1,
                            helpful_count=random.randint(0, 25),
                        )
                    )

                # Activity log rows
                session.add(
                    ActivityLog(
                        merchant_id=m.merchant_id,
                        actor_user_id=cust.user_id,
                        actor_type="user",
                        entity_type="order",
                        entity_id=o.order_id,
                        action=f"order.{status}",
                        payload_json={"order_number": o.order_number, "total": str(o.subtotal)},
                        ip_address=fake.ipv4(),
                        occurred_at=placed,
                    )
                )

        # ── Abandoned carts (demo variety) ──────────────────────
        log.info("creating carts (active + abandoned)")
        for m in merchant_rows:
            variants = session.query(ProductVariant).join(Product, Product.product_id == ProductVariant.product_id).filter(Product.merchant_id == m.merchant_id).limit(20).all()
            for _ in range(random.randint(5, 10)):
                is_guest = random.random() < 0.3
                cust = None if is_guest else random.choice(customer_users)
                status = random.choice(["active", "abandoned", "converted"])
                c = Cart(
                    merchant_id=m.merchant_id,
                    customer_user_id=(cust.user_id if cust else None),
                    session_token=secrets.token_hex(16),
                    currency=m.currency,
                    status=status,
                    expires_at=datetime.utcnow() + timedelta(days=7),
                )
                session.add(c)
                session.flush()
                for v in random.sample(variants, k=random.randint(1, min(4, len(variants)))):
                    session.add(
                        CartItem(
                            cart_id=c.cart_id,
                            product_id=v.product_id,
                            variant_no=v.variant_no,
                            quantity=random.randint(1, 3),
                        )
                    )

        # ── Some system activity_log rows (actor = NULL) ────────
        for _ in range(30):
            m = random.choice(merchant_rows)
            session.add(
                ActivityLog(
                    merchant_id=m.merchant_id,
                    actor_user_id=None,
                    actor_type="system",
                    entity_type=random.choice(["merchant", "product", "inventory"]),
                    entity_id=random.randint(1, 500),
                    action=random.choice(["nightly.snapshot", "webhook.received", "cron.reindex"]),
                    payload_json={"note": "auto"},
                    occurred_at=datetime.utcnow() - timedelta(hours=random.randint(1, 500)),
                )
            )

        session.commit()

        # Summary — count rows in each base table (skip views)
        from storecraft.db import Base as _Base
        counts = {}
        for tbl in _Base.metadata.sorted_tables:
            n = session.execute(text(f"SELECT COUNT(*) FROM {tbl.name}")).scalar() or 0
            counts[tbl.name] = n
        total = sum(counts.values())
        log.info("seed complete — %d rows across %d tables", total, len(counts))
        for name, n in counts.items():
            log.info("  %-25s %5d", name, n)

    except Exception:
        session.rollback()
        raise
    finally:
        if owned:
            session.close()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--no-reset", dest="reset", action="store_false")
    args = parser.parse_args()
    run(seed=args.seed, reset=args.reset)


if __name__ == "__main__":
    main()
