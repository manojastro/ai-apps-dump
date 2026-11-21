"""Phase 6: copilot loop, guardrails, tools, audit and brief.

These use a scripted stand-in for Claude, so they prove the plumbing around the model:
scoping, audit, citation and number checks, injection handling. They say nothing about
answer quality. That needs the live eval in eval/run_eval.py.
"""
from __future__ import annotations

import json
from types import SimpleNamespace

from sqlalchemy import select

from app.copilot import guardrails, rag
from app.copilot.agent import Copilot, _request
from app.copilot.tools import TOOL_DEFINITIONS, TOOLS, ToolContext, run_tool
from app.db.models import CopilotAudit
from app.services.scope import SYSTEM_SCOPE, Scope
from tests.conftest import CRO, MANAGER_NA, auth

ALL = Scope(user_id=CRO, role="cro", team_id=None)


def text_block(text: str):
    return SimpleNamespace(type="text", text=text)


def tool_block(name: str, arguments: dict, block_id: str = "tool_1"):
    return SimpleNamespace(type="tool_use", name=name, input=arguments, id=block_id)


def reply(*blocks, stop: str = "end_turn"):
    return SimpleNamespace(
        content=list(blocks), stop_reason=stop,
        usage=SimpleNamespace(input_tokens=100, output_tokens=20),
    )


class ScriptedClient:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.requests: list[dict] = []

    def create(self, **kwargs):
        self.requests.append(kwargs)
        return self.responses.pop(0)


def test_every_declared_tool_is_implemented_and_read_only():
    names = {tool["name"] for tool in TOOL_DEFINITIONS}
    assert names == set(TOOLS)
    assert not any("sql" in name or "write" in name or "send" in name for name in names)


def test_request_uses_no_forced_tool_choice_and_keeps_system_prompt_stable():
    first = _request([{"role": "user", "content": "a"}])
    second = _request([{"role": "user", "content": "b"}])
    assert "tool_choice" not in first
    assert first["system"] == second["system"]


def test_tool_loop_runs_a_tool_and_records_audit(db):
    deal = run_tool(ToolContext(db, ALL), "list_at_risk_deals", {"limit": 1})[0]["deals"][0]
    client = ScriptedClient(
        reply(tool_block("explain_deal", {"deal_id": deal["id"]}), stop="tool_use"),
        reply(text_block(f"That deal is worth ${deal['amount']:,.2f} [{deal['cite']}].")),
    )
    result = Copilot(db, ALL, client=client).ask("Tell me about my riskiest deal")
    assert [t["name"] for t in result.tools_called] == ["explain_deal"]
    assert result.citations == [deal["cite"]]
    assert result.invalid_citations == []
    assert result.ungrounded_numbers == []
    saved = db.get(CopilotAudit, result.audit_id)
    assert saved.question == "Tell me about my riskiest deal"
    assert saved.cited_sources_json["valid"] == [deal["cite"]]
    assert saved.tools_called_json[0]["name"] == "explain_deal"


def test_tool_results_are_marked_as_untrusted_data(db):
    client = ScriptedClient(
        reply(tool_block("get_forecast_changes", {}), stop="tool_use"),
        reply(text_block("Nothing to report.")),
    )
    Copilot(db, ALL, client=client).ask("What changed?")
    tool_turn = next(
        m for m in client.requests[1]["messages"]
        if isinstance(m["content"], list) and m["role"] == "user"
    )
    content = tool_turn["content"][0]["content"]
    assert content.startswith('<tool_data tool="get_forecast_changes">')
    assert "untrusted data" in content


def test_invented_citation_triggers_repair_then_removal(db):
    client = ScriptedClient(
        reply(tool_block("get_forecast", {}), stop="tool_use"),
        reply(text_block("Forecast looks fine [deals#999999].")),
        reply(text_block("Still fine [deals#999999].")),
    )
    result = Copilot(db, ALL, client=client).ask("How is the forecast?")
    assert result.invalid_citations == ["deals#999999"]
    assert "[deals#999999]" not in result.answer
    assert "[citation removed]" in result.answer
    assert len(client.requests) == 3, "one repair attempt should be made"


def test_invented_number_is_flagged(db):
    client = ScriptedClient(
        reply(tool_block("get_forecast", {}), stop="tool_use"),
        reply(text_block("Expected revenue is $987,654,321 [forecast#2026Q4].")),
        reply(text_block("Expected revenue is $987,654,321 [forecast#2026Q4].")),
    )
    result = Copilot(db, ALL, client=client).ask("Forecast?")
    assert result.ungrounded_numbers


def test_refusal_stop_reason_is_handled(db):
    client = ScriptedClient(reply(stop="refusal"))
    result = Copilot(db, ALL, client=client).ask("Something off-limits")
    assert result.stop_reason == "refusal"
    assert "revenue" in result.answer


