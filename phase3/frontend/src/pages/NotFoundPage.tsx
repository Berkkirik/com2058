import { Link } from "react-router-dom";
import { motion } from "framer-motion";

export default function NotFoundPage() {
  return (
    <section className="section-dark min-h-[70vh] flex items-center justify-center">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
        className="text-center px-6"
      >
        <p className="text-caption uppercase tracking-[0.2em] text-link-bright font-semibold">404</p>
        <h1 className="display-hero text-white mt-3">Not found.</h1>
        <p className="text-sub text-white/70 mt-3">The URL you followed doesn't match any route.</p>
        <Link to="/" className="btn-primary mt-8">Back home</Link>
      </motion.div>
    </section>
  );
}
