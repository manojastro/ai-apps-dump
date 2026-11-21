"""Optional OIDC seam for Microsoft Entra ID. Disabled unless OIDC_ENABLED=true.

When enabled, an ID token is accepted only if its signature verifies against the issuer JWKS,
the issuer and audience match configuration, the Entra tenant (tid) matches OIDC_TENANT_ID, and
the subject maps to an existing user with a membership in a Procurement Navigator tenant.
Membership is never created from token claims.
"""

from __future__ import annotations

from typing import Any

import jwt
from sqlalchemy import select

from ..core.config import get_settings
from ..core.db import global_session
from ..core.models import Membership, User


class OidcError(Exception):
    pass


def _jwks_client() -> jwt.PyJWKClient:
    s = get_settings()
    issuer = (s.oidc_issuer or "").rstrip("/")
    # Entra v2 issuers publish keys at the tenant discovery document's jwks_uri.
    return jwt.PyJWKClient(f"{issuer.removesuffix('/v2.0')}/discovery/v2.0/keys")


def verify_id_token(id_token: str) -> dict[str, Any]:
    s = get_settings()
    if not s.oidc_enabled:
        raise OidcError("OIDC is disabled")
    key = _jwks_client().get_signing_key_from_jwt(id_token)
    claims = jwt.decode(
        id_token,
        key.key,
        algorithms=["RS256"],
        audience=s.oidc_audience,
        issuer=s.oidc_issuer,
        options={"require": ["exp", "iat", "iss", "aud", "sub", "tid"]},
    )
    if claims.get("tid") != s.oidc_tenant_id:
        raise OidcError("token tenant does not match configured Entra tenant")
    return claims


def user_for_claims(claims: dict[str, Any]) -> User:
    with global_session() as s:
        user = s.scalar(select(User).where(User.oidc_subject == f"{claims['iss']}|{claims['sub']}"))
        if user is None or not user.is_active:
            raise OidcError("no active user is linked to this identity")
        if not s.scalar(select(Membership.id).where(Membership.user_id == user.id).limit(1)):
            raise OidcError("user has no tenant membership")
        return user