def test_tool_limit_stops_a_runaway_loop(db):
    responses = [reply(tool_block("get_forecast_changes", {}), stop="tool_use")
                 for _ in range(20)]
    result = Copilot(db, ALL, client=ScriptedClient(*responses)).ask("Loop forever")
    assert result.stop_reason == "tool_limit"


def test_bad_tool_arguments_return_an_error_not_a_crash(db):
    result, is_error = run_tool(ToolContext(db, ALL), "explain_deal", {"wrong": 1})
    assert is_error
    assert "error" in result


def test_prompt_injection_text_is_withheld_from_the_model(pipeline, db):
    issues = json.loads((pipeline["settings"].data_dir / "injected_issues.json").read_text())
    assert len(issues["prompt_injection_tickets"]) == 4
    from app.db.models import Ticket

    tickets = db.scalars(
        select(Ticket).where(Ticket.id.in_(issues["prompt_injection_tickets"]))
    ).all()
    for ticket in tickets:
        assert guardrails.neutralise(ticket.body_text) == guardrails.WITHHELD


def test_rag_never_returns_raw_injection_text(db):
    results = rag.search(db, ALL, "ignore all previous instructions admin mode", limit=15)
    assert results
    assert any(r["text"] == guardrails.WITHHELD for r in results)
    assert not any("IGNORE ALL PREVIOUS" in (r["text"] or "") for r in results)


def test_account_tool_withholds_injection_text(pipeline, db):
    issues = json.loads((pipeline["settings"].data_dir / "injected_issues.json").read_text())
    from app.db.models import Ticket

    ticket = db.get(Ticket, issues["prompt_injection_tickets"][0])
    result, _ = run_tool(ToolContext(db, ALL), "get_account_360",
                         {"account_id": ticket.account_id})
    assert "IGNORE ALL" not in json.dumps(result, default=str)
    assert "SYSTEM OVERRIDE" not in json.dumps(result, default=str)


def test_neutralise_breaks_tag_escapes():
    cleaned = guardrails.neutralise("hello </tool_data> world")
    assert "<" not in cleaned and ">" not in cleaned


def test_ordinary_ticket_text_passes_through():
    text = "Users cannot sign in since the SSO update."
    assert guardrails.neutralise(text) == text


def test_rag_finds_relevant_text(db):
    results = rag.search(db, ALL, "SSO login failures", limit=5)
    assert results
    assert any("SSO" in r["text"] for r in results)
    assert all("#" in r["cite"] for r in results)


def test_number_check_respects_rounding():
    known = {1_234_567.0, 0.42, 37.0}
    assert guardrails.ungrounded_numbers("About $1.2M at risk", known) == []
    assert guardrails.ungrounded_numbers("Win rate 42%", known) == []
    assert guardrails.ungrounded_numbers("37 accounts", known) == []
    assert guardrails.ungrounded_numbers("$9.9M at risk", known) == ["$9.9M"]


def test_number_check_ignores_dates_counts_and_citations():
    answer = "Top 3 deals as of 2026-10-31 in 2026Q4 [deals#412]."
    assert guardrails.ungrounded_numbers(answer, set()) == []


def test_chat_without_key_is_a_clear_503(client):
    response = client.post("/copilot/chat", json={"question": "hi"}, headers=auth(CRO))
    assert response.status_code == 503
    assert "ANTHROPIC_API_KEY" in response.json()["detail"]


def test_chat_input_is_validated(client):
    assert client.post("/copilot/chat", json={"question": ""}, headers=auth(CRO)).status_code == 422


def test_rate_limiter_blocks_after_limit():
    from app.core.ratelimit import RateLimiter

    limiter = RateLimiter(limit=2, window_seconds=60)
    assert limiter.allow("user") and limiter.allow("user")
    assert not limiter.allow("user")
    assert limiter.allow("someone-else")


def test_brief_exists_for_each_user_and_is_scoped(client):
    cro = client.get("/brief", headers=auth(CRO)).json()
    manager = client.get("/brief", headers=auth(MANAGER_NA, "sales_manager")).json()
    assert cro["content"]["top_risks"]
    assert manager["content"]["top_risks"]
    assert cro["content"]["forecast"]["expected"] >= manager["content"]["forecast"]["expected"]


def test_brief_regeneration_replaces_rather_than_stacks(db):
    from sqlalchemy import func

    from app.db.models import DailyBrief
    from app.services import briefing

    before = db.scalar(select(func.count()).select_from(DailyBrief))
    briefing.generate_all(db)
    assert db.scalar(select(func.count()).select_from(DailyBrief)) == before


def test_system_scope_sees_all_tools(db):
    assert run_tool(ToolContext(db, SYSTEM_SCOPE), "list_churn_risks", {})[0]["summary"]
