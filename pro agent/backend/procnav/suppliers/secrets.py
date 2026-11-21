"""Supplier credential resolution by reference. Secrets never enter the database, prompts, or logs."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from ..core.config import REPO_ROOT, get_settings


@dataclass(frozen=True)
class SupplierCredential:
    username: str
    password: str

    def __repr__(self) -> str:  # never print the password
        return f"SupplierCredential(username={self.username!r}, password='***')"


def _fixture_defaults() -> dict[str, SupplierCredential]:
    catalog = json.loads((Path(REPO_ROOT) / "fixtures" / "catalog.json").read_text(encoding="utf-8"))
    out = {}
    for tenant, spec in catalog["accounts"].items():
        for supplier in catalog["suppliers"]:
            out[f"supplier/{tenant}/{supplier}"] = SupplierCredential(spec["username"], spec["default_password"])
    return out


def resolve(credential_ref: str) -> SupplierCredential:
    settings = get_settings()
    configured = settings.supplier_credentials()
    if credential_ref in configured:
        c = configured[credential_ref]
        return SupplierCredential(c["username"], c["password"])
    if settings.app_env != "production":
        defaults = _fixture_defaults()
        if credential_ref in defaults:
            return defaults[credential_ref]
    raise KeyError(f"credential reference not configured: {credential_ref}")
