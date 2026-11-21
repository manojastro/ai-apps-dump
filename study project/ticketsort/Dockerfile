# syntax=docker/dockerfile:1
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder
WORKDIR /app
COPY pyproject.toml uv.lock* ./
COPY src ./src
COPY README.md ./
RUN uv sync --frozen --no-dev --no-install-project && uv sync --frozen --no-dev

FROM python:3.12-slim-bookworm AS runtime
WORKDIR /app
RUN useradd -m -u 10001 appuser
COPY --from=builder /app/.venv /app/.venv
COPY src ./src
COPY config ./config
ENV PATH="/app/.venv/bin:$PATH" PYTHONPATH="/app/src" LLM_PROVIDER="mock"
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
CMD ["uvicorn", "ticketsort.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
