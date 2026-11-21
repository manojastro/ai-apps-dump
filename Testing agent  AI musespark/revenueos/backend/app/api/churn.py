"""Retention and expansion endpoints."""
from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import Db, Pagination, UserScope, not_found
from app.api.schemas import ChurnExplain, ExpansionRow, Page, RetentionRow, RetentionSummary
from app.services import retention

router = APIRouter(tags=["retention"])


@router.get("/churn/at-risk", response_model=Page[RetentionRow])
def at_risk(
    db: Db, scope: UserScope, paging: Pagination, band: str | None = None
) -> Page[RetentionRow]:
    items, total = retention.list_at_risk(db, scope, paging.page, paging.page_size, band)
    return Page(items=items, total=total, page=paging.page, page_size=paging.page_size)


@router.get("/churn/summary", response_model=RetentionSummary)
def churn_summary(db: Db, scope: UserScope) -> dict:
    return retention.summary(db, scope)


@router.get("/churn/{account_id}/explain", response_model=ChurnExplain)
def explain(account_id: int, db: Db, scope: UserScope) -> dict:
    result = retention.explain_churn(db, scope, account_id)
    if result is None:
        raise not_found()
    return result


@router.get("/expansion", response_model=Page[ExpansionRow])
def expansion(db: Db, scope: UserScope, paging: Pagination) -> Page[ExpansionRow]:
    rows = retention.expansion_candidates(db, scope)
    start = (paging.page - 1) * paging.page_size
    return Page(items=rows[start:start + paging.page_size], total=len(rows),
                page=paging.page, page_size=paging.page_size)
