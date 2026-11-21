FROM python:3.11.15-slim
COPY --from=ghcr.io/astral-sh/uv:0.11.20 /uv /usr/local/bin/uv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY services ./services
COPY packages ./packages
COPY demo ./demo
COPY infra/migrations ./infra/migrations
COPY alembic.ini ./
RUN useradd --uid 10001 --create-home lens && mkdir -p /app/.productionlens && chown -R lens:lens /app
USER lens
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1
CMD ["uvicorn", "services.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-keep-alive", "65"]
