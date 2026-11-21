"""Server-side authentication and workspace authorization.

Every request resolves a Principal from the bearer token (the Next.js BFF forwards it from an
httpOnly cookie). Every workspace-scoped query goes through `require_member`, which checks the
membership and role on the server. Records in other workspaces are reported as 404 so their
existence is not revealed; the denial is written to the audit log.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from spreadlens.config import get_settings
from spreadlens.db import get_db
from spreadlens.models import AuthSession, Membership, User, utcnow
from spreadlens.observability import correlation_id
from spreadlens.security.passwords import new_token, token_hash, verify_password
from spreadlens.services.audit import audit

ROLE_RANK = {"analyst": 1, "reviewer": 2, "admin": 3}


@dataclass
class Principal:
    user: User
    memberships: dict[str, str]  # workspace_id -> role

    @property
    def id(self) -> str:
        return self.user.id

    def role_in(self, workspace_id: str) -> str | None:
        return self.memberships.get(workspace_id)


def login(db: Session, email: str, password: str) -> tuple[str, User] | None:
    user = db.scalar(select(User).where(User.email == email.lower().strip()))
    if user is None or not user.is_active or not verify_password(password, user.password_hash):
        audit(db, None, None, "auth.login", outcome="denied", details={"email_domain": email.split("@")[-1][:60]})
        return None
    token = new_token()
    db.add(AuthSession(user_id=user.id, token_hash=token_hash(token),
                       expires_at=utcnow() + timedelta(hours=get_settings().session_ttl_hours)))
    audit(db, None, user.id, "auth.login")
    return token, user


def logout(db: Session, token: str) -> None:
    s = db.scalar(select(AuthSession).where(AuthSession.token_hash == token_hash(token)))
    if s:
        db.delete(s)


def get_principal(request: Request, db: Session = Depends(get_db), authorization: str | None = Header(default=None)) -> Principal:
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
    if not token:
        token = request.cookies.get("sl_session")
    if not token:
        raise HTTPException(401, "Not authenticated")
    s = db.scalar(select(AuthSession).where(AuthSession.token_hash == token_hash(token)))
    if s is None or s.expires_at < utcnow():
        raise HTTPException(401, "Session expired")
    user = db.get(User, s.user_id)
    if user is None or not user.is_active:
        raise HTTPException(401, "Not authenticated")
    ms = {m.workspace_id: m.role for m in db.scalars(select(Membership).where(Membership.user_id == user.id))}
    return Principal(user=user, memberships=ms)


def require_member(db: Session, principal: Principal, workspace_id: str, min_role: str = "analyst",
                   action: str = "access") -> str:
    role = principal.role_in(workspace_id)
    if role is None:
        audit(db, workspace_id, principal.id, f"authz.{action}", outcome="denied", details={"reason": "not a member"})
        db.commit()
        raise HTTPException(404, "Not found")
    if ROLE_RANK[role] < ROLE_RANK[min_role]:
        audit(db, workspace_id, principal.id, f"authz.{action}", outcome="denied", details={"role": role, "required": min_role})
        db.commit()
        raise HTTPException(403, f"Requires {min_role} role")
    return role


def require_service_token(authorization: str | None = Header(default=None)) -> None:
    """For eve agent tools calling back into the engine."""
    expected = get_settings().agent_tool_token
    if not expected or not authorization or authorization != f"Bearer {expected}":
        raise HTTPException(401, "Invalid service token")


__all__ = ["Principal", "login", "logout", "get_principal", "require_member", "require_service_token", "correlation_id"]
