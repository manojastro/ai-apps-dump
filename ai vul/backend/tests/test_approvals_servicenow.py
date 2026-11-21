"""Approval engine, write gate, ServiceNow adapters (mock + REST via mocked HTTP), concurrency."""

from __future__ import annotations

import threading

import httpx
import pytest
import respx
from pydantic import ValidationError
from sqlalchemy import func, select

from app.approvals import service as approvals
from app.approvals.write_gate import evaluate_write_gate
from app.core.config import get_settings
from app.core.db import SessionLocal
from app.graphs.runner import get_runner
from app.integrations.servicenow.base import ServiceNowAuthError, ServiceNowSchemaError
from app.integrations.servicenow.factory import write_allowlist
from app.integrations.servicenow.mock import MockServiceNowClient, matches_query
from app.integrations.servicenow.rest import RestServiceNowClient
from app.models.remediation import ApprovalDecision, ApprovalRequest, RemediationPlan
from app.models.servicenow import ServiceNowRecord
from app.models.workflow import AuditEvent, WorkflowRun
from app.services.servicenow_sync import ChangeRequestPayload, ServiceNowSyncService
from tests.conftest import finding_id, principal


@pytest.fixture()
def fresh_plan(db):
    """A plan waiting for an approval request, produced by a real investigation."""

    def make(hostname: str, cve: str) -> RemediationPlan:
        analyst = principal(db, "analyst@northstar.example")
        run = get_runner().start(finding_id(db, hostname, cve), analyst.id)
        db.expire_all()
        return db.get(RemediationPlan, db.get(WorkflowRun, run.id).plan_id)

    return make


def test_viewer_and_analyst_cannot_approve(db, fresh_plan) -> None:
    plan = fresh_plan("ledger-app-02", "CVE-2022-22965")
    req = approvals.request_approval(db, plan.id, principal(db, "analyst@northstar.example"))
    db.commit()
    for email in ("viewer@northstar.example", "analyst2@northstar.example"):
        with pytest.raises(approvals.ApprovalForbidden):
            approvals.decide(db, req.id, principal(db, email), "approve")
    db.expire_all()
    denied = db.scalars(select(ApprovalDecision).where(ApprovalDecision.approval_request_id == req.id)).all()
    assert len(denied) == 2 and all(d.outcome == "denied" for d in denied)
    assert db.get(ApprovalRequest, req.id).state == "PENDING"
    assert (
        db.scalar(
            select(func.count()).select_from(AuditEvent).where(AuditEvent.target_id == req.id, AuditEvent.outcome == "denied")
        )
        >= 2
    )


def test_separation_of_duties_blocks_self_approval(db, fresh_plan) -> None:
    admin = principal(db, "admin@northstar.example")
    plan = fresh_plan("mes-app-02", "CVE-2022-22965")
    req = approvals.request_approval(db, plan.id, admin)  # admin may request and (normally) approve
    db.commit()
    assert req.risk_level in ("critical", "high")
    with pytest.raises(approvals.ApprovalForbidden, match="separation of duties"):
        approvals.decide(db, req.id, admin, "approve")


def test_comment_required_for_reject_and_double_decision_conflict(db, fresh_plan) -> None:
    plan = fresh_plan("pay-api-stg-01", "CVE-2022-22965")
    approver = principal(db, "approver@northstar.example")
    req = approvals.request_approval(db, plan.id, principal(db, "analyst@northstar.example"))
    db.commit()
    with pytest.raises(approvals.ApprovalInvalid):
        approvals.decide(db, req.id, approver, "reject", "")
    approvals.decide(db, req.id, approver, "approve", "fine")
    db.commit()
    with pytest.raises(approvals.ApprovalConflict):
        approvals.decide(db, req.id, principal(db, "approver2@northstar.example"), "reject", "too late")


def test_duplicate_pending_request_rejected(db, fresh_plan) -> None:
    plan = fresh_plan("store-app-02", "CVE-2023-38545")
    analyst = principal(db, "analyst@northstar.example")
    approvals.request_approval(db, plan.id, analyst)
    db.commit()
    with pytest.raises(approvals.ApprovalConflict):
        approvals.request_approval(db, plan.id, analyst)


