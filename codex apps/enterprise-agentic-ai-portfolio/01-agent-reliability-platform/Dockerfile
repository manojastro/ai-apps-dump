FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATABASE_PATH=/app/data/reliability.db \
    LLM_MODE=mock

WORKDIR /app
COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.txt && \
    addgroup --system app && adduser --system --ingroup app app
COPY backend ./backend
RUN mkdir -p /app/data && chown -R app:app /app
USER app
EXPOSE 8101
HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8101/ready', timeout=2)"
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8101"]
