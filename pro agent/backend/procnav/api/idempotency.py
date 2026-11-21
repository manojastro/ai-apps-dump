"""Idempotency-Key handling for mutating endpoints.

A replay with the same key and body returns the stored response; the same key with a different
body is rejected with IDEMPOTENCY_CONFLICT.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth.service import Principal
from ..core.models import IdempotencyKey
from .errors import ApiError


def body_hash(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()


def key_from(request: Request) -> str | None:
    key = request.headers.get("idempotency-key")
    if key is not None and not (8 <= len(key) <= 200):
        raise ApiError(422, "VALIDATION_FAILED", "Idempotency-Key must be 8-200 characters")
    return key


def lookup(db: Session, principal: Principal, endpoint: str, key: str | None, payload: Any) -> dict | None:
    if not key:
        return None
    row = db.scalar(
        select(IdempotencyKey).where(
            IdempotencyKey.user_id == principal.user_id, IdempotencyKey.endpoint == endpoint, IdempotencyKey.key == key
        )
    )
    if row is None:
        return None
    if row.request_hash != body_hash(payload):
        raise ApiError(409, "IDEMPOTENCY_CONFLICT", "Idempotency-Key reused with a different request body")
    return {"status": row.status_code, "body": row.response}


def store(
    db: Session, principal: Principal, endpoint: str, key: str | None, payload: Any, status: int, response: dict
) -> None:
    if not key:
        return
    db.add(
        IdempotencyKey(
            tenant_id=principal.tenant_id,
            user_id=principal.user_id,
            endpoint=endpoint,
            key=key,
            request_hash=body_hash(payload),
            status_code=status,
            response=response,
        )
    )
