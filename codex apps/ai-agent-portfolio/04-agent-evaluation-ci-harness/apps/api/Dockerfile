FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY apps/api ./apps/api
COPY config ./config
RUN pip install --no-cache-dir .
EXPOSE 8004
CMD ["uvicorn", "evalharness.api:app", "--host", "0.0.0.0", "--port", "8004"]

