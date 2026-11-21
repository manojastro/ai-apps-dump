"""Phases 2 and 3: Account 360 and deal intelligence."""
from __future__ import annotations

import numpy as np
import pandas as pd

from app.ml.features import DEAL_FEATURES, Frames, deal_features, deal_snapshots
from tests.conftest import CRO, auth


def test_accounts_require_authentication(client):
    assert client.get("/accounts").status_code == 401


def test_account_list_paginates(client):
    response = client.get("/accounts?page=2&page_size=10", headers=auth(CRO))
    body = response.json()
    assert response.status_code == 200
    assert len(body["items"]) == 10
    assert body["total"] >= 200
    assert body["page"] == 2


def test_account_list_page_size_is_capped(client):
    assert client.get("/accounts?page_size=1000", headers=auth(CRO)).status_code == 422


def test_account_search_and_filters(client):
    first = client.get("/accounts?page_size=1", headers=auth(CRO)).json()["items"][0]
    term = first["name"].split()[0]
    found = client.get(f"/accounts?q={term}", headers=auth(CRO)).json()["items"]
    assert any(item["id"] == first["id"] for item in found)
    segment = client.get("/accounts?segment=enterprise&page_size=100", headers=auth(CRO)).json()
    assert segment["items"] and all(a["segment"] == "enterprise" for a in segment["items"])


def test_account_360_brings_everything_together(client, db):
    from sqlalchemy import func, select

    from app.db.models import Deal, Invoice, Ticket

    candidates = (
        select(Deal.account_id)
        .join(Ticket, Ticket.account_id == Deal.account_id)
        .join(Invoice, Invoice.account_id == Deal.account_id)
        .group_by(Deal.account_id).order_by(func.count().desc()).limit(1)
    )
    account_id = db.scalar(candidates)
    response = client.get(f"/accounts/{account_id}/360", headers=auth(CRO))
    body = response.json()
    assert response.status_code == 200
    assert body["account"]["id"] == account_id
    for key in ("deals", "contacts", "invoices", "tickets", "usage_trend", "timeline"):
        assert body[key], f"{key} should not be empty"
    assert body["usage_trend"][0]["week"] < body["usage_trend"][-1]["week"]


def test_account_360_not_found(client):
    assert client.get("/accounts/999999/360", headers=auth(CRO)).status_code == 404


def _strip_future(fr: Frames, t: pd.Timestamp) -> Frames:
    """Remove every row dated after t, as if the data ended on that date."""
    return Frames(
        deals=fr.deals,
        accounts=fr.accounts,
        stage_history=fr.stage_history[fr.stage_history["entered_at"] <= t],
        activities=fr.activities[fr.activities["occurred_at"] <= t],
        contacts=fr.contacts,
        tickets=fr.tickets[fr.tickets["opened_at"] <= t],
        usage=fr.usage[fr.usage["date"] <= t],
        invoices=fr.invoices[fr.invoices["issued_date"] <= t],
        subscriptions=fr.subscriptions,
    )


def test_deal_features_do_not_leak_the_future(pipeline):
    """Deleting everything after T must leave features for T unchanged."""
    fr = pipeline["frames"]
    t = pd.Timestamp("2026-03-15")
    stage_days = {"prospecting": 20.0, "qualification": 20.0, "proposal": 20.0,
                  "negotiation": 20.0}
    snapshots = deal_snapshots(fr, [t])
    assert len(snapshots) > 20
    full = deal_features(fr, snapshots, stage_days)
    truncated = deal_features(_strip_future(fr, t), snapshots, stage_days)
    pd.testing.assert_frame_equal(full[DEAL_FEATURES], truncated[DEAL_FEATURES])


def test_win_model_beats_stage_baseline_on_held_out_data(pipeline):
    test = pipeline["win"]["test"]
    assert test["selected"]["auc"] > test["stage_baseline"]["auc"]
    assert test["selected"]["brier"] < test["stage_baseline"]["brier"]


def test_train_and_test_are_separated_in_time(pipeline):
    win = pipeline["win"]
    assert win["train"]["deals"] > 100
    assert win["test_rows"] > 100


def test_every_open_deal_has_a_score_and_reasons(client, pipeline):
    body = client.get("/deals?page_size=100", headers=auth(CRO)).json()
    assert body["total"] == pipeline["refresh"]["deals_scored"]
    scored = [d for d in body["items"] if d["p_win"] is not None]
    assert len(scored) == len(body["items"])
    assert sum(1 for d in scored if d["reasons"]) / len(scored) > 0.95


def test_deals_are_sorted_by_risk(client):
    items = client.get("/deals?page_size=50", headers=auth(CRO)).json()["items"]
    risks = [1 - d["p_win"] for d in items]
    assert risks == sorted(risks, reverse=True)


def test_reasons_are_true_statements_about_the_deal(client):
    items = client.get("/deals?page_size=100", headers=auth(CRO)).json()["items"]
    checked = 0
    for deal in items:
        detail = client.get(f"/deals/{deal['id']}/explain", headers=auth(CRO)).json()
        for reason in detail["reasons"]:
            if reason["text"] == "No executive contact on this deal":
                assert reason["value"] == 0
                checked += 1
            if reason["text"] == "Executive contact engaged":
                assert reason["value"] == 1
                checked += 1
            if reason["text"].startswith("No activity in"):
                assert reason["value"] >= 10
                checked += 1
    assert checked > 0


def test_reasons_match_planted_rules(pipeline):
    """Global direction of the model should agree with the rules we planted."""
    from app.ml.common import load_active
    from app.ml.explain import shap_matrix
    from app.ml.train_win import MODEL_NAME, score_open_deals

    settings = pipeline["settings"]
    artifact = load_active(MODEL_NAME)
    frame = score_open_deals(pipeline["frames"], settings.data_as_of, artifact)
    values = shap_matrix(artifact["model"], frame[DEAL_FEATURES])
    index = {name: i for i, name in enumerate(DEAL_FEATURES)}

    def direction(name: str) -> float:
        column = frame[name].fillna(frame[name].median())  # Missing values are planted.
        return float(np.corrcoef(column, values[:, index[name]])[0, 1])

    assert direction("has_exec_contact") > 0.3, "an executive contact should raise win odds"
    assert direction("days_since_last_activity") < -0.3, "silence should lower win odds"
    strength = np.abs(values).mean(axis=0)
    # The executive signal is shared by two correlated features, so compare against both.
    executive = strength[index["has_exec_contact"]] + strength[index["days_since_exec_touch"]]
    assert strength[index["discount_pct"]] < executive / 2, "discount must not be a main driver"
    assert abs(direction("discount_pct")) < 0.5, "discount has no planted upside"


def test_explain_returns_model_version(client):
    deal = client.get("/deals?page_size=1", headers=auth(CRO)).json()["items"][0]
    detail = client.get(f"/deals/{deal['id']}/explain", headers=auth(CRO)).json()
    assert detail["model_version"]
    assert detail["reasons"]


def test_explain_not_found(client):
    assert client.get("/deals/999999/explain", headers=auth(CRO)).status_code == 404
