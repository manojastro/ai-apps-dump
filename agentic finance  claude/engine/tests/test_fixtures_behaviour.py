"""Each synthetic fixture exercises a known behaviour (integration, demo mode)."""

from __future__ import annotations

import io

import pytest
from openpyxl import load_workbook

from tests.conftest import drain, new_company, upload

pytestmark = pytest.mark.integration


def _doc(client, h, dv):
    return client.get(f"/api/documents/{dv}", headers=h).json()


def _spreads(client, h, cid):
    return client.get(f"/api/companies/{cid}", headers=h).json()["spreads"]


def _vals(client, h, sid):
    return client.get(f"/api/spreads/{sid}/validations", headers=h).json()["results"]


def _exc(client, h, sid):
    return client.get(f"/api/spreads/{sid}/exceptions", headers=h).json()


def test_xlsx_lakhs_indian_numbering(client, analyst, workspace_id):
    cid = new_company(client, analyst, workspace_id, "XLSX lakhs co")
    up = upload(client, analyst, cid, "04_aravalli_fy25_lakhs.xlsx")
    drain()
    assert _doc(client, analyst, up["document_version_id"])["status"] == "ready_for_review"
    sp = _spreads(client, analyst, cid)[0]
    grid = client.get(f"/api/spreads/{sp['id']}/grid", headers=analyst).json()
    row = next(r for r in grid["statements"]["balance_sheet"] if r["canonical_code"] == "bs.total_assets")
    c = row["cells"]["2025-03-31"]
    assert c["display"] == "2670.70"  # 2,67,070 lakhs shown in crores, exact
    ev = client.get(f"/api/observations/{c['observation_id']}", headers=analyst).json()
    assert ev["source"]["sheet"] == "Balance Sheet" and ev["source"]["cell_ref"].startswith("C")
    assert ev["observation"]["original_scale"] == "lakhs"
    eps = next(r for r in grid["statements"]["income_statement"] if r["canonical_code"] == "is.eps_basic")
    assert eps["cells"]["2025-03-31"]["display"] == "19.71"  # EPS never scaled
    assert all(v["status"] in ("pass", "not_applicable") for v in _vals(client, analyst, sp["id"]))


def test_missing_cash_flow_is_insufficient(client, analyst, workspace_id):
    cid = new_company(client, analyst, workspace_id, "No CF co")
    upload(client, analyst, cid, "05_aravalli_fy25_no_cashflow.pdf")
    drain()
    sp = _spreads(client, analyst, cid)[0]
    vals = _vals(client, analyst, sp["id"])
    for rid in ("R07", "R08"):
        v = next(x for x in vals if x["rule_id"] == rid)
        assert v["status"] == "insufficient_data" and v["difference"] is None
    assert any(e["category"] == "missing_statement" for e in _exc(client, analyst, sp["id"]))
    grid = client.get(f"/api/spreads/{sp['id']}/grid", headers=analyst).json()
    fcf = [m for m in grid["metrics"] if m["metric"] == "free_cash_flow"]
    assert fcf and all(m["status"] == "insufficient_data" and m["value"] is None for m in fcf)


def test_standalone_and_consolidated_kept_separate(client, analyst, workspace_id):
    cid = new_company(client, analyst, workspace_id, "Two scopes co")
    upload(client, analyst, cid, "06_aravalli_fy25_standalone_and_consolidated.pdf")
    drain()
    spreads = _spreads(client, analyst, cid)
    assert sorted(s["scope"] for s in spreads) == ["consolidated", "standalone"]
    vals = {}
    for s in spreads:
        grid = client.get(f"/api/spreads/{s['id']}/grid", headers=analyst).json()
        row = next(r for r in grid["statements"]["balance_sheet"] if r["canonical_code"] == "bs.total_assets")
        vals[s["scope"]] = row["cells"]["2025-03-31"]["display"]
    assert vals["standalone"] == "2670.70" and vals["consolidated"] != vals["standalone"]


