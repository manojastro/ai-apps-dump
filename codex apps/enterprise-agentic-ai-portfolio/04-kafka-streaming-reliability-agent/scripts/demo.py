"""Run every ground-truth incident through investigation, approval, remediation, and validation."""

import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.database import Repository  # noqa: E402
from app.models import ApprovalRequest  # noqa: E402
from app.simulator import SCENARIOS  # noqa: E402
from app.workflow import ReliabilityWorkflow  # noqa: E402


def main() -> None:
    database_path = Path(os.getenv("DATABASE_PATH", PROJECT_ROOT / "data" / "streaming.db"))
    repository = Repository(database_path)
    repository.initialize()
    workflow = ReliabilityWorkflow(repository)
    output = []
    for scenario in SCENARIOS:
        incident = workflow.investigate(scenario)
        incident_id = incident["incident_id"]
        workflow.approve(incident_id, ApprovalRequest(
            approved=True, approved_by="demo-script", reason="pre-authorized synthetic-only demonstration"
        ))
        result = workflow.execute_and_validate(incident_id)
        output.append({
            "incident_id": incident_id,
            "scenario": scenario,
            "predicted": result["predicted_root_cause"],
            "ground_truth": result["ground_truth"],
            "status": result["status"],
        })
    print(json.dumps({"runs": output, "evaluation": repository.evaluation_summary()}, indent=2))


if __name__ == "__main__":
    main()
