/**
 * Typed API client for the FastAPI backend.
 *
 * - Base URL from VITE_API_BASE (defaults to '' → same-origin via Vite proxy).
 * - Parses the server's unified error envelope
 *     {"error": {"code", "message", "details"}}
 *   into a typed `ApiError` that callers can pattern-match.
 * - Accepts an `AbortSignal` on every call so React hooks can abort on unmount.
 * - Per-call timeout (default 15s) via a combined AbortController.
 * - Idempotent requests are retried once on 502/503/504 / network errors.
 */

import { logger } from "./logger";

const BASE: string = import.meta.env.VITE_API_BASE ?? "";
const DEFAULT_TIMEOUT_MS = 15_000;
const RETRIABLE_STATUS = new Set<number>([502, 503, 504]);

// ─── Error class ──────────────────────────────────────────────────────────────

export interface ApiErrorDetail {
  loc?: string[];
  msg?: string;
  type?: string;
  [key: string]: unknown;
}

export class ApiError extends Error {
  readonly code: string;
  readonly status: number;
  readonly details: ApiErrorDetail[];
  readonly requestId: string | null;

  constructor(params: {
    code: string;
    message: string;
    status: number;
    details?: ApiErrorDetail[];
    requestId?: string | null;
  }) {
    super(params.message);
    this.name = "ApiError";
    this.code = params.code;
    this.status = params.status;
    this.details = params.details ?? [];
    this.requestId = params.requestId ?? null;
  }

  get isClientError(): boolean {
    return this.status >= 400 && this.status < 500;
  }
  get isServerError(): boolean {
    return this.status >= 500;
  }
  get isNotFound(): boolean {
    return this.status === 404;
  }
  get isValidation(): boolean {
    return this.status === 422;
  }
}

// ─── Internal request helper ──────────────────────────────────────────────────

export interface RequestOptions {
  signal?: AbortSignal;
  timeoutMs?: number;
  retry?: boolean;
}

/** Merges caller's signal with an internal timeout signal. */
function combinedSignal(
  external: AbortSignal | undefined,
  timeoutMs: number,
): { signal: AbortSignal; cancelTimeout: () => void } {
  const ctrl = new AbortController();
  const timeoutId = setTimeout(
    () => ctrl.abort(new DOMException("Request timeout", "TimeoutError")),
    timeoutMs,
  );
  if (external) {
    if (external.aborted) {
      ctrl.abort(external.reason);
    } else {
      external.addEventListener("abort", () => ctrl.abort(external.reason), { once: true });
    }
  }
  return {
    signal: ctrl.signal,
    cancelTimeout: () => clearTimeout(timeoutId),
  };
}

interface ServerEnvelope {
  error?: {
    code?: string;
    message?: string;
    details?: ApiErrorDetail[];
  };
  detail?: unknown;
}

async function parseError(res: Response): Promise<ApiError> {
  let body: ServerEnvelope | null = null;
  try {
    body = (await res.json()) as ServerEnvelope;
  } catch {
    body = null;
  }
  const requestId = res.headers.get("X-Request-ID");
  const envelope = body?.error;
  if (envelope?.code) {
    return new ApiError({
      code: envelope.code,
      message: envelope.message ?? res.statusText ?? "request failed",
      status: res.status,
      details: envelope.details,
      requestId,
    });
  }
  // Fall back to HTTP status text / FastAPI `detail` shape.
  const msg =
    typeof body?.detail === "string"
      ? body.detail
      : res.statusText || `HTTP ${res.status}`;
  return new ApiError({
    code: `HTTP_${res.status}`,
    message: msg,
    status: res.status,
    requestId,
  });
}

