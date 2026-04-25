import { ApiError } from "@/lib/api";

export function Loading({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-3 py-16" role="status" aria-live="polite">
      <span className="inline-flex h-2 w-2 rounded-full bg-accent animate-pulse-glow" aria-hidden />
      <span className="text-body text-ink/60">{label}</span>
    </div>
  );
}

export function ErrorBox({ error }: { error: Error | unknown }) {
  const isApi = error instanceof ApiError;
  const msg = error instanceof Error ? error.message : String(error);
  const code = isApi ? error.code : null;
  const requestId = isApi ? error.requestId : null;
  return (
    <div
      role="alert"
      className="card border border-red-200 bg-red-50 text-red-800 max-w-xl mx-auto text-caption"
    >
      <strong className="font-semibold">Error{code ? ` · ${code}` : ""}:</strong> {msg}
      {isApi && error.isValidation && error.details.length > 0 ? (
        <ul className="mt-2 list-disc pl-5 text-red-900/80 text-[11px]">
          {error.details.map((d, i) => (
            <li key={i}>
              {(d.loc ?? []).join(".")}: {d.msg}
            </li>
          ))}
        </ul>
      ) : null}
      {requestId ? (
        <p className="mt-2 text-[10px] text-red-900/50">request-id: {requestId}</p>
      ) : null}
    </div>
  );
}

/** Skeleton rectangle block — use for placeholder UI while data loads. */
export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`shimmer rounded-[6px] ${className}`} aria-hidden />;
}
