import { Navigate, useLocation, useParams } from "react-router-dom";
import type { ReactNode } from "react";

/**
 * Route guard: `/dashboard/:slug/*` requires a merchant slug in the URL AND a
 * session token in localStorage (demo: any non-empty `sc_session` value).
 * Redirects to the storefront (or home if no slug) when not authorized.
 *
 * NOTE: this is a demo-grade guard. A production build would verify the
 * session via the backend, not trust localStorage.
 */
export function RequireMerchantRoute({ children }: { children: ReactNode }): JSX.Element {
  const { slug } = useParams();
  const location = useLocation();
  if (!slug) {
    return <Navigate to="/" replace />;
  }
  const hasSession =
    typeof window !== "undefined" && window.localStorage.getItem("sc_session");
  if (!hasSession) {
    return <Navigate to={`/m/${slug}`} replace state={{ from: location.pathname }} />;
  }
  return <>{children}</>;
}

/**
 * Route guard: `/admin` requires `sc_admin` truthy in localStorage. Redirects
 * to home otherwise.
 */
export function RequireAdminRoute({ children }: { children: ReactNode }): JSX.Element {
  const location = useLocation();
  const isAdmin =
    typeof window !== "undefined" && window.localStorage.getItem("sc_admin") === "1";
  if (!isAdmin) {
    return <Navigate to="/" replace state={{ from: location.pathname }} />;
  }
  return <>{children}</>;
}
