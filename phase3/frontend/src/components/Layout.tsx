import { Link, Outlet } from "react-router-dom";

export default function Layout() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-ink text-white border-b-4 border-accent-light">
        <div className="max-w-6xl mx-auto flex items-center gap-4 px-6 py-4">
          <Link to="/" className="font-bold text-lg tracking-wide text-white no-underline">
            StoreCraft
          </Link>
          <nav className="flex gap-4 text-sm text-stone-300">
            <Link to="/" className="hover:text-white no-underline">Home</Link>
            <Link to="/admin" className="hover:text-white no-underline">Admin</Link>
            <a href="/docs" target="_blank" rel="noreferrer" className="hover:text-white no-underline">API Docs</a>
          </nav>
          <span className="flex-1" />
          <span className="text-stone-400 text-xs">COM2058 · Phase 3 · Berk Kırık</span>
        </div>
      </header>
      <main className="flex-1 max-w-6xl w-full mx-auto px-6 py-8">
        <Outlet />
      </main>
      <footer className="text-center text-xs text-muted py-8">
        StoreCraft — MySQL 8 + FastAPI + React + TanStack Query
      </footer>
    </div>
  );
}