async function request<T>(
  path: string,
  init: RequestInit = {},
  opts: RequestOptions = {},
): Promise<T> {
  const { signal: externalSignal, timeoutMs = DEFAULT_TIMEOUT_MS, retry = true } = opts;
  const method = (init.method ?? "GET").toUpperCase();
  const isIdempotent = method === "GET" || method === "HEAD";
  const attempts = retry && isIdempotent ? 2 : 1;

  let lastErr: unknown = null;
  for (let attempt = 0; attempt < attempts; attempt++) {
    const { signal, cancelTimeout } = combinedSignal(externalSignal, timeoutMs);
    try {
      const res = await fetch(`${BASE}${path}`, {
        ...init,
        method,
        signal,
        headers: {
          Accept: "application/json",
          ...(init.body ? { "Content-Type": "application/json" } : {}),
          ...(init.headers ?? {}),
        },
      });
      cancelTimeout();

      if (!res.ok) {
        const err = await parseError(res);
        // Retry eligible network-ish failures only; 4xx is never retried.
        if (attempt + 1 < attempts && RETRIABLE_STATUS.has(err.status)) {
          lastErr = err;
          logger.warn("api_retry", { path, status: err.status, attempt });
          continue;
        }
        throw err;
      }

      // 204 No Content → return undefined cast to T.
      if (res.status === 204) return undefined as T;
      return (await res.json()) as T;
    } catch (err: unknown) {
      cancelTimeout();
      if (err instanceof ApiError) throw err;
      if (err instanceof DOMException && err.name === "AbortError") {
        throw err;
      }
      // Network-level error — retry once if idempotent.
      if (attempt + 1 < attempts) {
        lastErr = err;
        logger.warn("api_network_retry", { path, attempt, err: String(err) });
        continue;
      }
      // Wrap as ApiError so callers always see the same shape.
      const message = err instanceof Error ? err.message : String(err);
      throw new ApiError({
        code: "NETWORK_ERROR",
        message,
        status: 0,
      });
    }
  }
  // Should never reach here; throw last captured error defensively.
  throw lastErr instanceof Error ? lastErr : new Error("unknown request failure");
}

// ─── Response types (mirror the backend Pydantic schemas) ────────────────────

export interface Merchant {
  merchant_id: number;
  slug: string;
  store_name: string;
  plan: string;
  currency: string;
  city?: string | null;
  country?: string | null;
  contact_email: string;
  created_at?: string | null;
  activated_at?: string | null;
  suspended?: boolean;
}

export interface MerchantDetail extends Merchant {
  stats: {
    staff_count: number;
    categories: number;
    warehouses: number;
    products: number;
  };
}

export interface Product {
  product_id: number;
  slug: string;
  title: string;
  product_type: string | null;
  base_price: number;
  currency: string;
  status: string;
  variants_count: number;
}

export interface Variant {
  variant_no: number;
  sku: string;
  option_name: string | null;
  option_value: string | null;
  price_override: number | null;
  barcode: string | null;
  is_default: boolean;
}

export interface Review {
  review_id: number;
  rating: number;
  title: string | null;
  body: string | null;
  is_verified_purchase: boolean;
  helpful_count: number;
  created_at: string | null;
}

export interface ProductDetail {
  product_id: number;
  title: string;
  base_price: number;
  currency: string;
  product_type: string | null;
  status: string;
  variants: Variant[];
  reviews: Review[];
}

export interface Category {
  category_id: number;
  parent_id: number | null;
  slug: string;
  name: string;
  display_order: number;
}

export interface OrderSummary {
  order_id: number;
  order_number: string;
  status: string;
  subtotal: number;
  discount_total: number;
  tax_total: number;
  grand_total: number;
  currency: string;
  placed_at: string | null;
  line_count: number;
  customer: { user_id: number | null; full_name: string | null };
}

export interface OrderItemRow {
  line_no: number;
  product_id: number;
  variant_no: number;
  product_title: string | null;
  variant_label: string | null;
  sku: string | null;
  unit_price: number;
  quantity: number;
  line_subtotal: number;
}

export interface PaymentRow {
  payment_id: number;
  method: string;
  amount: number;
  status: string;
  gateway_reference: string | null;
  processed_at: string | null;
}

export interface ShipmentRow {
  shipment_id: number;
  carrier: string | null;
  tracking_number: string | null;
  status: string;
  shipped_at: string | null;
  delivered_at: string | null;
}

export interface OrderDetail {
  order_id: number;
  order_number: string;
  status: string;
  subtotal: number;
  discount_total: number;
  tax_total: number;
  grand_total: number;
  currency: string;
  placed_at: string | null;
  canceled_at: string | null;
  ship_address: { line1: string | null; city: string | null; country: string | null; zip: string | null };
  bill_address: { line1: string | null; city: string | null; country: string | null; zip: string | null };
  customer: { user_id: number | null; email: string | null; full_name: string | null };
  items: OrderItemRow[];
  payments: PaymentRow[];
  shipments: ShipmentRow[];
  discount_usages: { discount_id: number; amount_applied: number; used_at: string | null }[];
}

export interface ActivityEvent {
  event_id: number;
  merchant_id: number;
  actor_label: string | null;
  entity_type: string | null;
  entity_id: number | null;
  action: string | null;
  occurred_at: string | null;
}

export interface MerchantKpi {
  merchant_id: number;
  store_name: string;
  orders_count: number;
  gross_sales: number | null;
  avg_order_value: number | null;
  first_order: string | null;
  last_order: string | null;
}

