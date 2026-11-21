FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /srv
COPY pyproject.toml ./
RUN pip install --no-cache-dir fastapi uvicorn "pydantic>=2" "sqlalchemy>=2" pyyaml anthropic \
    opentelemetry-sdk opentelemetry-exporter-otlp-proto-http jinja2 python-multipart itsdangerous python-dotenv httpx
COPY app ./app
COPY scripts ./scripts
COPY evals ./evals
RUN useradd -m eir && mkdir -p /data && chown eir /data
USER eir
ENV EIR_DB_URL=sqlite:////data/eir.db EIR_LLM_MODE=MOCK
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
