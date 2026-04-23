import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Loading, ErrorBox } from "@/components/Loading";
import StatusBadge from "@/components/StatusBadge";

export default function OrdersListPage() {
  const { slug = "" } = useParams();
  const merchantQ = useQuery({ queryKey: ["merchant", slug], queryFn: () => api.getMerchant(slug), enabled: !!slug });
  const ordersQ = useQuery({ queryKey: ["orders", slug], queryFn: () => api.listOrders(slug), enabled: !!slug });

  if (merchantQ.isLoading || ordersQ.isLoading) return <Loading label="Loading orders…" />;
  if (merchantQ.error) return <ErrorBox error={merchantQ.error} />;
  if (ordersQ.error) return <ErrorBox error={ordersQ.error} />;

  const m = merchantQ.data!;
  return (
    <>
      <p><Link to={`/dashboard/${slug}`}>← Dashboard</Link></p>
      <h1>Orders · {m.store_name}</h1>
      <p className="text-muted">{ordersQ.data?.length ?? 0} most-recent orders.</p>

      <table className="data">
        <thead>
          <tr><th>#</th><th>Customer</th><th>Status</th><th>Lines</th><th>Total</th><th>Placed</th></tr>
        </thead>
        <tbody>
          {ordersQ.data?.map((o) => (
            <tr key={o.order_id}>
              <td>
                <Link to={`/dashboard/${slug}/orders/${o.order_id}`}>
                  <code>{o.order_number}</code>
                </Link>
              </td>
              <td>{o.customer.full_name ?? `user#${o.customer.user_id ?? "—"}`}</td>
              <td><StatusBadge value={o.status} /></td>
              <td>{o.line_count}</td>
              <td>{Number(o.grand_total).toFixed(2)} {o.currency}</td>
              <td>{o.placed_at?.replace("T", " ").slice(0, 16)}</td>
            </tr>
          ))}
          {ordersQ.data?.length === 0 && (
            <tr><td colSpan={6} className="text-muted">No orders yet.</td></tr>
          )}
        </tbody>
      </table>
    </>
  );
}
