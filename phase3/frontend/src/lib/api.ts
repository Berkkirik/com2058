/**
 * Typed API client for the FastAPI backend.
 * Base URL is read from VITE_API_BASE (defaults to '' → same-origin via Vite proxy).
 */

const BASE = import.meta.env.VITE_API_BASE ?? "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}${text ? `: ${text}` : ""}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string; db: string }>(`/health`),

  listMerchants: () => request<Merchant[]>(`/api/merchants`),
  getMerchant: (slug: string) => request<MerchantDetail>(`/api/merchants/${slug}`),

  listProducts: (slug: string, q = "") =>
    request<Product[]>(`/api/merchants/${slug}/products${q ? `?q=${encodeURIComponent(q)}` : ""}`),
  getProduct: (slug: string, productId: number) =>
    request<ProductDetail>(`/api/merchants/${slug}/products/${productId}`),

  listCategories: (slug: string) => request<Category[]>(`/api/merchants/${slug}/categories`),

  listOrders: (slug: string) => request<OrderSummary[]>(`/api/merchants/${slug}/orders`),
  getOrder: (slug: string, orderId: number) =>
    request<OrderDetail>(`/api/merchants/${slug}/orders/${orderId}`),

  adminActivity: (limit = 50) => request<ActivityEvent[]>(`/api/admin/activity?limit=${limit}`),

  // Showcase queries
  kpi: () => request<MerchantKpi[]>(`/api/queries/kpi`),
  thisMonth: () => request<MonthKpi[]>(`/api/queries/this-month`),
  activePro: () => request<Merchant[]>(`/api/queries/active-pro-merchants`),
  topCustomers: (slug: string) => request<TopCustomer[]>(`/api/queries/top-customers/${slug}`),
  categoryTree: (slug: string) => request<CategoryTreeRow[]>(`/api/queries/category-tree/${slug}`),
  lowStock: (slug: string) => request<LowStockRow[]>(`/api/queries/low-stock/${slug}`),
  topProducts: (slug: string, limit = 10) =>
    request<TopProduct[]>(`/api/queries/top-products/${slug}?limit=${limit}`),
};

// ── Types ──────────────────────────────────────────────────────────────────
export interface Merchant {
  merchant_id: number;
  slug: string;
  store_name: string;
  plan: string;
  currency?: string;
  city?: string | null;
  country?: string | null;
  contact_email?: string;
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
  product_type: string;
  base_price: number;
  currency: string;
  status: string;
  variants_count: number;
}

export interface Variant {
  variant_no: number;
  sku: string;
  option_name: string;
  option_value: string;
  price_override: number | null;
  barcode: string | null;
  is_default: boolean;
}

export interface Review {
  review_id: number;
  rating: number;
  title: string;
  body: string;
  is_verified_purchase: boolean;
  helpful_count: number;
  created_at: string | null;
}

export interface ProductDetail {
  product_id: number;
  title: string;
  base_price: number;
  currency: string;
  product_type: string;
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
  product_title: string;
  variant_label: string;
  sku: string;
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
  carrier: string;
  tracking_number: string | null;
  status: string;
  shipped_at: string | null;
  delivered_at: string | null;
}

export interface OrderDetail extends OrderSummary {
  ship_address: { line1: string; city: string; country: string; zip: string };
  bill_address: { line1: string; city: string; country: string; zip: string };
  customer: { user_id: number | null; email: string | null; full_name: string | null };
  items: OrderItemRow[];
  payments: PaymentRow[];
  shipments: ShipmentRow[];
  discount_usages: { discount_id: number; amount_applied: number; used_at: string | null }[];
  canceled_at: string | null;
}

export interface ActivityEvent {
  event_id: number;
  merchant_id: number;
  actor_label: string;
  entity_type: string;
  entity_id: number;
  action: string;
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
