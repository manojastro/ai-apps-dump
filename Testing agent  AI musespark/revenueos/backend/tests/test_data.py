"""Phase 0 and 1: health, synthetic data, loader, data quality."""
from __future__ import annotations

import json

import pandas as pd

from scripts import data_quality, generate_synthetic_data, load_data


def test_health_reports_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["database"] == "ok"


def test_row_counts_match_targets(pipeline):
    counts = pipeline["counts"]
    assert 200 <= counts["accounts"] <= 210
    assert counts["deals"] == 600
    assert 1400 <= counts["tickets"] <= 1600
    assert counts["invoices"] > 1500
    assert counts["usage_daily"] > 50_000
    assert counts["activities"] > 3000
    assert counts["contacts"] > 800


def test_generation_is_reproducible(pipeline, tmp_path):
    settings = pipeline["settings"]
    generate_synthetic_data.write_dataset(tmp_path, settings.data_as_of)
    for table in ("deals", "tickets", "invoices", "usage_daily"):
        first = pd.read_csv(settings.data_dir / f"{table}.csv")
        second = pd.read_csv(tmp_path / f"{table}.csv")
        pd.testing.assert_frame_equal(first, second)


def test_loader_is_idempotent(pipeline):
    second_run = load_data.load(pipeline["connector"])
    assert second_run == pipeline["counts"]


def test_orphans_are_quarantined_not_loaded(pipeline):
    issues = json.loads((pipeline["settings"].data_dir / "injected_issues.json").read_text())
    expected = len(issues["orphan_tickets"]) + len(issues["orphan_activities"])
    assert pipeline["counts"]["load_rejects"] == expected


def test_data_quality_finds_every_injected_issue(pipeline):
    issues = json.loads((pipeline["settings"].data_dir / "injected_issues.json").read_text())
    report = pipeline["quality"]
    assert sorted(map(sorted, issues["duplicate_account_pairs"])) == sorted(report["duplicates"])
    assert report["stale_open_deals"] == issues["stale_open_deals"]
    assert report["impossible_dates"]["deals.closed_before_created"] == issues["impossible_deals"]
    assert report["impossible_dates"]["tickets.resolved_before_opened"] == \
        issues["impossible_tickets"]
    assert report["orphans"]["tickets.account_id"] == issues["orphan_tickets"]
    assert report["orphans"]["activities.contact_id"] == issues["orphan_activities"]
    assert report["nulls"]["deals.source"] == issues["missing_source_deals"]
    assert report["nulls"]["contacts.title"] == issues["missing_title_contacts"]


def test_region_na_is_not_parsed_as_missing(pipeline):
    accounts = pipeline["connector"].fetch("accounts")
    assert accounts["region"].isna().sum() == 0
    assert (accounts["region"] == "NA").sum() > 0


def test_name_normalisation_catches_legal_suffixes():
    assert data_quality.normalise_name("ACME SYSTEMS, Inc.") == "acme systems"
    assert data_quality.normalise_name("Acme Systems LLC") == "acme systems"


def _deal_frame(pipeline) -> pd.DataFrame:
    frames = pipeline["frames"]
    deals = frames.deals[frames.deals["outcome"].notna()
                         & frames.deals["type"].isin(["new", "expansion"])].copy()
    exec_ids = frames.contacts[frames.contacts["is_executive"]]["id"]
    touched = frames.activities[frames.activities["contact_id"].isin(exec_ids)]["deal_id"]
    deals["has_exec"] = deals["id"].isin(touched)
    deals["won"] = deals["outcome"] == "won"
    return deals


def test_planted_rule_executive_contact_lifts_win_rate(pipeline):
    deals = _deal_frame(pipeline)
    rates = deals.groupby("has_exec")["won"].mean()
    assert rates[True] > rates[False] + 0.10


def test_planted_rule_heavy_discount_does_not_lift_win_rate(pipeline):
    deals = _deal_frame(pipeline)
    heavy = deals[deals["discount_pct"] > 25]["won"].mean()
    light = deals[deals["discount_pct"] <= 25]["won"].mean()
    assert heavy <= light + 0.03
