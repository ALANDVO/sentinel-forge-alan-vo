# Sentinel Forge — Backend Dockerfile
# Multi-stage build with nonroot user, healthcheck.
FROM python:3.12-slim AS base

RUN addgroup --system app \
 && adduser --system --ingroup app app

WORKDIR /app

# --- Dependencies stage ---
FROM base AS dependencies

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Runtime stage ---
FROM base AS runtime

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

COPY --from=dependencies /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin
COPY backend/ /app/backend

RUN mkdir -p /data && chown -R app:app /data /app

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" || exit 1

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]