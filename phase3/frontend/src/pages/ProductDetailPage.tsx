import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { api } from "@/lib/api";
import { Loading, ErrorBox } from "@/components/Loading";
import StatusBadge from "@/components/StatusBadge";
import SectionReveal from "@/components/SectionReveal";

export default function ProductDetailPage() {
  const { slug = "", id = "" } = useParams();
  const productId = Number(id);
  const { data, isLoading, error } = useQuery({
    queryKey: ["product", slug, productId],
    queryFn: () => api.getProduct(slug, productId),
    enabled: !!slug && Number.isFinite(productId),
  });

  if (isLoading) return <Loading label="Loading product…" />;
  if (error) return <ErrorBox error={error} />;
  if (!data) return null;

  const colorSeed = (data.product_id * 47) % 360;

  return (
    <>
      {/* ─────────────── Hero on black (product-as-hero) ─────────────── */}
      <section className="section-dark py-20 md:py-28 relative overflow-hidden">
        <div className="max-w-[1200px] mx-auto px-6">
          <Link to={`/m/${slug}`} className="cta-link text-link-bright mb-6 inline-block">
            <span className="rotate-180 inline-block mr-1">›</span>
            <span className="ml-6">Back to catalog</span>
          </Link>

          <div className="grid md:grid-cols-2 gap-12 items-center mt-6">
            {/* Product art block */}
            <motion.div
              initial={{ opacity: 0, scale: 0.96 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
              className="aspect-square rounded-xl-apple relative overflow-hidden flex items-center justify-center animate-float"
              style={{
                background: `linear-gradient(135deg, hsl(${colorSeed}, 55%, 22%), hsl(${(colorSeed + 40) % 360}, 45%, 14%))`,
                boxShadow: "rgba(0, 0, 0, 0.6) 0 30px 80px",
              }}
            >
              <span className="font-display font-semibold text-white/95 select-none"
                    style={{ fontSize: "clamp(120px, 16vw, 240px)", lineHeight: 1 }}>
                {data.title.slice(0, 1)}
              </span>
              <div className="absolute top-5 left-5 flex gap-2">
                <span className="badge badge-info bg-white/15 text-white">{data.product_type}</span>
                <StatusBadge value={data.status} />
              </div>
            </motion.div>

            {/* Title + CTA */}
            <motion.div
              initial={{ opacity: 0, x: 30 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.7, delay: 0.15, ease: [0.22, 1, 0.36, 1] }}
            >
              <p className="text-caption uppercase tracking-[0.2em] text-link-bright font-semibold">
                Product detail
              </p>
              <h1 className="display-hero text-white mt-4">{data.title}</h1>
              <p className="mt-6 font-display text-section" style={{ color: "#2997ff" }}>
                {data.base_price.toFixed(2)} {data.currency}
              </p>
              <p className="mt-4 text-sub text-white/70 max-w-[520px]">
                {data.variants.length} variant{data.variants.length !== 1 && "s"} · {data.reviews.length} review{data.reviews.length !== 1 && "s"} from verified purchases
              </p>
              <div className="mt-8 flex flex-wrap gap-3">
                <button className="btn-primary" onClick={() => alert("Demo: checkout flow lives in Q25 transactional SQL.")}>
                  Buy — {data.base_price.toFixed(2)} {data.currency}
                </button>
                <button className="btn-outline-dark">Learn more</button>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* ─────────────── Variants ─────────────── */}
      <section className="section-light py-20">
        <div className="max-w-[1080px] mx-auto px-6">
          <SectionReveal>
            <p className="text-caption uppercase tracking-[0.2em] text-accent font-semibold">Choose</p>
            <h2 className="display-section mt-3">Variants</h2>
            <p className="text-sub text-ink/60 mt-2">{data.variants.length} options · weak entity in the ER model.</p>
          </SectionReveal>

          <div className="mt-10 overflow-x-auto">
            <table className="data min-w-full">
              <thead>
                <tr>
                  <th>#</th>
                  <th>SKU</th>
                  <th>Option</th>
                  <th>Price</th>
                  <th>Barcode</th>
                  <th>Default</th>
                </tr>
              </thead>
              <tbody className="stagger-child">
                {data.variants.map((v) => (
                  <tr key={v.variant_no}>
                    <td className="font-semibold">#{v.variant_no}</td>
                    <td><code>{v.sku}</code></td>
                    <td>
                      <span className="text-ink/60">{v.option_name}:</span>{" "}
                      <span className="font-semibold">{v.option_value}</span>
                    </td>
                    <td>
                      {v.price_override != null
                        ? <span className="font-semibold">{v.price_override.toFixed(2)} {data.currency}</span>
                        : <span className="text-ink/45">base</span>}
                    </td>
                    <td className="text-ink/55 font-mono">{v.barcode ?? "—"}</td>
                    <td>{v.is_default ? <span className="badge badge-info">default</span> : ""}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* ─────────────── Reviews ─────────────── */}
      <section className="section-light pb-28">
        <div className="max-w-[980px] mx-auto px-6">
          <SectionReveal>
            <p className="text-caption uppercase tracking-[0.2em] text-accent font-semibold">What people say</p>
            <h2 className="display-section mt-3">Reviews</h2>
          </SectionReveal>

          {data.reviews.length === 0 ? (
            <div className="card mt-10 text-center text-ink/55 py-10">
              <p>No reviews yet.</p>
            </div>
          ) : (
            <div className="grid md:grid-cols-2 gap-6 mt-10 stagger-child">
              {data.reviews.map((r) => (
                <motion.article
                  key={r.review_id}
                  whileHover={{ y: -4 }}
                  transition={{ duration: 0.3 }}
                  className="card-lift"
                >
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-[18px] tracking-wider" style={{ color: "#0071e3" }}>
                      {"★".repeat(r.rating)}<span className="text-ink/15">{"★".repeat(5 - r.rating)}</span>
                    </span>
                    {r.is_verified_purchase && (
                      <span className="badge badge-ok">verified</span>
                    )}
                  </div>
                  <h4 className="font-display text-emphasis text-ink">{r.title}</h4>
                  <p className="text-body text-ink/70 mt-2">{r.body}</p>
                  <p className="text-caption text-ink/45 mt-4">
                    {r.helpful_count} helpful · {r.created_at?.slice(0, 10)}
                  </p>
                </motion.article>
              ))}
            </div>
          )}
        </div>
      </section>
    </>
  );
}
