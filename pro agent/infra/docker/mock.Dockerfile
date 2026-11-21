# Synthetic supplier portals + private fixture control API.
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.11.20 /uv /usr/local/bin/uv
ENV UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/opt/venv PYTHONUNBUFFERED=1
WORKDIR /app/mock_portals
COPY mock_portals/pyproject.toml mock_portals/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY mock_portals/ ./
RUN uv sync --frozen --no-dev
COPY fixtures/ /app/fixtures/
RUN useradd --create-home --uid 10001 portals
USER portals
ENV PATH=/opt/venv/bin:$PATH FIXTURES_DIR=/app/fixtures MOCK_HOST=0.0.0.0 CONTROL_HOST=0.0.0.0
EXPOSE 8301 8302 8303 8309
HEALTHCHECK --interval=10s --timeout=3s --retries=10 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8309/healthz', timeout=2)" || exit 1
CMD ["python", "-m", "mockportals.main"]
