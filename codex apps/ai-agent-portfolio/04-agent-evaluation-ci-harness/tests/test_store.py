from evalharness.dataset import generate_demo_cases
from evalharness.engine import EvaluationEngine
from evalharness.store import Database
from evalharness.targets import DemoAgentTarget


def test_database_seeds_persists_run_and_baseline(tmp_path):
    database = Database(f"sqlite:///{tmp_path / 'test.db'}")
    database.initialize()
    assert database.seed_demo()["test_cases"] == 200
    assert len(database.get_cases()) == 200
    report = EvaluationEngine().run(generate_demo_cases()[:2], DemoAgentTarget("good"))
    database.save_run(report)
    database.mark_baseline(report.project_id, report.id)
    restored = database.get_baseline(report.project_id)
    assert restored is not None
    assert restored.to_dict() == report.to_dict()

