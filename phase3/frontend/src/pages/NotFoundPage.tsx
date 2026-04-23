import { Link } from "react-router-dom";

export default function NotFoundPage() {
  return (
    <div className="text-center py-20">
      <h1>404 — Not Found</h1>
      <p className="text-muted">The page you requested doesn't exist.</p>
      <p className="mt-4"><Link to="/">← Home</Link></p>
    </div>
  );
}
