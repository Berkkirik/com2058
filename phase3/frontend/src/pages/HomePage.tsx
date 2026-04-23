import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "@/lib/api";
import { Loading, ErrorBox } from "@/components/Loading";

export default function HomePage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["merchants"],
    queryFn: api.listMerchants,
  });

  if (isLoading) return <Loading label="Loading merchants…" />;
  if (error) return <ErrorBox error={error} />;

  return (
    <>
      <h1>Merchant Directory</h1>
      <p className="text-muted">
        Every StoreCraft tenant lives behind its own <code>/m/&lt;slug&gt;</code> storefront.
        Pick one to browse its catalog or jump to the dashboard.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
        {data?.map((m) => (
          <div key={m.merchant_id} className="card">
            <h3 className="mt-0">{m.store_name}</h3>
            <div className="flex items-center gap-2 mb-2 text-sm text-muted">
              <span className="badge badge-info">{m.plan}</span>
              <span className="badge">{m.currency}</span>
              {m.city && <span>· {m.city}</span>}
            </div>
            <p className="text-sm">Contact: <code>{m.contact_email}</code></p>
            <div className="flex flex-col gap-1 mt-3">
              <Link to={`/m/${m.slug}`}>Browse catalog →</Link>
              <Link to={`/dashboard/${m.slug}`}>Dashboard →</Link>
              <Link to={`/dashboard/${m.slug}/orders`}>Orders →</Link>
            </div>
          </div>
        ))}
      </div>

      <section className="mt-10">
        <h2>About the demo</h2>
        <p>
          This storefront and dashboard are backed by a 22-table MySQL&nbsp;8 schema derived from the Phase&nbsp;2
          ER diagram (17 entities + 5 bridges). The React SPA you're looking at talks to the FastAPI JSON
          backend exclusively — every page load fires real SQL and renders the results via TanStack Query.
        </p>
      </section>
    </>
  );
}
