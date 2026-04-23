import { useQuery } from "@tanstack/react-query";
import { Link, useNavigate } from "react-router-dom";
import { motion, useScroll, useTransform } from "framer-motion";
import { useRef } from "react";
import { api } from "@/lib/api";
import { Loading, ErrorBox } from "@/components/Loading";
import SectionReveal from "@/components/SectionReveal";
import TextReveal from "@/components/TextReveal";
import MagneticButton from "@/components/MagneticButton";
import TiltCard from "@/components/TiltCard";
import GradientMesh from "@/components/GradientMesh";
import Marquee from "@/components/Marquee";
import SpotlightCursor from "@/components/SpotlightCursor";
import CountUp from "@/components/CountUp";

export default function HomePage() {
  const navigate = useNavigate();
  const { data, isLoading, error } = useQuery({
    queryKey: ["merchants"],
    queryFn: api.listMerchants,
  });
  const kpiQ = useQuery({ queryKey: ["kpi"], queryFn: api.kpi });

  // Parallax: hero content drifts up as user scrolls
  const heroRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: heroRef, offset: ["start start", "end start"] });
  const heroY = useTransform(scrollYProgress, [0, 1], [0, -80]);
  const heroOpacity = useTransform(scrollYProgress, [0, 1], [1, 0.2]);
  const heroScale = useTransform(scrollYProgress, [0, 1], [1, 0.95]);

  // Aggregate totals across all merchants for the stat strip
  const totals = (kpiQ.data ?? []).reduce(
    (acc, k) => ({
      orders: acc.orders + (k.orders_count ?? 0),
      sales: acc.sales + Number(k.gross_sales ?? 0),
    }),
    { orders: 0, sales: 0 }
  );

  return (
    <>
      <SpotlightCursor />

      {/* ═══════════════════════ HERO ═══════════════════════ */}
      <section
        ref={heroRef}
        className="section-dark relative overflow-hidden min-h-[92vh] flex items-center"
      >
        <GradientMesh variant="dark" />

        {/* Grid texture for depth */}
        <div
          aria-hidden
          className="absolute inset-0 opacity-[0.05] pointer-events-none"
          style={{
            backgroundImage:
              "linear-gradient(rgba(255,255,255,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.5) 1px, transparent 1px)",
            backgroundSize: "64px 64px",
          }}
        />

        <motion.div
          style={{ y: heroY, opacity: heroOpacity, scale: heroScale }}
          className="max-w-[1200px] mx-auto px-6 py-24 relative w-full text-center"
        >
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center gap-2 px-4 py-1.5 rounded-pill bg-white/5 border border-white/10 backdrop-blur mb-8"
          >
            <span className="h-2 w-2 rounded-full bg-link-bright animate-pulse-glow" />
            <span className="text-micro text-white/80 tracking-[0.15em] uppercase font-semibold">
              COM2058 · Spring 2026 · Phase 3
            </span>
          </motion.div>

          <TextReveal
            text="StoreCraft."
            as="h1"
            className="display-hero text-white block"
            delay={0.15}
          />
          <TextReveal
            text="Commerce, reimagined."
            as="h1"
            className="display-hero gradient-text block mt-2"
            delay={0.4}
            stagger={0.05}
          />

          <motion.p
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 1.0, ease: [0.22, 1, 0.36, 1] }}
            className="mt-8 text-sub text-white/70 max-w-[620px] mx-auto"
          >
            A multi-tenant e-commerce platform powered by MySQL&nbsp;8, FastAPI, and React&nbsp;18.
            <span className="block mt-1 text-white/50">
              17 entities · 25 relationships · one reproducible demo.
            </span>
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 1.15, ease: [0.22, 1, 0.36, 1] }}
            className="mt-12 flex flex-wrap items-center justify-center gap-3"
          >
            <MagneticButton className="btn-primary" onClick={() => navigate("/admin")}>
              Open admin
            </MagneticButton>
            <MagneticButton className="btn-outline-dark" onClick={() => window.open("/docs", "_blank")}>
              View API docs
            </MagneticButton>
          </motion.div>

          {/* Scroll hint */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.8, duration: 0.8 }}
            className="absolute bottom-8 left-1/2 -translate-x-1/2 text-white/40 text-micro flex flex-col items-center gap-2"
          >
            <span className="uppercase tracking-[0.25em]">Scroll</span>
            <motion.span
              animate={{ y: [0, 6, 0] }}
              transition={{ duration: 1.8, repeat: Infinity, ease: "easeInOut" }}
              className="text-[14px]"
            >
              ↓
            </motion.span>
          </motion.div>
        </motion.div>
      </section>

      {/* ═══════════════════════ STAT STRIP ═══════════════════════ */}
      <section className="section-dark py-14 border-t border-white/5 relative overflow-hidden">
        <div className="max-w-[1200px] mx-auto px-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
            {[
              { label: "Entities", value: 17, decimals: 0 },
              { label: "Relationships", value: 25, decimals: 0 },
              { label: "Total orders", value: totals.orders, decimals: 0 },
              { label: "Gross sales", value: totals.sales, decimals: 0, prefix: "$" },
            ].map((s, i) => (
              <motion.div
                key={s.label}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.55, delay: i * 0.08, ease: [0.22, 1, 0.36, 1] }}
              >
                <div className="font-display text-section text-white">
                  <CountUp
                    value={Number(s.value ?? 0)}
                    decimals={s.decimals}
                    prefix={s.prefix ?? ""}
                  />
                </div>
                <div className="kpi-label text-white/50 mt-2">{s.label}</div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════════════ MARQUEE ═══════════════════════ */}
      <section className="section-light py-10 border-y border-black/5">
        <Marquee speed={45}>
          {MARQUEE_ITEMS.map((item) => (
            <span
              key={item}
              className="font-display text-[32px] font-semibold text-ink/20 hover:text-accent transition-colors duration-300"
            >
              {item}
            </span>
          ))}
        </Marquee>
      </section>

      {/* ═══════════════════════ MERCHANT DIRECTORY ═══════════════════════ */}
      <section className="section-light py-24 md:py-32 relative overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div
            aria-hidden
            className="absolute top-0 left-1/2 -translate-x-1/2 h-[400px] w-[800px] rounded-full blur-[120px] opacity-40"
            style={{ background: "radial-gradient(circle, rgba(0,113,227,0.15), transparent 70%)" }}
          />
        </div>
        <div className="max-w-[1200px] mx-auto px-6 relative">
          <SectionReveal className="text-center mb-16 max-w-[640px] mx-auto">
            <p className="text-caption uppercase tracking-[0.2em] text-accent font-semibold">
              Tenants
            </p>
            <h2 className="display-section mt-3">
              Three merchants.
              <span className="text-ink/40"> One schema.</span>
            </h2>
            <p className="text-sub text-ink/60 mt-4">
              Every tenant shares the 22-table MySQL schema with logical isolation through
              <code className="mx-1 text-accent">merchant_id</code>. Their catalogs, orders, inventory
              and customers never leak across boundaries.
            </p>
          </SectionReveal>

          {isLoading && <Loading label="Loading merchants…" />}
          {error && <ErrorBox error={error} />}

          {data && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {data.map((m, i) => (
                <SectionReveal key={m.merchant_id} delay={i * 0.08}>
                  <TiltCard className="product-tile cursor-pointer h-full" max={8}>
                    <Link
                      to={`/m/${m.slug}`}
                      className="block no-underline text-ink h-full"
                    >
                      {/* Monogram on colored gradient */}
                      <div
                        className="aspect-[4/3] rounded-[12px] relative overflow-hidden mb-6"
                        style={{
                          background: `linear-gradient(135deg, hsl(${(m.merchant_id * 97) % 360}, 70%, 45%), hsl(${(m.merchant_id * 97 + 40) % 360}, 75%, 30%))`,
                        }}
                      >
                        <motion.span
                          initial={{ scale: 1 }}
                          whileHover={{ scale: 1.08 }}
                          transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
                          className="absolute inset-0 flex items-center justify-center font-display font-semibold text-white/95 select-none"
                          style={{ fontSize: "120px", lineHeight: 1 }}
                        >
                          {m.store_name.slice(0, 1)}
                        </motion.span>
                        <div className="absolute top-4 left-4 flex gap-2 z-10">
                          <span className="badge bg-white/20 text-white backdrop-blur">
                            {m.plan}
                          </span>
                          <span className="badge bg-white/20 text-white backdrop-blur">
                            {m.currency}
                          </span>
                        </div>
                        {/* Shine sweep */}
                        <motion.div
                          className="absolute inset-0 pointer-events-none"
                          style={{
                            background: "linear-gradient(115deg, transparent 30%, rgba(255,255,255,0.15) 50%, transparent 70%)",
                            backgroundSize: "200% 200%",
                          }}
                          initial={{ backgroundPosition: "200% 200%" }}
                          whileHover={{ backgroundPosition: "-100% -100%" }}
                          transition={{ duration: 0.8 }}
                        />
                      </div>

                      <h3 className="font-display text-tile text-ink">{m.store_name}</h3>
                      <p className="text-caption text-ink/55 mt-2">
                        {m.city ?? "—"} · <span className="font-mono">{m.contact_email}</span>
                      </p>

                      <div className="mt-6 flex flex-col gap-2 border-t border-black/5 pt-4">
                        <Link to={`/m/${m.slug}`} className="cta-link">Browse catalog</Link>
                        <Link to={`/dashboard/${m.slug}`} className="cta-link">View dashboard</Link>
                        <Link to={`/dashboard/${m.slug}/orders`} className="cta-link">See orders</Link>
                      </div>
                    </Link>
                  </TiltCard>
                </SectionReveal>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* ═══════════════════════ STACK ═══════════════════════ */}
      <section className="section-dark py-24 md:py-32 relative overflow-hidden">
        <GradientMesh variant="dark" />
        <div className="max-w-[1200px] mx-auto px-6 relative">
          <SectionReveal className="text-center mb-16 max-w-[640px] mx-auto">
            <p className="text-caption uppercase tracking-[0.2em] text-link-bright font-semibold">
              Built on
            </p>
            <h2 className="display-section text-white mt-3">
              A carefully-chosen stack.
            </h2>
            <p className="text-sub text-white/60 mt-4">
              Every piece of StoreCraft is deliberate — from the compound FK pattern in MySQL to
              the type-safe fetch client on the client.
            </p>
          </SectionReveal>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 stagger-child">
            {FEATURES.map((f) => (
              <div key={f.title} className="card-dark text-center h-full relative overflow-hidden group">
                <motion.div
                  className="text-[56px] mb-4 inline-block"
                  whileHover={{ rotate: [0, -10, 10, -6, 6, 0], scale: 1.15 }}
                  transition={{ duration: 0.8 }}
                >
                  {f.icon}
                </motion.div>
                <h4 className="font-display text-emphasis text-white">{f.title}</h4>
                <p className="text-caption text-white/55 mt-2 leading-relaxed">{f.desc}</p>
                <div
                  aria-hidden
                  className="absolute inset-0 pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-500"
                  style={{
                    background: "radial-gradient(circle at top, rgba(0,113,227,0.2), transparent 70%)",
                  }}
                />
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════════════ CTA ═══════════════════════ */}
      <section className="section-light py-24 md:py-32 relative overflow-hidden">
        <div
          aria-hidden
          className="absolute inset-0 pointer-events-none opacity-50"
          style={{
            background:
              "radial-gradient(circle at 30% 50%, rgba(0,113,227,0.1), transparent 50%), radial-gradient(circle at 70% 50%, rgba(41,151,255,0.08), transparent 50%)",
          }}
        />
        <div className="max-w-[980px] mx-auto px-6 text-center relative">
          <SectionReveal>
            <p className="text-caption uppercase tracking-[0.2em] text-accent font-semibold">
              Ready
            </p>
            <h2 className="display-section mt-3">
              Explore the data model.
            </h2>
            <p className="text-sub text-ink/60 mt-4 max-w-[560px] mx-auto">
              The FastAPI Swagger UI documents every endpoint, phpMyAdmin browses every row,
              and the showcase SQL scripts walk through 25 query patterns.
            </p>
            <div className="mt-10 flex flex-wrap items-center justify-center gap-3">
              <MagneticButton className="btn-primary" onClick={() => window.open("/docs", "_blank")}>
                API reference
              </MagneticButton>
              <MagneticButton className="btn-outline-light" onClick={() => window.open("http://localhost:8080", "_blank")}>
                Browse schema (phpMyAdmin)
              </MagneticButton>
            </div>
          </SectionReveal>
        </div>
      </section>
    </>
  );
}

const FEATURES = [
  { icon: "🗄️", title: "MySQL 8", desc: "22 tables · compound PKs · generated columns · views · triggers." },
  { icon: "⚡", title: "FastAPI", desc: "JSON API · CORS · Pydantic · automatic OpenAPI." },
  { icon: "⚛️", title: "React 18", desc: "Vite · TypeScript · Tailwind · TanStack Query." },
  { icon: "📦", title: "Docker", desc: "One compose up. 4 services · reproducible demo." },
];

const MARQUEE_ITEMS = [
  "MySQL 8",
  "✦",
  "FastAPI",
  "✦",
  "React 18",
  "✦",
  "TypeScript",
  "✦",
  "Tailwind CSS",
  "✦",
  "TanStack Query",
  "✦",
  "SQLAlchemy",
  "✦",
  "Docker",
  "✦",
  "Vite",
  "✦",
  "Faker",
];
