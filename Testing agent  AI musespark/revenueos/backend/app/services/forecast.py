"""Forecast by quarter, team and region, plus the weekly variance explainer."""
from __future__ import annotations

import json
from datetime import date, timedelta

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.db.models import Deal, ForecastSnapshot, Team, User
from app.ml.common import load_active
from app.ml.features import Frames, close_date_at
from app.ml.forecast_sim import (
    N_SIMULATIONS,
    quarter_bounds,
    quarter_label,
    rep_commit,
    simulate,
    stage_weighted,
)
from app.ml.train_win import MODEL_NAME, score_open_deals
from app.services.predictions import WIN_MODEL, active_version, scores
from app.services.scope import Scope

PROBABILITY_MOVE = 0.03
DEFAULT_SLIP = 0.85


def slip_rates(session: Session) -> dict[str, float]:
    version = active_version(session, WIN_MODEL)
    return (version.metrics_json or {}).get("slip_rates", {}) if version else {}


def _pipeline(
    session: Session, scope: Scope, quarter: str, team_id: int | None, region: str | None
) -> tuple[list[dict], float]:
    """Open deals expected this quarter, plus revenue already closed won in it."""
    start, end = quarter_bounds(quarter)
    filters = [scope.deals()]
    team = scope.effective_team(team_id)
    if team is not None:
        filters.append(Deal.owner_id.in_(select(User.id).where(User.team_id == team)))
    if region:
        filters.append(Deal.owner_id.in_(
            select(User.id).join(Team, User.team_id == Team.id).where(Team.region == region)
        ))
    deals = session.scalars(
        select(Deal).options(joinedload(Deal.owner).joinedload(User.team)).where(*filters)
    ).all()
    wins = scores(session, WIN_MODEL)
    slip = slip_rates(session)
    rows: list[dict] = []
    closed_won = 0.0
    for d in deals:
        if d.outcome == "won" and d.closed_at and start.date() <= d.closed_at <= end.date():
            closed_won += float(d.amount)
        if d.outcome is None and d.close_date and start.date() <= d.close_date <= end.date():
            prediction = wins.get(d.id)
            if prediction is None:
                continue
            p_win = prediction.score
            p_quarter = slip.get(d.stage, DEFAULT_SLIP)
            rows.append({
                "id": d.id, "name": d.name, "amount": float(d.amount), "stage": d.stage,
                "team": d.owner.team.name if d.owner and d.owner.team else None,
                "region": d.owner.team.region if d.owner and d.owner.team else None,
                "p_win": p_win, "p_in_quarter": p_quarter,
                "expected_value": float(d.amount) * p_win * p_quarter,
                "cite": f"deals#{d.id}",
            })
    return rows, closed_won


def _figures(rows: list[dict], closed_won: float) -> dict:
    amounts = np.array([r["amount"] for r in rows], dtype=float)
    probabilities = np.array([r["p_win"] * r["p_in_quarter"] for r in rows], dtype=float)
    stages = pd.Series([r["stage"] for r in rows], dtype="object")
    result = simulate(amounts, probabilities, base=closed_won)
    return {
        "low": round(result.low, 2),
        "expected": round(result.expected, 2),
        "high": round(result.high, 2),
        "closed_won_to_date": round(closed_won, 2),
        "rep_commit": round(closed_won + rep_commit(amounts, stages), 2),
        "stage_weighted": round(closed_won + stage_weighted(amounts, stages), 2),
        "open_deals": len(rows),
        "open_pipeline": round(float(amounts.sum()), 2),
    }


def get_forecast(
    session: Session,
    scope: Scope,
    quarter: str | None = None,
    team_id: int | None = None,
    region: str | None = None,
) -> dict:
    quarter = quarter or quarter_label(get_settings().data_as_of)
    rows, closed_won = _pipeline(session, scope, quarter, team_id, region)
    result = _figures(rows, closed_won)

    def breakdown(key: str) -> list[dict]:
        groups = sorted({r[key] for r in rows if r[key]})
        output = []
        for group in groups:
            subset = [r for r in rows if r[key] == group]
            won = _closed_won_for(session, scope, quarter, key, group)
            output.append({key: group, **_figures(subset, won)})
        return output

    top = sorted(rows, key=lambda r: r["expected_value"], reverse=True)[:10]
    return {
        "quarter": quarter,
        "as_of": get_settings().data_as_of,
        "simulations": N_SIMULATIONS,
        **result,
        "by_team": breakdown("team"),
        "by_region": breakdown("region"),
        "top_deals": [{
            **{k: r[k] for k in ("id", "name", "amount", "stage", "cite")},
            "p_win": round(r["p_win"], 4),
            "expected_value": round(r["expected_value"], 2),
        } for r in top],
        "cite": f"forecast#{quarter}",
    }


def _closed_won_for(session: Session, scope: Scope, quarter: str, key: str, group: str) -> float:
    start, end = quarter_bounds(quarter)
    column = Team.name if key == "team" else Team.region
    deals = session.scalars(
        select(Deal).join(User, Deal.owner_id == User.id).join(Team, User.team_id == Team.id)
        .where(scope.deals(), column == group, Deal.outcome == "won",
               Deal.closed_at.between(start.date(), end.date()))
    ).all()
    return float(sum(float(d.amount) for d in deals))


def backtest_results() -> dict | None:
    path = get_settings().artifact_dir / "forecast_backtest.json"
    return json.loads(path.read_text()) if path.exists() else None


# ---- weekly snapshots -----------------------------------------------------


