import { useEffect, useRef, useState } from "react";

/** Animated number — counts from 0 to `value` over `duration` ms with Apple-ish ease. */
export default function CountUp({
  value,
  duration = 900,
  decimals = 0,
  prefix = "",
  suffix = "",
  className = "",
}: {
  value: number;
  duration?: number;
  decimals?: number;
  prefix?: string;
  suffix?: string;
  className?: string;
}) {
  const [display, setDisplay] = useState(0);
  const rafRef = useRef<number>();
  const startRef = useRef<number>();

  useEffect(() => {
    const safe = Number.isFinite(value) ? value : 0;
    startRef.current = undefined;
    const step = (t: number) => {
      if (!startRef.current) startRef.current = t;
      const progress = Math.min(1, (t - startRef.current!) / duration);
      // easeOutCubic (close to Apple's curve)
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(safe * eased);
      if (progress < 1) {
        rafRef.current = requestAnimationFrame(step);
      } else {
        setDisplay(safe);
      }
    };
    rafRef.current = requestAnimationFrame(step);
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [value, duration]);

  const formatted = display.toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });

  return <span className={className}>{prefix}{formatted}{suffix}</span>;
}
