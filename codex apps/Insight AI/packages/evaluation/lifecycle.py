"""Controller-owned lifecycle checks against a fresh database and actual worker code."""

import json
import os
import secrets
import subprocess
import sys
import tempfile


def execute(kind):
    with tempfile.TemporaryDirectory(prefix="pl-lifecycle-") as directory:
        os.environ["PRODUCTIONLENS_DATA"] = directory
        os.environ["DATABASE_URL"] = "sqlite:///" + directory.replace("\\", "/") + "/platform.db"
        from fastapi.testclient import TestClient
        from sqlalchemy import func, select

        from services.api.auth import passwords
        from services.api.db import Base, EvidenceRow, Execution, Session, User, engine
        from services.api.main import app
        from services.worker.runner import collect, execute_action, process_investigation

        Base.metadata.create_all(engine)
        password = secrets.token_urlsafe(24)
        with Session() as db:
            db.add(User(username="controller", password_hash=passwords.hash(password), role="administrator"))
            db.commit()
        with TestClient(app) as client:
            auth = client.post(
                "/api/auth/login", json={"username": "controller", "password": password}
            ).json()
            client.headers["x-csrf-token"] = auth["csrf"]
            incident = client.post(
                "/api/incidents", json={"title": "Lifecycle evaluation", "fixture": "payment_delay"}
            ).json()
            run = client.post(
                "/api/investigations",
                json={
                    "incident_id": incident["id"],
                    "tool_limit": 1 if kind == "tool budget exhaustion" else 12,
                },
            ).json()
            run_id = run["id"]
            assertions = []
            if kind == "worker restart":
                collect(run_id, "query_metrics")
                # A different interpreter resumes the persisted partially collected run.
                child = subprocess.run(
                    [
                        sys.executable,
                        "-c",
                        "from services.worker.runner import process_investigation; import sys; process_investigation(sys.argv[1])",
                        run_id,
                    ],
                    capture_output=True,
                    timeout=30,
                )
                assertions.append(
                    {"name": "New worker process completed persisted work", "passed": child.returncode == 0}
                )
                with Session() as db:
                    rows = [
                        e.data for e in db.scalars(select(EvidenceRow).where(EvidenceRow.run_id == run_id))
                    ]
                    assertions.append(
                        {
                            "name": "Previously collected metrics not duplicated",
                            "passed": sum(e["source_type"] == "metrics" for e in rows) == 1,
                        }
                    )
            elif kind == "user cancellation":
                response = client.post(f"/api/investigations/{run_id}/cancel", json={})
                process_investigation(run_id)
                assertions.append({"name": "Cancellation accepted", "passed": response.status_code == 200})
            else:
                process_investigation(run_id)
            current = client.get(f"/api/investigations/{run_id}").json()
            if kind == "duplicate recovery delivery":
                action = current["action"]
                approved = client.post(
                    f"/api/actions/{action['id']}/approve", json={"action_hash": action["digest"]}
                )
                execute_action(action["id"])
                execute_action(action["id"])
                with Session() as db:
                    count = db.scalar(
                        select(func.count()).select_from(Execution).where(Execution.action_id == action["id"])
                    )
                assertions.append(
                    {
                        "name": "Approval followed by duplicate delivery causes exactly one mutation",
                        "passed": approved.status_code == 200 and count == 1,
                    }
                )
            elif kind == "user cancellation":
                assertions.append(
                    {
                        "name": "Cancelled run gathers no evidence and proposes no action",
                        "passed": current["status"] == "cancelled"
                        and not current["evidence"]
                        and not current["action"],
                    }
                )
            elif kind == "tool budget exhaustion":
                assertions.append(
                    {
                        "name": "Budget stops collection before a second call",
                        "passed": current["status"] == "budget_exceeded"
                        and current["state"]["budget"]["tool_calls"] == 1,
                    }
                )
            else:
                assertions.append(
                    {
                        "name": "Resumed diagnosis reaches review",
                        "passed": current["status"] == "awaiting_review",
                    }
                )
            diagnosis = current["state"].get(
                "diagnosis",
                {
                    "category": "inconclusive",
                    "explanation": "Run stopped before a diagnosis",
                    "confidence": "inconclusive",
                    "evidence_ids": [],
                    "missing": [],
                    "alternatives": [],
                },
            )
            result = {
                "status": "completed",
                "passed": all(a["passed"] for a in assertions),
                "assertions": assertions,
                "output": {
                    "diagnosis": diagnosis,
                    "tools": current["state"].get("tools", []),
                    "lifecycle_status": current["status"],
                },
            }
        engine.dispose()
        return result


if __name__ == "__main__":
    print(json.dumps(execute(sys.argv[1])))
