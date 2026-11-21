"""HTTP API tests: authentication, CSRF, authorisation, imports, investigations, approvals, assistant, evaluation."""

from __future__ import annotations

import json

from tests.conftest import DEMO_PASSWORD, login


def test_health(client) -> None:
    assert client.get("/api/health").json()["status"] == "ok"
    assert client.get("/api/health/ready").json()["status"] == "ready"


def test_login_failure_and_audit(client, admin_h) -> None:
    from app.api.routes_auth import login_limiter

    login_limiter.reset()
    r = client.post("/api/auth/login", json={"email": "analyst@northstar.example", "password": "wrong"})
    assert r.status_code == 401
    events = client.get("/api/audit?action=login_failed", headers=admin_h).json()
    assert events["total"] >= 1


def test_login_rate_limit(client) -> None:
    from app.api.routes_auth import login_limiter

    login_limiter.reset()
    codes = [
        client.post("/api/auth/login", json={"email": "x@northstar.example", "password": "bad"}).status_code for _ in range(12)
    ]
    assert 429 in codes
    login_limiter.reset()


def test_unauthenticated_requests_rejected(client) -> None:
    client.cookies.clear()
    assert client.get("/api/dashboard").status_code == 401
    assert client.get("/api/dashboard", headers={"Authorization": "Bearer not-a-token"}).status_code == 401


def test_cookie_session_requires_csrf_header_for_writes(client) -> None:
    from app.api.routes_auth import login_limiter

    login_limiter.reset()
    r = client.post("/api/auth/login", json={"email": "analyst@northstar.example", "password": DEMO_PASSWORD})
    assert "token" not in r.json() and "aegis_session" in r.cookies
    assert client.get("/api/auth/me").status_code == 200  # cookie auth works for reads
    fid = client.get("/api/findings?page_size=1").json()["items"][0]["id"]
    assert client.post(f"/api/findings/{fid}/reassess").status_code == 403
    assert client.post(f"/api/findings/{fid}/reassess", headers={"X-Requested-With": "aegis"}).status_code == 200
    client.cookies.clear()


def test_role_enforcement(client, viewer_h, approver_h) -> None:
    fid = client.get("/api/findings?page_size=1", headers=viewer_h).json()["items"][0]["id"]
    assert client.post(f"/api/findings/{fid}/investigate", headers=viewer_h).status_code == 403
    assert client.post(f"/api/findings/{fid}/investigate", headers=approver_h).status_code == 403
    assert client.put("/api/settings/risk-policy", json={}, headers=viewer_h).status_code == 403
    assert client.get("/api/audit", headers=viewer_h).status_code == 403


def test_dashboard_is_data_driven(client, analyst_h) -> None:
    d = client.get("/api/dashboard", headers=analyst_h).json()
    k = d["kpis"]
    assert k["open_findings"] > 0 and k["pending_approvals"] >= 2 and k["verified_remediations"] >= 1
    assert sum(b["count"] for b in d["risk_distribution"]) == k["open_findings"]
    assert {s["priority"] for s in d["sla_exposure"]} == {"P1", "P2", "P3", "P4"}


def test_vulnerability_listing_filters_and_export(client, analyst_h) -> None:
    page = client.get("/api/vulnerabilities?page_size=50", headers=analyst_h).json()
    assert page["total"] == 20
    scores = [r["max_risk_score"] for r in page["items"] if r["max_risk_score"] is not None]
    assert scores == sorted(scores, reverse=True)
    kev = client.get("/api/vulnerabilities?kev=true&page_size=50", headers=analyst_h).json()
    assert kev["total"] == 12 and all(r["kev"] for r in kev["items"])
    csv_text = client.get("/api/vulnerabilities/export.csv", headers=analyst_h).text
    assert csv_text.splitlines()[0].startswith("cve_id,severity") and len(csv_text.splitlines()) == 21


