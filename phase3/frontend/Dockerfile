# Single-stage: Node.js builds and serves the SPA via Vite's preview server.
# - `npm run build` emits production bundle to dist/
# - `vite preview` serves dist/ over HTTP on :5173 with SPA fallback built in
# - The Vite config's `server.proxy` forwards /api/* to the FastAPI backend
#
# This replaces the previous nginx stage — one fewer image, simpler mental model.

FROM node:20-alpine
WORKDIR /app

# Install deps first (layer caching)
COPY package.json ./
RUN npm install

# Copy source + build
COPY tsconfig.json vite.config.ts tailwind.config.js postcss.config.js index.html ./
COPY src ./src
ENV VITE_API_BASE=""
RUN npm run build

EXPOSE 5173
HEALTHCHECK --interval=10s --timeout=3s --start-period=15s --retries=5 \
  CMD wget -q --spider http://localhost:5173/ || exit 1

# `vite preview` serves the built dist/ with SPA fallback and uses the proxy
# defined in vite.config.ts — no nginx, no separate runtime stage needed.
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "5173"]
