"""End-to-end demo: inject a bad ACL change, catch it, fix it, approve, apply, verify."""
from __future__ import annotations

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "backend"))

os.environ.setdefault("APP_DB_PATH", "data/demo.db")

from fastapi.testclient import TestClient  # noqa: E402

from app.db import reset_db  # noqa: E402
from app.main import app  # noqa: E402


def banner(title: str) -> None:
    print()
    print("=" * 74)
    print(f" {title}")
    print("=" * 74)


def main() -> int:
    client = TestClient(app)
    reset_db()

    banner("STAGE 0 - SEED BASELINE DIGITAL TWIN")
    r = client.post("/api/v1/network/snapshot", json={})
    print(f"  POST /api/v1/network/snapshot -> {r.status_code} {r.json()}")
    intents = client.get("/api/v1/intents").json()
    print(f"  baseline intent compliance: {intents['compliance_pct']}% "
          f"({len(intents['results'])} policies)")

    banner("STAGE 1 - SUBMIT BAD CHANGE (acl_blackhole fault)")
    diff_text = (
        "device fw-01\n"
        "+ip access-list APP-DB-GUARD\n"
        "+ deny tcp 10.30.0.0/24 10.30.1.0/24 eq 5432\n"
        "+ permit ip any any\n"
        "interface Vlan210\n"
        "+ ip access-group APP-DB-GUARD in\n"
    )
    r = client.post("/api/v1/changes", json={
        "title": "Add APP-DB-GUARD ACL on firewall",
        "config_diff": diff_text,
        "requested_by": "demo-netops",
    })
    change = r.json()
    cid = change["id"]
    validation = change["validation"]
    print(f"  change #{cid} submitted; status={change['status']}")
    stages = validation["stages"]
    print(f"  pipeline executed {len(stages)} stages:")
    for s in stages:
        name = s.get("stage", "?")
        extra = {k: v for k, v in s.items() if k != "stage"}
        print(f"    - {name}: {extra}")

    banner("STAGE 2 - REGRESSIONS DETECTED ON CANDIDATE TWIN")
    print(f"  verdict={validation['verdict']}  risk_band={validation['risk']['band']} "
          f"(score={validation['risk']['score']})")
    for reg in validation["regressions"]:
        print(f"    [{reg['severity']}] {reg['kind']}")
        print(f"        {reg['message'][:110]}")
    blocked = [m for m in validation["matrix_diff_summary"].get(
        "newly_blocked_detail", [])]
    for m in blocked:
        flow = m["flow"]
        print(f"    matrix: {flow['src']} -> {flow['dst']} {flow['proto']}/"
              f"{flow['port']} BLOCKED ({flow['status']})")
    assert any("app-tier-to-postgres" in g["message"] or "5432" in g["message"]
               for g in validation["regressions"]), "app->db regression not detected"

    banner("STAGE 3 - ROOT CAUSE ANALYSIS")
    rca = validation.get("rca") or {}
    print(f"  incident_id : {rca.get('incident_id')}")
    print(f"  root cause  : {rca.get('root_cause')}")
    print(f"  confidence  : {rca.get('confidence')}")
    confirmed = [h for h in rca.get("hypotheses", []) if h["status"] == "confirmed"]
    rejected = [h for h in rca.get("hypotheses", []) if h["status"] == "rejected"]
    print(f"  hypotheses confirmed={len(confirmed)} rejected={len(rejected)}")

    banner("STAGE 4 - RISK SCORE BREAKDOWN")
    for key, value in validation["risk"]["components"].items():
        print(f"    {key:28s} {value}")
    print(f"  blast radius devices: {', '.join(validation['blast_radius_devices'])}")
    print(f"  agent narration: {validation['narration'][:150]}")

    banner("STAGE 5 - SAFER CONFIG PROPOSED AND RE-SIMULATED")
    fix_diff = change.get("proposed_fix_diff") or ""
    print("  proposed remediation diff:")
    for line in fix_diff.splitlines():
        print(f"    {line}")
    print(f"  re-simulation of fixed config: fix_validated={change['fix_validated']}")
    assert change["fix_validated"], "proposed fix did not re-validate clean"

    banner("STAGE 6 - HUMAN APPROVAL GATE")
    r = client.post(f"/api/v1/changes/{cid}/approve", json={
        "approver": "net-manager",
        "comment": "fix validated on twin; approved",
        "justification": "HIGH risk change reviewed with remediation applied",
    })
    print(f"  POST /changes/{cid}/approve -> {r.status_code} {r.json()}")

    banner("STAGE 7 - APPLY TO CURRENT SNAPSHOT + POST-APPLY VERIFICATION")
    r = client.post(f"/api/v1/changes/{cid}/apply")
    print(f"  POST /changes/{cid}/apply -> {r.status_code} {r.json()}")
    assert r.json()["status"] == "COMPLETED", "post-apply verification failed"

    banner("STAGE 8 - FINAL NETWORK HEALTH")
    kpis = client.get("/api/v1/kpis").json()
    intents = client.get("/api/v1/intents").json()
    print(f"  intent compliance after apply: {intents['compliance_pct']}%")
    print(f"  KPIs: runs={kpis['validation_runs_total']} "
          f"prevented={kpis['unsafe_changes_prevented']} "
          f"avg_validation_ms={kpis['avg_validation_duration_ms']}")
    print()
    print("DEMO COMPLETE: bad change caught, root-caused, fixed, approved, "
          "applied and verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
