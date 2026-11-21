from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.config import get_settings  # noqa: E402
from backend.app.database import Database  # noqa: E402
from backend.app.evaluation import Evaluator  # noqa: E402
from backend.app.workflow import ReliabilityWorkflow  # noqa: E402


def main() -> None:
    database = Database(get_settings().database_path)
    database.migrate()
    workflow = ReliabilityWorkflow(database)
    for scenario in ("reliable", "looping", "expensive", "wrong_tool", "hallucinated_success", "partial_completion", "slow", "unsafe_action", "retrieval_failure"):
        result = workflow.run(scenario, "1.0.0")
        print(f"{scenario:24} incident={result.incident_id or 'none':16} detections={len(result.detections)} verified={result.verified_outcome.success}")
    evaluator = Evaluator(database)
    benchmark = evaluator.run_detector_benchmark()
    gate = evaluator.compare_versions("1.0.0", "1.1.0-regressed")
    print(f"benchmark passed={benchmark['passed']} recall={benchmark['metrics']['detection_recall']}")
    print(f"regressed candidate gate={gate['decision']}")


if __name__ == "__main__":
    main()
