import { Routes, Route } from "react-router-dom";
import Layout from "@/components/Layout";
import HomePage from "@/pages/HomePage";
import StorefrontPage from "@/pages/StorefrontPage";
import ProductDetailPage from "@/pages/ProductDetailPage";
import DashboardPage from "@/pages/DashboardPage";
import OrdersListPage from "@/pages/OrdersListPage";
import OrderDetailPage from "@/pages/OrderDetailPage";
import AdminPage from "@/pages/AdminPage";
import NotFoundPage from "@/pages/NotFoundPage";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/m/:slug" element={<StorefrontPage />} />
        <Route path="/m/:slug/product/:id" element={<ProductDetailPage />} />
        <Route path="/dashboard/:slug" element={<DashboardPage />} />
        <Route path="/dashboard/:slug/orders" element={<OrdersListPage />} />
        <Route path="/dashboard/:slug/orders/:id" element={<OrderDetailPage />} />
        <Route path="/admin" element={<AdminPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
