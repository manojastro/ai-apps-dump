# Procurement Navigator API + worker image.
# Base: official Playwright image pinned to the same version as the Python package (1.63.0),
# which bundles a matching Chromium and its Linux runtime libraries.
# Build from the repository root:  docker build -f infra/docker/app.Dockerfile -t procnav-app .

FROM node:22-bookworm-slim AS web
WORKDIR /src/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM mcr.microsoft.com/playwright/python:v1.63.0-noble
COPY --from=ghcr.io/astral-sh/uv:0.11.20 /uv /usr/local/bin/uv
ENV UV_LINK_MODE=copy UV_COMPILE_BYTECODE=1 UV_PROJECT_ENVIRONMENT=/opt/venv \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright PYTHONUNBUFFERED=1
WORKDIR /app/backend
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY backend/ ./
RUN uv sync --frozen --no-dev
COPY fixtures/ /app/fixtures/
COPY --from=web /src/frontend/dist /app/frontend/dist
RUN mkdir -p /app/var/evidence && chown -R pwuser:pwuser /app/var
# Non-root; Chromium's sandbox stays enabled (run with the Playwright seccomp profile).
USER pwuser
ENV PATH=/opt/venv/bin:$PATH EVIDENCE_DIR=/app/var/evidence
EXPOSE 8300
HEALTHCHECK --interval=15s --timeout=5s --retries=5 CMD python -c "import urllib.request,sys; urllib.request.urlopen('http://127.0.0.1:8300/api/health', timeout=4)" || exit 1
CMD ["uvicorn", "procnav.api.app:app", "--host", "0.0.0.0", "--port", "8300", "--proxy-headers"]
