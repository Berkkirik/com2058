import { motion } from "framer-motion";
import { ReactNode } from "react";

/** Wraps content in a fade-up-on-scroll container using framer-motion's whileInView. */
export default function SectionReveal({
  children,
  delay = 0,
  className = "",
  as = "div",
}: {
  children: ReactNode;
  delay?: number;
  className?: string;
  as?: "div" | "section" | "article";
}) {
  const MotionTag = as === "section" ? motion.section : as === "article" ? motion.article : motion.div;
  return (
    <MotionTag
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-10% 0px -10% 0px" }}
      transition={{ duration: 0.65, delay, ease: [0.22, 1, 0.36, 1] }}
      className={className}
    >
      {children}
    </MotionTag>
  );
}
