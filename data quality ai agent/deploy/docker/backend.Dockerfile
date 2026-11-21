FROM python:3.12-slim AS build
COPY --from=ghcr.io/astral-sh/uv:0.11.20 /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
COPY pyproject.toml uv.lock ./
COPY backend ./backend
COPY simulator ./simulator
COPY evals ./evals
RUN uv sync --frozen --no-dev

FROM python:3.12-slim AS runtime
RUN groupadd --gid 10001 recoverygraph && useradd --uid 10001 --gid recoverygraph --create-home recoverygraph
WORKDIR /app
COPY --from=build --chown=recoverygraph:recoverygraph /app /app
COPY --chown=recoverygraph:recoverygraph alembic.ini ./
COPY --chown=recoverygraph:recoverygraph scripts ./scripts
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
RUN mkdir -p /app/.runtime && chown recoverygraph:recoverygraph /app/.runtime
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=5s --start-period=30s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
