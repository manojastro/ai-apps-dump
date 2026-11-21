"""Account endpoints."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import Db, Pagination, UserScope, not_found
from app.api.schemas import Account360, AccountRow, Page
from app.services import account360

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.get("", response_model=Page[AccountRow])
def list_accounts(
    db: Db, scope: UserScope, paging: Pagination, q: str | None = None,
    region: str | None = None, segment: str | None = None, status: str | None = None,
    health: str | None = None,
) -> Page[AccountRow]:
    items, total = account360.list_accounts(
        db, scope, paging.page, paging.page_size, q, region, segment, status, health
    )
    return Page(items=items, total=total, page=paging.page, page_size=paging.page_size)


@router.get("/{account_id}/360", response_model=Account360)
def account_360(account_id: int, db: Db, scope: UserScope) -> dict:
    view = account360.get_360(db, scope, account_id)
    if view is None:
        raise not_found()
    return view
