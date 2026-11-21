"""FastAPI dependencies: settings injection."""

from functools import lru_cache

from ticketsort.config import Settings, get_settings


@lru_cache
def cached_settings() -> Settings:
    return get_settings()


def get_app_settings() -> Settings:
    return cached_settings()
