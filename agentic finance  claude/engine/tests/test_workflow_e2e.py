"""Integration: upload -> agents -> checks -> review -> correction -> recalculation -> approval -> exports."""

from __future__ import annotations

import io
from decimal import Decimal

import pytest
from openpyxl import load_workbook
from pypdf import PdfReader

from tests.conftest import drain, new_company, upload

pytestmark = pytest.mark.integration


def _spread(client, h, company_id, scope="standalone"):
    c = client.get(f"/api/companies/{company_id}", headers=h).json()
    return next(s for s in c["spreads"] if s["scope"] == scope)


def _cell(grid, st, code, period):
    row = next(r for r in grid["statements"][st] if r["canonical_code"] == code and period in r["cells"] and r["cells"][period]["preferred"])
    return row["cells"][period]


def test_full_workflow_clean_pdf(client, analyst, reviewer, workspace_id):
    cid = new_company(client, analyst, workspace_id, "Aravalli Polymers Limited (e2e)")
    up = upload(client, analyst, cid, "01_aravalli_fy25_standalone.pdf")
    drain()
    doc = client.get(f"/api/documents/{up['document_version_id']}", headers=analyst).json()
    assert doc["status"] == "ready_for_review", doc["runs"][0]
    assert doc["runs"][0]["mode"] == "demo"
    assert {s["type"] for s in doc["statements"]} == {"balance_sheet", "income_statement", "cash_flow"}

    sp = _spread(client, analyst, cid)
    grid = client.get(f"/api/spreads/{sp['id']}/grid", headers=analyst).json()
    assert grid["periods"] == ["2025-03-31", "2024-03-31"]
    ta = _cell(grid, "balance_sheet", "bs.total_assets", "2025-03-31")
    assert ta["display"] == "2670.70" and isinstance(ta["display"], str)  # decimal strings, not floats
    ev = client.get(f"/api/observations/{ta['observation_id']}", headers=analyst).json()
    assert ev["source"]["page"] == 2 and len(ev["source"]["bbox"]) == 4
    assert ev["observation"]["raw_text"] == "2,670.70"
    assert ev["observation"]["normalized_value"] == "26707000000"

    vals = client.get(f"/api/spreads/{sp['id']}/validations", headers=analyst).json()["results"]
    by = {(v["rule_id"], v["period_end"]): v for v in vals if v["rule_id"] != "R04"}
    for rid in ("R01", "R02", "R06", "R07", "R08", "R09"):
        assert by[(rid, "2025-03-31")]["status"] == "pass", by[(rid, "2025-03-31")]
    assert by[("R05", "2025-03-31")]["status"] == "not_applicable"
    assert by[("R03", "2025-03-31")]["status"] == "not_applicable"
    assert all(v["status"] == "pass" for v in vals if v["rule_id"] == "R04")

    # Correct a figure -> recalculation -> new version -> check now fails
    inv = _cell(grid, "balance_sheet", "bs.inventories", "2025-03-31")
    r = client.post(f"/api/spreads/{sp['id']}/actions", headers=analyst,
                    json={"action": "correct_value", "observation_id": inv["observation_id"], "value": "422.80", "reason": "test correction"})
    assert r.status_code == 200, r.text
    v2 = r.json()["version"]
    assert v2 == sp["version"] + 1
    vals2 = client.get(f"/api/spreads/{sp['id']}/validations", headers=analyst).json()["results"]
    r04 = [v for v in vals2 if v["rule_id"] == "R04" and v["period_end"] == "2025-03-31" and "current assets" in v["title"].lower()
           and "non" not in v["title"].lower()][0]
    assert r04["status"] == "fail" and Decimal(r04["difference"]) == Decimal("-100000000")
    ev2 = client.get(f"/api/observations/{inv['observation_id']}", headers=analyst).json()
    assert ev2["observation"]["raw_text"] == "412.80"  # original kept
    assert ev2["observation"]["current_value"] == "4228000000"
    assert ev2["adjustments"][0]["before"]["value_units"] == "4128000000"

    # Revert the correction, submit, try self-approval (blocked), approve as reviewer
    r = client.post(f"/api/spreads/{sp['id']}/actions", headers=analyst,
                    json={"action": "correct_value", "observation_id": inv["observation_id"], "value": "412.80", "reason": "revert"})
    v3 = r.json()["version"]
    assert client.post(f"/api/spreads/{sp['id']}/submit", headers=analyst, json={}).status_code == 200
    assert client.post(f"/api/spreads/{sp['id']}/approve", headers=analyst, json={"version": v3}).status_code == 403
    r = client.post(f"/api/spreads/{sp['id']}/approve", headers=reviewer, json={"version": v3, "comment": "ok"})
    assert r.status_code == 200, r.text
    snap_id = r.json()["snapshot_id"]

    # Exports match the approved snapshot
    snap = client.get(f"/api/exports/{snap_id}", headers=reviewer).json()
    assert snap["status"] == "approved" and snap["version"] == v3
    x = client.get(f"/api/exports/{snap_id}/download/xlsx", headers=reviewer)
    assert x.status_code == 200 and x.headers["x-snapshot-hash"] == snap["hash"]
    wb = load_workbook(io.BytesIO(x.content))
    assert snap["hash"] in wb["Read Me"]["A6"].value
    bs = wb["Balance Sheet"]
    rows = {bs.cell(row=i, column=2).value: bs.cell(row=i, column=4).value for i in range(2, bs.max_row + 1)}
    line = next(l for l in snap["snapshot"]["statements"]["balance_sheet"]["lines"] if l["code"] == "bs.total_assets")
    assert Decimal(str(rows["bs.total_assets"])) == Decimal(line["cells"]["2025-03-31"]["value"])
    pdf = client.get(f"/api/exports/{snap_id}/download/pdf", headers=reviewer)
    text = "".join(p.extract_text() for p in PdfReader(io.BytesIO(pdf.content)).pages)
    assert "APPROVED" in text and snap["hash"][:16] in text and "DRAFT" not in text.split("APPROVED")[0][:50]

    # A later correction invalidates the approval and marks the export stale
    r = client.post(f"/api/spreads/{sp['id']}/actions", headers=analyst,
                    json={"action": "correct_value", "observation_id": inv["observation_id"], "value": "412.90", "reason": "after approval"})
    assert r.status_code == 409  # approved versions are locked until reopened
    assert client.post(f"/api/spreads/{sp['id']}/reopen", headers=reviewer, json={"comment": "recheck"}).status_code == 200
    r = client.post(f"/api/spreads/{sp['id']}/actions", headers=analyst,
                    json={"action": "correct_value", "observation_id": inv["observation_id"], "value": "412.90", "reason": "after reopen"})
    assert r.status_code == 200
    detail = client.get(f"/api/spreads/{sp['id']}", headers=analyst).json()
    assert detail["review_status"] in ("reopened", "in_preparation")
    assert all(d["stale"] for d in detail["decisions"] if d["decision"] == "approve")
    exports = client.get(f"/api/spreads/{sp['id']}/exports", headers=analyst).json()
    assert next(e for e in exports if e["id"] == snap_id)["stale"] is True

    # Draft export is labelled unreviewed and includes unresolved exceptions sheet
    d = client.post(f"/api/spreads/{sp['id']}/exports", headers=analyst).json()
    assert d["status"] == "draft" and d["render_status"] == "ok"
    x = client.get(f"/api/exports/{d['id']}/download/xlsx", headers=analyst)
    wb = load_workbook(io.BytesIO(x.content))
    assert "UNREVIEWED DRAFT" in wb["Read Me"]["A2"].value
    assert "Unresolved Exceptions" in wb.sheetnames
    pdf = client.get(f"/api/exports/{d['id']}/download/pdf", headers=analyst)
    assert "UNREVIEWED DRAFT" in "".join(p.extract_text() for p in PdfReader(io.BytesIO(pdf.content)).pages)

    trace = client.get(f"/api/runs/{up['run_id']}", headers=analyst).json()
    agents = [e["agent"] for e in trace["agent_executions"]]
    for a in ("document_understanding", "table_extraction", "financial_mapping", "reconciliation"):
        assert a in agents
    assert all(e["mode"] == "demo" for e in trace["agent_executions"])
    assert any(t["tool"] == "extract_document" for e in trace["agent_executions"] for t in e["tools"])
