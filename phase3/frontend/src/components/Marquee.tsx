import { ReactNode } from "react";

/**
 * Infinite horizontal marquee — the content is duplicated and CSS-animated for
 * seamless looping. Used as a "powered by" tech strip on the home page.
 */
export default function Marquee({
  children,
  speed = 40,
  className = "",
}: {
  children: ReactNode;
  speed?: number;
  className?: string;
}) {
  return (
    <div className={`relative overflow-hidden ${className}`}
         style={{ maskImage: "linear-gradient(90deg, transparent, black 10%, black 90%, transparent)" }}>
      <div
        className="flex gap-16 whitespace-nowrap"
        style={{ animation: `marquee ${speed}s linear infinite` }}
      >
        <div className="flex gap-16 shrink-0">{children}</div>
        <div className="flex gap-16 shrink-0" aria-hidden>{children}</div>
      </div>
      <style>{`
        @keyframes marquee {
          0% { transform: translateX(0); }
          100% { transform: translateX(-50%); }
        }
      `}</style>
    </div>
  );
}
