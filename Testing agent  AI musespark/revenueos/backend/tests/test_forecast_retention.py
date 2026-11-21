"""Phases 4 and 5: forecast engine, retention, expansion."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from app.ml.features import CHURN_FEATURES, churn_features
from app.ml.forecast_sim import quarter_bounds, quarter_label, simulate
from app.services import forecast
from app.services.scope import SYSTEM_SCOPE
from tests.conftest import CRO, auth


def test_simulation_known_answer():
    """A certain deal adds its full amount, and an impossible one adds nothing."""
    result = simulate(np.array([100.0, 500.0]), np.array([1.0, 0.0]), base=50.0)
    assert result.low == result.expected == result.high == 150.0


def test_simulation_expected_value_converges():
    amounts = np.array([1000.0] * 50)
    result = simulate(amounts, np.full(50, 0.3))
    assert result.expected == pytest.approx(15_000, rel=0.01)
    assert result.low < result.expected < result.high


def test_simulation_is_reproducible():
    args = (np.array([100.0, 200.0, 300.0]), np.array([0.2, 0.5, 0.9]))
    assert simulate(*args) == simulate(*args)


def test_empty_pipeline_returns_base():
    result = simulate(np.array([]), np.array([]), base=42.0)
    assert (result.low, result.expected, result.high) == (42.0, 42.0, 42.0)


def test_quarter_helpers():
    assert quarter_label(pd.Timestamp("2026-10-31")) == "2026Q4"
    start, end = quarter_bounds("2026Q4")
    assert start == pd.Timestamp("2026-10-01")
    assert end == pd.Timestamp("2026-12-31")


def test_forecast_api_returns_a_range(client):
    body = client.get("/forecast", headers=auth(CRO)).json()
    assert body["quarter"] == "2026Q4"
    assert body["closed_won_to_date"] <= body["low"] <= body["expected"] <= body["high"]
    assert body["simulations"] == 5000
    assert body["by_team"] and body["by_region"]


def test_team_forecasts_cover_the_total_pipeline(client):
    body = client.get("/forecast", headers=auth(CRO)).json()
    assert sum(t["open_deals"] for t in body["by_team"]) == body["open_deals"]
    assert sum(t["open_pipeline"] for t in body["by_team"]) == pytest.approx(body["open_pipeline"])


def test_forecast_rejects_bad_quarter(client):
    assert client.get("/forecast?quarter=hello", headers=auth(CRO)).status_code == 422


def test_weekly_changes_reconcile_exactly(db):
    changes = forecast.get_changes(db, SYSTEM_SCOPE)
    assert changes["available"]
    total = sum(c["delta_expected"] for c in changes["categories"].values())
    assert total == pytest.approx(changes["total_change"], abs=1.0)
    assert changes["expected_previous"] + changes["total_change"] == pytest.approx(
        changes["expected_current"], abs=0.02
    )


def test_changes_include_real_movement(client):
    body = client.get("/forecast/changes", headers=auth(CRO)).json()
    assert body["items"]
    for item in body["items"]:
        assert item["cite"] == f"deals#{item['deal_id']}"


def test_backtest_reports_all_quarters_and_beats_baselines(pipeline, client):
    result = client.get("/forecast/backtest", headers=auth(CRO)).json()
    assert len(result["quarters"]) == 4
    assert result["mape_model"] < result["mape_stage_weighted"]
    assert result["mape_model"] < result["mape_rep_commit"]


def test_backtest_never_trains_on_the_future(pipeline):
    quarters = pipeline["backtest"]["quarters"]
    sizes = [q["training_rows"] for q in quarters]
    assert sizes == sorted(sizes), "each later quarter should see more history, never less"


def test_churn_model_beats_baseline(pipeline):
    churn = pipeline["churn"]
    assert churn["test"]["selected"]["auc"] > churn["test"]["renewal_baseline"]["auc"]
    selected = churn["selected_algorithm"]
    capture = churn["top_decile_capture"]
    assert capture[selected]["capture_rate"] > capture["renewal_baseline"]["capture_rate"]


def test_churn_training_is_purged_before_test_window(pipeline):
    churn = pipeline["churn"]
    last_train = pd.Timestamp(churn["train_snapshots"][-1])
    first_test = pd.Timestamp(churn["test_snapshots"][0])
    assert (first_test - last_train).days >= 90


def test_churn_features_do_not_leak_the_future(pipeline):
    fr = pipeline["frames"]
    t = pd.Timestamp("2026-05-01")
    full = churn_features(fr, [t])
    trimmed = type(fr)(
        deals=fr.deals, accounts=fr.accounts, stage_history=fr.stage_history,
        activities=fr.activities, contacts=fr.contacts,
        tickets=fr.tickets[fr.tickets["opened_at"] <= t],
        usage=fr.usage[fr.usage["date"] <= t],
        invoices=fr.invoices[fr.invoices["issued_date"] <= t],
        subscriptions=fr.subscriptions,
    )
    pd.testing.assert_frame_equal(
        full[CHURN_FEATURES], churn_features(trimmed, [t])[CHURN_FEATURES]
    )


def test_at_risk_arr_traces_to_accounts(client, db):
    from sqlalchemy import select

    from app.db.models import Account

    summary = client.get("/churn/summary", headers=auth(CRO)).json()
    ids = summary["at_risk_account_ids"]
    assert ids
    total = sum(float(a) for a in db.scalars(select(Account.arr).where(Account.id.in_(ids))))
    assert total == pytest.approx(summary["at_risk_arr"], abs=1.0)


def test_retention_list_has_reasons(client):
    rows = client.get("/churn/at-risk?band=high", headers=auth(CRO)).json()["items"]
    assert rows
    assert all(r["band"] == "high" for r in rows)
    assert all(r["reasons"] for r in rows)


def test_churn_explain_not_found(client):
    assert client.get("/churn/999999/explain", headers=auth(CRO)).status_code == 404


def test_expansion_triggers_are_evidence_based(client):
    body = client.get("/expansion?page_size=100", headers=auth(CRO)).json()
    assert body["items"]
    for row in body["items"]:
        assert row["triggers"]
        near_limit = row["seat_utilization"] >= 0.85
        growing = row["user_growth"] >= 0.15
        assert near_limit or growing
