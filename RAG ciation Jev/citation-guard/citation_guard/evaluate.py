"""Evaluation data, eval runner, metrics, calibration and dev-only threshold tuning.

Every metric is computed from a run's decisions.jsonl. Threshold re-gating uses only the
probabilities stored in that log, so no number needs a new model call to reproduce.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import random
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import yaml

from .config import Config, paths
from .gate import Thresholds, Verdict, claim_verdict
from .ingest import load_document
from .judges import CallBudget, make_judge
from .judges.base import LABELS
from .pipeline import ClaimDecision, ClaimIn, new_run_id, run_mode, verify_claims, write_decisions
from .quote_match import QuoteStatus, match_quote

ALL_LABELS = (*LABELS, "fabricated")
BAD_LABELS = {"contradicts", "says_nothing", "fabricated"}
REVIEWED = "manoj_reviewed"
DRAFT = "claude_draft"

# --------------------------------------------------------------------------- claims file


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def write_jsonl_atomic(path: Path, rows: list[dict]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    os.replace(tmp, path)


def assign_splits(records: list[dict], seed: int, existing: dict[str, str]) -> None:
    """50/50 dev/test, random with a fixed seed, stratified by label.
    Claims that already have a split keep it, so later additions never move items
    from dev into test (or back)."""
    rng = random.Random(seed)
    by_label: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        if r["claim_id"] in existing:
            r["split"] = existing[r["claim_id"]]
        else:
            by_label[str(r.get("label"))].append(r)
    counts = Counter(r["split"] for r in records if r.get("split"))
    for label in sorted(by_label):
        group = sorted(by_label[label], key=lambda r: r["claim_id"])
        rng.shuffle(group)
        for r in group:
            split = "dev" if counts["dev"] <= counts["test"] else "test"
            if counts["dev"] == counts["test"]:
                split = rng.choice(["dev", "test"])
            r["split"] = split
            counts[split] += 1


def build_claims_file(cfg: Config) -> tuple[Path, dict]:
    ev = paths()["eval"]
    out = ev / "claims.jsonl"
    old = {r["claim_id"]: r for r in read_jsonl(out)}
    records: list[dict] = []

    # 1. Generated claims (system under test output).
    gen_path = ev / "generated_answers.jsonl"
    drafts_path = ev / "generated_labels.yaml"
    drafts = {}
    if drafts_path.exists():
        drafts = (yaml.safe_load(drafts_path.read_text(encoding="utf-8")) or {}).get("labels", {}) or {}
    for row in read_jsonl(gen_path):
        doc = load_document(row.get("doc_id", "rfc7519"))
        for c in row.get("claims", []):
            label, source, note = None, "unlabelled", None
            d = drafts.get(c["claim_id"])
            if d:
                label, source, note = d["label"], DRAFT, d.get("note")
            elif match_quote(doc, c["quote"], c["section_id"], cfg.quote.min_chars).status == QuoteStatus.NOT_FOUND:
                label, source, note = "fabricated", DRAFT, "auto-drafted: quote not found in source"
            records.append({
                "claim_id": c["claim_id"], "origin": "generated", "doc_id": row.get("doc_id", "rfc7519"),
                "question_id": row["question_id"], "claim": c["claim"], "quote": c["quote"],
                "section_id": c["section_id"], "label": label, "label_source": source, "note": note,
            })

    # 2. Planted claims.
    planted = yaml.safe_load((ev / "planted_claims.yaml").read_text(encoding="utf-8"))["claims"]
    for c in planted:
        records.append({
            "claim_id": c["claim_id"], "origin": "planted", "doc_id": c.get("doc_id", "rfc7519"),
            "question_id": None, "claim": c["claim"], "quote": c["quote"], "section_id": str(c["section_id"]),
            "label": c["label"], "label_source": DRAFT, "note": c.get("note"),
        })

    # Keep human-reviewed labels when the claim text is unchanged.
    for r in records:
        o = old.get(r["claim_id"])
        if o and o.get("label_source") == REVIEWED and o["claim"] == r["claim"] and o["quote"] == r["quote"]:
            r["label"], r["label_source"] = o["label"], REVIEWED
            if o.get("review_note"):
                r["review_note"] = o["review_note"]

    existing_splits = {cid: o["split"] for cid, o in old.items() if o.get("split")}
    assign_splits(records, cfg.run.seed, existing_splits)
    write_jsonl_atomic(out, records)
    stats = {
        "total": len(records),
        "origin": dict(Counter(r["origin"] for r in records)),
        "label": dict(Counter(str(r["label"]) for r in records)),
        "label_source": dict(Counter(r["label_source"] for r in records)),
        "split": dict(Counter(r["split"] for r in records)),
    }
    return out, stats


# --------------------------------------------------------------------------- eval runner


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


async def run_eval(cfg: Config, judge_name: str, claims_path: Path) -> Path:
    records = read_jsonl(claims_path)
    if not records:
        raise FileNotFoundError(f"no claims in {claims_path}; run `citation-guard build-claims` first")
    judge = make_judge(judge_name, cfg)
    run_id = new_run_id(judge_name)
    run_dir = paths()["runs"] / run_id
    budget = CallBudget(cfg.run.max_api_calls_per_run)
    th = Thresholds(**cfg.gate.model_dump())
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")

    by_doc: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        by_doc[r.get("doc_id", "rfc7519")].append(r)

    async def run_all(j) -> list[ClaimDecision]:
        out: list[ClaimDecision] = []
        for doc_id, rows in by_doc.items():
            doc = load_document(doc_id)
            claims = [ClaimIn(claim_id=r["claim_id"], claim=r["claim"], quote=r["quote"], section_id=r["section_id"]) for r in rows]
            extras = {r["claim_id"]: {k: r.get(k) for k in ("label", "label_source", "split", "origin")} for r in rows}
            out += await verify_claims(doc, claims, j, cfg, judge_name=judge_name, run_id=run_id,
                                       thresholds=th, budget=budget, extras=extras)
        return out

    if judge is None:
        decisions = await run_all(None)
    else:
        async with judge:  # Jev raises here when TYPESAFE_API_KEY is missing: nothing is written
            decisions = await run_all(judge)

    write_decisions(run_dir, decisions)
    models = sorted({d.model for d in decisions if d.model})
    meta = {
        "run_id": run_id,
        "kind": "eval",
        "mode": run_mode(judge_name),
        "judge": judge_name,
        "configured_model": getattr(judge, "model", None),
        "models_seen": models,
        "started": started,
        "finished": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "claims_file": (claims_path.resolve().relative_to(paths()["root"].resolve()).as_posix()
                        if claims_path.resolve().is_relative_to(paths()["root"].resolve()) else claims_path.as_posix()),
        "claims_sha256": file_sha256(claims_path),
        "n_claims": len(decisions),
        "api_calls": budget.used,
        "max_api_calls_per_run": cfg.run.max_api_calls_per_run,
        "thresholds_at_run": th.model_dump(),
        "errors": sum(1 for d in decisions if d.error),
    }
    (run_dir / "run.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return run_dir


# --------------------------------------------------------------------------- metrics


def regate(d: ClaimDecision, th: Thresholds | None) -> Verdict:
    """Verdict under thresholds `th`, using only what the log stored."""
    if th is None or d.judge == "stringmatch":
        return d.verdict
    return claim_verdict(d.quote_status, d.probabilities, th)


def percentile(values: list[float], q: float) -> float | None:
    """Linear-interpolated percentile (same as numpy's default)."""
    if not values:
        return None
    xs = sorted(values)
    k = (len(xs) - 1) * q / 100
    lo, hi = math.floor(k), math.ceil(k)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def calibration(decisions: list[ClaimDecision], n_bins: int = 10) -> dict:
    items = [
        (d.confidence, d.top_label == d.label)
        for d in decisions
        if d.judge_called and d.confidence is not None and d.label in LABELS
    ]
    bins = []
    ece = 0.0
    for b in range(n_bins):
        lo, hi = b / n_bins, (b + 1) / n_bins
        inside = [(c, ok) for c, ok in items if (lo <= c < hi) or (b == n_bins - 1 and c == 1.0)]
        if not inside:
            bins.append({"bin": f"{lo:.1f}-{hi:.1f}", "n": 0, "avg_confidence": None, "accuracy": None, "warning": "empty"})
            continue
        conf = sum(c for c, _ in inside) / len(inside)
        acc = sum(1 for _, ok in inside if ok) / len(inside)
        ece += len(inside) / len(items) * abs(acc - conf)
        bins.append({
            "bin": f"{lo:.1f}-{hi:.1f}", "n": len(inside), "avg_confidence": conf, "accuracy": acc,
            "warning": "fewer than 10 items" if len(inside) < 10 else None,
        })
    return {"n": len(items), "bins": bins, "ece": ece if items else None}


def compute_metrics(decisions: list[ClaimDecision], th: Thresholds | None = None) -> dict:
    labelled = [d for d in decisions if d.label in ALL_LABELS]
    verdicts = {d.claim_id: regate(d, th) for d in labelled}
    bad = [d for d in labelled if d.label in BAD_LABELS]
    good = [d for d in labelled if d.label == "supports"]

    def rate(num: int, den: int) -> float | None:
        return num / den if den else None

    wrong_pass = sum(1 for d in bad if verdicts[d.claim_id] == Verdict.PASS)
    caught = sum(1 for d in bad if verdicts[d.claim_id] != Verdict.PASS)
    false_alarm = sum(1 for d in good if verdicts[d.claim_id] != Verdict.PASS)
    review = sum(1 for v in verdicts.values() if v == Verdict.HUMAN_REVIEW)

    confusion = {t: {p: 0 for p in LABELS} for t in LABELS}
    reached_b_fabricated = 0
    for d in labelled:
        if not d.judge_called or not d.probabilities:
            continue
        if d.label in LABELS:
            confusion[d.label][d.top_label] += 1
        else:
            reached_b_fabricated += 1

    judged = [d for d in labelled if d.judge_called]
    claim_lat = [d.latency_ms for d in labelled]
    judge_lat = [d.judge_latency_ms for d in judged if d.judge_latency_ms is not None]
    costs = [d.estimated_cost_usd for d in labelled]
    tokens = [d.input_tokens for d in judged]
    if any(c is None for c in costs):
        cost_per_1k = None
        cost_note = "unknown: some judge calls did not report input tokens"
    else:
        cost_per_1k = sum(costs) / len(labelled) * 1000 if labelled else None
        cost_note = None

    return {
        "n": len(labelled),
        "n_good": len(good),
        "n_bad": len(bad),
        "n_unlabelled_skipped": len(decisions) - len(labelled),
        "wrong_pass": wrong_pass,
        "wrong_pass_rate": rate(wrong_pass, len(bad)),
        "caught": caught,
        "catch_rate": rate(caught, len(bad)),
        "false_alarm": false_alarm,
        "false_alarm_rate": rate(false_alarm, len(good)),
        "human_review": review,
        "human_review_rate": rate(review, len(labelled)),
        "verdict_counts": dict(Counter(v.value for v in verdicts.values())),
        "confusion": confusion,
        "n_reached_check_b": len(judged),
        "fabricated_reached_check_b": reached_b_fabricated,
        "calibration": calibration(labelled),
        "latency_ms_p50": percentile(claim_lat, 50),
        "latency_ms_p95": percentile(claim_lat, 95),
        "judge_latency_ms_p50": percentile(judge_lat, 50),
        "judge_latency_ms_p95": percentile(judge_lat, 95),
        "input_tokens_total": sum(t for t in tokens if t is not None) if judged else 0,
        "cost_usd_per_1k_claims": cost_per_1k,
        "cost_note": cost_note,
        "errors": sum(1 for d in labelled if d.error),
    }


def tune_thresholds(dev: list[ClaimDecision], cfg: Config) -> tuple[Thresholds | None, list[dict]]:
    """Grid search on the DEV split only.

    Policy: keep the wrong-pass rate at or below `tuning.max_wrong_pass_rate`; among the
    pairs that meet it, take the lowest false-alarm rate, then the lowest review rate; ties
    go to the stricter (higher) thresholds. If no pair meets the target, take the lowest
    wrong-pass rate. On a small dev set one bad claim can force "review everything"; the
    report always shows config-threshold results next to tuned ones."""
    if not dev or dev[0].judge == "stringmatch":
        return None, []
    rows = []
    for ps in cfg.tuning.pass_supports_grid:
        for fc in cfg.tuning.fail_contradicts_grid:
            th = Thresholds(pass_supports=ps, fail_contradicts=fc)
            m = compute_metrics(dev, th)
            rows.append({
                "pass_supports": ps, "fail_contradicts": fc,
                "wrong_pass_rate": m["wrong_pass_rate"], "false_alarm_rate": m["false_alarm_rate"],
                "human_review_rate": m["human_review_rate"],
            })
    target = cfg.tuning.max_wrong_pass_rate
    key = lambda r: (
        0 if (r["wrong_pass_rate"] or 0.0) <= target + 1e-12 else 1,
        (r["wrong_pass_rate"] or 0.0) if (r["wrong_pass_rate"] or 0.0) > target + 1e-12 else 0.0,
        r["false_alarm_rate"] or 0.0, r["human_review_rate"] or 0.0,
        -r["pass_supports"], -r["fail_contradicts"],
    )
    rows.sort(key=key)
    best = rows[0]
    return Thresholds(pass_supports=best["pass_supports"], fail_contradicts=best["fail_contradicts"]), rows
