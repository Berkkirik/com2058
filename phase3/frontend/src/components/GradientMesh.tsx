import { motion } from "framer-motion";

/**
 * Animated gradient mesh background for hero sections — three radial blobs
 * that drift on independent loops, creating an ambient Apple-keynote feel.
 * Zero images, pure CSS + framer-motion.
 */
export default function GradientMesh({
  variant = "dark",
}: {
  variant?: "dark" | "light";
}) {
  const colors =
    variant === "dark"
      ? ["rgba(0,113,227,0.28)", "rgba(41,151,255,0.18)", "rgba(255,255,255,0.06)"]
      : ["rgba(0,113,227,0.14)", "rgba(41,151,255,0.09)", "rgba(0,113,227,0.06)"];
  return (
    <div aria-hidden className="absolute inset-0 pointer-events-none overflow-hidden">
      <motion.div
        className="absolute h-[800px] w-[800px] rounded-full"
        style={{ background: `radial-gradient(circle, ${colors[0]}, transparent 60%)`, filter: "blur(80px)" }}
        initial={{ x: "-30%", y: "-30%" }}
        animate={{ x: ["-30%", "10%", "-20%", "-30%"], y: ["-30%", "10%", "20%", "-30%"] }}
        transition={{ duration: 22, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="absolute h-[600px] w-[600px] rounded-full"
        style={{ background: `radial-gradient(circle, ${colors[1]}, transparent 60%)`, filter: "blur(90px)", right: 0 }}
        initial={{ x: "30%", y: "10%" }}
        animate={{ x: ["30%", "0%", "20%", "30%"], y: ["10%", "40%", "5%", "10%"] }}
        transition={{ duration: 28, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="absolute bottom-0 left-1/2 h-[500px] w-[500px] rounded-full -translate-x-1/2"
        style={{ background: `radial-gradient(circle, ${colors[2]}, transparent 60%)`, filter: "blur(70px)" }}
        initial={{ y: "30%" }}
        animate={{ y: ["30%", "0%", "20%", "30%"] }}
        transition={{ duration: 18, repeat: Infinity, ease: "easeInOut" }}
      />
    </div>
  );
}
