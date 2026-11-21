"""Score LLM proposals against the expected fixes in ground truth.

    python -m evals.proposal_eval                       # MOCK (default), all detected conflicts
    python -m evals.proposal_eval --profile noisy       # MOCK with fault injection
    LLM_MODE=real python -m evals.proposal_eval --limit 50 --yes   # real model (costs money)

Metrics:
  action_accuracy     proposed action == expected fix, over evaluated conflicts that exist in
                      ground truth (FAILED proposals count as wrong)
  params_accuracy     expected params (ids) also match, where ground truth lists them
  schema_valid_rate   share of proposals whose FIRST response passed every validation step
  failure_rate        share of proposals FAILED after retries
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

from app.config import get_settings
from app.core.detection import detect_dir
from app.core.models import ProposalStatus
from app.core.proposer import ProposalResult, propose
from app.llm.client import LLMClient, estimate_cost_usd
from app.llm.mock import MockLLM
from evals.common import load_ground_truth, percentile


def _params_match(expected: dict, got: dict) -> bool:
    return all(got.get(k) == v for k, v in expected.items())


def evaluate(data_dir: Path, gt_path: Path, llm: LLMClient, prompt_version: str, limit: int | None = None,
             sample_seed: int = 0) -> dict:
    gt = load_ground_truth(gt_path)
    expected = {(t["type"], t["customer_key"]): t for t in gt["conflicts"]}
    conflicts = sorted(detect_dir(Path(data_dir), respect_review_flags=False).conflicts, key=lambda c: c.id)
    if limit and limit < len(conflicts):
        conflicts = sorted(random.Random(sample_seed).sample(conflicts, limit), key=lambda c: c.id)

    records = []
    for c in conflicts:
        r: ProposalResult = propose(c, llm, prompt_version)
        exp = expected.get((c.type.value, c.customer_key))
        action = r.output.action.value if r.output else None
        correct = bool(exp and action == exp["expected_fix"])
        params_ok = bool(correct and r.output and _params_match(exp.get("expected_params") or {}, r.output.params))
        records.append({
            "conflict_id": c.id, "type": c.type.value, "customer_key": c.customer_key,
            "evidence": c.evidence, "status": r.status.value, "action": action,
            "params": r.output.params if r.output else None,
            "expected_action": exp["expected_fix"] if exp else None,
            "expected_params": exp.get("expected_params") if exp else None,
            "correct": correct, "params_correct": params_ok,
            "first_try_valid": r.first_try_valid, "attempts": len(r.attempts),
            "failure_category": r.failure_category, "failure_reason": r.failure_reason,
            "raw_responses": [a.raw for a in r.attempts], "attempt_errors": [a.error_category for a in r.attempts],
            "input_tokens": r.input_tokens, "output_tokens": r.output_tokens, "latency_ms": r.latency_ms,
            "model": r.model,
        })

    n = len(records)
    scored = [x for x in records if x["expected_action"]]
    inp = sum(x["input_tokens"] for x in records)
    out = sum(x["output_tokens"] for x in records)
    lat = [x["latency_ms"] for x in records]
    per_type: dict[str, dict] = {}
    for x in scored:
        d = per_type.setdefault(x["type"], {"n": 0, "correct": 0})
        d["n"] += 1
        d["correct"] += int(x["correct"])
    for d in per_type.values():
        d["accuracy"] = round(d["correct"] / d["n"], 4)
    cost = estimate_cost_usd(inp, out) if llm.mode == "real" else 0.0
    return {
        "dataset": {"seed": gt["seed"], "n": gt["n"], "profile": gt.get("profile", "default")},
        "prompt_version": prompt_version,
        "llm_mode": llm.mode,
        "model": llm.model_name,
        "n_conflicts": n,
        "metrics": {
            "action_accuracy": round(sum(x["correct"] for x in scored) / len(scored), 4) if scored else None,
            "params_accuracy": round(sum(x["params_correct"] for x in scored) / len(scored), 4) if scored else None,
            "schema_valid_rate": round(sum(x["first_try_valid"] for x in records) / n, 4) if n else None,
            "failure_rate": round(sum(x["status"] == ProposalStatus.FAILED.value for x in records) / n, 4)
            if n else None,
            "mean_attempts": round(sum(x["attempts"] for x in records) / n, 3) if n else None,
            "input_tokens": inp, "output_tokens": out,
            "tokens_estimated": llm.mode == "mock",
            "cost_usd_total": cost,
            "cost_usd_per_conflict": round(cost / n, 6) if n else None,
            "latency_ms_p50": percentile(lat, 50), "latency_ms_p95": percentile(lat, 95),
        },
        "per_type": per_type,
        "records": records,
    }


def summary_line(r: dict) -> str:
    m = r["metrics"]
    d = r["dataset"]
    return (f"[{r['llm_mode']}:{r['model']}] data={d['profile']}/seed{d['seed']} prompt={r['prompt_version']} "
            f"n={r['n_conflicts']} "
            f"action_acc={m['action_accuracy']} params_acc={m['params_accuracy']} "
            f"schema_valid={m['schema_valid_rate']} failure_rate={m['failure_rate']} "
            f"mean_attempts={m['mean_attempts']} tokens_in={m['input_tokens']} tokens_out={m['output_tokens']}"
            f"{' (estimated)' if m['tokens_estimated'] else ''} cost_usd={m['cost_usd_total']} "
            f"p50_ms={m['latency_ms_p50']} p95_ms={m['latency_ms_p95']}")


def main(argv: list[str] | None = None) -> None:
    s = get_settings()
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=s.generated_dir)
    ap.add_argument("--gt", type=Path, default=s.ground_truth)
    ap.add_argument("--prompt", default=s.prompt_version)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--profile", default=None, help="mock profile override: clean|noisy")
    ap.add_argument("--yes", action="store_true", help="confirm a real (paid) run")
    ap.add_argument("--json", type=Path, default=None, help="write full result JSON here")
    args = ap.parse_args(argv)
    if s.llm_mode == "real" and not args.yes:
        raise SystemExit("LLM_MODE=real costs money. Re-run with --yes after checking the expected cost.")
    llm = LLMClient(s, mock=MockLLM(profile=args.profile) if args.profile and s.llm_mode == "mock" else None)
    r = evaluate(args.data, args.gt, llm, args.prompt, args.limit)
    print(summary_line(r))
    for t, d in sorted(r["per_type"].items()):
        print(f"  {t:<32} {d['correct']:>3}/{d['n']:<3} acc={d['accuracy']}")
    if args.json:
        args.json.write_text(json.dumps(r, indent=2, default=str), encoding="utf-8")


if __name__ == "__main__":
    main()
