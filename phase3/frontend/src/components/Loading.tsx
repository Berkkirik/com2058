export function Loading({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-3 py-16">
      <span className="inline-flex h-2 w-2 rounded-full bg-accent animate-pulse-glow" aria-hidden />
      <span className="text-body text-ink/60">{label}</span>
    </div>
  );
}

export function ErrorBox({ error }: { error: Error | unknown }) {
  const msg = error instanceof Error ? error.message : String(error);
  return (
    <div className="card border border-red-200 bg-red-50 text-red-800 max-w-xl mx-auto text-caption">
      <strong className="font-semibold">Error:</strong> {msg}
    </div>
  );
}

/** Skeleton rectangle block — use for placeholder UI while data loads. */
export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`shimmer rounded-[6px] ${className}`} />;
}
