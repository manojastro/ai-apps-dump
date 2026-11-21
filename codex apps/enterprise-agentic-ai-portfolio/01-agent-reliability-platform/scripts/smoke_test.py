from __future__ import annotations

import json
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen


BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8101"


def call(path: str, payload: dict | None = None) -> dict:
    data = json.dumps(payload).encode() if payload is not None else None
    request = Request(BASE + path, data=data, headers={"Content-Type": "application/json"}, method="POST" if payload is not None else "GET")
    with urlopen(request, timeout=5) as response:
        return json.load(response)


def main() -> None:
    assert call("/health")["status"] == "healthy"
    assert call("/ready")["status"] == "ready"
    run = call("/api/v1/demo/run", {"scenario": "hallucinated_success", "agent_version": "smoke"})
    assert run["verified_outcome"]["success"] is False
    action_id = run["proposed_action"]["action_id"]
    try:
        call(f"/api/v1/actions/{action_id}/execute", {})
        raise AssertionError("unapproved action unexpectedly executed")
    except HTTPError as error:
        assert error.code == 403
    gate = call("/api/v1/regression/compare", {"current_version": "1.0.0", "candidate_version": "1.1.0-regressed"})
    assert gate["decision"] == "BLOCK"
    print(f"SMOKE PASS: incident={run['incident_id']} detections={len(run['detections'])} regression_gate={gate['decision']}")


if __name__ == "__main__":
    main()
