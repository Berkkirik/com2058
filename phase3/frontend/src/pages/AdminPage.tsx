import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { api } from "@/lib/api";
import { Loading, ErrorBox } from "@/components/Loading";
import SectionReveal from "@/components/SectionReveal";

export default function AdminPage() {
  const merchantsQ = useQuery({ queryKey: ["merchants"], queryFn: api.listMerchants });
  const activityQ = useQuery({ queryKey: ["activity"], queryFn: () => api.adminActivity(30) });

  if (merchantsQ.isLoading) return <Loading label="Loading admin…" />;
  if (merchantsQ.error) return <ErrorBox error={merchantsQ.error} />;

  return (
    <>
      {/* ─────────────── Hero ─────────────── */}
      <section className="section-dark py-20 relative overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute bottom-0 right-1/4 h-[400px] w-[600px] rounded-full blur-[120px] opacity-30"
               style={{ background: "radial-gradient(circle, rgba(0,113,227,0.5), transparent 70%)" }} />
        </div>
        <div className="max-w-[1200px] mx-auto px-6 relative">
          <p className="text-caption uppercase tracking-[0.2em] text-link-bright font-semibold">Platform</p>
          <h1 className="display-hero text-white mt-3">Admin console.</h1>
          <p className="text-sub text-white/70 mt-3 max-w-[640px]">
            Cross-tenant visibility for support and moderation roles. Audit log backed by the polymorphic
            ACTIVITY_LOG table (R25).
          </p>
        </div>
      </section>

      {/* ─────────────── Merchants ─────────────── */}
      <section className="section-light py-16">
        <div className="max-w-[1200px] mx-auto px-6">
          <SectionReveal>
            <p className="text-caption uppercase tracking-[0.2em] text-accent font-semibold">Tenants</p>
            <h2 className="display-section mt-3">Merchants</h2>
          </SectionReveal>
          <div className="mt-8 overflow-x-auto">
            <table className="data">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Store</th>
                  <th>Plan</th>
                  <th>Currency</th>
                  <th>Created</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody className="stagger-child">
                {merchantsQ.data?.map((m) => (
                  <tr key={m.merchant_id}>
                    <td className="font-mono text-caption text-ink/60">{m.merchant_id}</td>
                    <td>
                      <span className="font-display text-emphasis text-ink">{m.store_name}</span>
                      <span className="block text-caption text-ink/50 font-mono">/m/{m.slug}</span>
                    </td>
                    <td><span className="badge badge-info">{m.plan}</span></td>
                    <td className="font-mono text-caption">{m.currency}</td>
                    <td className="text-ink/55">{m.created_at?.slice(0, 10)}</td>
                    <td>
                      {m.suspended ? <span className="badge badge-danger">suspended</span>
                        : m.activated_at ? <span className="badge badge-ok">active</span>
                          : <span className="badge badge-warn">pending</span>}
                    </td>
                    <td className="space-x-3">
                      <Link to={`/m/${m.slug}`} className="text-link-dark hover:underline">Catalog</Link>
                      <Link to={`/dashboard/${m.slug}`} className="text-link-dark hover:underline">Dashboard</Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* ─────────────── Recent activity ─────────────── */}
      <section className="section-dark py-20 pb-28">
        <div className="max-w-[1200px] mx-auto px-6">
          <SectionReveal>
            <p className="text-caption uppercase tracking-[0.2em] text-link-bright font-semibold">Audit trail</p>
            <h2 className="display-section text-white mt-3">Recent activity · last 7 days</h2>
            <p className="text-caption text-white/55 mt-1">Via v_recent_activity (polymorphic entity reference).</p>
          </SectionReveal>

          {activityQ.isLoading ? (
            <Loading label="Loading activity…" />
          ) : (
            <motion.ol
              initial="hidden"
              whileInView="visible"
              viewport={{ once: true }}
              variants={{
                visible: { transition: { staggerChildren: 0.05 } },
              }}
              className="mt-10 space-y-2 max-w-[980px] mx-auto"
            >
              {activityQ.data?.map((a) => (
                <motion.li
                  key={a.event_id}
                  variants={{
                    hidden: { opacity: 0, x: -12 },
                    visible: { opacity: 1, x: 0 },
                  }}
                  className="card-dark flex items-start gap-4 hover:border-accent/40 transition-colors"
                  style={{ borderLeft: "3px solid rgba(0,113,227,0.5)" }}
                >
                  <div className="h-8 w-8 rounded-full flex-shrink-0 bg-accent/20 flex items-center justify-center text-link-bright font-semibold text-caption">
                    {a.actor_label?.slice(0, 1).toUpperCase() ?? "?"}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-baseline justify-between gap-3">
                      <span className="font-display text-emphasis text-white truncate">{a.actor_label}</span>
                      <time className="text-caption text-white/40 font-mono whitespace-nowrap">
                        {a.occurred_at?.replace("T", " ").slice(0, 16)}
                      </time>
                    </div>
                    <p className="text-caption text-white/70 mt-1">
                      <code className="text-link-bright">{a.action}</code>
                      <span className="mx-2 text-white/30">on</span>
                      <code className="text-white/85">{a.entity_type}:{a.entity_id}</code>
                    </p>
                  </div>
                </motion.li>
              ))}
              {activityQ.data?.length === 0 && (
                <li className="text-white/55 text-center py-8">No recent activity.</li>
              )}
            </motion.ol>
          )}
        </div>
      </section>
    </>
  );
}
