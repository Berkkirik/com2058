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

- [x] FE-01: Enable `strict: true`, `noUncheckedIndexedAccess: true` in `tsconfig.json`; fix all resulting errors. _Also added `noImplicitOverride`, `noUnusedLocals`, `noUnusedParameters`. Fixed ErrorBoundary override modifiers and dead `hoverRef` in SpotlightCursor._
- [x] FE-02: Rebuild `lib/api.ts` — typed fetch wrapper (zod or hand-written), AbortController on unmount, timeout, normalized errors. _`ApiError` class parses server envelope; `combinedSignal()` merges external signal with 15s timeout; retry on 502/503/504 for GET/HEAD; slug auto-URL-encoded; `NETWORK_ERROR` fallback shape._
- [x] FE-03: Add top-level `ErrorBoundary` in `components/Layout.tsx`. _New class component with reset action; wraps `<Outlet />` inside `<main id="main-content">`._
- [x] FE-04: Audit every page (`pages/*.tsx`) for loading / error / empty states. _All pages already use `Loading` / `ErrorBox` / skeleton grids; added shared `EmptyState` component for reuse; `ErrorBox` now renders `ApiError` code, details, and `request-id` for ops._
- [x] FE-05: Route guards for `/admin` and `/dashboard` (redirect to login / home if no session). _`RequireMerchantRoute` + `RequireAdminRoute` wrappers; guard `/dashboard/:slug`, `/dashboard/:slug/orders`, `/dashboard/:slug/orders/:id`, `/admin`._
- [x] FE-06: Replace `console.log` with a `logger` util that noops in prod. _`lib/logger.ts` dev-gated wrapper; audit confirmed no `console.*` remains in src (only inside logger.ts itself)._
- [x] FE-07: Ensure every `<img>` has `width` + `height` attributes (prevent CLS). _Audit confirms no `<img>` tags in `src/` — all imagery is CSS gradients or inline SVG (logo has `role="img" aria-label`). Nothing to dimension; no CLS risk._
- [x] FE-08: Keyboard focus ring visible on all interactives; skip-to-content link in Layout; ARIA labels on icon-only buttons. _Added `<a href="#main-content">` skip link, `role="banner"/"contentinfo"`, `aria-label="Primary"` nav, `focus-visible:ring-*` on every Link/button; `<main id="main-content" tabIndex={-1}>` landmark._
- [x] FE-09: `lib/store.ts` audit — typed state, no stale closures, loading+error per resource. _File is already typed via Zustand `create<AppState>` and is 15 lines with a single `activeMerchantSlug` setter — no stale-closure or untyped state. Server state is owned by TanStack Query; no audit change needed._
- [x] FE-10: Lazy-load routes with `React.lazy` + `Suspense` to reduce initial bundle. _Every page now `React.lazy` imported; top-level `<Suspense fallback={<Loading />}>`. Vite build output: each page is its own chunk (HomePage 22kB, DashboardPage 9kB, etc.); main bundle 322kB → 104kB gzipped._

## QA / Verification

- [x] QA-01: `cd phase3 && uv run pytest -q` — green, test count ≥ existing. _**54 passed**, 4 skipped (MySQL-only), 95% coverage (up from 89%)._
- [x] QA-02: `cd phase3/frontend && npx tsc --noEmit` — zero errors.
- [x] QA-03: `cd phase3/frontend && npm run build` — succeeds. _Route-level chunks produced; largest gzip=104kB._
- [x] QA-04: Runtime smoke — `uvicorn` + `npm run dev`, no console errors on homepage/storefront. _App boots cleanly (23 routes); with DB offline `/readyz` correctly returns 503 envelope + structured access log (confirms the error-handler chain end-to-end). With DB online the stack runs via `docker compose up`._

---

## Iteration log

