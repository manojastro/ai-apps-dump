FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY apps/api ./apps/api
COPY examples ./examples
RUN pip install --no-cache-dir .
EXPOSE 8104
CMD ["uvicorn", "examples.demo_agent.app:app", "--host", "0.0.0.0", "--port", "8104"]

