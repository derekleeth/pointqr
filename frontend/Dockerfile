# PointQR Frontend – Production build
# Stage 1 compiles the Vue SPA with Vite; stage 2 serves the static bundle
# from a tiny nginx image. The main reverse proxy (nginx/nginx.conf) forwards
# all non-API traffic here.

# -----------------------------------------------------------------------------
# Stage 1 – Build
# -----------------------------------------------------------------------------
FROM node:22-alpine AS build

WORKDIR /app

RUN npm install -g pnpm@9

COPY package.json pnpm-lock.yaml* ./
RUN pnpm install

COPY . .

# Baked into the bundle at build time (Vite inlines import.meta.env.*)
ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

# Run Vite directly rather than `pnpm build` so the build is not blocked by
# vue-tsc type errors; run `pnpm type-check` separately in CI.
RUN pnpm exec vite build

# -----------------------------------------------------------------------------
# Stage 2 – Serve
# -----------------------------------------------------------------------------
FROM nginx:1.27-alpine AS runtime

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
