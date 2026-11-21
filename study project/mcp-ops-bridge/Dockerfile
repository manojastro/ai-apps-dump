FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS base
WORKDIR /app
COPY pyproject.toml ./
RUN uv sync --group dev --no-install-project || uv sync --no-install-project
COPY src ./src
COPY scenarios ./scenarios
COPY tests ./tests
RUN uv sync --group dev
EXPOSE 8001 8002
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8001/health')"
USER nobody
CMD ["uv", "run", "uvicorn", "mock_itsm.app:app", "--host", "0.0.0.0", "--port", "8001"]
