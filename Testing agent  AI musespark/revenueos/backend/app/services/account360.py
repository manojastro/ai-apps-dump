"""Account list and the one-call Account 360 view."""
from __future__ import annotations

from datetime import timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.db.models import (
    Account,
    Activity,
    Contact,
    Deal,
    Invoice,
    Subscription,
    Ticket,
    UsageDaily,
)
from app.services.predictions import CHURN_MODEL, WIN_MODEL, churn_band, deal_band, scores
from app.services.scope import Scope

TIMELINE_LIMIT = 40


def list_accounts(
    session: Session,
    scope: Scope,
    page: int,
    page_size: int,
    q: str | None = None,
    region: str | None = None,
    segment: str | None = None,
    status: str | None = None,
    health: str | None = None,
) -> tuple[list[dict], int]:
    filters = [scope.accounts()]
    if q:
        like = f"%{q.strip()}%"
        filters.append(or_(Account.name.ilike(like), Account.domain.ilike(like)))
    for column, value in (
        (Account.region, region), (Account.segment, segment),
        (Account.status, status), (Account.health_status, health),
    ):
        if value:
            filters.append(column == value)
    total = session.scalar(select(func.count()).select_from(Account).where(*filters))
    rows = session.scalars(
        select(Account).options(joinedload(Account.owner)).where(*filters)
        .order_by(Account.arr.desc(), Account.id)
        .limit(page_size).offset((page - 1) * page_size)
    ).all()
    churn = scores(session, CHURN_MODEL, [a.id for a in rows])
    items = [account_summary(a, churn.get(a.id)) for a in rows]
    return items, total or 0


def account_summary(a: Account, churn_prediction=None) -> dict:
    p = churn_prediction.score if churn_prediction else None
    return {
        "id": a.id, "name": a.name, "domain": a.domain, "industry": a.industry,
        "region": a.region, "segment": a.segment, "arr": float(a.arr), "status": a.status,
        "churned_at": a.churned_at, "health_score": a.health_score,
        "health_status": a.health_status,
        "owner_name": a.owner.full_name if a.owner else None,
        "p_churn": round(p, 4) if p is not None else None, "churn_band": churn_band(p),
        "cite": f"accounts#{a.id}",
    }


def weekly_usage(session: Session, account_id: int) -> list[dict]:
    week = func.date_trunc("week", UsageDaily.date).label("week")
    rows = session.execute(
        select(week, func.avg(UsageDaily.active_users), func.sum(UsageDaily.key_feature_events),
               func.max(UsageDaily.seats_purchased))
        .where(UsageDaily.account_id == account_id).group_by(week).order_by(week)
    ).all()
    return [
        {"week": r[0].date(), "active_users": round(float(r[1]), 1),
         "key_feature_events": int(r[2]), "seats": int(r[3])}
        for r in rows
    ]


def open_risks(account: Account, invoices: list[Invoice], tickets: list[Ticket],
               deals: list[dict], churn_prediction) -> list[dict]:
    """Plain facts worth a human's attention, each traceable to a record."""
    today = get_settings().data_as_of
    risks: list[dict] = []
    overdue = [i for i in invoices if i.status == "overdue"]
    if overdue:
        total = sum(float(i.amount) for i in overdue)
        risks.append({"type": "billing", "text": f"{len(overdue)} overdue invoices "
                      f"totalling ${total:,.0f}", "cite": f"invoices#{overdue[0].id}"})
    severe = [t for t in tickets if t.severity <= 2 and t.resolved_at is None]
    if severe:
        risks.append({"type": "support", "text": f"{len(severe)} severe tickets still open",
                      "cite": f"tickets#{severe[0].id}"})
    for d in deals:
        if d["outcome"] is None and d["risk_band"] == "at_risk":
            risks.append({"type": "deal", "text": f"Deal {d['name']} is at risk "
                          f"({d['p_win']:.0%} win probability)", "cite": f"deals#{d['id']}"})
        if d["outcome"] is None and d["close_date"] and d["close_date"] < today:
            risks.append({"type": "hygiene", "text": f"Deal {d['name']} is past its close date",
                          "cite": f"deals#{d['id']}"})
    if churn_prediction and churn_band(churn_prediction.score) in ("high", "medium"):
        risks.append({
            "type": "churn",
            "text": f"Churn risk {churn_prediction.score:.0%} in the next 90 days",
            "cite": f"predictions#{churn_prediction.id}",
        })
    return risks


