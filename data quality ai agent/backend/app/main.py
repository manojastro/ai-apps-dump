import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.middleware import RequestPolicy, api_error
from app.api.routes import router
from app.config import Settings
from app.db.repository import Repository
from app.graph.persistence import checkpoint_store
from app.observability.tracing import configure_telemetry
from app.rag.retrieval import HybridKnowledge
from app.services.incidents import ConflictError, IncidentService


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        configure_telemetry(config.otel_exporter_otlp_endpoint)
        repository = Repository(config)
        await asyncio.to_thread(repository.migrate)
        knowledge = HybridKnowledge(repository, config)
        try:
            await knowledge.seed()
            async with checkpoint_store(config) as saver:
                service = IncidentService(config, repository, saver, knowledge)
                app.state.repository, app.state.service = repository, service
                try:
                    yield
                finally:
                    await service.close()
        finally:
            await knowledge.close()
            repository.close()

    app = FastAPI(title="RecoveryGraph", version="0.1.0", lifespan=lifespan)
    app.add_middleware(RequestPolicy, settings=config)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.allowed_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type", "Last-Event-ID"],
        expose_headers=["X-Correlation-ID"],
    )
    app.include_router(router)

    @app.exception_handler(KeyError)
    async def not_found(request: Request, error: KeyError):
        return api_error(request, 404, "NOT_FOUND", "Incident or collection not found")

    @app.exception_handler(ConflictError)
    async def conflict(request: Request, error: ConflictError):
        return api_error(request, 409, "CONFLICT", str(error))

    @app.exception_handler(RequestValidationError)
    async def invalid(request: Request, error: RequestValidationError):
        fields = [".".join(str(part) for part in e["loc"]) for e in error.errors()]
        return api_error(request, 422, "INVALID_INPUT", "Invalid fields: " + ", ".join(fields))

    @app.get("/health")
    async def health():
        return {"status": "ok", "service": "RecoveryGraph"}

    @app.get("/ready")
    async def ready(request: Request):
        def check_database():
            with request.app.state.repository.engine.connect() as connection:
                connection.execute(text("SELECT 1"))

        await asyncio.to_thread(check_database)
        return {"status": "ready", "provider": config.llm_provider, "production_mutations": False}

    return app


app = create_app()