export interface MonthKpi {
  merchant_id: number;
  store_name: string;
  plan: string;
  this_month_rev: number;
  this_month_orders: number;
}

export interface TopCustomer {
  merchant_id: number;
  customer_name: string;
  lifetime_spend: number;
  rank_in_store: number;
}

export interface CategoryTreeRow {
  category_id: number;
  depth: number;
  path: string;
}

export interface LowStockRow {
  warehouse_name: string;
  product_id: number;
  sku: string;
  qty_on_hand: number;
  qty_reserved: number;
  qty_available: number;
  reorder_level: number;
}

export interface TopProduct {
  product_id: number;
  title: string;
  units_sold: number;
  gross_revenue: number;
}

// ─── Public surface ──────────────────────────────────────────────────────────

export interface ListParams extends RequestOptions {
  limit?: number;
  offset?: number;
}

function buildQuery(params: Record<string, string | number | undefined>): string {
  const usable = Object.entries(params).filter(([, v]) => v !== undefined && v !== "") as [
    string,
    string | number,
  ][];
  if (usable.length === 0) return "";
  const sp = new URLSearchParams();
  for (const [k, v] of usable) sp.set(k, String(v));
  return `?${sp.toString()}`;
}

export const api = {
  health: (opts?: RequestOptions) => request<{ status: string }>(`/healthz`, {}, opts),
  readyz: (opts?: RequestOptions) =>
    request<{ status: string; db: string }>(`/readyz`, {}, opts),

  listMerchants: ({ limit, offset, ...opts }: ListParams = {}) =>
    request<Merchant[]>(`/api/merchants${buildQuery({ limit, offset })}`, {}, opts),

  getMerchant: (slug: string, opts?: RequestOptions) =>
    request<MerchantDetail>(`/api/merchants/${encodeURIComponent(slug)}`, {}, opts),

  listProducts: (
    slug: string,
    { limit, offset, q, ...opts }: ListParams & { q?: string } = {},
  ) =>
    request<Product[]>(
      `/api/merchants/${encodeURIComponent(slug)}/products${buildQuery({ q, limit, offset })}`,
      {},
      opts,
    ),

  getProduct: (slug: string, productId: number, opts?: RequestOptions) =>
    request<ProductDetail>(
      `/api/merchants/${encodeURIComponent(slug)}/products/${productId}`,
      {},
      opts,
    ),

  listCategories: (slug: string, opts?: RequestOptions) =>
    request<Category[]>(`/api/merchants/${encodeURIComponent(slug)}/categories`, {}, opts),

  listOrders: (slug: string, { limit, offset, ...opts }: ListParams = {}) =>
    request<OrderSummary[]>(
      `/api/merchants/${encodeURIComponent(slug)}/orders${buildQuery({ limit, offset })}`,
      {},
      opts,
    ),

  getOrder: (slug: string, orderId: number, opts?: RequestOptions) =>
    request<OrderDetail>(
      `/api/merchants/${encodeURIComponent(slug)}/orders/${orderId}`,
      {},
      opts,
    ),

  adminActivity: (limit = 50, opts?: RequestOptions) =>
    request<ActivityEvent[]>(`/api/admin/activity${buildQuery({ limit })}`, {}, opts),

  // Showcase queries
  kpi: (opts?: RequestOptions) => request<MerchantKpi[]>(`/api/queries/kpi`, {}, opts),
  thisMonth: (opts?: RequestOptions) =>
    request<MonthKpi[]>(`/api/queries/this-month`, {}, opts),
  activePro: (opts?: RequestOptions) =>
    request<Merchant[]>(`/api/queries/active-pro-merchants`, {}, opts),
  topCustomers: (slug: string, opts?: RequestOptions) =>
    request<TopCustomer[]>(
      `/api/queries/top-customers/${encodeURIComponent(slug)}`,
      {},
      opts,
    ),
  categoryTree: (slug: string, opts?: RequestOptions) =>
    request<CategoryTreeRow[]>(
      `/api/queries/category-tree/${encodeURIComponent(slug)}`,
      {},
      opts,
    ),
  lowStock: (slug: string, opts?: RequestOptions) =>
    request<LowStockRow[]>(
      `/api/queries/low-stock/${encodeURIComponent(slug)}`,
      {},
      opts,
    ),
  topProducts: (slug: string, limit = 10, opts?: RequestOptions) =>
    request<TopProduct[]>(
      `/api/queries/top-products/${encodeURIComponent(slug)}${buildQuery({ limit })}`,
      {},
      opts,
    ),
};

// Re-export names some older call-sites used (backwards-compat).
export type { Product as ProductSummary };
