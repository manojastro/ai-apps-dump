# syntax=docker/dockerfile:1.7
# Multi-stage image. Targets: api (FastAPI), worker (registry poller), ui (Streamlit).
# Status: written, NOT built on the build machine (Docker was not installed there).

ARG PYTHON_VERSION=3.12

FROM python:${PYTHON_VERSION}-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.11.20 /uv /usr/local/bin/uv
ENV UV_LINK_MODE=copy UV_COMPILE_BYTECODE=1 UV_PYTHON_DOWNLOADS=never
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project --extra postgres --extra llm --extra ui
COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --extra postgres --extra llm --extra ui

FROM python:${PYTHON_VERSION}-slim AS runtime
# git: open_pr creates local branches/commits; no compilers or shells beyond the base image.
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 schemaguard
WORKDIR /app
COPY --from=builder --chown=schemaguard:schemaguard /app /app
COPY --chown=schemaguard:schemaguard demo_pipeline ./demo_pipeline
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    SCHEMAGUARD_HOME=/data \
    SCHEMAGUARD_PIPELINE_DIR=/app/demo_pipeline
RUN mkdir -p /data && chown schemaguard:schemaguard /data
USER schemaguard

FROM runtime AS api
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health').status==200 else 1)"
CMD ["uvicorn", "schemaguard.api.app:app", "--host", "0.0.0.0", "--port", "8000"]

FROM runtime AS worker
CMD ["schemaguard", "worker"]

FROM runtime AS ui
EXPOSE 8501
ENV SCHEMAGUARD_API_URL=http://localhost:8000
CMD ["python", "-m", "streamlit", "run", "src/schemaguard/ui/app.py", "--server.port", "8501", "--server.address", "0.0.0.0", "--server.headless", "true", "--browser.gatherUsageStats", "false"]
