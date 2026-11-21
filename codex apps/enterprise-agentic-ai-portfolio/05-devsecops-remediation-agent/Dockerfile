FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATABASE_PATH=/app/data/security.db \
    WORKSPACE_ROOT=/app/data/workspaces \
    LLM_MODE=mock

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend ./backend
COPY frontend ./frontend
RUN mkdir -p /app/data/workspaces && chown -R 10001:10001 /app
USER 10001
EXPOSE 8105
HEALTHCHECK --interval=20s --timeout=3s --start-period=5s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8105/ready', timeout=2)"
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8105", "--no-server-header"]