def test_restatement_surfaced_and_both_versions_kept(client, analyst, workspace_id):
    cid = new_company(client, analyst, workspace_id, "Restated co")
    upload(client, analyst, cid, "01_aravalli_fy25_standalone.pdf")
    upload(client, analyst, cid, "07_aravalli_fy26_restated_comparative.pdf")
    drain()
    sp = _spreads(client, analyst, cid)[0]
    vals = _vals(client, analyst, sp["id"])
    r10 = [v for v in vals if v["rule_id"] == "R10" and v["status"] == "requires_review"]
    titles = " ".join(v["title"] for v in r10)
    assert "is.revenue" in titles and "is.other_expenses" in titles
    assert "restated" in next(v for v in r10 if "is.revenue" in v["title"])["explanation"]
    grid = client.get(f"/api/spreads/{sp['id']}/grid", headers=analyst).json()
    assert grid["periods"] == ["2026-03-31", "2025-03-31", "2024-03-31"]
    rev = [r for r in grid["statements"]["income_statement"] if r["canonical_code"] == "is.revenue"]
    fy25 = [r["cells"]["2025-03-31"] for r in rev if "2025-03-31" in r["cells"]]
    assert {c["display"] for c in fy25} == {"3842.60", "3851.10"}
    assert [c["display"] for c in fy25 if c["preferred"]] == ["3851.10"]


def test_duplicate_upload_not_reprocessed(client, analyst, workspace_id):
    cid = new_company(client, analyst, workspace_id, "Dup co")
    upload(client, analyst, cid, "01_aravalli_fy25_standalone.pdf")
    drain()
    up2 = upload(client, analyst, cid, "01_aravalli_fy25_standalone.pdf")
    assert up2["duplicate_of"] is not None
    drain()
    d = _doc(client, analyst, up2["document_version_id"])
    assert d["status"] == "duplicate" and d["statements"] == []
    assert any(e["category"] == "duplicate" for e in d["document_exceptions"])


def test_conflicting_units_waits_for_analyst_then_resumes(client, analyst, workspace_id):
    cid = new_company(client, analyst, workspace_id, "Units co")
    up = upload(client, analyst, cid, "08_conflicting_units.pdf")
    drain()
    d = _doc(client, analyst, up["document_version_id"])
    assert d["status"] == "awaiting_confirmation" and d["runs"][0]["status"] == "awaiting_input"
    assert _spreads(client, analyst, cid) == []  # nothing normalized before confirmation
    q = next(x for x in d["questions"] if x["field"] == "scale")
    assert set(q["options"]) == {"crores", "lakhs"}
    assert client.post(f"/api/questions/{q['id']}/answer", headers=analyst, json={"answer": "banana"}).status_code == 422
    assert client.post(f"/api/questions/{q['id']}/answer", headers=analyst, json={"answer": "crores"}).status_code == 200
    drain()
    assert _doc(client, analyst, up["document_version_id"])["status"] == "ready_for_review"
    sp = _spreads(client, analyst, cid)[0]
    grid = client.get(f"/api/spreads/{sp['id']}/grid", headers=analyst).json()
    assert next(r for r in grid["statements"]["balance_sheet"] if r["canonical_code"] == "bs.total_assets")["cells"]["2025-03-31"]["display"] == "2670.70"


def test_unreadable_and_dash_stay_unresolved(client, analyst, workspace_id):
    cid = new_company(client, analyst, workspace_id, "Unreadable co")
    upload(client, analyst, cid, "09_unreadable_cell.pdf")
    drain()
    sp = _spreads(client, analyst, cid)[0]
    grid = client.get(f"/api/spreads/{sp['id']}/grid", headers=analyst).json()
    oe = next(r for r in grid["statements"]["income_statement"] if r["canonical_code"] == "is.other_expenses")["cells"]["2025-03-31"]
    assert oe["state"] == "unreadable" and oe["display"] is None and oe["raw_text"] == "6l2.1O"
    cw = next(r for r in grid["statements"]["balance_sheet"] if r["canonical_code"] == "bs.capital_work_in_progress")["cells"]["2024-03-31"]
    assert cw["state"] == "dash_ambiguous" and cw["display"] is None
    vals = _vals(client, analyst, sp["id"])
    te = [v for v in vals if v["rule_id"] == "R04" and v["period_end"] == "2025-03-31" and "Total expenses" in v["title"]][0]
    assert te["status"] == "insufficient_data" and te["expected"] is None
    cats = {e["category"] for e in _exc(client, analyst, sp["id"])}
    assert {"unreadable_cell", "dash_ambiguous"} <= cats


