"""Shared API dependencies: the current user, role checks, pagination."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Cookie, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.core.security import decode_token
from app.db.models import User
from app.db.session import get_db
from app.services.scope import Scope

COOKIE_NAME = "revenueos_token"
Db = Annotated[Session, Depends(get_db)]


def current_user(
    db: Db,
    authorization: Annotated[str | None, Header()] = None,
    revenueos_token: Annotated[str | None, Cookie()] = None,
) -> User:
    """Accept a Bearer token (API clients) or the httpOnly cookie (the web app)."""
    token = revenueos_token
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:]
    claims = decode_token(token) if token else None
    if claims is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    user = (db.query(User).options(joinedload(User.team))
            .filter(User.id == int(claims["sub"])).one_or_none())
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    return user


CurrentUser = Annotated[User, Depends(current_user)]


def current_scope(user: CurrentUser) -> Scope:
    return Scope(user_id=user.id, role=user.role, team_id=user.team_id)


UserScope = Annotated[Scope, Depends(current_scope)]


def require_roles(*roles: str):
    def check(user: CurrentUser) -> User:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Not permitted for this role")
        return user

    return check


@dataclass
class Paging:
    page: int
    page_size: int


def paging(
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 25,
) -> Paging:
    return Paging(page=page, page_size=page_size)


Pagination = Annotated[Paging, Depends(paging)]


def not_found() -> HTTPException:
    """Same answer whether a record is missing or belongs to another team."""
    return HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