def write_snapshots(session: Session, fr: Frames, as_of: date, weeks: int = 4) -> int:
    """Record each open deal as it looked at the end of each recent week."""
    artifact = load_active(MODEL_NAME)
    slip = artifact["slip_rates"]
    count = 0
    for offset in range(weeks):
        t = as_of - timedelta(days=7 * offset)
        scored = score_open_deals(fr, t, artifact)
        deals = fr.deals.set_index("id").loc[scored["deal_id"]]
        closes = close_date_at(deals, pd.Timestamp(t))
        label = quarter_label(t)
        start, end = quarter_bounds(label)
        session.query(ForecastSnapshot).filter_by(snapshot_date=t).delete()
        for (_, row), amount, close in zip(
            scored.iterrows(), deals["amount"], closes, strict=True
        ):
            session.add(ForecastSnapshot(
                snapshot_date=t, deal_id=int(row["deal_id"]), quarter=label,
                amount=float(amount), stage=row["stage"],
                close_date=close.date() if pd.notna(close) else None,
                p_win=float(row["p_win"]),
                p_in_quarter=float(slip.get(row["stage"], DEFAULT_SLIP)),
                in_quarter=bool(pd.notna(close) and start <= close <= end),
            ))
            count += 1
    session.commit()
    return count


def _expected(snapshot: ForecastSnapshot) -> float:
    return float(snapshot.amount) * snapshot.p_win * snapshot.p_in_quarter


def _closed_won_until(session: Session, scope: Scope, quarter: str, t: date) -> float:
    start, _ = quarter_bounds(quarter)
    deals = session.scalars(
        select(Deal).where(scope.deals(), Deal.outcome == "won",
                           Deal.closed_at.between(start.date(), t))
    ).all()
    return float(sum(float(d.amount) for d in deals))


def get_changes(session: Session, scope: Scope) -> dict:
    """Explain the week-on-week change in expected revenue, deal by deal.

    Each deal's change falls into exactly one category, so the items add up to the total
    change. A test checks that reconciliation.
    """
    dates = session.scalars(
        select(ForecastSnapshot.snapshot_date).distinct()
        .order_by(ForecastSnapshot.snapshot_date.desc()).limit(2)
    ).all()
    if len(dates) < 2:
        return {"available": False, "items": [], "categories": {}}
    current_date, previous_date = dates
    visible = set(session.scalars(select(Deal.id).where(scope.deals())))

    def load(t: date) -> dict[int, ForecastSnapshot]:
        rows = session.scalars(select(ForecastSnapshot).where(
            ForecastSnapshot.snapshot_date == t
        )).all()
        return {r.deal_id: r for r in rows if r.deal_id in visible}

    previous, current = load(previous_date), load(current_date)
    quarter = quarter_label(current_date)
    start, end = quarter_bounds(quarter)
    deals = {d.id: d for d in session.scalars(
        select(Deal).where(Deal.id.in_(visible))
    )}

    prev_in = {k: v for k, v in previous.items() if v.in_quarter}
    curr_in = {k: v for k, v in current.items() if v.in_quarter}
    won_now = {
        d.id for d in deals.values()
        if d.outcome == "won" and d.closed_at
        and max(previous_date, start.date() - timedelta(days=1)) < d.closed_at <= current_date
    }

    items: list[dict] = []

    def add(deal_id: int, category: str, delta: float, detail: str) -> None:
        d = deals[deal_id]
        items.append({
            "deal_id": deal_id, "name": d.name, "category": category,
            "delta_expected": round(delta, 2), "detail": detail, "cite": f"deals#{deal_id}",
        })

    for deal_id in sorted(set(prev_in) | set(curr_in) | won_now):
        before = prev_in.get(deal_id)
        after = curr_in.get(deal_id)
        old = _expected(before) if before else 0.0
        new = _expected(after) if after else 0.0
        d = deals[deal_id]
        if deal_id in won_now:
            add(deal_id, "closed_won", float(d.amount) - old, "Closed won this week")
        elif before and deal_id not in current:
            add(deal_id, "closed_lost", -old, "Closed lost this week")
        elif before and not after:
            add(deal_id, "slipped_out", -old,
                f"Close date moved out of {quarter} to {current[deal_id].close_date}")
        elif after and not before:
            add(deal_id, "moved_in", new, f"Now expected to close in {quarter}")
        elif before and after:
            moved = abs(after.p_win - before.p_win) >= PROBABILITY_MOVE
            if after.close_date != before.close_date:
                add(deal_id, "slipped_within_quarter", new - old,
                    f"Close date moved from {before.close_date} to {after.close_date}")
            elif moved:
                add(deal_id, "probability_changed", new - old,
                    f"Win probability {before.p_win:.0%} to {after.p_win:.0%}")
            elif new != old:
                add(deal_id, "minor_changes", new - old, "Small score drift")

    expected_previous = (_closed_won_until(session, scope, quarter, previous_date)
                         + sum(_expected(v) for v in prev_in.values()))
    expected_current = (_closed_won_until(session, scope, quarter, current_date)
                        + sum(_expected(v) for v in curr_in.values()))
    categories: dict[str, dict] = {}
    for item in items:
        bucket = categories.setdefault(item["category"], {"count": 0, "delta_expected": 0.0})
        bucket["count"] += 1
        bucket["delta_expected"] = round(bucket["delta_expected"] + item["delta_expected"], 2)
    items.sort(key=lambda i: abs(i["delta_expected"]), reverse=True)
    return {
        "available": True,
        "quarter": quarter,
        "previous_date": previous_date,
        "current_date": current_date,
        "expected_previous": round(expected_previous, 2),
        "expected_current": round(expected_current, 2),
        "total_change": round(expected_current - expected_previous, 2),
        "categories": categories,
        "items": [i for i in items if i["category"] != "minor_changes"][:50],
        "cite": f"forecast#{quarter}",
    }
