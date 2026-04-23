import { motion, useMotionValue, useSpring } from "framer-motion";
import { useEffect, useRef } from "react";

/**
 * Spotlight cursor — a soft glowing disc that follows the mouse.
 * Only renders on devices with fine pointer (disabled on touch).
 * Placed at the top of the page so it overlays all content.
 */
export default function SpotlightCursor({
  color = "rgba(0, 113, 227, 0.12)",
  size = 520,
}: {
  color?: string;
  size?: number;
}) {
  const x = useMotionValue(-1000);
  const y = useMotionValue(-1000);
  const springX = useSpring(x, { stiffness: 90, damping: 16 });
  const springY = useSpring(y, { stiffness: 90, damping: 16 });
  const hoverRef = useRef(false);

  useEffect(() => {
    if (!window.matchMedia("(pointer: fine)").matches) return;
    const onMove = (e: MouseEvent) => {
      x.set(e.clientX - size / 2);
      y.set(e.clientY - size / 2);
    };
    window.addEventListener("mousemove", onMove);
    return () => window.removeEventListener("mousemove", onMove);
  }, [x, y, size]);

  return (
    <motion.div
      aria-hidden
      style={{
        position: "fixed",
        left: springX,
        top: springY,
        width: size,
        height: size,
        borderRadius: "50%",
        background: color,
        pointerEvents: "none",
        zIndex: 1,
        filter: "blur(40px)",
        mixBlendMode: "screen",
      }}
    />
  );
}
