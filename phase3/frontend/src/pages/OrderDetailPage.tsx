import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { api } from "@/lib/api";
import { Loading, ErrorBox } from "@/components/Loading";
import StatusBadge from "@/components/StatusBadge";
import SectionReveal from "@/components/SectionReveal";

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
      {/* ─────────────── Hero summary on dark ─────────────── */}
      <section className="section-dark py-14">
        <div className="max-w-[1200px] mx-auto px-6">
          <Link to={`/dashboard/${slug}/orders`} className="cta-link text-link-bright">
            <span className="rotate-180 inline-block mr-1">›</span>
            <span className="ml-6">All orders</span>
          </Link>
          <div className="flex items-end justify-between flex-wrap gap-4 mt-4">
            <div>
              <p className="text-caption uppercase tracking-[0.2em] text-link-bright font-semibold">Order</p>
              <h1 className="display-hero text-white mt-3 font-mono">
                <span className="font-display">{data.order_number}</span>
              </h1>
              <p className="text-caption text-white/55 mt-2">
                Placed {data.placed_at?.replace("T", " ").slice(0, 16)}
              </p>
            </div>
            <div className="text-right">
              <StatusBadge value={data.status} />
              <p className="font-display text-section mt-2" style={{ color: "#2997ff" }}>
                {data.grand_total.toFixed(2)} <span className="text-white/70 text-sub">{data.currency}</span>
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ─────────────── Parties + addresses ─────────────── */}
      <section className="section-light py-12">
        <div className="max-w-[1200px] mx-auto px-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 stagger-child">
            <motion.div whileHover={{ y: -3 }} className="card-lift">
              <p className="text-caption text-ink/55 uppercase tracking-widest font-semibold">Customer</p>
              <h3 className="font-display text-emphasis text-ink mt-2">
                {data.customer.full_name ?? "Unknown"}
              </h3>
              {data.customer.email && (
                <p className="text-caption text-ink/60 mt-1 font-mono">{data.customer.email}</p>
              )}
            </motion.div>
            <motion.div whileHover={{ y: -3 }} className="card-lift">
              <p className="text-caption text-ink/55 uppercase tracking-widest font-semibold">Ship to</p>
              <p className="text-body text-ink mt-2">{data.ship_address.line1}</p>
              <p className="text-caption text-ink/60">
                {data.ship_address.city}, {data.ship_address.country} {data.ship_address.zip}
              </p>
            </motion.div>
            <motion.div whileHover={{ y: -3 }} className="card-lift">
              <p className="text-caption text-ink/55 uppercase tracking-widest font-semibold">Bill to</p>
              <p className="text-body text-ink mt-2">{data.bill_address.line1}</p>
              <p className="text-caption text-ink/60">
                {data.bill_address.city}, {data.bill_address.country} {data.bill_address.zip}
              </p>
            </motion.div>
          </div>
        </div>
      </section>

      {/* ─────────────── Line items ─────────────── */}
      <section className="section-light py-12">
        <div className="max-w-[1200px] mx-auto px-6">
          <SectionReveal>
            <p className="text-caption uppercase tracking-[0.2em] text-accent font-semibold">Line items</p>
            <h2 className="display-section mt-3">{data.items.length} items</h2>
          </SectionReveal>
          <div className="mt-8 overflow-x-auto">
            <table className="data">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Product</th>
                  <th>SKU</th>
                  <th>Unit</th>
                  <th>Qty</th>
                  <th>Subtotal</th>
                </tr>
              </thead>
              <tbody className="stagger-child">
                {data.items.map((it) => (
                  <tr key={it.line_no}>
                    <td className="font-semibold">{it.line_no}</td>
                    <td>
                      <span className="font-display text-emphasis">{it.product_title}</span>
                      <span className="block text-caption text-ink/55">{it.variant_label}</span>
                    </td>
                    <td><code>{it.sku}</code></td>
                    <td>{it.unit_price.toFixed(2)}</td>
                    <td>{it.quantity}</td>
                    <td className="font-semibold">{it.line_subtotal.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr><td colSpan={5} className="text-right text-ink/60">Subtotal</td><td className="font-semibold">{data.subtotal.toFixed(2)}</td></tr>
                <tr><td colSpan={5} className="text-right text-ink/60">Discount</td><td className="text-ok" style={{ color: "#248a3d" }}>− {data.discount_total.toFixed(2)}</td></tr>
                <tr><td colSpan={5} className="text-right text-ink/60">Tax</td><td>+ {data.tax_total.toFixed(2)}</td></tr>
                <tr>
                  <td colSpan={5} className="text-right font-display text-emphasis">Grand total</td>
                  <td className="font-display text-emphasis" style={{ color: "#0071e3" }}>
                    {data.grand_total.toFixed(2)} {data.currency}
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      </section>

      {/* ─────────────── Payments + shipments ─────────────── */}
      <section className="section-light py-12 pb-24">
        <div className="max-w-[1200px] mx-auto px-6 grid md:grid-cols-2 gap-8">
          <div>
            <SectionReveal>
              <p className="text-caption uppercase tracking-[0.2em] text-accent font-semibold">Payments</p>
              <h2 className="display-section mt-3">{data.payments.length}</h2>
            </SectionReveal>
            <div className="mt-6">
              <table className="data">
                <thead>
                  <tr><th>Method</th><th>Amount</th><th>Status</th><th>Processed</th></tr>
                </thead>
                <tbody className="stagger-child">
                  {data.payments.map((p) => (
                    <tr key={p.payment_id}>
                      <td>{p.method}</td>
                      <td className="font-semibold">{p.amount.toFixed(2)} {data.currency}</td>
                      <td><StatusBadge value={p.status} /></td>
                      <td className="text-ink/55">{p.processed_at?.replace("T", " ").slice(0, 16) ?? "—"}</td>
                    </tr>
                  ))}
                  {data.payments.length === 0 && (
                    <tr><td colSpan={4} className="text-ink/50">No payments yet.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
          <div>
            <SectionReveal>
              <p className="text-caption uppercase tracking-[0.2em] text-accent font-semibold">Shipments</p>
              <h2 className="display-section mt-3">{data.shipments.length}</h2>
            </SectionReveal>
            <div className="mt-6">
              <table className="data">
                <thead>
                  <tr><th>Carrier</th><th>Tracking</th><th>Status</th><th>Delivered</th></tr>
                </thead>
                <tbody className="stagger-child">
                  {data.shipments.map((s) => (
                    <tr key={s.shipment_id}>
                      <td className="font-display text-emphasis">{s.carrier}</td>
                      <td><code>{s.tracking_number ?? "—"}</code></td>
                      <td><StatusBadge value={s.status} /></td>
                      <td className="text-ink/55">{s.delivered_at?.slice(0, 10) ?? "—"}</td>
                    </tr>
                  ))}
                  {data.shipments.length === 0 && (
                    <tr><td colSpan={4} className="text-ink/50">No shipments yet.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
