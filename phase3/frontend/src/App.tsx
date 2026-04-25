import { lazy, Suspense } from "react";
import { Routes, Route } from "react-router-dom";
import Layout from "@/components/Layout";
import { Loading } from "@/components/Loading";
import { RequireAdminRoute, RequireMerchantRoute } from "@/components/RouteGuards";

// Route-level code splitting: each page becomes its own chunk, keeping the
// initial bundle (HomePage + Layout) small.
const HomePage = lazy(() => import("@/pages/HomePage"));
const StorefrontPage = lazy(() => import("@/pages/StorefrontPage"));
const ProductDetailPage = lazy(() => import("@/pages/ProductDetailPage"));
const DashboardPage = lazy(() => import("@/pages/DashboardPage"));
const OrdersListPage = lazy(() => import("@/pages/OrdersListPage"));
const OrderDetailPage = lazy(() => import("@/pages/OrderDetailPage"));
const AdminPage = lazy(() => import("@/pages/AdminPage"));
const NotFoundPage = lazy(() => import("@/pages/NotFoundPage"));

export default function App() {
  return (
    <Suspense fallback={<Loading label="Loading page…" />}>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<HomePage />} />
          <Route path="/m/:slug" element={<StorefrontPage />} />
          <Route path="/m/:slug/product/:id" element={<ProductDetailPage />} />
          <Route
            path="/dashboard/:slug"
            element={
              <RequireMerchantRoute>
                <DashboardPage />
              </RequireMerchantRoute>
            }
          />
          <Route
            path="/dashboard/:slug/orders"
            element={
              <RequireMerchantRoute>
                <OrdersListPage />
              </RequireMerchantRoute>
            }
          />
          <Route
            path="/dashboard/:slug/orders/:id"
            element={
              <RequireMerchantRoute>
                <OrderDetailPage />
              </RequireMerchantRoute>
            }
          />
          <Route
            path="/admin"
            element={
              <RequireAdminRoute>
                <AdminPage />
              </RequireAdminRoute>
            }
          />
          {/* Catch-all 404 */}
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
    </Suspense>
  );
}
