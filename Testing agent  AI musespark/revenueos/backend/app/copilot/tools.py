"""Copilot tools. All are read-only and all run inside the caller's Scope.

There is deliberately no SQL tool. A fixed tool list means the model can only ask
questions we have designed, each one tested and scoped, and a successful prompt injection
still has no way to write data or reach another team's records.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.copilot import rag
from app.copilot.guardrails import neutralise
from app.db.models import Account
from app.services import account360, deal_intel, forecast, retention
from app.services.scope import Scope

NOT_ACCESSIBLE = {"error": "not_found_or_not_permitted"}

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "get_account_360",
        "description": (
            "Full view of one account: deals, contacts, invoices, usage trend, tickets, open "
            "risks and churn reasons. Pass account_id, or account_name to look it up."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "account_id": {"type": "integer"},
                "account_name": {"type": "string", "description": "Full or partial name."},
            },
        },
    },
    {
        "name": "list_at_risk_deals",
        "description": (
            "Open deals ordered by value at risk, with win probability and reasons. Optional "
            "filter on risk band: at_risk, watch or healthy."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "minimum": 1, "maximum": 25},
                "band": {"type": "string", "enum": ["at_risk", "watch", "healthy"]},
            },
        },
    },
    {
        "name": "explain_deal",
        "description": "Win probability for one deal, and the reasons behind it.",
        "input_schema": {
            "type": "object",
            "properties": {"deal_id": {"type": "integer"}},
            "required": ["deal_id"],
        },
    },
    {
        "name": "get_forecast",
        "description": (
            "Forecast with low, expected and high figures, rep commit, and team and region "
            "breakdowns. quarter looks like 2026Q4 and defaults to the current quarter."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "quarter": {"type": "string", "pattern": "^20[0-9]{2}Q[1-4]$"},
                "team_id": {"type": "integer"},
                "region": {"type": "string", "enum": ["NA", "EMEA", "APAC", "LATAM"]},
            },
        },
    },
    {
        "name": "get_forecast_changes",
        "description": (
            "What changed in the forecast since last week: deals that closed, slipped, moved "
            "in, or changed probability."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "list_churn_risks",
        "description": (
            "Accounts ordered by expected ARR loss, with churn probability and reasons, plus "
            "total at-risk ARR. Optional filter on band: high, medium or low."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "minimum": 1, "maximum": 25},
                "band": {"type": "string", "enum": ["high", "medium", "low"]},
            },
        },
    },
    {
        "name": "search_tickets_and_notes",
        "description": (
            "Search support tickets and sales activity notes by keyword. Matching is lexical, "
            "so use words likely to appear in the text. Optional account_id narrows the search."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "account_id": {"type": "integer"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 15},
            },
            "required": ["query"],
        },
    },
]


def _clean_tickets(view: dict) -> dict:
    """Neutralise free text and trim long lists to what an answer needs."""
    view = dict(view)
    view["tickets"] = [
        {**t, "subject": neutralise(t["subject"]), "body_text": neutralise(t["body_text"])}
        for t in view["tickets"][:15]
    ]
    view["timeline"] = [{**e, "text": neutralise(e["text"])} for e in view["timeline"][:15]]
    view["invoices"] = view["invoices"][:6]
    view["usage_trend"] = view["usage_trend"][-12:]
    return view


@dataclass
class ToolContext:
    session: Session
    scope: Scope


def get_account_360(ctx: ToolContext, account_id: int | None = None,
                    account_name: str | None = None) -> dict:
    if account_id is None and account_name:
        like = f"%{account_name.strip()}%"
        matches = ctx.session.execute(
            select(Account.id, Account.name)
            .where(Account.name.ilike(like), ctx.scope.accounts())
            .order_by(Account.arr.desc()).limit(5)
        ).all()
        if not matches:
            return NOT_ACCESSIBLE
        if len(matches) > 1:
            exact = [m for m in matches if m[1].lower() == account_name.strip().lower()]
            if len(exact) != 1:
                return {"multiple_matches": [
                    {"account_id": m[0], "name": m[1], "cite": f"accounts#{m[0]}"}
                    for m in matches
                ]}
            matches = exact
        account_id = matches[0][0]
    if account_id is None:
        return {"error": "account_id or account_name is required"}
    view = account360.get_360(ctx.session, ctx.scope, account_id)
    return _clean_tickets(view) if view else NOT_ACCESSIBLE


def list_at_risk_deals(ctx: ToolContext, limit: int = 10, band: str | None = None) -> dict:
    items, total = deal_intel.list_deals(
        ctx.session, ctx.scope, 1, min(limit, 25), sort="value_at_risk", band=band
    )
    return {"total_matching": total, "deals": items}


def explain_deal(ctx: ToolContext, deal_id: int) -> dict:
    return deal_intel.explain_deal(ctx.session, ctx.scope, deal_id) or NOT_ACCESSIBLE


def get_forecast(ctx: ToolContext, quarter: str | None = None, team_id: int | None = None,
                 region: str | None = None) -> dict:
    return forecast.get_forecast(ctx.session, ctx.scope, quarter, team_id, region)


def get_forecast_changes(ctx: ToolContext) -> dict:
    return forecast.get_changes(ctx.session, ctx.scope)


def list_churn_risks(ctx: ToolContext, limit: int = 10, band: str | None = None) -> dict:
    items, total = retention.list_at_risk(ctx.session, ctx.scope, 1, min(limit, 25), band)
    totals = retention.summary(ctx.session, ctx.scope)
    totals.pop("at_risk_account_ids", None)
    return {"total_matching": total, "summary": totals, "accounts": items}


def search_tickets_and_notes(ctx: ToolContext, query: str, account_id: int | None = None,
                             limit: int = 8) -> dict:
    results = rag.search(ctx.session, ctx.scope, query, account_id, min(limit, 15))
    return {"results": results}


TOOLS: dict[str, Callable[..., dict]] = {
    "get_account_360": get_account_360,
    "list_at_risk_deals": list_at_risk_deals,
    "explain_deal": explain_deal,
    "get_forecast": get_forecast,
    "get_forecast_changes": get_forecast_changes,
    "list_churn_risks": list_churn_risks,
    "search_tickets_and_notes": search_tickets_and_notes,
}


def run_tool(ctx: ToolContext, name: str, arguments: dict) -> tuple[dict, bool]:
    """Run a tool and return (result, is_error). Failures go back to the model as data."""
    tool = TOOLS.get(name)
    if tool is None:
        return {"error": f"unknown tool {name}"}, True
    try:
        return tool(ctx, **arguments), False
    except TypeError:
        return {"error": "invalid arguments"}, True
