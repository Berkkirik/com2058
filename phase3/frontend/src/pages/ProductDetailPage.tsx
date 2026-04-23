import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Loading, ErrorBox } from "@/components/Loading";
import StatusBadge from "@/components/StatusBadge";

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

  return (
    <>
      <p>
        <Link to={`/m/${slug}`}>← Back to catalog</Link>
      </p>
      <h1>{data.title}</h1>
      <div className="text-sm mb-4">
        <span className="text-accent text-xl mr-3">
          {data.base_price.toFixed(2)} {data.currency}
        </span>
        <span className="badge badge-info mr-1">{data.product_type}</span>
        <StatusBadge value={data.status} />
      </div>

      <h2>Variants ({data.variants.length})</h2>
      <table className="data">
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
        <tbody>
          {data.variants.map((v) => (
            <tr key={v.variant_no}>
              <td>#{v.variant_no}</td>
              <td><code>{v.sku}</code></td>
              <td>
                {v.option_name}: <strong>{v.option_value}</strong>
              </td>
              <td>
                {v.price_override != null
                  ? `${v.price_override.toFixed(2)} ${data.currency}`
                  : <span className="text-muted">base</span>}
              </td>
              <td className="text-muted">{v.barcode ?? "—"}</td>
              <td>{v.is_default ? "✓" : ""}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>Reviews ({data.reviews.length})</h2>
      {data.reviews.length === 0 ? (
        <p className="text-muted">No reviews yet.</p>
      ) : (
        data.reviews.map((r) => (
          <div key={r.review_id} className="card mb-3">
            <div className="flex items-center gap-2">
              <strong>
                {"★".repeat(r.rating)}
                <span className="text-stone-300">{"★".repeat(5 - r.rating)}</span>
              </strong>
              <em>· {r.title}</em>
            </div>
            <p className="mt-1">{r.body}</p>
            <p className="text-xs text-muted mt-2 flex items-center gap-2">
              {r.is_verified_purchase && <span className="badge badge-ok">verified purchase</span>}
              <span>{r.helpful_count} helpful</span>
              <span>·</span>
              <time>{r.created_at?.slice(0, 10)}</time>
            </p>
          </div>
        ))
      )}
    </>
  );
}
