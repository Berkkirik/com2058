import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "@/lib/api";
import { Loading, ErrorBox } from "@/components/Loading";

export default function AdminPage() {
  const merchantsQ = useQuery({ queryKey: ["merchants"], queryFn: api.listMerchants });
  const activityQ = useQuery({ queryKey: ["activity"], queryFn: () => api.adminActivity(30) });

  if (merchantsQ.isLoading) return <Loading label="Loading admin…" />;
  if (merchantsQ.error) return <ErrorBox error={merchantsQ.error} />;

  return (
    <>
      <h1>Platform Admin</h1>
      <p className="text-muted">Cross-tenant view for support / moderation roles.</p>

      <h2>Merchants</h2>
      <table className="data">
        <thead>
          <tr><th>ID</th><th>Store</th><th>Plan</th><th>Currency</th><th>Created</th><th>Status</th><th>Actions</th></tr>
        </thead>
        <tbody>
          {merchantsQ.data?.map((m) => (
            <tr key={m.merchant_id}>
              <td>{m.merchant_id}</td>
              <td>
                <strong>{m.store_name}</strong> <span className="text-muted">(/m/{m.slug})</span>
              </td>
              <td><span className="badge badge-info">{m.plan}</span></td>
              <td>{m.currency}</td>
              <td>{m.created_at?.slice(0, 10)}</td>
              <td>
                {m.suspended
                  ? <span className="badge badge-danger">suspended</span>
                  : m.activated_at
                    ? <span className="badge badge-ok">active</span>
                    : <span className="badge badge-warn">pending</span>}
              </td>
              <td className="space-x-2">
                <Link to={`/m/${m.slug}`}>Catalog</Link>
                <Link to={`/dashboard/${m.slug}`}>Dashboard</Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2>Recent activity (last 7 days)</h2>
      {activityQ.isLoading ? (
        <Loading />
      ) : (
        <table className="data">
          <thead><tr><th>When</th><th>Actor</th><th>Entity</th><th>Action</th></tr></thead>
          <tbody>
            {activityQ.data?.map((a) => (
              <tr key={a.event_id}>
                <td>{a.occurred_at?.replace("T", " ").slice(0, 16)}</td>
                <td>{a.actor_label}</td>
                <td><code>{a.entity_type}:{a.entity_id}</code></td>
                <td><code>{a.action}</code></td>
              </tr>
            ))}
            {activityQ.data?.length === 0 && (
              <tr><td colSpan={4} className="text-muted">No recent activity.</td></tr>
            )}
          </tbody>
        </table>
      )}
    </>
  );
}
