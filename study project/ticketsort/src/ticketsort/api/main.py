"""App factory."""

from fastapi import FastAPI

from ticketsort.api.errors import unhandled_exception_handler
from ticketsort.api.routes import router
from ticketsort.config import Settings
from ticketsort.logging import RequestIdMiddleware, setup_logging


def create_app(settings: Settings | None = None) -> FastAPI:
    from ticketsort.api.deps import get_app_settings
    from ticketsort.config import get_settings

    active = settings or get_settings()
    setup_logging(active.log_level)

    app = FastAPI(title="TicketSort", version="0.1.0")
    app.add_middleware(RequestIdMiddleware)
    app.add_exception_handler(Exception, unhandled_exception_handler)
    app.include_router(router)
    if settings is not None:
        app.dependency_overrides[get_app_settings] = lambda: active
    return app


app = create_app()
