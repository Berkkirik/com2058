import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { api } from "@/lib/api";
import { Loading, ErrorBox, Skeleton } from "@/components/Loading";
import CountUp from "@/components/CountUp";
import SectionReveal from "@/components/SectionReveal";

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
      {/* ─────────────── Dashboard hero on black ─────────────── */}
      <section className="section-dark py-16 md:py-24 relative overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-0 left-1/3 h-[500px] w-[700px] rounded-full blur-[120px] opacity-40"
               style={{ background: "radial-gradient(circle, rgba(0,113,227,0.35), transparent 70%)" }} />
        </div>
        <div className="max-w-[1200px] mx-auto px-6 relative">
          <div className="flex items-center gap-2 text-caption text-white/55 mb-4">
            <Link to="/" className="link-bright">Home</Link>
            <span>/</span>
            <Link to={`/m/${slug}`} className="link-bright">{slug}</Link>
            <span>/</span>
            <span>dashboard</span>
          </div>
          <div className="flex items-end justify-between flex-wrap gap-4">
            <div>
              <p className="text-caption uppercase tracking-[0.2em] text-link-bright font-semibold">Overview</p>
              <h1 className="display-hero text-white mt-3">{m.store_name}</h1>
              <p className="mt-3 text-sub text-white/70">Live KPIs · powered by Q14 / Q18 / Q21 SQL.</p>
            </div>
            <Link to={`/dashboard/${slug}/orders`} className="btn-outline-dark">
              View orders
            </Link>
          </div>

          {/* KPI tiles with animated CountUp */}
          <div className="mt-12 grid grid-cols-2 md:grid-cols-4 gap-4">
            <Kpi label="Orders (all-time)" value={Number(myKpi?.orders_count ?? 0)} />
            <Kpi
              label="Gross sales"
              value={Number(myKpi?.gross_sales ?? 0)}
              suffix={` ${m.currency}`}
              decimals={0}
            />
            <Kpi
              label="Avg order value"
              value={Number(myKpi?.avg_order_value ?? 0)}
              decimals={2}
            />
            <Kpi
              label="This month"
              value={Number(myMonth?.this_month_rev ?? 0)}
              suffix={` ${m.currency}`}
              accent
            />
          </div>
        </div>
      </section>

      {/* ─────────────── Tenant stats strip ─────────────── */}
      <section className="section-light py-16">
        <div className="max-w-[1200px] mx-auto px-6">
          <SectionReveal>
            <p className="text-caption uppercase tracking-[0.2em] text-accent font-semibold">At a glance</p>
            <h2 className="display-section mt-3">Tenant footprint</h2>
          </SectionReveal>
          {m.stats && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-8">
              <Kpi label="Products" value={m.stats.products} small />
              <Kpi label="Categories" value={m.stats.categories} small />
              <Kpi label="Warehouses" value={m.stats.warehouses} small />
              <Kpi label="Staff" value={m.stats.staff_count} small />
            </div>
          )}
        </div>
      </section>

      {/* ─────────────── Top products ─────────────── */}
      <section className="section-light py-16">
        <div className="max-w-[1200px] mx-auto px-6">
          <SectionReveal className="flex items-end justify-between gap-4 mb-8">
            <div>
              <p className="text-caption uppercase tracking-[0.2em] text-accent font-semibold">Bestsellers</p>
              <h2 className="display-section mt-3">Top products</h2>
              <p className="text-caption text-ink/55 mt-1">Via v_top_products_by_merchant.</p>
            </div>
          </SectionReveal>
          {topProductsQ.isLoading ? <SkelTable cols={3} /> : (
            <table className="data">
              <thead>
                <tr><th>Product</th><th>Units sold</th><th>Gross revenue</th></tr>
              </thead>
              <tbody className="stagger-child">
                {topProductsQ.data?.map((p) => (
                  <tr key={p.product_id}>
                    <td className="font-display text-emphasis">{p.title}</td>
                    <td>
                      <span className="badge badge-info">{p.units_sold}</span>
                    </td>
                    <td className="font-semibold">{Number(p.gross_revenue).toFixed(2)} {m.currency}</td>
                  </tr>
                ))}
                {topProductsQ.data?.length === 0 && (
                  <tr><td colSpan={3} className="text-ink/50">No sales yet.</td></tr>
                )}
              </tbody>
            </table>
          )}
        </div>
      </section>

      {/* ─────────────── Low-stock alerts ─────────────── */}
      <section className="section-dark py-20">
        <div className="max-w-[1200px] mx-auto px-6">
          <SectionReveal className="flex items-end justify-between gap-4 mb-8">
            <div>
              <p className="text-caption uppercase tracking-[0.2em] text-link-bright font-semibold">Attention</p>
              <h2 className="display-section text-white mt-3">Low-stock alerts</h2>
              <p className="text-caption text-white/55 mt-1">Via v_low_stock_alerts.</p>
            </div>
          </SectionReveal>
          <div className="overflow-x-auto">
            {lowStockQ.isLoading ? <SkelTable cols={4} dark /> : (
              <table className="data" style={{ background: "#1d1d1f" }}>
                <thead style={{ background: "#141416" }}>
                  <tr className="text-white/60">
                    <th style={{ color: "rgba(255,255,255,0.55)" }}>Warehouse</th>
                    <th style={{ color: "rgba(255,255,255,0.55)" }}>SKU</th>
                    <th style={{ color: "rgba(255,255,255,0.55)" }}>Available</th>
                    <th style={{ color: "rgba(255,255,255,0.55)" }}>Reorder level</th>
                  </tr>
                </thead>
                <tbody className="text-white stagger-child">
                  {lowStockQ.data?.map((r, idx) => (
                    <tr key={`${r.sku}-${idx}`} className="border-t border-white/10">
                      <td className="text-white/90">{r.warehouse_name}</td>
                      <td><code className="text-white/90">{r.sku}</code></td>
                      <td>
                        <span className={`badge ${r.qty_available === 0 ? "badge-danger" : "badge-warn"}`}>
                          {r.qty_available}
                        </span>
                      </td>
                      <td className="text-white/80">{r.reorder_level}</td>
                    </tr>
                  ))}
                  {lowStockQ.data?.length === 0 && (
                    <tr><td colSpan={4} className="text-white/60">All stock above reorder levels.</td></tr>
                  )}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </section>

      {/* ─────────────── Top customers ─────────────── */}
      <section className="section-light py-16 pb-28">
        <div className="max-w-[1080px] mx-auto px-6">
          <SectionReveal>
            <p className="text-caption uppercase tracking-[0.2em] text-accent font-semibold">Q18 · Window function</p>
            <h2 className="display-section mt-3">Top customers</h2>
            <p className="text-caption text-ink/55 mt-1">ROW_NUMBER() OVER (PARTITION BY merchant_id ORDER BY lifetime_spend DESC)</p>
          </SectionReveal>
          {topCustomersQ.isLoading ? <SkelTable cols={3} /> : (
            <table className="data mt-8">
              <thead>
                <tr><th>Rank</th><th>Name</th><th>Lifetime spend</th></tr>
              </thead>
              <tbody className="stagger-child">
                {topCustomersQ.data?.slice(0, 10).map((c) => (
                  <tr key={`${c.merchant_id}-${c.rank_in_store}`}>
                    <td>
                      <motion.span
                        className="inline-flex items-center justify-center h-7 w-7 rounded-full font-display font-semibold text-white text-caption"
                        style={{
                          background: c.rank_in_store <= 3
                            ? `linear-gradient(135deg, #0071e3, #2997ff)`
                            : "#c8c8cc",
                        }}
                        whileHover={{ scale: 1.1 }}
                      >
                        {c.rank_in_store}
                      </motion.span>
                    </td>
                    <td className="font-display text-emphasis">{c.customer_name}</td>
                    <td className="font-semibold">{Number(c.lifetime_spend).toFixed(2)} {m.currency}</td>
                  </tr>
                ))}
                {topCustomersQ.data?.length === 0 && (
                  <tr><td colSpan={3} className="text-ink/50">No customers yet.</td></tr>
                )}
              </tbody>
            </table>
          )}
        </div>
      </section>
    </>
  );
}

function Kpi({
  label,
  value,
  suffix = "",
  decimals = 0,
  accent = false,
  small = false,
}: {
  label: string;
  value: number;
  suffix?: string;
  decimals?: number;
  accent?: boolean;
  small?: boolean;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
      className="kpi-tile"
    >
      <div className="kpi-label">{label}</div>
      <div className={`kpi-value ${accent ? "kpi-accent" : ""} ${small ? "text-tile" : ""}`}>
        <CountUp value={value} decimals={decimals} suffix={suffix} />
      </div>
    </motion.div>
  );
}

function SkelTable({ cols, dark = false }: { cols: number; dark?: boolean }) {
  return (
    <div className="rounded-xl-apple overflow-hidden" style={{ background: dark ? "#1d1d1f" : "#fff" }}>
      <div className="grid gap-0" style={{ gridTemplateColumns: `repeat(${cols}, 1fr)` }}>
        {Array.from({ length: cols * 4 }).map((_, i) => (
          <div key={i} className="px-4 py-3 border-b border-black/5">
            <Skeleton className="h-4 w-3/4" />
          </div>
        ))}
      </div>
    </div>
  );
}
