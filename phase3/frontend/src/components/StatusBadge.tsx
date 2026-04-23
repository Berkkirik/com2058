const MAP: Record<string, string> = {
  paid: "badge-ok",
  fulfilled: "badge-ok",
  captured: "badge-ok",
  delivered: "badge-ok",
  active: "badge-ok",
  pending: "badge-warn",
  preparing: "badge-warn",
  in_transit: "badge-warn",
  draft: "badge-warn",
  canceled: "badge-danger",
  refunded: "badge-danger",
  failed: "badge-danger",
  archived: "badge-danger",
};

export default function StatusBadge({ value }: { value: string }) {
  const extra = MAP[value] ?? "badge-info";
  return <span className={`badge ${extra}`}>{value}</span>;
}