def test_csv_import_with_duplicates_and_invalid_rows(client, analyst_h) -> None:
    csv_body = (
        "hostname,cve,severity,software,version,ip\n"
        "pay-api-01.fin.northstar.example,CVE-2023-38545,High,libcurl,8.2.1,10.10.1.10\n"
        "pay-api-01.fin.northstar.example,CVE-2023-38545,High,libcurl,8.2.1,10.10.1.10\n"
        "pay-api-01.fin.northstar.example,NOT-A-CVE,High,libcurl,8.2.1,10.10.1.10\n"
        ",CVE-2023-38545,High,libcurl,8.2.1,\n"
    )
    files = {"file": ("scan.csv", csv_body, "text/csv")}
    r = client.post("/api/findings/import", files=files, data={"scanner": "nessus_export"}, headers=analyst_h)
    assert r.status_code == 200, r.text
    body = r.json()
    assert (body["created"], body["duplicates"], body["invalid"]) == (1, 1, 2)
    again = client.post("/api/findings/import", files=files, data={"scanner": "nessus_export"}, headers=analyst_h).json()
    assert again["created"] == 0 and again["duplicates"] == 2


def test_json_import_rejects_garbage(client, analyst_h) -> None:
    r = client.post("/api/findings/import", files={"file": ("x.json", "{not json", "application/json")}, headers=analyst_h)
    assert r.status_code == 400


def test_investigation_and_approval_over_http(client, analyst_h, approver_h, viewer_h) -> None:
    items = client.get("/api/findings?q=collab-wiki-stg-01&page_size=5", headers=analyst_h).json()["items"]
    fid = items[0]["id"]
    r = client.post(f"/api/findings/{fid}/investigate", headers=analyst_h)
    assert r.status_code == 202
    run_id = r.json()["workflow_run_id"]
    assert client.post(f"/api/findings/{fid}/investigate", headers=analyst_h).status_code == 409
    wf = client.get(f"/api/workflows/{run_id}", headers=analyst_h).json()
    assert wf["run"]["status"] == "waiting_approval"
    assert wf["node_states"]["calculate_risk"]["status"] == "completed"
    assert wf["pending_interrupt"]["value"]["type"] == "approval"
    events = client.get(f"/api/workflows/{run_id}/events?after=0", headers=analyst_h).json()["events"]
    assert any(e["event_type"] == "agent_completed" for e in events)
    plan_id = wf["run"]["plan_id"]

    # material edit -> new revision, validation re-run
    edit = client.patch(
        f"/api/plans/{plan_id}",
        headers=analyst_h,
        json={"maintenance_window": "Saturday 02:00-04:00 UTC", "edit_reason": "Agreed with owner"},
    ).json()
    assert edit["changed"] and edit["plan"]["revision"] == 2

    req = client.post(f"/api/plans/{plan_id}/request-approval", json={"comment": "please"}, headers=analyst_h).json()
    assert req["state"] == "PENDING"
    assert (
        client.post(
            f"/api/approvals/{req['id']}/decision", json={"decision": "approve", "confirm": True}, headers=viewer_h
        ).status_code
        == 403
    )
    assert (
        client.post(
            f"/api/approvals/{req['id']}/decision", json={"decision": "approve", "confirm": False}, headers=approver_h
        ).status_code
        == 422
    )
    ok = client.post(
        f"/api/approvals/{req['id']}/decision", json={"decision": "approve", "comment": "ok", "confirm": True}, headers=approver_h
    )
    assert ok.status_code == 200 and ok.json()["state"] == "APPROVED"
    plan = client.get(f"/api/plans/{plan_id}", headers=analyst_h).json()
    assert {r["table_name"] for r in plan["servicenow_records"]} == {"change_request", "change_task"}
    assert plan["plan"]["lifecycle_stage"] == "SYNCED"
    # Editing an already-synchronised plan is refused.
    r = client.patch(f"/api/plans/{plan_id}", headers=analyst_h, json={"summary": "changed", "edit_reason": "late change"})
    assert r.status_code == 409
    export = client.get(f"/api/plans/{plan_id}/export", headers=analyst_h)
    assert export.status_code == 200 and "Proposal only" in export.text


