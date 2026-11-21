FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir fastapi uvicorn pydantic sqlalchemy httpx scikit-learn pandas numpy scipy joblib pytest

COPY backend ./backend
COPY simulator ./simulator
COPY scripts ./scripts
COPY frontend ./frontend
COPY tests ./tests

ENV PYTHONPATH=/app
EXPOSE 8613

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8613"]
