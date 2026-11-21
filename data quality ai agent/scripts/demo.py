"""Scripted showcase against the running API, including an intentionally rejected candidate."""
import argparse
import json

import httpx


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--token", default="")
    args = parser.parse_args()
    headers = {"Authorization": f"Bearer {args.token}"} if args.token else {}
    with httpx.Client(base_url=args.url, timeout=180, headers=headers) as client:
        response = client.post("/api/v1/incidents", json={"scenario": "schema_drift",
            "title": "Schema drift in orders_daily", "demo_force_first_fix_fail": True})
        response.raise_for_status()
        incident_id = response.json()["id"]
        response = client.post(f"/api/v1/incidents/{incident_id}/run?wait=true")
        response.raise_for_status()
        incident = response.json()
        state = client.get(f"/api/v1/incidents/{incident_id}/state").json()["values"]
        attempts = state["attempt_history"]
        assert [a["status"] for a in attempts] == ["REJECTED", "PASSED"]
        assert incident["artifact"]["post_validation"] == "PASS"
        print(f"Incident {incident_id}")
        print("Fan-out: " + ", ".join(e["branch"] for e in state["aggregated_evidence"]))
        print("Root cause: " + state["selected_hypothesis"]["summary"])
        for attempt in attempts:
            print(f"Attempt {attempt['number']} - {attempt['status']}")
            for feedback in attempt["feedback"]:
                print("  " + feedback)
        print("Independent verifier: " + state["verification_result"]["decision"])
        print("Artifact SHA-256: " + incident["artifact"]["sha256"])
        print(json.dumps(incident["metrics"], indent=2))
        print("Final status: " + incident["status"])


if __name__ == "__main__":
    main()
