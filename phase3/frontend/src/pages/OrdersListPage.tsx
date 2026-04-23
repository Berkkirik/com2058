import { useParams, Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Loading, ErrorBox } from "@/components/Loading";
import StatusBadge from "@/components/StatusBadge";
import SectionReveal from "@/components/SectionReveal";

export default function OrdersListPage() {
  const { slug = "" } = useParams();
  const merchantQ = useQuery({ queryKey: ["merchant", slug], queryFn: () => api.getMerchant(slug), enabled: !!slug });
  const ordersQ = useQuery({ queryKey: ["orders", slug], queryFn: () => api.listOrders(slug), enabled: !!slug });

  if (merchantQ.isLoading || ordersQ.isLoading) return <Loading label="Loading orders…" />;
  if (merchantQ.error) return <ErrorBox error={merchantQ.error} />;
  if (ordersQ.error) return <ErrorBox error={ordersQ.error} />;

  const m = merchantQ.data!;
  return (
    <section className="section-light py-16 md:py-24">
      <div className="max-w-[1200px] mx-auto px-6">
        <SectionReveal>
          <div className="flex items-center gap-2 text-caption text-ink/55 mb-4">
            <Link to="/" className="link-bright text-link-dark">Home</Link>
            <span>/</span>
            <Link to={`/dashboard/${slug}`} className="link-bright text-link-dark">{slug}</Link>
            <span>/</span>
            <span>orders</span>
          </div>
          <p className="text-caption uppercase tracking-[0.2em] text-accent font-semibold">Commerce</p>
          <h1 className="display-hero mt-3">Orders · {m.store_name}</h1>
          <p className="text-sub text-ink/60 mt-2">{ordersQ.data?.length ?? 0} most-recent orders.</p>
        </SectionReveal>

        <div className="mt-10 overflow-x-auto">
          <table className="data">
            <thead>
              <tr>
                <th>#</th>
                <th>Customer</th>
                <th>Status</th>
                <th>Lines</th>
                <th>Total</th>
                <th>Placed</th>
              </tr>
            </thead>
            <tbody className="stagger-child">
              {ordersQ.data?.map((o) => (
                <tr key={o.order_id}>
                  <td>
                    <Link
                      to={`/dashboard/${slug}/orders/${o.order_id}`}
                      className="text-link-dark hover:underline font-mono text-caption"
                    >
                      {o.order_number}
                    </Link>
                  </td>
                  <td>{o.customer.full_name ?? `user#${o.customer.user_id ?? "—"}`}</td>
                  <td><StatusBadge value={o.status} /></td>
                  <td>{o.line_count}</td>
                  <td className="font-semibold">{Number(o.grand_total).toFixed(2)} {o.currency}</td>
                  <td className="text-ink/55">{o.placed_at?.replace("T", " ").slice(0, 16)}</td>
                </tr>
              ))}
              {ordersQ.data?.length === 0 && (
                <tr><td colSpan={6} className="text-center py-10 text-ink/50">No orders yet.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
