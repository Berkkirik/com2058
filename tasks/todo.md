# StoreCraft Hardening Punch List (Ralph Loop)

**Scope:** `phase3/src/storecraft/` (backend, excluding `models/`) and `phase3/frontend/src/` (frontend).

**Untouchable:** DB models, DDL, docs, slides, Phase 2 ER content, reports.

**Loop state:** `.claude/ralph-loop.local.md`.

---

## Backend (FastAPI)

- [x] BE-01: Introduce `APIError` exception + global `@app.exception_handler` emitting `{"error": {"code","message","details"}}`. _New `errors.py`; handlers for APIError, HTTPException, RequestValidationError, IntegrityError, OperationalError, SQLAlchemyError, unhandled Exception._
- [x] BE-02: Convert every endpoint in `routers/api.py` to declare typed Pydantic request + response schemas. _20+ response models: MerchantSummary, MerchantDetail, ProductSummary/Detail, VariantOut, ReviewOut, CategoryOut, OrderSummary/Detail, OrderItemOut, PaymentOut, ShipmentOut, DiscountUsageOut, ActivityOut, Address. `response_model=` on every non-showcase endpoint._
- [x] BE-03: Ensure `get_db()` / session dependency properly closes on error paths. _`db.py` now rolls back on any raised exception before closing; try/except/finally sequence guaranteed-close._
- [x] BE-04: Add `/healthz` (liveness) and `/readyz` (readiness — DB ping) endpoints. _Both added to `main.py`; `/readyz` emits `DB_UNAVAILABLE` envelope on failure; `/health` kept for back-compat._
- [x] BE-05: Lock down CORS to the `FRONTEND_ORIGIN` env var; drop `*`. _`CORS_ORIGINS` comma-separated in `config.py`, defaults to vite dev origins; `allow_methods`/`allow_headers` now explicit._
- [x] BE-06: Structured logging + `request-id` middleware (UUID per request, included in log lines and `X-Request-ID` response header). _New `middleware.py` (`RequestContextMiddleware`) + `logging_config.py` (KeyValueFormatter with secret redaction); rate-limit extension point commented in middleware._
- [x] BE-07: Tenant isolation audit — every tenant-scoped query filtered by `merchant_id`; add helper/dep. _New `tenant_scope()` FastAPI dependency resolves slug → Merchant; every downstream query uses `merchant.merchant_id`. Covered by e2e tests for products / categories / product detail / orders._
- [x] BE-08: Pagination on every list endpoint; `limit` default 20, max 100; cursor or offset. _`LimitQuery`/`OffsetQuery` Annotated types with `ge/le` caps; every list endpoint accepts `limit` + `offset`. Admin activity endpoint also paginated._
- [x] BE-09: Swap bare `except:` / broad try/except for narrow handlers; never leak tracebacks. _`main.py` now catches `SQLAlchemyError` specifically; generic unhandled path returns opaque `INTERNAL_ERROR` envelope via global handler._
- [x] BE-10: Use `Annotated[int, Path(..., gt=0)]` etc. for path param validation. _`SlugPath` (regex-restricted, length-limited), `PositiveInt` used on `{product_id}` / `{order_id}`; rejects negative/UPPERCASE with 422 validation envelope._
- [x] BE-11: `config.py` — pydantic-settings with explicit env var names and defaults; fail fast on missing required. _Added `cors_origins`, `log_level` (validated via `field_validator`), explicit `ge/le` constraints, helper `cors_origins_list()`._

## Frontend (React + TS)

- [ ] FE-01: Enable `strict: true`, `noUncheckedIndexedAccess: true` in `tsconfig.json`; fix all resulting errors.
- [ ] FE-02: Rebuild `lib/api.ts` — typed fetch wrapper (zod or hand-written), AbortController on unmount, timeout, normalized errors.
- [ ] FE-03: Add top-level `ErrorBoundary` in `components/Layout.tsx`.
- [ ] FE-04: Audit every page (`pages/*.tsx`) for loading / error / empty states.
- [ ] FE-05: Route guards for `/admin` and `/dashboard` (redirect to login / home if no session).
- [ ] FE-06: Replace `console.log` with a `logger` util that noops in prod.
- [ ] FE-07: Ensure every `<img>` has `width` + `height` attributes (prevent CLS).
- [ ] FE-08: Keyboard focus ring visible on all interactives; skip-to-content link in Layout; ARIA labels on icon-only buttons.
- [ ] FE-09: `lib/store.ts` audit — typed state, no stale closures, loading+error per resource.
- [ ] FE-10: Lazy-load routes with `React.lazy` + `Suspense` to reduce initial bundle.

## QA / Verification

- [ ] QA-01: `cd phase3 && uv run pytest -q` — green, test count ≥ existing.
- [ ] QA-02: `cd phase3/frontend && npx tsc --noEmit` — zero errors.
- [ ] QA-03: `cd phase3/frontend && npm run build` — succeeds.
- [ ] QA-04: Runtime smoke — `uvicorn` + `npm run dev`, no console errors on homepage/storefront.

---

## Iteration log

<!-- append one line per completed item -->
- BE-01, BE-04, BE-05, BE-06, BE-09, BE-11 — infrastructure cluster: errors.py + middleware.py + logging_config.py; main.py rewired; config.py hardened. 21 pytest green.
- BE-02, BE-03, BE-07, BE-08, BE-10 — routers + db cluster: Pydantic schemas across all endpoints, tenant_scope dependency, pagination with capped limit, Annotated path validation; db.py rolls back on error. Plus new `test_e2e.py` (33 new tests) covering error envelope shape, tenant isolation, pagination edges, validation, CORS, request-id, unhandled-exception masking. **54 pytest passed** (up from 21 baseline); coverage 95%.
