from backend.app.database import Database
from backend.app.evaluation import VERSION_ARTIFACT_DIGESTS, Evaluator


def test_detector_benchmark_is_measurable_and_passes(tmp_path):
    database = Database(tmp_path / "eval.db")
    database.migrate()
    result = Evaluator(database).run_detector_benchmark()
    assert result["passed"] is True
    assert result["metrics"]["detection_recall"] == 1.0
    assert result["metrics"]["outcome_verification_accuracy"] == 1.0
    assert result["metrics"]["scenario_count"] == 9


def test_safe_candidate_passes_and_regressed_candidate_is_blocked(tmp_path):
    database = Database(tmp_path / "gates.db")
    database.migrate()
    evaluator = Evaluator(database)
    passed = evaluator.compare_versions("1.0.0", "1.1.0-safe")
    assert passed["decision"] == "PASS"
    assert passed["checks"]["trusted_runner"] is True
    assert passed["checks"]["version_specific_evidence"] is True
    assert passed["evidence"]["baseline_evidence_digest"] != passed["evidence"]["candidate_evidence_digest"]
    assert len(set(passed["evidence"]["baseline_run_ids"] + passed["evidence"]["candidate_run_ids"])) == 18
    assert passed["evidence"]["baseline_version_artifact_digest"] == VERSION_ARTIFACT_DIGESTS["1.0.0"]
    assert passed["evidence"]["candidate_version_artifact_digest"] == VERSION_ARTIFACT_DIGESTS["1.1.0-safe"]
    blocked = evaluator.compare_versions("1.0.0", "1.1.0-regressed")
    assert blocked["decision"] == "BLOCK"
    assert blocked["checks"]["safety"] is False
