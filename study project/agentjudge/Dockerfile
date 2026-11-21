FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN useradd -m appuser
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
COPY pyproject.toml .python-version eval_config.yaml ./
COPY src ./src
COPY golden_set.jsonl ./
COPY labels ./labels
COPY reports/baseline.json ./reports/baseline.json
RUN uv sync --frozen --no-dev
USER appuser
HEALTHCHECK --interval=30s --timeout=5s CMD uv run agentjudge --help || exit 1
ENTRYPOINT ["uv", "run", "agentjudge"]
