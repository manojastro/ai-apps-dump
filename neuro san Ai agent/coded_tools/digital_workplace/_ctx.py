"""Shared context for coded tools (M7): deterministic mock-first bundles.

Observe/diagnose tools ALWAYS use use_mock=True so ambient env (e.g. a
future real .env with ServiceNow creds) can never make diagnostics
non-deterministic or network-dependent. Live ITSM is only wired through
the ServiceNow coordinator path (M18), never through observation.
"""

from __future__ import annotations

from typing import Any

from common.config import load_settings
from integrations.factory import build_providers
from integrations.ports import Providers

_BUNDLES: dict[int, Providers] = {}


def get_bundle(seed: int = 42) -> Providers:
    """One cached Providers bundle per seed (shared estate)."""
    try:
        seed = int(seed)
    except (TypeError, ValueError):
        seed = 42
    if seed not in _BUNDLES:
        settings = load_settings(env_file=".env")
        _BUNDLES[seed] = build_providers(settings, use_mock=True, seed=seed)
    return _BUNDLES[seed]


def resolve_ids(args: dict[str, Any], sly_data: dict[str, Any],
                need: tuple[str, ...] = ("device_id",)) -> dict[str, str]:
    """Pull aliased ids from args → sly_data → demo defaults."""
    defaults = {"device_id": "DEVICE_001", "user_id": "USER_001", "case_id": ""}
    resolved: dict[str, str] = {}
    for key in ("device_id", "user_id", "case_id", "seed"):
        value = args.get(key, sly_data.get(key, defaults.get(key, "")))
        resolved[key] = str(value)
    missing = [k for k in need if not resolved.get(k)]
    if missing:
        raise ValueError(f"missing required ids: {missing}")
    return resolved
