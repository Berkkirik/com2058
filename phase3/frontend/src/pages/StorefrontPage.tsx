import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Loading, ErrorBox } from "@/components/Loading";

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
    queryFn: () => api.listProducts(slug, q),
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
      <h1>{m.store_name}</h1>
      <div className="flex items-center gap-2 text-sm text-muted mb-6">
        <span className="badge badge-info">{m.plan}</span>
        {m.city && <span>· {m.city}</span>}
        <span>·</span>
        <Link to={`/dashboard/${m.slug}`}>Dashboard</Link>
      </div>

      <div className="flex gap-2 mb-4">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Search products…"
          className="input max-w-xs"
        />
      </div>

      {productsQ.isLoading ? (
        <Loading label="Loading products…" />
      ) : productsQ.error ? (
        <ErrorBox error={productsQ.error} />
      ) : (
        <>
          <h2>Products ({productsQ.data?.length ?? 0})</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {productsQ.data?.map((p) => (
              <Link
                key={p.product_id}
                to={`/m/${slug}/product/${p.product_id}`}
                className="card hover:shadow-md transition-shadow no-underline text-ink"
              >
                <h3 className="mt-0 font-serif text-base">{p.title}</h3>
                <p className="text-accent font-semibold my-1">
                  {p.base_price.toFixed(2)} {p.currency}
                </p>
                <p className="text-xs text-muted">
                  {p.product_type} · {p.variants_count} variant{p.variants_count !== 1 && "s"}
                </p>
              </Link>
            ))}
            {productsQ.data?.length === 0 && (
              <p className="text-muted col-span-full">No products match your search.</p>
            )}
          </div>
        </>
      )}

      {categoriesQ.data && categoriesQ.data.length > 0 && (
        <>
          <h2>Categories</h2>
          <div className="flex flex-wrap gap-2">
            {categoriesQ.data.map((c) => (
              <span key={c.category_id} className="badge badge-info">
                {c.name}
              </span>
            ))}
          </div>
        </>
      )}
    </>
  );
}
