import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Loading, ErrorBox } from "@/components/Loading";
import StatusBadge from "@/components/StatusBadge";

export default function OrderDetailPage() {
  const { slug = "", id = "" } = useParams();
  const orderId = Number(id);

  const { data, isLoading, error } = useQuery({
    queryKey: ["order", slug, orderId],
    queryFn: () => api.getOrder(slug, orderId),
    enabled: !!slug && Number.isFinite(orderId),
  });

  if (isLoading) return <Loading label="Loading order…" />;
  if (error) return <ErrorBox error={error} />;
  if (!data) return null;

  return (
    <>
      <p><Link to={`/dashboard/${slug}/orders`}>← Orders</Link></p>
      <h1>Order <code>{data.order_number}</code></h1>
      <p>
        <StatusBadge value={data.status} />
        <span className="ml-3 text-sm text-muted">
          Placed {data.placed_at?.replace("T", " ").slice(0, 16)}
        </span>
      </p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-4">
        <div className="card">
          <h3 className="mt-0">Customer</h3>
          {data.customer.full_name && <strong>{data.customer.full_name}</strong>}
          {data.customer.email && <p className="text-muted text-sm">{data.customer.email}</p>}
        </div>
        <div className="card">
          <h3 className="mt-0">Ship to</h3>
          {data.ship_address.line1}<br />
          {data.ship_address.city}, {data.ship_address.country} {data.ship_address.zip}
        </div>
        <div className="card">
          <h3 className="mt-0">Bill to</h3>
          {data.bill_address.line1}<br />
          {data.bill_address.city}, {data.bill_address.country} {data.bill_address.zip}
        </div>
      </div>

      <h2>Line items</h2>
      <table className="data">
        <thead>
          <tr><th>#</th><th>Product</th><th>SKU</th><th>Unit</th><th>Qty</th><th>Subtotal</th></tr>
        </thead>
        <tbody>
          {data.items.map((it) => (
            <tr key={it.line_no}>
              <td>{it.line_no}</td>
              <td>{it.product_title} <span className="text-muted">({it.variant_label})</span></td>
              <td><code>{it.sku}</code></td>
              <td>{it.unit_price.toFixed(2)}</td>
              <td>{it.quantity}</td>
              <td>{it.line_subtotal.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
        <tfoot>
          <tr><td colSpan={5} className="text-right"><strong>Subtotal</strong></td><td>{data.subtotal.toFixed(2)}</td></tr>
          <tr><td colSpan={5} className="text-right">Discount</td><td>− {data.discount_total.toFixed(2)}</td></tr>
          <tr><td colSpan={5} className="text-right">Tax</td><td>+ {data.tax_total.toFixed(2)}</td></tr>
          <tr>
            <td colSpan={5} className="text-right"><strong>Grand total</strong></td>
            <td><strong>{data.grand_total.toFixed(2)} {data.currency}</strong></td>
          </tr>
        </tfoot>
      </table>

      <h2>Payments</h2>
      <table className="data">
        <thead><tr><th>Method</th><th>Amount</th><th>Status</th><th>Processed</th></tr></thead>
        <tbody>
          {data.payments.map((p) => (
            <tr key={p.payment_id}>
              <td>{p.method}</td>
              <td>{p.amount.toFixed(2)} {data.currency}</td>
              <td><StatusBadge value={p.status} /></td>
              <td>{p.processed_at?.replace("T", " ").slice(0, 16) ?? "—"}</td>
            </tr>
          ))}
          {data.payments.length === 0 && (
            <tr><td colSpan={4} className="text-muted">No payments yet.</td></tr>
          )}
        </tbody>
      </table>

      <h2>Shipments</h2>
      <table className="data">
        <thead><tr><th>Carrier</th><th>Tracking</th><th>Status</th><th>Shipped</th><th>Delivered</th></tr></thead>
        <tbody>
          {data.shipments.map((s) => (
            <tr key={s.shipment_id}>
              <td>{s.carrier}</td>
              <td><code>{s.tracking_number ?? "—"}</code></td>
              <td><StatusBadge value={s.status} /></td>
              <td>{s.shipped_at?.slice(0, 10) ?? "—"}</td>
              <td>{s.delivered_at?.slice(0, 10) ?? "—"}</td>
            </tr>
          ))}
          {data.shipments.length === 0 && (
            <tr><td colSpan={5} className="text-muted">No shipments yet.</td></tr>
          )}
        </tbody>
      </table>

      {data.discount_usages.length > 0 && (
        <>
          <h2>Discounts applied</h2>
          <ul className="list-disc ml-6">
            {data.discount_usages.map((du) => (
              <li key={du.discount_id}>
                Discount #{du.discount_id}: {du.amount_applied.toFixed(2)} {data.currency}
                <span className="text-muted"> ({du.used_at?.slice(0, 10)})</span>
              </li>
            ))}
          </ul>
        </>
      )}
    </>
  );
}