def test_material_edit_invalidates_approval_and_gate_denies(db, fresh_plan) -> None:
    plan = fresh_plan("order-svc-02", "CVE-2023-38545")
    analyst = principal(db, "analyst@northstar.example")
    req = approvals.request_approval(db, plan.id, analyst)
    db.commit()
    plan = db.get(RemediationPlan, plan.id)
    plan.rollback_steps = [*plan.rollback_steps, "Tamper after request"]  # change without going through the API
    db.commit()
    with pytest.raises(approvals.ApprovalConflict, match="changed"):
        approvals.decide(db, req.id, principal(db, "approver@northstar.example"), "approve", "x")
    db.expire_all()
    assert db.get(ApprovalRequest, req.id).state == "INVALIDATED"
    assert not evaluate_write_gate(db, req.id, write_allowlist()).allowed


def test_concurrent_approvals_produce_single_decision(seeded_db, fresh_plan, db) -> None:
    plan = fresh_plan("ci-jenkins-02", "CVE-2024-23897")
    req = approvals.request_approval(db, plan.id, principal(db, "analyst@northstar.example"))
    db.commit()
    results: list[str] = []

    def attempt(email: str, decision: str) -> None:
        s = SessionLocal()
        try:
            approvals.decide(s, req.id, principal(s, email), decision, "concurrent")
            s.commit()
            results.append("ok")
        except (approvals.ApprovalConflict, approvals.ApprovalForbidden):
            s.rollback()
            results.append("conflict")
        except Exception as exc:  # SQLite may report a locked database for the loser
            s.rollback()
            results.append(f"error:{type(exc).__name__}")
        finally:
            s.close()

    threads = [
        threading.Thread(target=attempt, args=("approver@northstar.example", "approve")),
        threading.Thread(target=attempt, args=("approver2@northstar.example", "reject")),
    ]
    [t.start() for t in threads]
    [t.join() for t in threads]
    db.expire_all()
    decisions = db.scalars(
        select(ApprovalDecision).where(ApprovalDecision.approval_request_id == req.id, ApprovalDecision.outcome == "accepted")
    ).all()
    assert results.count("ok") == 1 and len(decisions) == 1


def test_gate_denies_real_mode_writes_when_disabled(db, monkeypatch) -> None:
    req = db.scalar(select(ApprovalRequest).where(ApprovalRequest.state == "APPROVED"))
    assert evaluate_write_gate(db, req.id, write_allowlist()).checks["writes_enabled"]
    s = get_settings()
    monkeypatch.setattr(s, "servicenow_mode", "real")
    monkeypatch.setattr(s, "enable_servicenow_writes", False)
    decision = evaluate_write_gate(db, req.id, {"change_request"})
    assert not decision.allowed and not decision.checks["writes_enabled"]


def test_gate_rejects_non_allowlisted_table(db) -> None:
    req = db.scalar(select(ApprovalRequest).where(ApprovalRequest.state == "APPROVED"))
    decision = evaluate_write_gate(db, req.id, {"sys_user"})
    assert not decision.allowed and not decision.checks["table_allowlisted"]


def test_sync_of_pending_or_rejected_approval_is_denied(db) -> None:
    actor = principal(db, "analyst@northstar.example")
    for state in ("PENDING", "REJECTED"):
        req = db.scalar(select(ApprovalRequest).where(ApprovalRequest.state == state))
        before = db.scalar(select(func.count()).select_from(ServiceNowRecord))
        outcome = ServiceNowSyncService(db).sync_approved_plan(req.id, actor)
        assert not outcome.ok and outcome.gate_reasons
        assert db.scalar(select(func.count()).select_from(ServiceNowRecord)) == before


def test_resync_of_synced_approval_is_noop(db) -> None:
    req = db.scalar(
        select(ApprovalRequest)
        .join(ServiceNowRecord, ServiceNowRecord.approval_request_id == ApprovalRequest.id)
        .where(ServiceNowRecord.sync_state == "SYNCED")
    )
    before = db.scalar(select(func.count()).select_from(ServiceNowRecord))
    outcome = ServiceNowSyncService(db).sync_approved_plan(req.id, principal(db, "analyst@northstar.example"))
    # the plan is APPROVED and unchanged, so the gate passes and existing records are reused
    assert outcome.ok and db.scalar(select(func.count()).select_from(ServiceNowRecord)) == before


