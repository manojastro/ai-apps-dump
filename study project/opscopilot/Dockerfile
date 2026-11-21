# P1 mock-first slice: no DB yet, so a single app stage is enough.
# pgvector + Langfuse arrive in later milestones; the compose file keeps a
# named volume + service slot ready for postgres.
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    PYTHONPATH=/app/src

WORKDIR /app

# Install deps first for layer caching.
COPY pyproject.toml uv.lock* ./
RUN pip install --no-cache-dir fastapi "uvicorn[standard]" pydantic pydantic-settings httpx pyyaml

COPY src/ ./src/
COPY data/ ./data/
COPY scripts/ ./scripts/

RUN useradd -m -u 10001 appuser && chown -R appuser:appuser /app
USER 10001

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["python", "-m", "uvicorn", "opscopilot.app:app", "--host", "0.0.0.0", "--port", "8000"]
