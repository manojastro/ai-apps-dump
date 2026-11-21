from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

POLICY_PATH = Path(__file__).with_name("policy.yaml")


@lru_cache(maxsize=1)
def load_policy() -> dict:
    return yaml.safe_load(POLICY_PATH.read_text())


def reload_policy() -> None:
    load_policy.cache_clear()


def roles() -> list[str]:
    return list(load_policy()["roles"])


def allowed_tools(role: str) -> list[str]:
    return list(load_policy()["roles"].get(role, []))


def is_allowed(role: str, tool: str) -> bool:
    return tool in load_policy()["roles"].get(role, [])


def field_limit(tool: str, role: str) -> list[str] | None:
    return (load_policy().get("field_limits", {}).get(tool, {}) or {}).get(role)


def filter_fields(tool: str, role: str, data):
    """Apply the role's field limit to a tool result (a record dict, or {"items": [records]})."""
    allowed = field_limit(tool, role)
    if allowed is None:
        return data

    def keep(rec):
        return {k: v for k, v in rec.items() if k in allowed}

    if isinstance(data, dict) and isinstance(data.get("items"), list):
        return {**data, "items": [keep(r) for r in data["items"]]}
    return keep(data) if isinstance(data, dict) else data
