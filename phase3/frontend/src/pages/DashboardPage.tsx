import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Loading, ErrorBox } from "@/components/Loading";

export default function DashboardPage() {
  const { slug = "" } = useParams();

  const merchantQ = useQuery({ queryKey: ["merchant", slug], queryFn: () => api.getMerchant(slug), enabled: !!slug });
  const kpiQ = useQuery({ queryKey: ["kpi"], queryFn: api.kpi });
  const monthQ = useQuery({ queryKey: ["thisMonth"], queryFn: api.thisMonth });
  const topProductsQ = useQuery({ queryKey: ["topProducts", slug], queryFn: () => api.topProducts(slug), enabled: !!slug });
  const lowStockQ = useQuery({ queryKey: ["lowStock", slug], queryFn: () => api.lowStock(slug), enabled: !!slug });
  const topCustomersQ = useQuery({ queryKey: ["topCustomers", slug], queryFn: () => api.topCustomers(slug), enabled: !!slug });

  if (merchantQ.isLoading) return <Loading label="Loading dashboard…" />;
  if (merchantQ.error) return <ErrorBox error={merchantQ.error} />;
  const m = merchantQ.data!;

  const myKpi = kpiQ.data?.find((k) => k.merchant_id === m.merchant_id);
  const myMonth = monthQ.data?.find((k) => k.merchant_id === m.merchant_id);

  return (
    <>
      <p className="flex items-center gap-2 text-sm">
        <Link to={`/m/${slug}`}>← Storefront</Link>
        <span>·</span>
        <Link to={`/dashboard/${slug}/orders`}>Orders →</Link>
      </p>
      <h1>{m.store_name} — Dashboard</h1>
      <p className="text-muted">
        KPIs powered by live SQL (showcase queries Q14, Q18, Q21 + analytics views).
      </p>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4">
        <div className="kpi">
          <div className="kpi-label">Orders (all-time)</div>
          <div className="kpi-value">{myKpi?.orders_count ?? 0}</div>
        </div>
        <div className="kpi">
          <div className="kpi-label">Gross sales</div>
          <div className="kpi-value">
            {Number(myKpi?.gross_sales ?? 0).toFixed(0)} {m.currency}
          </div>
        </div>
        <div className="kpi">
          <div className="kpi-label">Avg order value</div>
          <div className="kpi-value">{Number(myKpi?.avg_order_value ?? 0).toFixed(2)}</div>
        </div>
        <div className="kpi">
          <div className="kpi-label">This month</div>
          <div className="kpi-value">
            {Number(myMonth?.this_month_rev ?? 0).toFixed(0)} {m.currency}
          </div>
        </div>
      </div>

      <h2>Top products</h2>
      {topProductsQ.isLoading ? (
        <Loading />
      ) : (
        <table className="data">
          <thead>
            <tr><th>Product</th><th>Units</th><th>Gross revenue</th></tr>
          </thead>
          <tbody>
            {topProductsQ.data?.map((p) => (
              <tr key={p.product_id}>
                <td>{p.title}</td>
                <td>{p.units_sold}</td>
                <td>{Number(p.gross_revenue).toFixed(2)} {m.currency}</td>
              </tr>
            ))}
            {topProductsQ.data?.length === 0 && (
              <tr><td colSpan={3} className="text-muted">No sales yet.</td></tr>
            )}
          </tbody>
        </table>
      )}

      <h2>Low-stock alerts</h2>
      {lowStockQ.isLoading ? (
        <Loading />
      ) : (
        <table className="data">
          <thead>
            <tr><th>Warehouse</th><th>SKU</th><th>Available</th><th>Reorder level</th></tr>
          </thead>
          <tbody>
            {lowStockQ.data?.map((r, idx) => (
              <tr key={`${r.sku}-${idx}`}>
                <td>{r.warehouse_name}</td>
                <td><code>{r.sku}</code></td>
                <td>
                  <span className={`badge ${r.qty_available === 0 ? "badge-danger" : "badge-warn"}`}>
                    {r.qty_available}
                  </span>
                </td>
                <td>{r.reorder_level}</td>
              </tr>
            ))}
            {lowStockQ.data?.length === 0 && (
              <tr><td colSpan={4} className="text-muted">All stocks above reorder levels.</td></tr>
            )}
          </tbody>
        </table>
      )}

      <h2>Top customers (by lifetime spend)</h2>
      {topCustomersQ.isLoading ? (
        <Loading />
      ) : (
        <table className="data">
          <thead>
            <tr><th>Rank</th><th>Name</th><th>Lifetime spend</th></tr>
          </thead>
          <tbody>
            {topCustomersQ.data?.slice(0, 10).map((c) => (
              <tr key={`${c.merchant_id}-${c.rank_in_store}`}>
                <td>#{c.rank_in_store}</td>
                <td>{c.customer_name}</td>
                <td>{Number(c.lifetime_spend).toFixed(2)} {m.currency}</td>
              </tr>
            ))}
            {topCustomersQ.data?.length === 0 && (
              <tr><td colSpan={3} className="text-muted">No customers yet.</td></tr>
            )}
          </tbody>
        </table>
      )}
    </>
  );
}
