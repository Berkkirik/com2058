# StoreCraft — Phase 3 Implementation

**COM2058 Database Systems · Ankara University · Spring 2026**
**Author:** Berk Kırık (solo)

StoreCraft is a multi-tenant e-commerce platform reference implementation built on top of the Phase 2 ER diagram (17 entities, 25 relationships). This directory houses the Phase 3 implementation — MySQL DDL, FastAPI backend, server-rendered HTMX frontend, Faker-based seed data, and a showcase of 25 SQL queries demonstrating the full spectrum of relational operations.

> Phase 1 (requirements) lives in `../docs/phase1_data_requirements.md`.
> Phase 2 (ER diagram + explanation) lives in `../docs/phase2_er_diagram.drawio` and `../docs/phase2_er_explanation.md`.
> Phase 4 (report) renders to `../docs/phase4_report.pdf`.

## Quick Start

```bash
cp .env.example .env
docker compose up -d --build        # MySQL + app + phpMyAdmin
docker compose exec app python -m storecraft.scripts.init_db   # apply DDL, seed=42
docker compose exec app python -m storecraft.scripts.seed      # populate Faker data
open http://localhost:8000          # app
open http://localhost:8080          # phpMyAdmin (browse the schema)
```

## Ports

| Port | Service | Access |
|------|---------|--------|
| `8000` | FastAPI app | `http://localhost:8000` |
| `8080` | phpMyAdmin | `http://localhost:8080` — user `root` / password from `.env` |
| `3307` | MySQL (exposed) | `mysql -h 127.0.0.1 -P 3307 -u storecraft -p storecraft` |

## Stack

| Layer | Choice |
|-------|--------|
| Database | MySQL 8.0 (InnoDB, utf8mb4) |
| ORM | SQLAlchemy 2.0 (declarative) |
| Backend | FastAPI + Uvicorn |
| Frontend | Jinja2 server-rendered templates + HTMX (no SPA toolchain) |
| Seed | Faker (deterministic, seed=42) |
| Tests | pytest with coverage |
| Orchestration | Docker Compose |

## Demo Walkthrough

See [§7 of the README](#demo-walkthrough) after seeding. A typical path:

1. Land on the public catalog, browse products by category
2. Log in as customer `ayse@example.com` (seeded), add items to cart
3. Checkout → create order, payment, shipment
4. Switch role to merchant owner for "Berk'in Kitapçısı" → dashboard shows new order, inventory reservation, and KPIs (revenue this month, top products, low-stock alerts)
5. As platform admin, browse the ACTIVITY_LOG and merchant directory

## Query Showcase

`sql/999_showcase_queries.sql` contains 25 annotated queries (SELECT, JOIN, subquery, aggregation, window, CTE, recursive CTE, VIEW, UPDATE, transaction). Reproduce via:

```bash
docker compose exec mysql mysql -u storecraft -pstorecraft storecraft < /app/sql/999_showcase_queries.sql
```

## Testing

```bash
docker compose exec app pytest
```

Target: 80%+ coverage on business logic, tenant-isolation assertions per endpoint.

## Project Layout

```
phase3/
├── docker-compose.yml       # MySQL + app + phpMyAdmin
├── Dockerfile               # python:3.11-slim
├── pyproject.toml
├── .env.example
├── src/storecraft/
│   ├── main.py              # FastAPI app factory
│   ├── db.py                # engine + session
│   ├── config.py
│   ├── models/              # SQLAlchemy ORM (5 modules mirroring ER zones)
│   ├── routers/             # FastAPI route handlers
│   ├── queries/             # showcase queries (SQLAlchemy Core)
│   ├── templates/           # Jinja2 HTML
│   └── static/
├── sql/
│   ├── 001_schema.sql       # DDL (17 tables + bridges + indexes + CHECKs)
│   ├── 002_views.sql
│   ├── 003_triggers.sql
│   └── 999_showcase_queries.sql
├── scripts/
│   ├── init_db.py
│   └── seed.py
├── tests/
└── slides/
    ├── presentation.md
    └── presentation.pdf
```

## License

MIT. See parent repository root.
