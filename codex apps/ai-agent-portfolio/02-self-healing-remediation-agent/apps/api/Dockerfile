FROM python:3.13-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY apps ./apps
COPY services ./services
COPY config ./config
COPY migrations ./migrations
RUN pip install --no-cache-dir .
ENV PYTHONUNBUFFERED=1
EXPOSE 8002
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]