def build_timeline(deals, tickets, invoices, activities) -> list[dict]:
    events = []
    for d in deals:
        events.append({"date": d["created_at"], "kind": "deal", "cite": f"deals#{d['id']}",
                       "text": f"Deal opened: {d['name']}"})
        if d["closed_at"]:
            events.append({"date": d["closed_at"], "kind": "deal", "cite": f"deals#{d['id']}",
                           "text": f"Deal {d['outcome']}: {d['name']}"})
    events += [{"date": t.opened_at, "kind": "ticket", "cite": f"tickets#{t.id}",
                "text": f"Sev {t.severity} ticket: {t.subject}"} for t in tickets]
    events += [{"date": i.due_date, "kind": "invoice", "cite": f"invoices#{i.id}",
                "text": f"Invoice ${float(i.amount):,.0f} due ({i.status})"} for i in invoices]
    events += [{"date": a.occurred_at, "kind": "activity", "cite": f"activities#{a.id}",
                "text": a.summary_text or a.type} for a in activities]
    events.sort(key=lambda e: e["date"], reverse=True)
    return events[:TIMELINE_LIMIT]


def get_360(session: Session, scope: Scope, account_id: int) -> dict | None:
    account = session.scalars(
        select(Account).options(joinedload(Account.owner))
        .where(Account.id == account_id, scope.accounts())
    ).first()
    if account is None:
        return None

    deal_rows = session.scalars(
        select(Deal).where(Deal.account_id == account_id).order_by(Deal.created_at.desc())
    ).all()
    wins = scores(session, WIN_MODEL, [d.id for d in deal_rows])
    deals = []
    for d in deal_rows:
        p = wins[d.id].score if d.id in wins and d.outcome is None else None
        deals.append({
            "id": d.id, "name": d.name, "amount": float(d.amount), "stage": d.stage,
            "type": d.type, "created_at": d.created_at, "close_date": d.close_date,
            "closed_at": d.closed_at, "outcome": d.outcome, "discount_pct": d.discount_pct,
            "p_win": round(p, 4) if p is not None else None, "risk_band": deal_band(p),
            "cite": f"deals#{d.id}",
        })

    contacts = session.scalars(
        select(Contact).where(Contact.account_id == account_id)
        .order_by(Contact.is_executive.desc(), Contact.full_name)
    ).all()
    invoices = session.scalars(
        select(Invoice).where(Invoice.account_id == account_id)
        .order_by(Invoice.due_date.desc())
    ).all()
    tickets = session.scalars(
        select(Ticket).where(Ticket.account_id == account_id)
        .order_by(Ticket.opened_at.desc())
    ).all()
    subscriptions = session.scalars(
        select(Subscription).where(Subscription.account_id == account_id)
        .order_by(Subscription.start.desc())
    ).all()
    today = get_settings().data_as_of
    activities = session.scalars(
        select(Activity).join(Deal, Activity.deal_id == Deal.id)
        .where(Deal.account_id == account_id,
               Activity.occurred_at >= today - timedelta(days=180))
        .order_by(Activity.occurred_at.desc()).limit(20)
    ).all()
    churn = scores(session, CHURN_MODEL, [account_id]).get(account_id)

    return {
        "account": account_summary(account, churn),
        "deals": deals,
        "contacts": [{
            "id": c.id, "full_name": c.full_name, "title": c.title,
            "is_executive": c.is_executive, "is_champion": c.is_champion,
            "last_seen": c.last_seen, "cite": f"contacts#{c.id}",
        } for c in contacts],
        "subscriptions": [{
            "id": s.id, "start": s.start, "end": s.end, "mrr": float(s.mrr), "seats": s.seats,
            "status": s.status, "renewal_date": s.renewal_date, "cite": f"subscriptions#{s.id}",
        } for s in subscriptions],
        "invoices": [{
            "id": i.id, "amount": float(i.amount), "issued_date": i.issued_date,
            "due_date": i.due_date, "paid_date": i.paid_date, "status": i.status,
            "cite": f"invoices#{i.id}",
        } for i in invoices],
        "tickets": [{
            "id": t.id, "opened_at": t.opened_at, "resolved_at": t.resolved_at,
            "severity": t.severity, "subject": t.subject, "body_text": t.body_text,
            "cite": f"tickets#{t.id}",
        } for t in tickets],
        "usage_trend": weekly_usage(session, account_id),
        "open_risks": open_risks(account, list(invoices), list(tickets), deals, churn),
        "churn_reasons": churn.reasons_json if churn else [],
        "timeline": build_timeline(deals, tickets, invoices, activities),
    }
