from __future__ import annotations

import time


def test_seed_fixture_2_plan_and_pdf(client):
    res = client.post("/api/v1/demo/seed/2")
    assert res.status_code == 200, res.text
    plan_id = res.json()["data"]["plan_id"]
    status = "queued"
    for _ in range(50):
        st = client.get(f"/api/v1/plans/{plan_id}/status")
        assert st.status_code == 200
        status = st.json()["data"]["status"]
        if status in {"complete", "warning", "failed"}:
            break
        time.sleep(0.15)
    assert status in {"complete", "warning"}, status
    plan = client.get(f"/api/v1/plans/{plan_id}")
    assert plan.status_code == 200
    body = plan.json()
    assert body["meta"]["disclaimer"]
    names = {s["name"] for s in body["data"]["scenarios"]}
    assert names == {"protect", "balance", "grow"}
    pdf = client.get(f"/api/v1/plans/{plan_id}/pdf")
    assert pdf.status_code == 200
    assert pdf.content.startswith(b"%PDF")
    assert b"Aegis" in pdf.content or len(pdf.content) > 2000
