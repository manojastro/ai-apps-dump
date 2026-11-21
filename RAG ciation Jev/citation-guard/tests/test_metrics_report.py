"""Metric maths on a small fixed fixture with hand-computed expected values, plus report header."""

from datetime import datetime, timezone

import pytest

from citation_guard.config import load_config
from citation_guard.evaluate import compute_metrics, percentile, tune_thresholds
from citation_guard.gate import Thresholds, Verdict, claim_verdict
from citation_guard.pipeline import ClaimDecision
from citation_guard.quote_match import QuoteStatus
from citation_guard.report import SMALL_SAMPLE, analyse_run, render_run_md

TH = Thresholds(pass_supports=0.80, fail_contradicts=0.50)
F = QuoteStatus.FOUND_IN_CITED_SECTION


def dec(cid, label, status, probs, latency, cost, split="test"):
    judged = probs is not None
    conf = max(probs.values()) if probs else None
    top = max(probs, key=probs.get) if probs else None
    return ClaimDecision(
        run_id="r", mode="MOCK", judge="mock", model="mock", doc_id="d", claim_id=cid, cited_section_id="1",
        quote_status=status, judge_called=judged, probabilities=probs, confidence=conf, top_label=top,
        verdict=claim_verdict(status, probs, TH), thresholds=TH, latency_ms=latency,
        judge_latency_ms=latency if judged else None, estimated_cost_usd=cost, mock=True,
        timestamp=datetime.now(timezone.utc).isoformat(), label=label, label_source="claude_draft",
        split=split, origin="planted",
    )


def P(s, c, n):
    return {"supports": s, "contradicts": c, "says_nothing": n}


@pytest.fixture
def fixture():
    return [
        dec("g1", "supports", F, P(0.90, 0.05, 0.05), 10, 0.001),  # PASS, top correct
        dec("g2", "supports", F, P(0.60, 0.10, 0.30), 20, 0.001),  # REVIEW (false alarm), top correct
        dec("g3", "supports", QuoteStatus.QUOTE_TOO_SHORT, None, 30, 0.0),  # REVIEW (false alarm)
        dec("b1", "contradicts", F, P(0.85, 0.10, 0.05), 40, 0.001),  # PASS -> wrong pass, top wrong
        dec("b2", "says_nothing", F, P(0.20, 0.10, 0.70), 50, 0.001),  # REVIEW, top correct
        dec("b3", "fabricated", QuoteStatus.NOT_FOUND, None, 60, 0.0),  # FAIL_FABRICATED
        dec("b4", "contradicts", F, P(0.10, 0.80, 0.10), 70, 0.001),  # FAIL_CONTRADICTED, top correct
    ]


def test_rates(fixture):
    m = compute_metrics(fixture, TH)
    assert (m["n"], m["n_good"], m["n_bad"]) == (7, 3, 4)
    assert m["wrong_pass"] == 1 and m["wrong_pass_rate"] == pytest.approx(0.25)
    assert m["caught"] == 3 and m["catch_rate"] == pytest.approx(0.75)
    assert m["false_alarm"] == 2 and m["false_alarm_rate"] == pytest.approx(2 / 3)
    assert m["human_review"] == 3 and m["human_review_rate"] == pytest.approx(3 / 7)
    assert m["verdict_counts"] == {"PASS": 2, "HUMAN_REVIEW": 3, "FAIL_FABRICATED_QUOTE": 1, "FAIL_CONTRADICTED": 1}


def test_confusion(fixture):
    c = compute_metrics(fixture, TH)["confusion"]
    assert c["supports"] == {"supports": 2, "contradicts": 0, "says_nothing": 0}
    assert c["contradicts"] == {"supports": 1, "contradicts": 1, "says_nothing": 0}
    assert c["says_nothing"] == {"supports": 0, "contradicts": 0, "says_nothing": 1}


def test_calibration_ece(fixture):
    cal = compute_metrics(fixture, TH)["calibration"]
    assert cal["n"] == 5
    # bins: 0.6 (acc 1) -> .4*1/5; 0.7 (acc 1) -> .3*1/5; {0.85 F, 0.8 T} -> |.5-.825|*2/5; 0.9 T -> .1*1/5
    assert cal["ece"] == pytest.approx(0.08 + 0.06 + 0.13 + 0.02)
    used = {b["bin"]: b for b in cal["bins"] if b["n"]}
    assert used["0.8-0.9"]["n"] == 2 and used["0.8-0.9"]["accuracy"] == pytest.approx(0.5)
    assert all(b["warning"] == "fewer than 10 items" for b in used.values())


def test_latency_and_cost(fixture):
    m = compute_metrics(fixture, TH)
    assert m["latency_ms_p50"] == pytest.approx(40)
    assert m["latency_ms_p95"] == pytest.approx(67)  # 60 + 0.7 * 10
    assert m["cost_usd_per_1k_claims"] == pytest.approx(0.005 / 7 * 1000)
    assert percentile([1, 2, 3, 4], 50) == pytest.approx(2.5)


def test_regate_with_other_thresholds(fixture):
    m = compute_metrics(fixture, Thresholds(pass_supports=0.90, fail_contradicts=0.50))
    assert m["wrong_pass"] == 0  # b1 (0.85) no longer passes
    assert m["false_alarm"] == 2  # g1 (0.90) still passes


def test_unknown_cost_when_tokens_missing(fixture):
    fixture[0].estimated_cost_usd = None
    m = compute_metrics(fixture, TH)
    assert m["cost_usd_per_1k_claims"] is None and m["cost_note"]


def test_tuning_uses_only_given_split(fixture):
    th, grid = tune_thresholds(fixture, load_config())
    assert th is not None and grid
    assert compute_metrics(fixture, th)["wrong_pass_rate"] == 0.0


def test_report_shows_mock_and_small_sample_warning(fixture):
    dev = [d.model_copy(update={"split": "dev"}) for d in fixture]
    meta = {
        "run_id": "r", "mode": "MOCK", "judge": "mock", "models_seen": ["mock-heuristic-v1"],
        "started": "2026-11-21T00:00:00+00:00", "claims_file": "data/eval/claims.jsonl", "claims_sha256": "0" * 64,
        "api_calls": 0, "max_api_calls_per_run": 500, "thresholds_at_run": TH.model_dump(),
    }
    cfg = load_config()
    md = render_run_md(analyse_run(meta, cfg, decisions=fixture + dev), cfg)
    head = md[:1500]
    assert "MODE: MOCK" in head
    assert SMALL_SAMPLE in head
    assert "Small sample. Results are indicative, not statistically strong." in head
    assert "provisional" in head
    assert "14 `claude_draft`" in head
