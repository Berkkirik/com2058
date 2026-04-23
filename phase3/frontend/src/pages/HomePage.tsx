import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { api } from "@/lib/api";
import { Loading, ErrorBox } from "@/components/Loading";
import SectionReveal from "@/components/SectionReveal";

export default function HomePage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["merchants"],
    queryFn: api.listMerchants,
  });

  return (
    <>
      {/* ─────────────── Hero ─────────────── */}
      <section className="section-dark relative overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-1/4 left-1/2 -translate-x-1/2 h-[600px] w-[900px] max-w-full rounded-full blur-[120px]"
               style={{ background: "radial-gradient(circle, rgba(0,113,227,0.25), transparent 70%)" }} />
        </div>
        <div className="max-w-[1080px] mx-auto px-6 py-24 md:py-36 text-center relative">
          <motion.p
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
            className="text-body-l text-link-bright mb-4 tracking-[0.16em] uppercase font-semibold"
          >
            COM2058 · Spring 2026
          </motion.p>
          <motion.h1
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1, ease: [0.22, 1, 0.36, 1] }}
            className="display-hero text-white"
          >
            StoreCraft.<br />
            <span className="gradient-text">Commerce, reimagined.</span>
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2, ease: [0.22, 1, 0.36, 1] }}
            className="mt-6 text-sub text-white/80 max-w-[640px] mx-auto"
          >
            A multi-tenant e-commerce platform powered by MySQL&nbsp;8, FastAPI, and a React SPA.
            17 entities · 25 relationships · one reproducible demo.
          </motion.p>
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3, ease: [0.22, 1, 0.36, 1] }}
            className="mt-10 flex flex-wrap items-center justify-center gap-3"
          >
            <Link to="/admin" className="btn-primary">
              Open admin
            </Link>
            <a href="/docs" target="_blank" rel="noreferrer" className="btn-outline-dark">
              API docs
            </a>
          </motion.div>
        </div>
      </section>

      {/* ─────────────── Merchant directory ─────────────── */}
      <section className="section-light py-20 md:py-28">
        <div className="max-w-[1200px] mx-auto px-6">
          <SectionReveal className="text-center mb-16">
            <p className="text-caption uppercase tracking-[0.2em] text-accent font-semibold">Tenants</p>
            <h2 className="display-section mt-3">Browse the merchant directory.</h2>
            <p className="text-sub text-ink/60 mt-3 max-w-[580px] mx-auto">
              Every StoreCraft tenant lives behind its own <code>/m/&lt;slug&gt;</code> storefront.
              Each one shares the same schema, but owns its own products, orders, inventory and customers.
            </p>
          </SectionReveal>

          {isLoading && <Loading label="Loading merchants…" />}
          {error && <ErrorBox error={error} />}

          {data && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 stagger-child">
              {data.map((m, i) => (
                <motion.div
                  key={m.merchant_id}
                  whileHover={{ y: -6 }}
                  transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
                  className="product-tile"
                >
                  <div className="aspect-[4/3] rounded-[8px] bg-gradient-to-br from-accent/10 via-off-white to-accent/5 flex items-center justify-center mb-5 relative overflow-hidden">
                    <span className="font-display text-[80px] font-semibold text-accent/40 select-none">
                      {m.store_name.slice(0, 1)}
                    </span>
                    <div className="absolute top-3 right-3">
                      <span className="badge badge-info">{m.plan}</span>
                    </div>
                  </div>
                  <h3 className="font-display text-card-title text-ink">{m.store_name}</h3>
                  <p className="text-caption text-ink/55 mt-1">
                    {m.city ?? "—"} · {m.currency}
                  </p>
                  <p className="text-caption text-ink/45 mt-2 font-mono">{m.contact_email}</p>

                  <div className="flex flex-col gap-1.5 mt-5 border-t border-black/5 pt-4">
                    <Link to={`/m/${m.slug}`} className="cta-link">Browse catalog</Link>
                    <Link to={`/dashboard/${m.slug}`} className="cta-link">View dashboard</Link>
                    <Link to={`/dashboard/${m.slug}/orders`} className="cta-link">See orders</Link>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* ─────────────── Feature strip ─────────────── */}
      <section className="section-dark py-20 md:py-28">
        <div className="max-w-[1200px] mx-auto px-6">
          <SectionReveal className="text-center mb-16">
            <p className="text-caption uppercase tracking-[0.2em] text-link-bright font-semibold">Built on</p>
            <h2 className="display-section mt-3 text-white">A carefully-chosen stack.</h2>
          </SectionReveal>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {FEATURES.map((f, i) => (
              <SectionReveal key={f.title} delay={i * 0.08} className="card-dark text-center">
                <div className="text-[40px] mb-3">{f.icon}</div>
                <h4 className="font-display text-emphasis text-white">{f.title}</h4>
                <p className="text-caption text-white/55 mt-2">{f.desc}</p>
              </SectionReveal>
            ))}
          </div>
        </div>
      </section>
    </>
  );
}

const FEATURES = [
  { icon: "🗄️", title: "MySQL 8", desc: "22 tables with compound PKs, generated columns, triggers, views." },
  { icon: "⚡", title: "FastAPI", desc: "JSON-only API, CORS, Pydantic models, automatic OpenAPI." },
  { icon: "⚛️", title: "React 18", desc: "Vite + TypeScript + Tailwind. TanStack Query handles server state." },
  { icon: "📦", title: "Docker", desc: "One compose up. MySQL + backend + frontend + phpMyAdmin." },
];