def test_arithmetic_mismatch_detected_and_explained(client, analyst, workspace_id):
    cid = new_company(client, analyst, workspace_id, "Mismatch co")
    upload(client, analyst, cid, "10_arithmetic_mismatch.pdf")
    drain()
    sp = _spreads(client, analyst, cid)[0]
    fails = [v for v in _vals(client, analyst, sp["id"]) if v["status"] == "fail"]
    assert len(fails) == 1 and fails[0]["rule_id"] == "R04" and "Total current assets" in fails[0]["title"]
    assert fails[0]["difference"] == "-90000000"
    exc = next(e for e in _exc(client, analyst, sp["id"]) if e["category"] == "validation" and e["status"] == "open")
    assert "transposed digits in 'Inventories'" in (exc["agent_explanation"] or "")
    # the agent never changed the figure
    grid = client.get(f"/api/spreads/{sp['id']}/grid", headers=analyst).json()
    assert next(r for r in grid["statements"]["balance_sheet"] if r["canonical_code"] == "bs.inventories")["cells"]["2025-03-31"]["display"] == "421.80"


def test_zero_and_negative_denominators(client, analyst, workspace_id):
    cid = new_company(client, analyst, workspace_id, "Nimbus co")
    up = upload(client, analyst, cid, "11_nimbus_zero_negative_denominators.xlsx")
    drain()
    d = _doc(client, analyst, up["document_version_id"])
    assert d["status"] == "awaiting_confirmation"  # the workbook never states its scope: the agent asks, it does not guess
    for q in d["questions"]:
        assert q["field"] == "scope"
        assert client.post(f"/api/questions/{q['id']}/answer", headers=analyst, json={"answer": "standalone"}).status_code == 200
    drain()
    sp = _spreads(client, analyst, cid)[0]
    m = {(x["metric"], x["period_end"]): x for x in client.get(f"/api/spreads/{sp['id']}/grid", headers=analyst).json()["metrics"]}
    assert m[("revenue_growth", "2025-03-31")]["status"] == "special_interpretation"
    assert m[("debt_to_equity", "2025-03-31")]["status"] == "special_interpretation"
    assert m[("ocf_to_net_profit", "2025-03-31")]["status"] == "insufficient_data"
    assert m[("revenue_growth", "2025-03-31")]["value"] is None


def test_malicious_instructions_are_data_and_block_approval(client, analyst, reviewer, workspace_id):
    cid = new_company(client, analyst, workspace_id, "Malicious co")
    up = upload(client, analyst, cid, "12_malicious_instructions.pdf")
    drain()
    d = _doc(client, analyst, up["document_version_id"])
    assert d["status"] == "ready_for_review"
    inj = [e for e in d["document_exceptions"] if e["category"] == "prompt_injection"]
    assert inj and inj[0]["severity"] == "critical"
    sp = _spreads(client, analyst, cid)[0]
    # instructions inside the document changed nothing: checks still computed normally, nothing auto-approved
    detail = client.get(f"/api/spreads/{sp['id']}", headers=analyst).json()
    assert detail["review_status"] == "in_preparation" and detail["blocking"]
    client.post(f"/api/spreads/{sp['id']}/submit", headers=analyst, json={})
    r = client.post(f"/api/spreads/{sp['id']}/approve", headers=reviewer, json={"version": detail["version"]})
    assert r.status_code == 409 and "Critical document issue" in str(r.json())


def test_formula_injection_sanitized_in_export(client, analyst, workspace_id):
    cid = new_company(client, analyst, workspace_id, "Formula co")
    upload(client, analyst, cid, "13_formula_injection.xlsx")
    drain()
    sp = _spreads(client, analyst, cid)[0]
    e = client.post(f"/api/spreads/{sp['id']}/exports", headers=analyst).json()
    wb = load_workbook(io.BytesIO(client.get(f"/api/exports/{e['id']}/download/xlsx", headers=analyst).content))
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, str) and c.value.startswith("="):
                    # only our own generated check formula is allowed
                    assert ws.title == "Balance Sheet" and c.value.startswith("=D") or c.value.startswith("=E"), (ws.title, c.value)
    texts = [c.value for ws in wb.worksheets for row in ws.iter_rows() for c in row if isinstance(c.value, str)]
    assert any(t.startswith("'=HYPERLINK") for t in texts)
    assert any(t.startswith("'+cmd") for t in texts)
    assert any(t.startswith("'@SUM") for t in texts)


def test_bank_is_unsupported(client, analyst, workspace_id):
    cid = new_company(client, analyst, workspace_id, "Fictional Co-operative Bank Limited")
    up = upload(client, analyst, cid, "14_bank_unsupported.pdf")
    drain()
    d = _doc(client, analyst, up["document_version_id"])
    assert d["status"] == "unsupported"
    assert any(e["category"] == "unsupported_entity" for e in d["document_exceptions"])
    c = client.get(f"/api/companies/{cid}", headers=analyst).json()
    assert c["company"]["supported"] is False and c["spreads"] == []
