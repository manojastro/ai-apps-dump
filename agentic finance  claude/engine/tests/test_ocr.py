"""Scanned PDF through local OCR (slow: ~30 s per page on CPU). Run with: pytest -m ocr"""

import pytest

from tests.conftest import drain, new_company, upload

pytestmark = [pytest.mark.integration, pytest.mark.ocr]


def test_scanned_statement_via_local_ocr(client, analyst, workspace_id):
    cid = new_company(client, analyst, workspace_id, "Scanned co")
    up = upload(client, analyst, cid, "02_aravalli_fy25_scanned.pdf")
    drain()
    d = client.get(f"/api/documents/{up['document_version_id']}", headers=analyst).json()
    assert d["status"] == "ready_for_review", d["runs"][0]
    assert all(s["method"] == "ocr_local" for s in d["statements"])
    sp = client.get(f"/api/companies/{cid}", headers=analyst).json()["spreads"][0]
    grid = client.get(f"/api/spreads/{sp['id']}/grid", headers=analyst).json()
    ta = next(r for r in grid["statements"]["balance_sheet"] if r["canonical_code"] == "bs.total_assets")["cells"]["2025-03-31"]
    assert ta["display"] == "2670.70"
    assert ta["confidence"]["ocr"] is not None
    ev = client.get(f"/api/observations/{ta['observation_id']}", headers=analyst).json()
    assert ev["observation"]["extraction_method"] == "ocr_local" and ev["source"]["bbox"]
