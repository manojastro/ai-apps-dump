"""Phase 7: authentication, roles and team scoping enforced in the backend."""
from __future__ import annotations

import logging

import jwt
from sqlalchemy import select

from app.copilot.tools import ToolContext, run_tool
from app.core.logging import JsonFormatter, redact
from app.db.models import Deal, Ticket, User
from app.services.scope import Scope
from tests.conftest import ADMIN, CRO, CSM_NA, MANAGER_EMEA, MANAGER_NA, REVOPS, TEST_PASSWORD, auth

NA_MANAGER = auth(MANAGER_NA, "sales_manager")
EMEA_MANAGER = auth(MANAGER_EMEA, "sales_manager")


def _owned_deal(db, team_id: int, open_only: bool = True) -> Deal:
    query = select(Deal).join(User, Deal.owner_id == User.id).where(User.team_id == team_id)
    if open_only:
        query = query.where(Deal.outcome.is_(None))
    return db.scalars(query).first()


def test_login_succeeds_and_sets_http_only_cookie(client):
    response = client.post("/auth/login", json={
        "email": "cro@revenueos.example", "password": TEST_PASSWORD,
    })
    assert response.status_code == 200
    assert response.json()["user"]["role"] == "cro"
    assert "httponly" in response.headers["set-cookie"].lower()
    client.cookies.clear()


def test_login_rejects_wrong_password(client):
    response = client.post("/auth/login", json={
        "email": "cro@revenueos.example", "password": "wrong",
    })
    assert response.status_code == 401
    assert "password_hash" not in response.text


def test_login_gives_same_error_for_unknown_user(client):
    known = client.post("/auth/login", json={"email": "cro@revenueos.example", "password": "x"})
    unknown = client.post("/auth/login", json={"email": "ghost@example.com", "password": "x"})
    assert known.status_code == unknown.status_code
    assert known.json() == unknown.json()


def test_forged_token_is_rejected(client):
    forged = jwt.encode({"sub": str(CRO), "role": "cro"}, "not-the-secret", algorithm="HS256")
    response = client.get("/deals", headers={"Authorization": f"Bearer {forged}"})
    assert response.status_code == 401


def test_role_claim_in_token_cannot_grant_extra_access(client):
    """Role and team come from the database, not from the token."""
    response = client.get("/admin/audit", headers=auth(MANAGER_NA, "admin"))
    assert response.status_code == 403


def test_manager_list_contains_only_own_team(client, db):
    items = client.get("/deals?page_size=100", headers=NA_MANAGER).json()["items"]
    assert items
    assert {d["team_id"] for d in items} == {1}


def test_manager_cannot_open_another_teams_deal(client, db):
    other = _owned_deal(db, team_id=2)
    assert client.get(f"/deals/{other.id}/explain", headers=NA_MANAGER).status_code == 404
    assert client.get(f"/deals/{other.id}/explain", headers=EMEA_MANAGER).status_code == 200


def test_manager_cannot_widen_scope_with_team_filter(client):
    items = client.get("/deals?team_id=2&page_size=100", headers=NA_MANAGER).json()["items"]
    assert items
    assert {d["team_id"] for d in items} == {1}


def test_manager_cannot_open_another_teams_account(client, db):
    other = _owned_deal(db, team_id=2)
    response = client.get(f"/accounts/{other.account_id}/360", headers=NA_MANAGER)
    assert response.status_code == 404


def test_manager_forecast_is_limited_to_own_team(client):
    full = client.get("/forecast", headers=auth(CRO)).json()
    own = client.get("/forecast", headers=NA_MANAGER).json()
    widened = client.get("/forecast?team_id=2", headers=NA_MANAGER).json()
    assert own["open_deals"] < full["open_deals"]
    assert widened["open_deals"] == own["open_deals"]
    assert [t["team"] for t in own["by_team"]] == ["North America"]


def test_csm_is_scoped_like_a_manager(client):
    items = client.get("/accounts?page_size=100", headers=auth(CSM_NA, "csm")).json()["items"]
    assert items
    assert {a["region"] for a in items} == {"NA"}


def test_retention_is_scoped(client):
    full = client.get("/churn/summary", headers=auth(CRO)).json()
    own = client.get("/churn/summary", headers=NA_MANAGER).json()
    assert own["scored_accounts"] < full["scored_accounts"]


def test_citation_lookup_is_scoped(client, db):
    other = _owned_deal(db, team_id=2)
    assert client.get(f"/sources/deals/{other.id}", headers=NA_MANAGER).status_code == 404
    assert client.get(f"/sources/deals/{other.id}", headers=EMEA_MANAGER).status_code == 200
    ticket = db.scalars(select(Ticket).where(Ticket.account_id == other.account_id)).first()
    if ticket:
        path = f"/sources/tickets/{ticket.id}"
        assert client.get(path, headers=NA_MANAGER).status_code == 404


def test_source_lookup_never_exposes_password_hash(client):
    response = client.get("/sources/users/1", headers=auth(CRO))
    assert response.status_code == 404


def test_copilot_tools_inherit_team_scope(db):
    other = _owned_deal(db, team_id=2)
    manager = Scope(user_id=MANAGER_NA, role="sales_manager", team_id=1)
    context = ToolContext(db, manager)
    result, _ = run_tool(context, "explain_deal", {"deal_id": other.id})
    assert result == {"error": "not_found_or_not_permitted"}
    result, _ = run_tool(context, "get_account_360", {"account_id": other.account_id})
    assert result == {"error": "not_found_or_not_permitted"}
    deals, _ = run_tool(context, "list_at_risk_deals", {"limit": 25})
    assert {d["team_id"] for d in deals["deals"]} == {1}


def test_copilot_search_inherits_team_scope(db):
    manager = Scope(user_id=MANAGER_NA, role="sales_manager", team_id=1)
    results, _ = run_tool(ToolContext(db, manager), "search_tickets_and_notes",
                          {"query": "SSO login", "limit": 15})
    from app.db.models import Account

    ids = {r["account_id"] for r in results["results"]}
    assert ids
    regions = set(db.scalars(select(Account.region).where(Account.id.in_(ids))))
    assert regions == {"NA"}


def test_admin_pages_require_admin_role(client):
    assert client.get("/admin/audit", headers=NA_MANAGER).status_code == 403
    assert client.get("/admin/audit", headers=auth(REVOPS, "revops")).status_code == 403
    assert client.get("/admin/models", headers=NA_MANAGER).status_code == 403
    assert client.get("/admin/data-quality", headers=auth(CSM_NA, "csm")).status_code == 403


def test_admin_can_view_models_and_data_health(client):
    headers = auth(ADMIN, "admin")
    models = client.get("/admin/models", headers=headers).json()
    assert {m["model_name"] for m in models} == {"win_probability", "churn_90d"}
    assert all(m["trained_at"] for m in models)
    health = client.get("/admin/data-quality", headers=headers).json()
    assert health["summary"]["duplicate_groups"] == 6
    assert health["load_rejects"] == 25
    assert client.get("/admin/audit", headers=headers).status_code == 200


def test_logs_redact_secrets_and_emails():
    assert "person@acme.com" not in redact("user person@acme.com logged in")
    assert "sk-ant-abc123" not in redact("key sk-ant-abc123")
    record = logging.LogRecord("x", logging.INFO, "f", 1, "bearer abc.def.ghi", None, None)
    assert "abc.def.ghi" not in JsonFormatter().format(record)
