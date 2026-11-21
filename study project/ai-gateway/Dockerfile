FROM ghcr.io/astral-sh/uv:python AS builder
WORKDIR /app
COPY pyproject.toml ./
RUN uv sync --group dev --no-install-project

FROM python:3.12-slim
WORKDIR /app
RUN useradd -m appuser && mkdir -p data reports && chown appuser data reports
COPY --from=builder /app/.venv /app/.venv
COPY src ./src
COPY config ./config
COPY pyproject.toml ./
ENV PATH="/app/.venv/bin:$PATH" PYTHONPATH="/app/src"
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
CMD ["uvicorn", "gateway.app:app", "--host", "0.0.0.0", "--port", "8000"]
