import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  // Dev server (vite) and preview server (vite preview) share the same proxy
  // so /api/* and /health always reach the FastAPI backend.
  // - In Docker compose the backend is reachable at `app:8000` (service DNS).
  // - Running locally (outside Docker) it's `localhost:8000`.
  server: {
    host: "0.0.0.0",
    port: 5173,
    proxy: {
      "/api": { target: process.env.VITE_BACKEND ?? "http://app:8000", changeOrigin: true },
      "/health": { target: process.env.VITE_BACKEND ?? "http://app:8000", changeOrigin: true },
      "/docs": { target: process.env.VITE_BACKEND ?? "http://app:8000", changeOrigin: true },
      "/openapi.json": { target: process.env.VITE_BACKEND ?? "http://app:8000", changeOrigin: true },
    },
  },
  preview: {
    host: "0.0.0.0",
    port: 5173,
    proxy: {
      "/api": { target: process.env.VITE_BACKEND ?? "http://app:8000", changeOrigin: true },
      "/health": { target: process.env.VITE_BACKEND ?? "http://app:8000", changeOrigin: true },
      "/docs": { target: process.env.VITE_BACKEND ?? "http://app:8000", changeOrigin: true },
      "/openapi.json": { target: process.env.VITE_BACKEND ?? "http://app:8000", changeOrigin: true },
    },
    allowedHosts: true,
  },
  build: {
    outDir: "dist",
    sourcemap: true,
  },
});
