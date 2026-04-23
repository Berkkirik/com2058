import { motion, useMotionValue, useSpring, useTransform } from "framer-motion";
import { useRef, ReactNode, MouseEvent } from "react";

/**
 * 3D tilt card — rotates based on cursor position. Inspired by awwwards / getdesign.
 * The rotation is clamped and smoothed via spring physics for a tactile feel.
 */
export default function TiltCard({
  children,
  className = "",
  max = 10,
}: {
  children: ReactNode;
  className?: string;
  max?: number;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const springX = useSpring(x, { stiffness: 200, damping: 18 });
  const springY = useSpring(y, { stiffness: 200, damping: 18 });
  const rotateX = useTransform(springY, [-0.5, 0.5], [max, -max]);
  const rotateY = useTransform(springX, [-0.5, 0.5], [-max, max]);
  const glareX = useTransform(springX, [-0.5, 0.5], ["0%", "100%"]);
  const glareY = useTransform(springY, [-0.5, 0.5], ["0%", "100%"]);

  const onMove = (e: MouseEvent<HTMLDivElement>) => {
    if (!ref.current) return;
    const rect = ref.current.getBoundingClientRect();
    x.set((e.clientX - rect.left) / rect.width - 0.5);
    y.set((e.clientY - rect.top) / rect.height - 0.5);
  };

  const onLeave = () => {
    x.set(0);
    y.set(0);
  };

  return (
    <motion.div
      ref={ref}
      onMouseMove={onMove}
      onMouseLeave={onLeave}
      style={{ rotateX, rotateY, transformPerspective: 900, transformStyle: "preserve-3d" }}
      className={`relative ${className}`}
    >
      {children}
      {/* Glare */}
      <motion.div
        style={{
          background: `radial-gradient(circle 200px at ${glareX} ${glareY}, rgba(255,255,255,0.18), transparent 60%)`,
          pointerEvents: "none",
          position: "absolute",
          inset: 0,
          borderRadius: "inherit",
        }}
      />
    </motion.div>
  );
}
