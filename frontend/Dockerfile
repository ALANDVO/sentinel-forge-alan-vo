# Sentinel Forge — Frontend Dockerfile
# Multi-stage build: Vite production build served by nginx.
FROM node:24-alpine AS builder

WORKDIR /app

COPY frontend/package*.json ./
RUN npm ci --omit=dev

COPY frontend/ ./
RUN npm run build

# --- Runtime stage ---
FROM nginx:1.27-alpine AS runtime

RUN addgroup -g 1001 -S app \
 && adduser -u 1001 -S -G app app

COPY --from=builder /app/dist /usr/share/nginx/html
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

RUN chown -R app:app /usr/share/nginx/html /var/cache/nginx /var/log/nginx /etc/nginx/conf.d

USER app

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -q --spider http://localhost/ || exit 1