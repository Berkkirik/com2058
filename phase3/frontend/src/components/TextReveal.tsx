import { motion } from "framer-motion";

/**
 * Animates text reveal word-by-word with stagger. Each word lifts in from below
 * with a subtle blur + opacity fade. Matches Apple's "keynote reveal" aesthetic.
 */
export default function TextReveal({
  text,
  as: Tag = "span",
  className = "",
  delay = 0,
  stagger = 0.07,
}: {
  text: string;
  as?: keyof JSX.IntrinsicElements;
  className?: string;
  delay?: number;
  stagger?: number;
}) {
  const words = text.split(" ");
  return (
    // @ts-ignore — motion dynamic tag
    <Tag className={className}>
      {words.map((w, i) => (
        <motion.span
          key={`${w}-${i}`}
          initial={{ y: "100%", opacity: 0, filter: "blur(4px)" }}
          animate={{ y: 0, opacity: 1, filter: "blur(0px)" }}
          transition={{
            duration: 0.8,
            delay: delay + i * stagger,
            ease: [0.22, 1, 0.36, 1],
          }}
          style={{ display: "inline-block", whiteSpace: "pre" }}
        >
          {w}{i < words.length - 1 ? " " : ""}
        </motion.span>
      ))}
    </Tag>
  );
}
