"""Deal endpoints."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import Db, Pagination, UserScope, not_found
from app.api.schemas import DealExplain, DealRow, Page
from app.services import deal_intel

router = APIRouter(prefix="/deals", tags=["deals"])


@router.get("", response_model=Page[DealRow])
def list_deals(
    db: Db, scope: UserScope, paging: Pagination, sort: str = "risk", open_only: bool = True,
    q: str | None = None, stage: str | None = None, type: str | None = None,
    team_id: int | None = None, band: str | None = None, account_id: int | None = None,
) -> Page[DealRow]:
    items, total = deal_intel.list_deals(
        db, scope, paging.page, paging.page_size, sort, open_only, q, stage, type, team_id,
        band, account_id,
    )
    return Page(items=items, total=total, page=paging.page, page_size=paging.page_size)


@router.get("/{deal_id}/explain", response_model=DealExplain)
def explain(deal_id: int, db: Db, scope: UserScope) -> dict:
    result = deal_intel.explain_deal(db, scope, deal_id)
    if result is None:
        raise not_found()
    return result
