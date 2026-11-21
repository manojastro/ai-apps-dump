"""Routing table lookup with safe default."""

from pathlib import Path
from typing import Any

import yaml

from ticketsort.domain.models import Category, Service

_DEFAULT_GROUP = "SD-L1"
_ROUTING_CACHE: dict[str, Any] | None = None


def _default_table_path() -> Path:
    # Works both from repo root and any cwd: <repo>/config/routing.yaml
    here = Path(__file__).resolve()
    repo_root = here.parents[3]  # domain -> ticketsort -> src -> repo
    return repo_root / "config" / "routing.yaml"


def _load_table(path: Path | None = None) -> dict[str, Any]:
    global _ROUTING_CACHE
    if _ROUTING_CACHE is not None:
        return _ROUTING_CACHE
    table_path = path or _default_table_path()
    if not table_path.exists():
        fallback = Path("config/routing.yaml")
        table_path = fallback if fallback.exists() else table_path
    _ROUTING_CACHE = yaml.safe_load(table_path.read_text()) or {}
    return _ROUTING_CACHE


def route(category: Category, service: Service, path: Path | None = None) -> str:
    """Return assignment group for (category, service).

    Lookup order: "category:service" -> "category:*" -> "default".
    Never raise for unknown combos — return "SD-L1".
    """
    table = _load_table(path)
    rules: dict[str, str] = table.get("rules", {})
    default: str = str(table.get("default", _DEFAULT_GROUP))
    exact = rules.get(f"{category.value}:{service.value}")
    if exact:
        return exact
    wildcard = rules.get(f"{category.value}:*")
    if wildcard:
        return wildcard
    return default
