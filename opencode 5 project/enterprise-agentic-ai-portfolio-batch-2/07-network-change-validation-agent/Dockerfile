FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY pyproject.toml ./
COPY backend ./backend
COPY simulator ./simulator
COPY frontend ./frontend
COPY scripts ./scripts
COPY tests ./tests

RUN pip install --no-cache-dir fastapi "uvicorn[standard]" "pydantic>=2" \
    "sqlalchemy>=2" httpx pytest && \
    mkdir -p data

ENV PYTHONPATH="/app/backend:/app"

EXPOSE 8612

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8612"]
