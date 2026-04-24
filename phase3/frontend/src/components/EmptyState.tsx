import type { ReactNode } from "react";

interface Props {
  title: string;
  description?: ReactNode;
  action?: ReactNode;
}

export function EmptyState({ title, description, action }: Props) {
  return (
    <div
      role="status"
      aria-live="polite"
      className="text-center py-12 px-6 max-w-md mx-auto"
    >
      <p className="font-display text-sub text-ink mb-1">{title}</p>
      {description ? <p className="text-caption text-ink/60">{description}</p> : null}
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  );
}

export default EmptyState;
