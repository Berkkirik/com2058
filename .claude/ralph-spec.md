# StoreCraft Phase 3 + Phase 4 — Ralph Loop Specification

## Meta
- **Repo root:** `/Users/berkkirik/Dev/Ankara_University/com2058`
- **Branch:** `storecraft-phase2` (continue; do NOT create a new branch)
- **Target:** `main` (PR will merge later)
- **Author:** Berk Kırık (solo)
- **Course:** COM2058 Ankara University, due 24.05.2026

## Stack decisions (LOCKED — do NOT re-ask)
- **Database:** MySQL 8.0 via Docker Compose
- **Backend:** FastAPI + SQLAlchemy (Python 3.11+)
- **Frontend:** Jinja2 server-rendered templates + HTMX (no SPA, no npm toolchain)
- **Seed data:** Faker library (deterministic with fixed seed for reproducibility)
- **Report format:** Markdown → PDF via pandoc (not LaTeX, not Word)
- **Model scope:** Full StoreCraft 17 entities / 25 relationships

## Reference documents (READ FIRST each iteration if unsure of a detail)
- `docs/phase1_data_requirements.md` — entity attribute dictionary (163 attributes), R1–R25 cardinality table, business rules
- `docs/phase2_er_diagram.drawio` — authoritative ER diagram (Chen notation, Elmasri 6e)
- `docs/phase2_er_explanation.md` — relationship walkthrough, weak-entity rationale, mapping notes

## Task checklist (use TodoWrite — already seeded with 13 items)

### Phase 3 — Implementation (60%)

1. **Project skeleton**
   - `phase3/` root directory
   - `phase3/pyproject.toml` with FastAPI, SQLAlchemy, PyMySQL, Alembic, Faker, Jinja2, python-multipart, pytest, httpx
   - `phase3/docker-compose.yml` (MySQL 8.0 + app + volume + healthcheck)
   - `phase3/.env.example` (DB_URL, APP_HOST, APP_PORT)
   - `phase3/Dockerfile` (python:3.11-slim, copies src, installs deps, CMD uvicorn)
   - `phase3/README.md` (setup, run, demo walkthrough)

2. **MySQL DDL**
   - `phase3/sql/001_schema.sql` — all 17 tables, compound/weak PKs, FKs, indexes (CREATE INDEX on every FK column), CHECK constraints (enum-like columns), ON DELETE CASCADE for weak entities, RESTRICT for merchant refs
   - `phase3/sql/002_views.sql` — demo views (merchant_revenue_monthly, top_products_by_merchant, low_stock_alerts, customer_ltv)
   - `phase3/sql/003_triggers.sql` — optional triggers (updated_at auto, grand_total derivation, loyalty points)
   - Must compile against MySQL 8.0 with `ENGINE=InnoDB CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci`

3. **SQLAlchemy ORM**
   - `phase3/src/storecraft/models/` — one module per entity cluster (identity.py, catalog.py, inventory.py, commerce.py, engagement.py)
   - Use declarative Base; include relationships() with back_populates; mark weak-entity compound PKs properly

4. **Faker seed**
   - `phase3/scripts/seed.py` — idempotent, seed=42, generates: 3 merchants (Turkish names "Berk'in Kitapçısı", "Ankara Elektronik", "TechStore"), 1 owner + 2-3 staff per merchant, 20-30 customers, 40-60 products with 1-3 variants each, 2-3 warehouses per merchant, realistic inventory rows, 80-150 orders distributed over last 90 days, payments/shipments, reviews (~30% of orders), 5-10 discounts, 200+ activity_log rows
   - Run `python -m storecraft.scripts.seed`

5. **FastAPI routers**
   - `phase3/src/storecraft/routers/` — one file per resource: merchants, products, categories, warehouses, customers, carts, orders, payments, shipments, reviews, discounts, auth, admin
   - Tenant scoping: every query filters by `merchant_id` (query param or path param `/merchants/{mid}/...`)
   - Return both JSON (for HTMX fragments) and rendered templates

6. **Jinja2 + HTMX frontend**
   - `phase3/src/storecraft/templates/` — base.html, merchant dashboard, product catalog (search + filter + paginate via HTMX), cart view (add/remove inline), checkout flow, admin views
   - Invoke frontend-design:frontend-design skill for the aesthetic direction (picked: editorial/textbook typography, Times New Roman for headings matching the ER diagram, HTMX `hx-get`/`hx-post` for partial updates, Tailwind CSS CDN optional)

7. **Query showcase**
   - `phase3/sql/999_showcase_queries.sql` — 25 numbered queries with inline comments:
     - Q1–Q5: basic SELECT, WHERE, ORDER BY, LIMIT
     - Q6–Q10: INNER/LEFT/RIGHT JOIN across 2-4 tables
     - Q11–Q13: subqueries (scalar, IN, EXISTS, correlated)
     - Q14–Q17: GROUP BY + HAVING + aggregates (SUM, AVG, COUNT, MAX)
     - Q18–Q20: window functions (ROW_NUMBER, RANK, LAG, running SUM, NTILE)
     - Q21–Q22: CTEs (WITH) including recursive CTE for CATEGORIES tree
     - Q23: VIEW creation + usage
     - Q24: UPDATE with JOIN
     - Q25: transactional multi-statement (BEGIN; UPDATE; INSERT; COMMIT)
   - Mirror the same set in `phase3/src/storecraft/queries/showcase.py` using SQLAlchemy Core (text() or select())

