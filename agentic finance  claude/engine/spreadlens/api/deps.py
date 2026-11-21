"""API helpers: Decimal-safe JSON responses and tenant-scoped loading."""

from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any, TypeVar

from fastapi import HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from spreadlens.security.auth import Principal, require_member

T = TypeVar("T")


def _default(o: Any) -> Any:
    if isinstance(o, Decimal):
        return format(o, "f")  # decimals cross the API as strings, never floats
    if isinstance(o, (datetime, date)):
        return o.isoformat()
    if isinstance(o, set):
        return sorted(o)
    raise TypeError(f"not serialisable: {type(o).__name__}")


class J(Response):
    media_type = "application/json"

    def __init__(self, content: Any, status_code: int = 200, headers: dict | None = None) -> None:
        super().__init__(json.dumps(content, default=_default, ensure_ascii=False), status_code=status_code, headers=headers)


def scoped(db: Session, model: type[T], obj_id: str, principal: Principal, min_role: str = "analyst", action: str = "access") -> tuple[T, str]:
    obj = db.get(model, obj_id)
    if obj is None:
        raise HTTPException(404, "Not found")
    role = require_member(db, principal, obj.workspace_id, min_role, action)  # type: ignore[attr-defined]
    return obj, role


def row(o: Any, fields: list[str]) -> dict:
    return {f: getattr(o, f) for f in fields}
