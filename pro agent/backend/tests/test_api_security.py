"""API authentication, CSRF, roles, idempotency, and tenant isolation (security gate)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text

from procnav.api.app import create_app
from procnav.core.db import app_engine, global_session, tenant_session
from procnav.core.models import AuditEvent, EvidenceArtifact, ProcurementRun, Tenant
from procnav.evidence import store

PW = "procnav-demo"


def client() -> TestClient:
    return TestClient(create_app())


def login(c: TestClient, email: str) -> dict:
    r = c.post("/api/auth/login", json={"email": email, "password": PW})
    assert r.status_code == 200, r.text
    c.headers["X-CSRF-Token"] = r.json()["csrf_token"]
    return r.json()


def new_request_body(**over):
    body = {
        "title": "Ten laptops (api test)",
        "canonical_product_id": "NW-PRO14-16-512",
        "min_ram_gb": 16,
        "min_ssd_gb": 512,
        "quantity": 10,
        "currency": "INR",
        "budget_total": "500000.00",
        "address_ref": "ADDR-BLR-01",
        "delivery_deadline": (datetime.now(UTC) + timedelta(days=7)).date().isoformat(),
    }
    body.update(over)
    return body


@pytest.fixture(scope="module")
def acme_evidence():
    with global_session() as s:
        tid = s.scalar(select(Tenant.id).where(Tenant.slug == "acme"))
    with tenant_session(tid) as db:
        run = db.scalars(select(ProcurementRun).limit(1)).first()
        art = store.save(
            db,
            tenant_id=tid,
            run_id=run.id if run else None,
            kind="page_text",
            label="security probe",
            data=b"acme-only evidence",
            content_type="text/plain",
            ext="txt",
        )
        return {"tenant_id": tid, "evidence_id": str(art.id), "run_id": str(run.id) if run else None}


def test_login_rejects_bad_password_and_requires_session():
    c = client()
    assert (
        c.post("/api/auth/login", json={"email": "requester@acme.test", "password": "wrong"}).json()["error"]["code"]
        == "AUTH_INVALID"
    )
    assert c.get("/api/runs").json()["error"]["code"] == "AUTH_REQUIRED"


def test_csrf_required_for_cookie_mutations():
    c = client()
    login(c, "requester@acme.test")
    token = c.headers.pop("X-CSRF-Token")
    r = c.post("/api/requests", json=new_request_body())
    assert r.status_code == 403 and r.json()["error"]["code"] == "CSRF_FAILED"
    c.headers["X-CSRF-Token"] = token
    assert c.post("/api/requests", json=new_request_body()).status_code == 201


def test_roles_are_server_side_and_client_role_claims_ignored():
    c = client()
    login(c, "viewer@acme.test")
    r = c.post("/api/requests", json=new_request_body(), headers={"X-Role": "requester"})
    assert r.status_code == 403 and r.json()["error"]["code"] == "FORBIDDEN_ROLE"
    r = c.post(
        "/api/approvals/" + str(uuid.uuid4()) + "/decision",
        json={"decision": "approved", "reason": "nope", "acknowledged_fingerprint": "0" * 64},
    )
    assert r.status_code == 403
    c2 = client()
    login(c2, "requester@acme.test")
    assert c2.post("/api/admin/fixtures/reset", json={"scenario": "happy_path"}).status_code == 403


def test_request_creation_is_idempotent():
    c = client()
    login(c, "requester@acme.test")
    key = f"idem-{uuid.uuid4()}"
    a = c.post("/api/requests", json=new_request_body(), headers={"Idempotency-Key": key})
    b = c.post("/api/requests", json=new_request_body(), headers={"Idempotency-Key": key})
    assert a.status_code == b.status_code == 201 and a.json()["id"] == b.json()["id"]
    conflict = c.post("/api/requests", json=new_request_body(quantity=11), headers={"Idempotency-Key": key})
    assert conflict.status_code == 409 and conflict.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"


def test_validation_errors_use_stable_envelope():
    c = client()
    login(c, "requester@acme.test")
    r = c.post("/api/requests", json=new_request_body(quantity=0, address_ref="ADDR-NOPE"))
    assert r.status_code == 422 and r.json()["error"]["code"] == "VALIDATION_FAILED"
    r = c.post("/api/requests", json=new_request_body(address_ref="ADDR-NOPE"))
    assert r.json()["error"]["code"] == "REQUEST_INCOMPLETE"


def test_cross_tenant_evidence_and_runs_are_invisible(acme_evidence):
    own = client()
    login(own, "requester@acme.test")
    assert own.get(f"/api/evidence/{acme_evidence['evidence_id']}").content == b"acme-only evidence"
    other = client()
    login(other, "approver@globex.test")
    r = other.get(f"/api/evidence/{acme_evidence['evidence_id']}")
    assert r.status_code == 404 and r.json()["error"]["code"] == "NOT_FOUND"
    if acme_evidence["run_id"]:
        assert other.get(f"/api/runs/{acme_evidence['run_id']}").status_code == 404
        assert other.get(f"/api/runs/{acme_evidence['run_id']}/comparison").status_code == 404
    # Supplying another tenant's ID anywhere in input changes nothing: tenant comes from the session.
    r = other.get(f"/api/audit?run_id={acme_evidence['run_id']}") if acme_evidence["run_id"] else None
    if r is not None:
        assert r.json()["items"] == []


def test_database_rls_blocks_cross_tenant_reads_even_without_app_filters(acme_evidence):
    with global_session() as s:
        globex = s.scalar(select(Tenant.id).where(Tenant.slug == "globex"))
    with app_engine().connect() as conn:
        conn.execute(text("SELECT set_config('app.tenant_id', :t, false)"), {"t": str(globex)})
        n = conn.execute(
            text("SELECT count(*) FROM evidence_artifacts WHERE id = :i"), {"i": acme_evidence["evidence_id"]}
        ).scalar()
        assert n == 0
        conn.execute(text("SELECT set_config('app.tenant_id', '', false)"))
        assert conn.execute(text("SELECT count(*) FROM evidence_artifacts")).scalar() == 0
        conn.rollback()


def test_audit_events_are_append_only():
    with global_session() as s:
        tid = s.scalar(select(Tenant.id).where(Tenant.slug == "acme"))
    with pytest.raises(Exception) as exc, tenant_session(tid) as db:
        row = db.scalars(select(AuditEvent).limit(1)).first()
        row.action = "tampered"
        db.flush()
    assert "append-only" in str(exc.value) or "permission denied" in str(exc.value)


def test_order_ledger_rejects_invalid_transition_at_database_level():
    with global_session() as s:
        tid = s.scalar(select(Tenant.id).where(Tenant.slug == "acme"))
    with tenant_session(tid) as db:
        from procnav.core.models import OrderIntent

        intent = db.scalars(select(OrderIntent).where(OrderIntent.status == "reconciled")).first()
        if intent is None:
            pytest.skip("no reconciled intent yet (run the scenario suite first)")
        intent_id = intent.id
    with pytest.raises(Exception) as exc, tenant_session(tid) as db:
        db.execute(text("UPDATE order_intents SET status = 'submitting' WHERE id = :i"), {"i": intent_id})
    assert "invalid order intent transition" in str(exc.value)


def test_evidence_listing_hides_storage_paths(acme_evidence):
    c = client()
    login(c, "requester@acme.test")
    if acme_evidence["run_id"]:
        items = c.get(f"/api/runs/{acme_evidence['run_id']}/evidence").json()["items"]
        assert items and all("storage_path" not in i for i in items)
    _ = EvidenceArtifact