8. **pytest suite**
   - `phase3/tests/` — conftest with MySQL test DB fixture (docker compose health-waited)
   - Test model CRUD, tenant isolation (query for merchant A can't see merchant B's data), each showcase query returns non-empty, API happy path
   - Target: 80%+ coverage on business logic

9. **Docker Compose wiring**
   - Named volume `storecraft_mysql_data` for persistence
   - Healthcheck on MySQL (`mysqladmin ping -h localhost`)
   - App waits for DB healthy before starting
   - Port map 3306 → host 3307 (avoid clash), 8000 → 8000
   - Include phpMyAdmin on 8080 for graders to browse schema

10. **Phase 3 README**
    - Setup steps (docker compose up -d, seed command, open http://localhost:8000)
    - Demo walkthrough (login as merchant owner → create product → customer places order → merchant fulfills → reviewer writes review)
    - Query showcase section with `\i 003_showcase_queries.sql`
    - Troubleshooting

11. **Presentation slides**
    - `phase3/slides/presentation.md` (Marp format or Reveal.js-from-markdown)
    - ~15-20 slides: Title, problem statement, ER recap (show the drawio as image), relational mapping, architecture, live demo screenshots, query highlights, tech stack, lessons learned, Q&A
    - Render to `phase3/slides/presentation.pdf` via Marp CLI

### Phase 4 — Report (10%, 10-15 pages PDF)

12. **Phase 4 report** at `docs/phase4_report.md`:
    - **Cover page** (title, course, author, date)
    - **§1 Introduction** (1 page) — StoreCraft problem domain, motivation
    - **§2 Data Requirements Summary** (1 page) — recap of Phase 1, entity count, business rules
    - **§3 ER Design** (1-2 pages) — the diagram as a figure + design rationale
    - **§4 Relational Mapping** (2-3 pages) — ER→relational transformation per Elmasri Ch09 rules; 1:1/1:N/M:N/weak/ternary mappings, the 18 resulting tables
    - **§5 Normalization Analysis** (2 pages) — demonstrate 1NF/2NF/3NF/BCNF on 3-4 critical tables (ORDERS, ORDER_ITEMS, PRODUCT_VARIANTS), prove functional dependencies
    - **§6 Implementation Architecture** (1-2 pages) — Docker, FastAPI, SQLAlchemy, HTMX, Jinja, diagram of request flow
    - **§7 Query Showcase** (2-3 pages) — 5-8 highlighted queries with SQL, natural-language description, EXPLAIN output, result sample
    - **§8 Testing & Validation** (0.5 pages) — pytest summary, tenant-isolation proof
    - **§9 Screenshots** (1 page) — dashboard, catalog, cart, order, admin
    - **§10 Conclusion & Future Work** (0.5 pages) — what was delivered, Phase 5+ ideas (RBAC, returns, i18n)
    - **References** (Elmasri 6e, FastAPI docs, MySQL manual)
    - Rendered with pandoc to `docs/phase4_report.pdf` with clean typography (pandoc `--pdf-engine=xelatex` if available, else `--pdf-engine=weasyprint`)

13. **Final polish**
    - All tests pass, `docker compose up` produces working demo at http://localhost:8000
    - Phase 4 PDF rendered, 10-15 pages
    - Commit everything granularly on `storecraft-phase2` branch
    - Final verification: output a completion report (hash, URL, PDF path, line count)

## Operating protocol (per iteration)

1. **Start**: read `.claude/ralph-spec.md` (this file) + `TodoWrite` state
2. **Pick next item**: find first `pending` todo; mark it `in_progress`
3. **Use skills** before major work:
   - **Before designing a component**: invoke `superpowers:brainstorming` skill
   - **Before writing Python code**: invoke `superpowers:test-driven-development`
   - **For frontend visual direction**: invoke `frontend-design:frontend-design`
   - **Before marking complete**: invoke `superpowers:verification-before-completion`
4. **Work incrementally**: one or two sub-tasks per iteration; don't batch everything
5. **Commit after each substantive change**: `git add … && git commit -m "phase3: <what>"`
6. **Update TodoWrite**: mark completed, adjust if new sub-tasks discovered
7. **Verify**: run tests, check docker compose, ensure artifacts render
8. **Exit check**: output `<promise>STORECRAFT COMPLETE</promise>` only when ALL of these are true:
   - All 13 todos are `completed`
   - `cd phase3 && docker compose up -d && sleep 20 && curl http://localhost:8000/health` returns 200
   - `cd phase3 && docker compose exec app pytest` exits 0
   - `pandoc docs/phase4_report.md -o docs/phase4_report.pdf` produces a ≥10-page PDF
   - Git is clean (all changes committed)
   - Final report comment posted summarizing: last commit hash, demo URL, PDF path, report line count

## Forbidden / anti-patterns
- Do NOT rewrite Phase 1/2 docs to adjust — they're locked; adapt implementation to match them.
- Do NOT introduce new entities or relationships; if discrepancies arise, file a TODO for later, don't silently extend the schema.
- Do NOT skip tests or normalization proofs to shorten the loop.
- Do NOT create a new branch; stay on `storecraft-phase2`.
- Do NOT push force or rewrite history.
- Do NOT lie about the completion promise — only emit it when all verification steps truly pass.
