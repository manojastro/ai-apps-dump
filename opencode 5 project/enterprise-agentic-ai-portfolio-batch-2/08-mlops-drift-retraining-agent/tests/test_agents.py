"""Agent-level behaviour tests."""
from __future__ import annotations

from backend.app.agents.candidate_training import CandidateTrainingAgent
from backend.app.agents.data_drift import DataDriftAgent
from backend.app.agents.deployment_risk import DeploymentRiskAgent
from backend.app.agents.monitoring import ModelMonitoringAgent
from backend.app.agents.root_cause import RootCauseAgent
from backend.app.agents.shadow_canary import ShadowCanaryAgent
from backend.app.db import SessionLocal
from backend.app.ml.pipeline import train_reference_champion
from backend.app.repositories.results_repo import WindowRepository
from backend.app.schemas.dto import RootCauseAnalysis
from backend.app.services.baseline import train_baseline
import pytest

SEVERE_KNOBS = {
    "mean_shift": 1.4,
    "variance_shift": 1.8,
    "label_noise": 0.18,
}


@pytest.fixture()
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def baseline(db_session):
    return train_baseline(db_session, seed=42, n_samples=3000)


def _make_window(session, knobs: dict | None, seed: int = 2001, n: int = 2500) -> int:
    from backend.app.ml.data_generator import DriftKnobs, generate_customer_data

    frame = generate_customer_data(n, seed=seed, knobs=DriftKnobs.from_dict(knobs or {}))
    row = WindowRepository.create(
        session,
        name=f"agent-test-{seed}",
        step=None,
        n_samples=len(frame),
        seed=seed,
        knobs=DriftKnobs.from_dict(knobs or {}).to_dict(),
        data_path="",
    )
    import pandas as pd

    from backend.app.config import settings

    path = settings.window_data_dir / f"window_{row.id}.csv"
    frame.to_csv(path, index=False)
    row.data_path = str(path)
    session.commit()
    return int(row.id)


def test_data_drift_agent_flags_severe_window(db_session, baseline):
    window_id = _make_window(db_session, SEVERE_KNOBS, seed=3001)
    rows = DataDriftAgent().evaluate(db_session, window_id)
    drifted = [r.feature for r in rows if r.drifted]
    assert len(drifted) >= 2
    assert any(r.severity == "high" for r in rows)


def test_data_drift_agent_clean_window_quiet(db_session, baseline):
    window_id = _make_window(db_session, None, seed=3002)
    rows = DataDriftAgent().evaluate(db_session, window_id)
    assert not any(r.drifted for r in rows)


def test_monitoring_agent_full_evaluation(db_session, baseline):
    window_id = _make_window(db_session, SEVERE_KNOBS, seed=3003)
    outcome = ModelMonitoringAgent().evaluate_window(db_session, window_id)
    assert outcome.alert is True
    assert outcome.drift_count >= 2
    assert 0.0 <= outcome.fairness_ratio <= 1.0
    perf_rows_ok = True
    del perf_rows_ok


def test_monitoring_agent_rejects_double_evaluation(db_session, baseline):
    window_id = _make_window(db_session, None, seed=3004)
    ModelMonitoringAgent().evaluate_window(db_session, window_id)
    with pytest.raises(Exception):
        ModelMonitoringAgent().evaluate_window(db_session, window_id)


def test_root_cause_agent_returns_exact_pydantic(db_session, baseline):
    window_id = _make_window(db_session, {**SEVERE_KNOBS, "missingness_rate": 0.06}, seed=3005)
    ModelMonitoringAgent().evaluate_window(db_session, window_id)
    analysis = RootCauseAgent().investigate(db_session, window_id)
    assert isinstance(analysis, RootCauseAnalysis)
    assert analysis.incident_id == f"INC-{window_id:04d}"
    assert isinstance(analysis.observations, list) and analysis.observations
    assert isinstance(analysis.evidence, list) and analysis.evidence
    assert isinstance(analysis.hypotheses, list) and analysis.hypotheses
    assert isinstance(analysis.rejected_hypotheses, list) and analysis.rejected_hypotheses
    assert isinstance(analysis.root_cause, str) and len(analysis.root_cause) > 10
    assert 0.0 < analysis.confidence < 1.0
    assert isinstance(analysis.recommended_actions, list) and analysis.recommended_actions


def test_root_cause_names_top_drifted_features(db_session, baseline):
    window_id = _make_window(db_session, SEVERE_KNOBS, seed=3006)
    ModelMonitoringAgent().evaluate_window(db_session, window_id)
    analysis = RootCauseAgent().investigate(db_session, window_id)
    text_blob = analysis.root_cause + " ".join(analysis.observations)
    assert "tenure_months" in text_blob or "monthly_charges" in text_blob or "support_tickets_30d" in text_blob or "usage_gb" in text_blob


def test_deployment_risk_low_for_passing_candidate(db_session, baseline):
    window_id = _make_window(db_session, SEVERE_KNOBS, seed=3107)
    trained = CandidateTrainingAgent().train(
        db_session, source_window_id=window_id, seed=31
    )
    from backend.app.agents.candidate_evaluation import CandidateEvaluationAgent

    evaluation = CandidateEvaluationAgent().evaluate(db_session, trained.version)
    if evaluation.verdict != "pass":
        pytest.skip("candidate failed gates; risk test targets passing candidate")
    risk = DeploymentRiskAgent().assess(db_session, trained.version)
    assert risk["risk_level"] == "LOW"


def test_shadow_compare_and_canary(db_session, baseline):
    window_id = _make_window(db_session, SEVERE_KNOBS, seed=3108)
    trained = CandidateTrainingAgent().train(
        db_session, source_window_id=window_id, seed=33
    )
    agent = ShadowCanaryAgent()
    shadow = agent.shadow_compare(db_session, trained.version, n_requests=1500, seed=555)
    assert 0.0 <= shadow["disagreement_rate"] <= 1.0
    assert shadow["n_requests"] == 1500
    canary = agent.canary_evaluate(db_session, trained.version, n_requests=1200, seed=777)
    assert canary["passed"] is True
    assert set(canary["slices"]) == {"retail", "business"}


def test_reference_champion_metrics_sane():
    artifact = train_reference_champion(n_samples=2500, seed=42)
    assert artifact["metrics"]["roc_auc"] > 0.7
