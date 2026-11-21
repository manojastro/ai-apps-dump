"""Team-level data scoping.

Every read in the app goes through a Scope, whether it comes from the UI, the API or
the copilot's tools. Enforcing it in one backend place means a new endpoint cannot
forget it, and hiding a menu in the UI is never the only protection.
"""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import ColumnElement, false, select, true

from app.db.models import Account, Deal, User

ALL_DATA_ROLES = {"cro", "revops", "admin"}
ROLES = {"cro", "sales_manager", "csm", "revops", "admin"}


@dataclass(frozen=True)
class Scope:
    user_id: int
    role: str
    team_id: int | None

    @property
    def sees_all(self) -> bool:
        return self.role in ALL_DATA_ROLES

    def _owners(self):
        return select(User.id).where(User.team_id == self.team_id)

    def accounts(self) -> ColumnElement[bool]:
        if self.sees_all:
            return true()
        if self.team_id is None:
            return false()
        return Account.owner_id.in_(self._owners())

    def deals(self) -> ColumnElement[bool]:
        if self.sees_all:
            return true()
        if self.team_id is None:
            return false()
        return Deal.owner_id.in_(self._owners())

    def effective_team(self, requested: int | None) -> int | None:
        """A scoped user is always pinned to their own team, whatever they asked for."""
        return requested if self.sees_all else self.team_id


SYSTEM_SCOPE = Scope(user_id=0, role="admin", team_id=None)