def test_sse_stream_emits_events(client, analyst_h) -> None:
    run = client.get("/api/workflows?status=rejected", headers=analyst_h).json()["items"][0]
    with client.stream("GET", f"/api/workflows/{run['id']}/stream", headers=analyst_h) as resp:
        assert resp.headers["content-type"].startswith("text/event-stream")
        body = "".join(resp.iter_text())
    assert "event: workflow" in body and "agent_completed" in body


def test_simulation_controls_and_servicenow_views(client, analyst_h, viewer_h) -> None:
    assert (
        client.post("/api/simulation/servicenow/failure", json={"mode": "timeout", "remaining": 1}, headers=viewer_h).status_code
        == 403
    )
    assert (
        client.post("/api/simulation/servicenow/failure", json={"mode": "none", "remaining": 0}, headers=analyst_h).status_code
        == 200
    )
    status = client.get("/api/servicenow/status", headers=analyst_h).json()
    assert status["mode"] == "mock" and "change_request" in status["write_allowlist"]
    assert client.post("/api/servicenow/test-connection", headers=analyst_h).json()["ok"]
    records = client.get("/api/servicenow/records", headers=analyst_h).json()
    assert records["total"] >= 10
    activity = client.get(f"/api/servicenow/records/{records['items'][0]['id']}/activity", headers=analyst_h).json()
    assert activity["remote_activity"]


def test_integrations_report_honest_status(client, analyst_h) -> None:
    items = {i["key"]: i for i in client.get("/api/integrations", headers=analyst_h).json()["integrations"]}
    assert items["servicenow"]["status"] == "Mock"
    assert items["defender"]["status"] == "Not Configured"
    assert items["tenable"]["status"] == "Unsupported" and items["qualys"]["status"] == "Unsupported"


def test_risk_policy_update_and_audit(client, admin_h) -> None:
    current = client.get("/api/settings", headers=admin_h).json()["risk_policy"]
    bad = {**current, "weights": {**current["weights"], "cvss": 90}}
    assert client.put("/api/settings/risk-policy", json=bad, headers=admin_h).status_code == 422
    good = {k: v for k, v in current.items() if k != "policy_version"}
    r = client.put("/api/settings/risk-policy", json=good, headers=admin_h)
    assert r.status_code == 200 and r.json()["version"] == current["version"] + 1


def test_assistant_answers_with_evidence(client, analyst_h) -> None:
    r = client.post(
        "/api/assistant/chat", json={"message": "Why was CVE-2021-44228 assigned a risk score of 100?"}, headers=analyst_h
    ).json()
    assert "deterministic" in r["answer"] and r["facts"] and r["tool_calls"]
    r = client.post(
        "/api/assistant/chat", json={"message": "Prepare a remediation plan for CVE-2024-6387"}, headers=analyst_h
    ).json()
    assert r["proposed_actions"][0]["type"] == "start_investigation" and r["proposed_actions"][0]["requires_confirmation"]


def test_evaluation_run_is_persisted(client, analyst_h) -> None:
    r = client.post("/api/evaluation/run", json={"provider": "mock"}, headers=analyst_h).json()
    assert r["total"] == 46 and r["metrics"]["unsafe_action_prevention"] == 1.0
    detail = client.get(f"/api/evaluation/runs/{r['id']}", headers=analyst_h).json()
    assert len(detail["cases"]) == 46
    failed = {c["case_id"] for c in detail["cases"] if not c["passed"]}
    assert failed <= {"risk-03", "risk-04"}  # documented policy-calibration disagreements


def test_audit_log_has_approval_trail(client, admin_h) -> None:
    page = client.get("/api/audit?action=approval_approve,servicenow_record_created&page_size=100", headers=admin_h).json()
    actions = {e["action"] for e in page["items"]}
    assert {"approval_approve", "servicenow_record_created"} <= actions
    assert all("password" not in json.dumps(e) for e in page["items"])


def test_login_helper_roles(client) -> None:
    me = client.get("/api/auth/me", headers=login(client, "approver@northstar.example")).json()["user"]
    assert me["role"] == "approver" and "approval:decide" in me["permissions"]
