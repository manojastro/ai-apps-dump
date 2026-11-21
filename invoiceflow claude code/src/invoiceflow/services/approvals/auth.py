"""Who is calling the approval service. Identity and role come only from the credential,
never from the request body.

v1 DevTokenAuth: random bearer tokens mapped to synthetic users, stored in the git-ignored
state directory (`invoiceflow approvals dev-tokens` creates them).
v2 OidcAuth: Microsoft Entra ID access tokens (RS256 JWT). App roles in the `roles` claim
map to AP roles; `oid` (or `sub`) is the user id. See docs/ENTRA_SETUP.md; nothing is
created in Entra ID by this code.
"""

import json
import secrets
from pathlib import Path
from typing import Any, Protocol

import jwt

from invoiceflow.data.models import Role
from invoiceflow.policy.models import Identity

APP_ROLES = {
    "AP.Clerk": Role.AP_CLERK,
    "AP.Manager": Role.AP_MANAGER,
    "Finance.Controller": Role.FINANCE_CONTROLLER,
    "AP.Auditor": Role.AUDITOR,
    "Platform.Admin": Role.PLATFORM_ADMIN,
}
ROLE_PRECEDENCE = [
    Role.FINANCE_CONTROLLER,
    Role.AP_MANAGER,
    Role.AP_CLERK,
    Role.AUDITOR,
    Role.PLATFORM_ADMIN,
]


class AuthError(Exception):
    pass


class Authenticator(Protocol):
    def identify(self, authorization: str | None) -> Identity: ...


def _bearer(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise AuthError("missing bearer token")
    return authorization.split(" ", 1)[1].strip()


class DevTokenAuth:
    def __init__(self, tokens: dict[str, Identity]) -> None:
        self._tokens = tokens

    @classmethod
    def load_or_create(cls, path: Path) -> "DevTokenAuth":
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            users = [
                ("u-clerk-1", Role.AP_CLERK),
                ("u-clerk-2", Role.AP_CLERK),
                ("u-manager-1", Role.AP_MANAGER),
                ("u-fc-1", Role.FINANCE_CONTROLLER),
                ("u-audit-1", Role.AUDITOR),
                ("u-admin-1", Role.PLATFORM_ADMIN),
            ]
            data = {
                secrets.token_urlsafe(24): {"id": uid, "kind": "human", "role": role.value}
                for uid, role in users
            }
            path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        raw = json.loads(path.read_text(encoding="utf-8"))
        return cls({token: Identity.model_validate(v) for token, v in raw.items()})

    def identify(self, authorization: str | None) -> Identity:
        token = _bearer(authorization)
        for known, identity in self._tokens.items():
            if secrets.compare_digest(known, token):
                return identity
        raise AuthError("unknown token")


class OidcAuth:
    def __init__(self, issuer: str, audience: str, jwks_client: Any) -> None:
        self._issuer = issuer
        self._audience = audience
        self._jwks = jwks_client  # jwt.PyJWKClient(jwks_url) in production

    def identify(self, authorization: str | None) -> Identity:
        token = _bearer(authorization)
        try:
            key = self._jwks.get_signing_key_from_jwt(token).key
            claims = jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                audience=self._audience,
                issuer=self._issuer,
                options={"require": ["exp", "iss", "aud"]},
            )
        except jwt.PyJWTError as exc:
            raise AuthError(f"invalid token: {exc}") from exc
        roles = [APP_ROLES[r] for r in claims.get("roles", []) if r in APP_ROLES]
        if not roles:
            raise AuthError("token has no InvoiceFlow app role")
        role = next(r for r in ROLE_PRECEDENCE if r in roles)
        user = claims.get("oid") or claims.get("sub")
        if not user:
            raise AuthError("token has no subject")
        return Identity(id=str(user), kind="human", role=role)