def test_change_payload_validation() -> None:
    base = dict(
        short_description="x",
        description="d",
        justification="j",
        implementation_plan="i",
        backout_plan="b",
        test_plan="t",
        risk="2",
        impact="1",
        type="normal",
        category="Software",
        correlation_id="k",
        correlation_display="Aegis",
    )
    ChangeRequestPayload(**base)
    with pytest.raises(ValidationError):
        ChangeRequestPayload(**(base | {"risk": "9"}))
    with pytest.raises(ValidationError):
        ChangeRequestPayload(**(base | {"short_description": "x" * 200}))
    with pytest.raises(ValidationError):
        ChangeRequestPayload(**(base | {"type": "rm -rf"}))


def test_mock_client_query_and_unknown_fields(seeded_db) -> None:
    client = MockServiceNowClient()
    rec = client.create("change_request", {"short_description": "unit", "correlation_id": "unit-test-1"})
    assert rec["number"].startswith("CHG") and rec["state"] == "-5"
    assert client.query("change_request", "correlation_id=unit-test-1")[0]["sys_id"] == rec["sys_id"]
    from app.integrations.servicenow.base import ServiceNowServerError

    with pytest.raises(ServiceNowServerError):
        client.create("change_request", {"u_not_a_field": "x"})
    assert matches_query({"a": "1", "b": "xyz"}, "a=1^bLIKEY")
    assert not matches_query({"a": "1"}, "a!=1")


# ------------------------------------------------------------------ real REST adapter against mocked HTTP
@respx.mock
def test_rest_client_oauth_schema_verification_and_create(monkeypatch) -> None:
    s = get_settings()
    monkeypatch.setattr(s, "servicenow_instance_url", "https://dev12345.service-now.com")
    monkeypatch.setattr(s, "servicenow_client_id", "cid")
    monkeypatch.setattr(s, "servicenow_client_secret", type(s.servicenow_client_secret)("secret"))
    base = "https://dev12345.service-now.com"
    respx.post(f"{base}/oauth_token.do").mock(return_value=httpx.Response(200, json={"access_token": "tok", "expires_in": 1800}))
    respx.get(f"{base}/api/now/table/sys_db_object").mock(
        side_effect=[
            httpx.Response(200, json={"result": [{"super_class.name": "task"}]}),
            httpx.Response(200, json={"result": [{"super_class.name": ""}]}),
        ]
    )
    respx.get(f"{base}/api/now/table/sys_dictionary").mock(
        side_effect=[
            httpx.Response(200, json={"result": [{"element": f} for f in ("short_description", "risk", "type")]}),
            httpx.Response(200, json={"result": [{"element": f} for f in ("description", "correlation_id")]}),
        ]
    )
    create = respx.post(f"{base}/api/now/table/change_request").mock(
        return_value=httpx.Response(201, json={"result": {"sys_id": "a" * 32, "number": "CHG0040001", "state": "-5"}})
    )
    client = RestServiceNowClient(s)
    out = client.create("change_request", {"short_description": "x", "correlation_id": "k", "description": "d"})
    assert out["number"] == "CHG0040001"
    assert create.calls.last.request.headers["authorization"] == "Bearer tok"
    with pytest.raises(ServiceNowSchemaError):
        client.create("change_request", {"u_custom": "x"})  # schema cached; unknown field refused before any write
    assert create.call_count == 1
    assert client.record_url("change_request", "a" * 32).startswith(base)


@respx.mock
def test_rest_client_maps_auth_failure(monkeypatch) -> None:
    s = get_settings()
    monkeypatch.setattr(s, "servicenow_instance_url", "https://dev12345.service-now.com")
    monkeypatch.setattr(s, "servicenow_client_id", "")
    monkeypatch.setattr(s, "servicenow_username", "admin")
    monkeypatch.setattr(s, "servicenow_password", type(s.servicenow_password)("pw"))
    respx.get("https://dev12345.service-now.com/api/now/table/change_request").mock(return_value=httpx.Response(401))
    with pytest.raises(ServiceNowAuthError):
        RestServiceNowClient(s).query("change_request", "", ["sys_id"], 1)
    result = RestServiceNowClient(s).test_connection()
    assert result["ok"] is False and "401" in result["detail"]


def test_rest_client_refuses_non_allowlisted_host(monkeypatch) -> None:
    from app.integrations.http import EgressDenied

    s = get_settings()
    monkeypatch.setattr(s, "servicenow_instance_url", "http://169.254.169.254")
    with pytest.raises(EgressDenied):
        RestServiceNowClient(s)
