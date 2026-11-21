import argparse
import json
from pathlib import Path

from packages.agent.version import version_metadata
from packages.evaluation.harness import process_evaluation
from services.api.db import Evaluation, Session

parser = argparse.ArgumentParser()
parser.add_argument("--candidate", choices=["script-v1", "script-regression"], default="script-regression")
parser.add_argument("--trials", type=int, choices=[1, 2, 3], default=1)
args = parser.parse_args()
with Session() as db:
    row = Evaluation(
        mode="replay",
        config={
            "candidate": args.candidate,
            "trials": args.trials,
            "baseline_version": version_metadata("script-v1"),
            "candidate_version": version_metadata(args.candidate),
        },
    )
    db.add(row)
    db.commit()
    evaluation_id = row.id
process_evaluation(evaluation_id)
with Session() as db:
    row = db.get(Evaluation, evaluation_id)
    Path("docs/evidence").mkdir(exist_ok=True, parents=True)
    Path(f"docs/evidence/{args.candidate}-benchmark.json").write_text(json.dumps(row.report, indent=2))
    print(json.dumps(row.report, indent=2))
