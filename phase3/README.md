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
docker compose up -d --build        # MySQL + backend + React SPA + phpMyAdmin
docker compose exec app python /app/scripts/seed.py     # populate Faker data
open http://localhost:5173          # React SPA (the demo)
open http://localhost:8000/docs     # FastAPI Swagger UI
open http://localhost:8080          # phpMyAdmin
```

## Ports

| Port | Service | Access |
|------|---------|--------|
| `5173` | React SPA (Vite preview) | `http://localhost:5173` — the demo |
| `8000` | FastAPI JSON API | `http://localhost:8000/docs` (Swagger), `/health` |
| `8080` | phpMyAdmin | `http://localhost:8080` — user `root` / password from `.env` |
| `3307` | MySQL (exposed) | `mysql -h 127.0.0.1 -P 3307 -u storecraft -p storecraft` |

## Stack

| Layer | Choice |
|-------|--------|
| Database | MySQL 8.0 (InnoDB, utf8mb4) |
| ORM | SQLAlchemy 2.0 (declarative) |
| Backend | FastAPI + Uvicorn (JSON-only) |
| Frontend | React 18 + Vite + TypeScript + Tailwind CSS |
| Data fetching | TanStack Query (React Query) |
| Client state | Zustand |
| Seed | Faker (deterministic, seed=42) |
| Tests | pytest (backend) |
| Orchestration | Docker Compose (4 services: mysql, app, frontend, phpmyadmin) |

## Demo Walkthrough

After seeding, open `http://localhost:5173` and try:

1. **Home** → see 3 merchants (Helix Books, Voltaic Electronics, TechStore)
2. **Storefront** → click "Browse catalog" on Helix Books → type in the search box to live-filter products (TanStack Query refetches on each keystroke)
3. **Product detail** → click any product → variants table, review cards with star ratings
4. **Merchant dashboard** → KPI tiles (orders count, gross sales, AOV, this-month revenue) all powered by live SQL
5. **Orders list** → `/dashboard/helix-books/orders` → 30+ orders with status badges
6. **Order detail** → full line items, payments, shipments, discount usages
7. **Platform admin** → `/admin` → cross-tenant merchant directory + last-7-day activity log

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
├── docker-compose.yml              # mysql + app + frontend + phpmyadmin
├── Dockerfile                      # backend: python:3.11-slim
├── pyproject.toml
├── .env.example
├── src/storecraft/                 # FastAPI (JSON-only)
│   ├── main.py                     # app factory (CORS enabled)
│   ├── db.py                       # SQLAlchemy engine + session
│   ├── config.py
│   ├── models/                     # SQLAlchemy ORM (5 modules, 22 tables)
│   ├── routers/
│   │   └── api.py                  # every JSON endpoint consumed by React
│   └── queries/showcase.py         # Q1/Q14/Q18/Q21/Q22 + view helpers
├── frontend/                       # React 18 + Vite + TS + Tailwind SPA
│   ├── Dockerfile                  # node:20-alpine → vite build + preview
│   ├── package.json
│   ├── vite.config.ts              # proxy /api /health to app:8000
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── index.html
│   └── src/
│       ├── main.tsx                # entry, QueryClient + Router providers
│       ├── App.tsx                 # route table
│       ├── index.css               # Tailwind + design-system classes
│       ├── lib/
│       │   ├── api.ts              # typed fetch client (17 interfaces)
│       │   └── store.ts            # Zustand client state
│       ├── components/             # Layout, Loading/Error, StatusBadge
│       └── pages/                  # Home, Storefront, ProductDetail,
│                                   #  Dashboard, OrdersList, OrderDetail, Admin
├── sql/
│   ├── 001_schema.sql              # DDL (17 tables + 5 bridges + indexes + CHECKs)
│   ├── 002_views.sql               # 5 analytics views
│   ├── 003_triggers.sql            # 3 triggers (loyalty, inventory, discount)
│   └── 999_showcase_queries.sql    # 25 annotated queries
├── scripts/
│   ├── init_db.py                  # apply 0??_*.sql in order
│   └── seed.py                     # Faker seed=42 → 1440 rows
├── tests/                          # pytest (backend)
└── slides/
    ├── presentation.md             # Marp format
    └── presentation.pdf
```

## License

MIT. See parent repository root.
