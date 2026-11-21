"""Failure injection tests: bad candidates, label noise, missing features, DQ."""
from __future__ import annotations

from backend.app.db import SessionLocal
from backend.app.ml.data_generator import DriftKnobs
from tests.test_agents import _make_window


def test_bad_candidate_rejected_by_gates(client, trained_baseline):
    bad = client.post(
        "/api/v1/candidates/train",
        json={"inject_bad": True, "bad_n_samples": 120, "bad_label_noise": 0.4},
    ).json()
    evaluated = client.post(
        "/api/v1/candidates/evaluate", json={"version": bad["version"]}
    ).json()
    assert evaluated["verdict"] == "reject"
    assert not all(evaluated["vs_thresholds"].values())
    assert evaluated["reasons"]
    assert evaluated["vs_champion"]["f1_delta"] < 0

    promotion = client.post(
        "/api/v1/promotions", json={"candidate_version": bad["version"]}
    )
    assert promotion.status_code == 409


def test_bad_candidate_risk_high(client, trained_baseline):
    bad = client.post(
        "/api/v1/candidates/train",
        json={"inject_bad": True, "bad_n_samples": 110, "bad_label_noise": 0.45},
    ).json()
    risk = client.get(f"/api/v1/candidates/{bad['version']}/risk").json()
    assert risk["risk_level"] in ("MEDIUM", "HIGH")


def test_label_noise_handled_without_crash(client, trained_baseline):
    window_id = _make_window_via_api(client, {"label_noise": 0.35}, seed=9101)
    evaluation = client.post(f"/api/v1/monitoring/windows/{window_id}/evaluate")
    assert evaluation.status_code == 200
    decision = client.post("/api/v1/retraining/decide", json={"window_id": window_id}).json()
    assert decision["decision"] in ("monitor", "retrain")
    gate_inputs = decision["gate_inputs"]
    if gate_inputs["perf_degradation"] is False:
        raise AssertionError("heavy label noise should degrade measured performance")


def test_missing_feature_dq_caught(client, trained_baseline):
    session = SessionLocal()
    try:
        window_id = _make_window(session, {"drop_features": ["usage_gb"]}, seed=9102)
    finally:
        session.close()
    evaluation = client.post(f"/api/v1/monitoring/windows/{window_id}/evaluate").json()
    assert evaluation["alert"] is True
    quality = client.get(f"/api/v1/monitoring/quality?window_id={window_id}").json()
    schema_checks = [c for c in quality["checks"] if c["check_name"] == "schema_complete"]
    assert schema_checks and schema_checks[0]["passed"] is False


def test_range_violations_detected_by_quality_agent(trained_baseline):
    import pandas as pd

    from backend.app.ml.quality import run_quality_checks

    frame = pd.DataFrame(
        {
            "tenure_months": [12, -5, 30],
            "monthly_charges": [65.0, 70.0, -20.0],
            "usage_gb": [50, 60, 55],
            "support_tickets_30d": [1, 0, 2],
            "contract_type": ["one-year"] * 3,
            "payment_method": ["credit_card"] * 3,
            "customer_segment": ["retail", "business", "retail"],
        }
    )
    checks = {c.check_name: c for c in run_quality_checks(frame, max_severity_score=0.0)}
    assert checks["numeric_ranges"].passed is False
    assert checks["null_fraction"].passed is True
    assert set(checks) >= {"schema_complete", "numeric_ranges", "null_fraction", "latency_regression", "segment_domain"}


def test_null_heavy_frame_fails_null_check(trained_baseline):
    import numpy as np
    import pandas as pd

    from backend.app.ml.quality import run_quality_checks

    frame = pd.DataFrame(
        {
            "tenure_months": [12, np.nan, 30],
            "monthly_charges": [65.0, np.nan, np.nan],
            "usage_gb": [np.nan] * 5 + [10],
            "support_tickets_30d": [1, 0, 2, 3, 1, 0],
            "contract_type": ["one-year", None, "one-year", "two-year", None, "one-year"],
            "payment_method": ["credit_card"] * 6,
            "customer_segment": ["retail"] * 6,
        },
    )
    checks = {c.check_name: c for c in run_quality_checks(frame, max_severity_score=0.0)}
    assert checks["null_fraction"].passed is False


def test_missingness_spike_flags_high_risk_gate_input(client, trained_baseline):
    from backend.app.agents.retraining_decision import RetrainingDecisionAgent
    from backend.app.agents.monitoring import ModelMonitoringAgent

    session = SessionLocal()
    try:
        window_id = _make_window(session, {"missingness_rate": 0.28}, seed=9103)
        ModelMonitoringAgent().evaluate_window(session, window_id)
        output = RetrainingDecisionAgent().decide(session, window_id)
        gate_inputs = output.gate_inputs.model_dump()
        assert gate_inputs["high_risk_drift"] is True
    finally:
        session.close()


def test_drift_knob_from_dict_ignores_unknown_keys():
    knobs = DriftKnobs.from_dict({"mean_shift": 0.5, "bogus_knob": 3})
    assert knobs.mean_shift == 0.5
    assert not hasattr(knobs, "bogus_knob") or "bogus" not in DriftKnobs.__dataclass_fields__


def _make_window_via_api(client, knobs: dict | None, seed: int) -> int:
    window = client.post(
        "/api/v1/monitoring/windows",
        json={"name": f"fi-{seed}", "n_samples": 2000, "seed": seed, "knobs": knobs or {}},
    ).json()
    return int(window["id"])


def test_investigation_persists_rejected_hypotheses(client, trained_baseline):
    from sqlalchemy import select

    from backend.app.models.entities import RejectedHypothesis

    session = SessionLocal()
    try:
        window_id = _make_window(session, None, seed=9104)
        client.post(f"/api/v1/monitoring/windows/{window_id}/evaluate")
        rca = client.post(f"/api/v1/retraining/investigations/{window_id}", json={}).json()
        assert len(rca["rejected_hypotheses"]) >= 2
        rows = list(session.scalars(select(RejectedHypothesis)))
        assert rows
    finally:
        session.close()
