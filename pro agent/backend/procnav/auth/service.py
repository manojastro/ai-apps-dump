"""Password hashing, server-side sessions, CSRF tokens and principals."""

from __future__ import annotations

import hashlib
import secrets
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from sqlalchemy import select

from ..core.config import get_settings
from ..core.db import global_session
from ..core.models import AuthSession, Membership, Tenant, User

_hasher = PasswordHasher()
# Hash of a random string, used to equalise timing when the email does not exist.
_DUMMY_HASH = _hasher.hash(secrets.token_hex(16))

ROLES = ("requester", "approver", "admin", "viewer")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(stored: str | None, password: str) -> bool:
    try:
        return _hasher.verify(stored or _DUMMY_HASH, password) and stored is not None
    except (VerificationError, InvalidHashError):
        return False


def _token_id(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


@dataclass(frozen=True)
class Principal:
    user_id: uuid.UUID
    email: str
    display_name: str
    tenant_id: uuid.UUID
    tenant_slug: str
    tenant_name: str
    roles: frozenset[str] = field(default_factory=frozenset)
    csrf_token: str = ""
    session_id: str = ""

    def has(self, role: str) -> bool:
        return role in self.roles or "admin" in self.roles and role == "viewer"


def authenticate(email: str, password: str, tenant_slug: str | None = None) -> tuple[str, Principal] | None:
    """Return (session_token, principal) on success. The raw token is only ever sent as a cookie."""
    with global_session() as s:
        user = s.scalar(select(User).where(User.email == email.lower().strip(), User.is_active.is_(True)))
        if not verify_password(user.password_hash if user else None, password) or user is None:
            return None
        q = (
            select(Tenant, Membership.role)
            .join(Membership, Membership.tenant_id == Tenant.id)
            .where(Membership.user_id == user.id)
        )
        rows = s.execute(q).all()
        if not rows:
            return None
        tenants = {t.slug: t for t, _ in rows}
        tenant = tenants.get(tenant_slug) if tenant_slug else sorted(tenants.values(), key=lambda t: t.slug)[0]
        if tenant is None:
            return None
        roles = frozenset(r for t, r in rows if t.id == tenant.id)
        token = secrets.token_urlsafe(32)
        csrf = secrets.token_urlsafe(24)
        now = datetime.now(UTC)
        s.add(
            AuthSession(
                id=_token_id(token),
                user_id=user.id,
                tenant_id=tenant.id,
                csrf_token=csrf,
                expires_at=now + timedelta(seconds=get_settings().session_ttl_seconds),
            )
        )
        principal = Principal(
            user.id, user.email, user.display_name, tenant.id, tenant.slug, tenant.name, roles, csrf, _token_id(token)
        )
        return token, principal


def load_principal(token: str | None) -> Principal | None:
    if not token:
        return None
    sid = _token_id(token)
    with global_session() as s:
        row = s.execute(
            select(AuthSession, User, Tenant)
            .join(User, User.id == AuthSession.user_id)
            .join(Tenant, Tenant.id == AuthSession.tenant_id)
            .where(AuthSession.id == sid, AuthSession.revoked.is_(False), User.is_active.is_(True))
        ).first()
        if row is None:
            return None
        sess, user, tenant = row
        if sess.expires_at <= datetime.now(UTC):
            return None
        roles = frozenset(
            s.scalars(
                select(Membership.role).where(Membership.user_id == user.id, Membership.tenant_id == tenant.id)
            ).all()
        )
        if not roles:
            return None
        return Principal(
            user.id, user.email, user.display_name, tenant.id, tenant.slug, tenant.name, roles, sess.csrf_token, sid
        )


def revoke(token: str | None) -> None:
    if not token:
        return
    with global_session() as s:
        sess = s.get(AuthSession, _token_id(token))
        if sess:
            sess.revoked = True
