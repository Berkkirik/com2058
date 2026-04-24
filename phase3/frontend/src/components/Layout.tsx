import { Link, NavLink, Outlet, useLocation } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { useEffect, useState } from "react";
import ErrorBoundary from "@/components/ErrorBoundary";

/**
 * Apple-style layout:
 *  - Glass-nav: 48px fixed header, rgba(0,0,0,0.72) + blur(20px), floating above content
 *  - Content: full-bleed container, centered column max 980-1200px wide
 *  - Footer: minimal, light gray info strip
 *  - Route transitions: fade+subtle-up for every page
 *  - Accessibility: skip-to-content link, focus-visible rings, aria-labels,
 *    <main id="main-content"> landmark.
 */
export default function Layout() {
  const location = useLocation();
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <div className="min-h-screen flex flex-col">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-[100] focus:px-4 focus:py-2 focus:rounded-md focus:bg-black focus:text-white focus:ring-2 focus:ring-offset-2 focus:ring-accent"
      >
        Skip to content
      </a>
      <header
        className={`fixed top-0 inset-x-0 z-50 glass-nav transition-all duration-300 ease-apple ${
          scrolled ? "border-b border-white/10" : ""
        }`}
        role="banner"
      >
        <div className="max-w-[1200px] mx-auto h-12 flex items-center px-6 gap-8">
          <Link
            to="/"
            aria-label="StoreCraft home"
            className="flex items-center gap-2 no-underline focus:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-black rounded"
          >
            <span
              aria-hidden
              className="inline-block h-6 w-6 rounded-[6px] bg-gradient-to-br from-white to-white/60 flex items-center justify-center"
            >
              <svg viewBox="0 0 16 16" className="h-3 w-3 text-black" role="img" aria-label="logo">
                <path fill="currentColor" d="M8 1L1 4.5v7L8 15l7-3.5v-7L8 1zm0 1.5l5.5 2.75L8 8 2.5 5.25 8 2.5z" />
              </svg>
            </span>
            <span className="text-white font-display font-semibold text-[15px] tracking-tight">
              StoreCraft
            </span>
          </Link>
          <nav aria-label="Primary" className="hidden md:flex items-center gap-1 text-[12px]">
            <NavItem to="/">Home</NavItem>
            <NavItem to="/admin">Admin</NavItem>
            <a
              href="/docs"
              target="_blank"
              rel="noreferrer"
              aria-label="API documentation (opens in new tab)"
              className="px-3 py-1.5 text-white/90 hover:text-white transition-colors duration-200 no-underline focus:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-black rounded"
            >
              API Docs
            </a>
          </nav>
          <span className="flex-1" />
          <span className="hidden md:inline text-white/55 text-[12px] tracking-wide">
            COM2058 · Phase 3 · Berk Kırık
          </span>
        </div>
      </header>

      <main id="main-content" tabIndex={-1} className="flex-1 pt-12 focus:outline-none">
        <ErrorBoundary>
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </ErrorBoundary>
      </main>

      <footer role="contentinfo" className="section-light py-12 border-t border-black/5">
        <div className="max-w-[980px] mx-auto px-6 text-center">
          <p className="text-caption text-ink/55">
            StoreCraft · COM2058 Phase 3 · Spring 2026
          </p>
          <p className="text-caption text-ink/40 mt-2">
            MySQL&nbsp;8 · FastAPI · React 18 · TanStack Query · Tailwind CSS
          </p>
        </div>
      </footer>
    </div>
  );
}

function NavItem({ to, children }: { to: string; children: React.ReactNode }) {
  return (
    <NavLink
      to={to}
      end
      className={({ isActive }) =>
        `px-3 py-1.5 rounded-md transition-colors duration-200 no-underline focus:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-black ${
          isActive
            ? "text-white bg-white/10"
            : "text-white/90 hover:text-white hover:bg-white/5"
        }`
      }
    >
      {children}
    </NavLink>
  );
}
