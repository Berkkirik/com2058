import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import { api } from "@/lib/api";
import { Loading, ErrorBox, Skeleton } from "@/components/Loading";
import SectionReveal from "@/components/SectionReveal";

export default function StorefrontPage() {
  const { slug = "" } = useParams();
  const [q, setQ] = useState("");

  const merchantQ = useQuery({
    queryKey: ["merchant", slug],
    queryFn: () => api.getMerchant(slug),
    enabled: !!slug,
  });
  const productsQ = useQuery({
    queryKey: ["products", slug, q],
    queryFn: () => api.listProducts(slug, { q }),
    enabled: !!slug,
  });
  const categoriesQ = useQuery({
    queryKey: ["categories", slug],
    queryFn: () => api.listCategories(slug),
    enabled: !!slug,
  });

  if (merchantQ.isLoading) return <Loading label="Loading merchant…" />;
  if (merchantQ.error) return <ErrorBox error={merchantQ.error} />;

  const m = merchantQ.data!;

  return (
    <>
      {/* ─────────────── Storefront hero ─────────────── */}
      <section className="section-light py-16 md:py-24 relative overflow-hidden">
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-10 right-10 h-[300px] w-[300px] rounded-full blur-[100px] opacity-40"
               style={{ background: "radial-gradient(circle, rgba(0,113,227,0.25), transparent)" }} />
        </div>
        <div className="max-w-[1200px] mx-auto px-6 relative">
          <div className="flex items-center gap-2 text-caption text-ink/55 mb-4">
            <Link to="/" className="link-bright text-link-dark">Home</Link>
            <span>/</span>
            <span>{m.slug}</span>
          </div>
          <h1 className="display-hero">
            {m.store_name}
          </h1>
          <div className="mt-5 flex flex-wrap items-center gap-2 text-caption">
            <span className="badge badge-info">{m.plan}</span>
            <span className="badge badge-default">{m.currency}</span>
            {m.city && <span className="badge badge-default">{m.city}</span>}
            {m.stats && (
              <>
                <span className="badge badge-default">{m.stats.products} products</span>
                <span className="badge badge-default">{m.stats.warehouses} warehouses</span>
              </>
            )}
            <Link to={`/dashboard/${m.slug}`} className="cta-link ml-2">Merchant dashboard</Link>
          </div>
        </div>
      </section>

      {/* ─────────────── Products ─────────────── */}
      <section className="section-light pb-24">
        <div className="max-w-[1200px] mx-auto px-6">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-10">
            <div>
              <h2 className="display-section">Products</h2>
              <p className="text-caption text-ink/55 mt-1">
                {productsQ.data?.length ?? "—"} item{(productsQ.data?.length ?? 0) !== 1 && "s"} in the catalog
              </p>
            </div>
            <div className="relative md:w-[340px]">
              <input
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Search products…"
                className="input pr-10"
              />
              <span className="absolute right-3 top-1/2 -translate-y-1/2 text-ink/35">⌕</span>
            </div>
          </div>

          {productsQ.isLoading ? (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-5">
              {Array.from({ length: 8 }).map((_, i) => (
                <div key={i} className="card-lift">
                  <Skeleton className="aspect-[4/3] mb-4" />
                  <Skeleton className="h-5 w-3/4 mb-2" />
                  <Skeleton className="h-4 w-1/2" />
                </div>
              ))}
            </div>
          ) : productsQ.error ? (
            <ErrorBox error={productsQ.error} />
          ) : (
            <AnimatePresence mode="popLayout">
              <motion.div
                key={q || "all"}
                layout
                className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-5 stagger-child"
              >
                {productsQ.data?.map((p) => (
                  <Link
                    key={p.product_id}
                    to={`/m/${slug}/product/${p.product_id}`}
                    className="product-tile no-underline text-ink group"
                  >
                    <div className="aspect-[4/3] rounded-[8px] mb-4 relative overflow-hidden"
                         style={{ background: `linear-gradient(135deg, hsl(${(p.product_id * 47) % 360}, 35%, 92%), hsl(${(p.product_id * 47 + 30) % 360}, 45%, 96%))` }}>
                      <span className="absolute inset-0 flex items-center justify-center font-display text-[56px] font-semibold text-ink/25 group-hover:scale-110 transition-transform duration-500 ease-apple">
                        {p.title.slice(0, 1)}
                      </span>
                      <span className="absolute top-2 left-2 badge badge-info text-[10px]">
                        {p.product_type}
                      </span>
                    </div>
                    <h3 className="font-display text-sub text-ink leading-tight">{p.title}</h3>
                    <p className="mt-1 text-body font-semibold" style={{ color: "#0071e3" }}>
                      {p.base_price.toFixed(2)} {p.currency}
                    </p>
                    <p className="text-caption text-ink/55 mt-1">
                      {p.variants_count} variant{p.variants_count !== 1 && "s"}
                    </p>
                    <span className="cta-link mt-3 text-link text-[13px]">View details</span>
                  </Link>
                ))}
                {productsQ.data?.length === 0 && (
                  <motion.p
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="col-span-full text-center py-12 text-ink/50 text-body"
                  >
                    No products match "{q}".
                  </motion.p>
                )}
              </motion.div>
            </AnimatePresence>
          )}
        </div>
      </section>

      {/* ─────────────── Categories strip ─────────────── */}
      {categoriesQ.data && categoriesQ.data.length > 0 && (
        <section className="section-dark py-20">
          <div className="max-w-[1200px] mx-auto px-6">
            <SectionReveal className="text-center mb-12">
              <p className="text-caption uppercase tracking-[0.2em] text-link-bright font-semibold">
                Taxonomy
              </p>
              <h2 className="display-section text-white mt-3">Categories</h2>
            </SectionReveal>
            <div className="flex flex-wrap gap-2 justify-center stagger-child">
              {categoriesQ.data.map((c) => (
                <span
                  key={c.category_id}
                  className="badge badge-info bg-white/10 text-white hover:bg-white/20 transition-colors cursor-default"
                >
                  {c.name}
                </span>
              ))}
            </div>
          </div>
        </section>
      )}
    </>
  );
}