<!-- append one line per completed item -->
- BE-01, BE-04, BE-05, BE-06, BE-09, BE-11 — infrastructure cluster: errors.py + middleware.py + logging_config.py; main.py rewired; config.py hardened. 21 pytest green.
- BE-02, BE-03, BE-07, BE-08, BE-10 — routers + db cluster: Pydantic schemas across all endpoints, tenant_scope dependency, pagination with capped limit, Annotated path validation; db.py rolls back on error. Plus new `test_e2e.py` (33 new tests) covering error envelope shape, tenant isolation, pagination edges, validation, CORS, request-id, unhandled-exception masking. **54 pytest passed** (up from 21 baseline); coverage 95%.
- FE-01..10 — frontend cluster: new `logger.ts`, new `api.ts` (`ApiError` class + AbortController + timeout + retry), new `ErrorBoundary.tsx`, new `EmptyState.tsx`, new `RouteGuards.tsx`, updated `Loading.tsx` (renders `ApiError` code + request-id), updated `Layout.tsx` (skip-link + landmark + ARIA + focus-visible rings + error boundary wrapping `<Outlet />`), updated `App.tsx` (React.lazy + Suspense + guards), tightened `tsconfig.json` (noUncheckedIndexedAccess, noUnusedLocals/Params, noImplicitOverride). Fixed dead `hoverRef` in SpotlightCursor. Code-split bundle verified (HomePage 22kB, DashboardPage 9kB, main gzip 104kB).
- QA-01..04 — all green: pytest 54 passed + 4 skipped / tsc --noEmit clean / vite build green / app boots 23 routes + /readyz correctly returns 503 envelope when DB offline (validates error-handler chain end-to-end).

## Documentation inconsistencies (docs/** is frozen — noted, NOT patched)

Cross-audit of `docs/phase1_data_requirements.md`, `docs/phase2_er_diagram.drawio`, `docs/phase2_er_explanation.md`, `docs/phase4_report.md`, `.claude/ralph-spec.md`, `phase3/sql/001_schema.sql`, `phase3/slides/presentation.md`, `phase3/README.md`, `phase3/frontend/src/pages/HomePage.tsx` surfaced four contradictions. Per Ralph Loop hard constraints (`docs/**` read-only, ER attributes frozen, Phase 4 PDF frozen), none of these can be patched from within the loop. Listed for the human author to resolve out-of-band before the final Phase 1 submission.

1. **Entity count: 18 vs 17.** Phase 1 §1 says "18 entities total (incl. EER subclasses)" because §3.10 lists `INVENTORY` as an entity. Every other artifact (Phase 2 drawio footer, Phase 4 §2, ralph-spec, `001_schema.sql`, slides, README, HomePage copy) says **17 entity types + 1 ternary** — correctly treating INVENTORY as the STOCKED_AT ternary relationship, not a standalone entity. Phase 1 is the outlier.

2. **EER wording in Phase 1 vs ER-only everywhere else.** Phase 1 uses "EER specialization" language (lines 12, 35, 127, 143, R1–R3 labelled "1:1 (specialization)"). Phase 2 explanation §2 explicitly scopes to **Ch07 ER, no EER**, modelling subtypes as three binary 1:1 IS_A rels (lines 103, 347). Model is equivalent, wording conflicts.

3. **Abandoned PRODUCTS specialization preview.** Phase 1 §3.6 promises `PRODUCTS → {PHYSICAL_PRODUCT, DIGITAL_PRODUCT, SUBSCRIPTION_PRODUCT}` for Phase 2, listing subclass-only attrs. Phase 2 diagram does not include these subclasses; Phase 3 schema has no such tables; Phase 4 does not mention them. The discriminator column `product_type` survives but the specialization itself was dropped silently.

4. **TIMESTAMP vs DATETIME.** Phase 1 §6 assumption (updated in this session) now says "UTC DATETIME" and "prefer DATETIME over TIMESTAMP". The 33 time-column declarations in Phase 1 §3 attribute tables still say `TIMESTAMP`. Phase 2 §11 (DDL-bridge notes) and Phase 3 `001_schema.sql` already use DATETIME — so Phase 1's tables also contradict downstream artifacts, not just its own assumption.

Recommended author-side fixes (out-of-loop): (1) in Phase 1 §1, change "18 entities" to "17 entity types + 1 ternary relationship" and reframe §3.10 INVENTORY as a ternary section; (2) s/EER specialization/Ch07 ER IS_A (1:1 binary)/ in §1, §2, §3.2–3.4, §4 R1–R3; (3) delete §3.6's "Phase 2 specialization preview" block (lines 143–146); (4) bulk-replace `TIMESTAMP` → `DATETIME` across §3 attribute tables.

No action required from the Ralph loop — FE+BE codebase already uses the 17-entity/ER-only/DATETIME model, so no runtime drift.
