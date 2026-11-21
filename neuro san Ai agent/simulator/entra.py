"""MockEntraProvider (M6): IdentityProvider over the shared estate."""

from __future__ import annotations

from typing import Any

from integrations.ports import IdentityState
from simulator.estate import Estate


class MockEntraProvider:
    source = "entra"

    def __init__(self, estate: Estate) -> None:
        self._estate = estate

    def get_identity(self, user_id: str) -> IdentityState:
        identity = self._estate.get_identity(user_id)
        return IdentityState(user_id=identity.user_id,
                             account_state=identity.account_state,
                             mfa_ok=identity.mfa_ok, locked=identity.locked,
                             last_signin=identity.last_signin)

    def get_signin_history(self, user_id: str, limit: int = 10) -> list[dict[str, Any]]:
        identity = self._estate.get_identity(user_id)
        return [{"event": s.event, "at": s.at, "result": s.result,
                 "detail": s.detail} for s in identity.signins[:limit]]
