"""Resolve a citation like `deals#412` to its underlying record, within the user's scope.

This is what makes citations clickable and auditable.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import (
    Account,
    Activity,
    Contact,
    Deal,
    Invoice,
    Prediction,
    Subscription,
    Ticket,
)
from app.services.scope import Scope

ACCOUNT_CHILDREN = {
    "tickets": Ticket, "invoices": Invoice, "subscriptions": Subscription, "contacts": Contact,
}


def _row_dict(row) -> dict:
    return {c.name: getattr(row, c.name) for c in row.__table__.columns
            if c.name not in ("vector", "password_hash")}


def _visible_account(session: Session, scope: Scope, account_id: int) -> bool:
    return session.scalar(
        select(Account.id).where(Account.id == account_id, scope.accounts())
    ) is not None


def _visible_deal(session: Session, scope: Scope, deal_id: int) -> bool:
    return session.scalar(select(Deal.id).where(Deal.id == deal_id, scope.deals())) is not None


def get_source(session: Session, scope: Scope, table: str, source_id: int) -> dict | None:
    if table == "accounts":
        row = session.scalars(
            select(Account).where(Account.id == source_id, scope.accounts())
        ).first()
    elif table == "deals":
        row = session.scalars(select(Deal).where(Deal.id == source_id, scope.deals())).first()
    elif table == "activities":
        row = session.get(Activity, source_id)
        if row and not _visible_deal(session, scope, row.deal_id):
            row = None
    elif table in ACCOUNT_CHILDREN:
        row = session.get(ACCOUNT_CHILDREN[table], source_id)
        if row and not _visible_account(session, scope, row.account_id):
            row = None
    elif table == "predictions":
        row = session.get(Prediction, source_id)
        if row:
            allowed = (_visible_deal if row.entity_type == "deal" else _visible_account)
            if not allowed(session, scope, row.entity_id):
                row = None
    else:
        return None
    return {"table": table, "id": source_id, "record": _row_dict(row)} if row else None
