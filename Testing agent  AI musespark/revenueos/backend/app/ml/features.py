"""Point-in-time feature engineering.

The rule that matters: a feature row for date T may only use facts known on T. Models
are trained on snapshots of each deal or account as they looked at a past date, and
scored the same way, so training and live scoring cannot drift apart. Using final
values instead (for example last activity before closing) would leak the outcome.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd
from sqlalchemy import Engine

from app.db.session import get_engine

STAGE_ORDER = {"prospecting": 0, "qualification": 1, "proposal": 2, "negotiation": 3}

DEAL_FEATURES = [
    "days_since_last_activity", "has_exec_contact", "days_since_exec_touch",
    "stakeholders_engaged", "activities_30d", "inbound_share", "stage_index",
    "days_in_stage", "stage_velocity_ratio", "discount_pct", "deal_age_days", "log_amount",
    "amount_to_arr", "open_severe_tickets", "severe_tickets_45d", "days_to_close",
    "close_date_pushed", "is_renewal", "is_expansion",
]

CHURN_FEATURES = [
    "usage_trend_30d", "events_trend_30d", "seat_utilization", "tickets_30d", "ticket_trend",
    "severe_tickets_60d", "avg_days_late", "overdue_invoices", "champion_silent",
    "days_to_renewal", "tenure_days", "log_arr", "is_enterprise", "is_mid_market",
]


@dataclass
class Frames:
    """All source tables needed for features, loaded once."""

    deals: pd.DataFrame
    accounts: pd.DataFrame
    stage_history: pd.DataFrame
    activities: pd.DataFrame
    contacts: pd.DataFrame
    tickets: pd.DataFrame
    usage: pd.DataFrame
    invoices: pd.DataFrame
    subscriptions: pd.DataFrame


def load_frames(engine: Engine | None = None) -> Frames:
    engine = engine or get_engine()

    def read(table: str, dates: list[str]) -> pd.DataFrame:
        frame = pd.read_sql_table(table, engine)
        for column in dates:
            frame[column] = pd.to_datetime(frame[column])
        return frame

    deals = read("deals", ["created_at", "close_date", "original_close_date",
                           "close_date_changed_at", "closed_at"])
    deals["amount"] = deals["amount"].astype(float)
    # Rows flagged by the data-quality report cannot be trusted for training.
    deals = deals[~(deals["closed_at"] < deals["created_at"])].copy()
    tickets = read("tickets", ["opened_at", "resolved_at"])
    tickets.loc[tickets["resolved_at"] < tickets["opened_at"], "resolved_at"] = pd.NaT
    subscriptions = read("subscriptions", ["start", "end", "renewal_date"])
    subscriptions["mrr"] = subscriptions["mrr"].astype(float)
    invoices = read("invoices", ["issued_date", "due_date", "paid_date"])
    accounts = read("accounts", ["churned_at"])
    accounts["arr"] = accounts["arr"].astype(float)
    return Frames(
        deals=deals, accounts=accounts,
        stage_history=read("deal_stage_history", ["entered_at"]),
        activities=read("activities", ["occurred_at"]),
        contacts=read("contacts", ["last_seen"]),
        tickets=tickets, usage=read("usage_daily", ["date"]),
        invoices=invoices, subscriptions=subscriptions,
    )


def snapshot_dates(start: date, end: date) -> list[pd.Timestamp]:
    """The 1st and 15th of each month, a cadence that catches short deals."""
    months = pd.date_range(pd.Timestamp(start).replace(day=1), end, freq="MS")
    days = sorted(list(months) + [m + pd.Timedelta(days=14) for m in months])
    return [d for d in days if pd.Timestamp(start) <= d <= pd.Timestamp(end)]


def fit_stage_days(fr: Frames, cutoff: pd.Timestamp) -> dict[str, float]:
    """Average days a deal spends in each stage, using only deals closed before cutoff."""
    closed_ids = fr.deals[fr.deals["closed_at"] < cutoff]["id"]
    history = fr.stage_history[fr.stage_history["deal_id"].isin(closed_ids)]
    history = history.sort_values(["deal_id", "entered_at"])
    history = history.assign(left=history.groupby("deal_id")["entered_at"].shift(-1))
    history = history.dropna(subset=["left"])
    spans = (history["left"] - history["entered_at"]).dt.days
    averages = spans.groupby(history["stage"]).mean().to_dict()
    return {s: float(averages.get(s, 20.0)) for s in STAGE_ORDER}


def close_date_at(deals: pd.DataFrame, t: pd.Timestamp) -> pd.Series:
    """The close date a user would have seen on date t."""
    changed = deals["close_date_changed_at"].notna() & (deals["close_date_changed_at"] <= t)
    known = deals["close_date"].where(changed, deals["original_close_date"])
    return known.fillna(deals["close_date"])


def open_deals_at(fr: Frames, t: pd.Timestamp) -> pd.DataFrame:
    deals = fr.deals
    is_open = (deals["created_at"] <= t) & (deals["closed_at"].isna() | (deals["closed_at"] > t))
    return deals[is_open]


def deal_snapshots(fr: Frames, dates: list[pd.Timestamp]) -> pd.DataFrame:
    rows = [
        pd.DataFrame({"deal_id": open_deals_at(fr, t)["id"].values, "as_of": t}) for t in dates
    ]
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(
        columns=["deal_id", "as_of"]
    )


def deal_features(
    fr: Frames, snapshots: pd.DataFrame, stage_days: dict[str, float]
) -> pd.DataFrame:
    """Build one feature row per (deal_id, as_of)."""
    deals = fr.deals.set_index("id")
    contacts = fr.contacts.set_index("id")
    activities = fr.activities.assign(
        is_exec=fr.activities["contact_id"].map(contacts["is_executive"]).fillna(False).astype(bool)
    )
    by_deal = {k: g for k, g in activities.groupby("deal_id")}
    stages = {k: g.sort_values("entered_at") for k, g in fr.stage_history.groupby("deal_id")}
    severe = fr.tickets[fr.tickets["severity"] <= 2]
    severe_by_account = {k: g for k, g in severe.groupby("account_id")}
    first_mrr = fr.subscriptions.sort_values("start").groupby("account_id")["mrr"].first()

    rows = []
    for deal_id, t in zip(snapshots["deal_id"], snapshots["as_of"], strict=True):
        d = deals.loc[deal_id]
        acts = by_deal.get(deal_id)
        if acts is not None:
            acts = acts[acts["occurred_at"] <= t]
        if acts is None or acts.empty:
            last_touch, exec_touch = None, None
            stakeholders, recent, inbound = 0, 0, 0.0
        else:
            last_touch = acts["occurred_at"].max()
            execs = acts[acts["is_exec"]]
            exec_touch = execs["occurred_at"].max() if not execs.empty else None
            stakeholders = acts["contact_id"].nunique()
            recent = int((acts["occurred_at"] > t - pd.Timedelta(days=30)).sum())
            inbound = float((acts["direction"] == "inbound").mean())

        age = (t - d["created_at"]).days
        history = stages.get(deal_id)
        stage_name, entered = "prospecting", d["created_at"]
        if history is not None:
            seen = history[(history["entered_at"] <= t)
                           & history["stage"].isin(STAGE_ORDER)]
            if not seen.empty:
                stage_name, entered = seen.iloc[-1]["stage"], seen.iloc[-1]["entered_at"]
        in_stage = (t - entered).days

        tickets = severe_by_account.get(d["account_id"])
        open_severe = recent_severe = 0
        if tickets is not None:
            opened = tickets[tickets["opened_at"] <= t]
            open_severe = int((opened["resolved_at"].isna() | (opened["resolved_at"] > t)).sum())
            recent_severe = int((opened["opened_at"] > t - pd.Timedelta(days=45)).sum())

        changed = d["close_date_changed_at"]
        pushed = int(pd.notna(changed) and changed <= t)
        known_close = d["close_date"] if pushed else d["original_close_date"]
        if pd.isna(known_close):
            known_close = d["close_date"]
        arr = first_mrr.get(d["account_id"], np.nan) * 12
        rows.append({
            "deal_id": deal_id,
            "as_of": t,
            "stage": stage_name,
            "days_since_last_activity": (t - last_touch).days if last_touch is not None else age,
            "has_exec_contact": int(exec_touch is not None),
            "days_since_exec_touch": (t - exec_touch).days if exec_touch is not None else age,
            "stakeholders_engaged": stakeholders,
            "activities_30d": recent,
            "inbound_share": inbound,
            "stage_index": STAGE_ORDER[stage_name],
            "days_in_stage": in_stage,
            "stage_velocity_ratio": in_stage / max(stage_days.get(stage_name, 20.0), 1.0),
            "discount_pct": d["discount_pct"],
            "deal_age_days": age,
            "log_amount": float(np.log1p(d["amount"])),
            "amount_to_arr": d["amount"] / arr if arr and arr > 0 else np.nan,
            "open_severe_tickets": open_severe,
            "severe_tickets_45d": recent_severe,
            "days_to_close": (known_close - t).days,
            "close_date_pushed": pushed,
            "is_renewal": int(d["type"] == "renewal"),
            "is_expansion": int(d["type"] == "expansion"),
        })
    return pd.DataFrame(rows)


def active_accounts_at(fr: Frames, t: pd.Timestamp) -> pd.DataFrame:
    """Subscriptions in force on date t, one row per account."""
    subs = fr.subscriptions
    live = subs[(subs["start"] <= t) & (subs["end"].isna() | (subs["end"] > t))]
    return live.sort_values("start").drop_duplicates("account_id", keep="last")


def _window_mean(values: pd.Series, dates: pd.Series, t, start_days: int, end_days: int) -> float:
    mask = (dates > t - pd.Timedelta(days=start_days)) & (dates <= t - pd.Timedelta(days=end_days))
    chunk = values[mask]
    return float(chunk.mean()) if len(chunk) else np.nan


def churn_features(fr: Frames, dates: list[pd.Timestamp]) -> pd.DataFrame:
    """Build one feature row per (account_id, as_of) for accounts active on as_of."""
    usage = {k: g for k, g in fr.usage.groupby("account_id")}
    tickets = {k: g for k, g in fr.tickets.groupby("account_id")}
    invoices = {k: g.sort_values("due_date") for k, g in fr.invoices.groupby("account_id")}
    champions = fr.contacts[fr.contacts["is_champion"]].set_index("account_id")["last_seen"]
    first_start = fr.subscriptions.groupby("account_id")["start"].min()

    rows = []
    for t in dates:
        for _, sub in active_accounts_at(fr, t).iterrows():
            account_id = sub["account_id"]
            u = usage.get(account_id)
            if u is None:
                continue
            u = u[u["date"] <= t]
            if len(u) < 14:
                continue  # Too new to have a usage trend.
            recent = _window_mean(u["active_users"], u["date"], t, 30, 0)
            prior = _window_mean(u["active_users"], u["date"], t, 60, 30)
            recent_e = _window_mean(u["key_feature_events"], u["date"], t, 30, 0)
            prior_e = _window_mean(u["key_feature_events"], u["date"], t, 60, 30)
            seats = float(u["seats_purchased"].iloc[-1]) or 1.0

            tk = tickets.get(account_id)
            n30 = n90 = sev60 = 0
            if tk is not None:
                opened = tk[tk["opened_at"] <= t]
                age = (t - opened["opened_at"]).dt.days
                n30 = int((age < 30).sum())
                n90 = int(((age >= 30) & (age < 120)).sum())
                sev60 = int(((age < 60) & (opened["severity"] <= 2)).sum())

            late_avg, overdue = 0.0, 0
            inv = invoices.get(account_id)
            if inv is not None:
                due = inv[inv["due_date"] <= t].tail(3)
                if len(due):
                    paid_by_t = due["paid_date"].where(due["paid_date"] <= t)
                    settled = paid_by_t.fillna(t)
                    late_avg = float((settled - due["due_date"]).dt.days.clip(lower=0).mean())
                    overdue = int(paid_by_t.isna().sum())

            seen = champions.get(account_id, pd.NaT)
            silent = int(pd.notna(seen) and seen < t - pd.Timedelta(days=45))
            renewal = sub["renewal_date"]
            mrr = float(sub["mrr"])
            segment = fr.accounts.loc[fr.accounts["id"] == account_id, "segment"].iloc[0]
            rows.append({
                "account_id": account_id,
                "as_of": t,
                "arr": mrr * 12,
                "usage_trend_30d": recent / prior if prior else np.nan,
                "events_trend_30d": recent_e / prior_e if prior_e else np.nan,
                "seat_utilization": recent / seats,
                "tickets_30d": n30,
                "ticket_trend": n30 - n90 / 3,
                "severe_tickets_60d": sev60,
                "avg_days_late": late_avg,
                "overdue_invoices": overdue,
                "champion_silent": silent,
                "days_to_renewal": (renewal - t).days if pd.notna(renewal) else 365,
                "tenure_days": (t - first_start[account_id]).days,
                "log_arr": float(np.log1p(mrr * 12)),
                "is_enterprise": int(segment == "enterprise"),
                "is_mid_market": int(segment == "mid_market"),
            })
    return pd.DataFrame(rows)
