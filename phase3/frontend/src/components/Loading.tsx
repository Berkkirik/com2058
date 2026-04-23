export function Loading({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex items-center gap-2 text-muted py-6">
      <span className="inline-block h-3 w-3 rounded-full bg-accent animate-pulse" />
      {label}
    </div>
  );
}

export function ErrorBox({ error }: { error: Error | unknown }) {
  const msg = error instanceof Error ? error.message : String(error);
  return (
    <div className="card border-danger bg-rose-50 text-danger">
      <strong>Error:</strong> {msg}
    </div>
  );
}
