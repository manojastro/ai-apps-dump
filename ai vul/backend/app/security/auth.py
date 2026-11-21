"""Session tokens and FastAPI authentication/authorization dependencies.

Sessions are short-lived HS256 JWTs delivered in an ``HttpOnly`` + ``SameSite=Lax`` cookie.
Because the browser talks to the API through the Next.js same-origin proxy, the cookie is
first-party. State-changing requests authenticated by cookie must also carry the
``X-Requested-With: aegis`` header, which cross-site forms cannot set without a CORS
preflight (CSRF defence in depth). A bearer token is accepted for API clients and tests.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import timedelta

import jwt
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.core.types import new_id, utcnow
from app.models.identity import User
from app.security.permissions import Permission, has_permission, permissions_for

COOKIE_NAME = "aegis_session"
CSRF_HEADER = "x-requested-with"
CSRF_VALUE = "aegis"
ALGORITHM = "HS256"
UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


@dataclass(frozen=True)
class Principal:
    id: str
    email: str
    full_name: str
    role: str
    permissions: list[str] = field(default_factory=list)

    @property
    def label(self) -> str:
        return f"{self.full_name} <{self.email}>"

    def can(self, permission: Permission) -> bool:
        return has_permission(self.role, permission)

    @classmethod
    def from_user(cls, user: User) -> Principal:
        return cls(user.id, user.email, user.full_name, user.role, permissions_for(user.role))


SYSTEM_PRINCIPAL = Principal("system", "system@aegis.local", "AegisRemediate System", "system", [])


def create_session_token(user: User) -> str:
    settings = get_settings()
    now = utcnow()
    claims = {
        "sub": user.id,
        "role": user.role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.session_ttl_minutes)).timestamp()),
        "jti": new_id(),
        "iss": "aegisremediate",
    }
    return jwt.encode(claims, settings.secret_key.get_secret_value(), algorithm=ALGORITHM)


def decode_session_token(token: str) -> dict:
    settings = get_settings()
    return jwt.decode(
        token,
        settings.secret_key.get_secret_value(),
        algorithms=[ALGORITHM],
        issuer="aegisremediate",
        options={"require": ["exp", "sub", "iat"]},
    )


def _extract_token(request: Request) -> tuple[str | None, str]:
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip(), "bearer"
    return request.cookies.get(COOKIE_NAME), "cookie"


def get_current_user(request: Request, db: Session = Depends(get_db)) -> Principal:
    token, transport = _extract_token(request)
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authentication required")
    try:
        claims = decode_session_token(token)
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expired") from None
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid session") from None
    csrf_ok = request.headers.get(CSRF_HEADER, "").lower() == CSRF_VALUE
    if transport == "cookie" and request.method in UNSAFE_METHODS and not csrf_ok:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Missing CSRF header")
    user = db.get(User, claims["sub"])
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Account disabled or not found")
    principal = Principal.from_user(user)
    request.state.principal = principal
    return principal


def require(permission: Permission) -> Callable[..., Principal]:
    """Dependency factory: ``Depends(require(Permission.APPROVAL_DECIDE))``."""

    def _dep(request: Request, principal: Principal = Depends(get_current_user), db: Session = Depends(get_db)) -> Principal:
        if not principal.can(permission):
            from app.services.audit import record_audit  # local import avoids a cycle

            record_audit(
                db,
                actor=principal,
                action="permission_denied",
                target_type="endpoint",
                target_id=request.url.path[:64],
                details={"method": request.method, "permission": permission.value, "role": principal.role},
                outcome="denied",
                ip_address=request.client.host if request.client else None,
            )
            db.commit()
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"Role '{principal.role}' lacks permission '{permission.value}'")
        return principal

    return _dep
