"""Score the rule-based detector against planted ground truth.

    python -m evals.detection_eval
    python -m evals.detection_eval --data data/generated_seed7 --gt data/generated_seed7/ground_truth.json
    python -m evals.detection_eval --strategy name_only     # debugging exercise
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.config import get_settings
from app.core.detection import detect_dir
from app.core.models import ConflictType
from evals.common import load_ground_truth, prf


def evaluate(data_dir: Path, gt_path: Path, strategy: str = "default") -> dict:
    gt = load_ground_truth(gt_path)
    run = detect_dir(Path(data_dir), strategy=strategy, respect_review_flags=False)
    truth = {(t["type"], t["customer_key"]) for t in gt["conflicts"]}
    found = {(c.type.value, c.customer_key) for c in run.conflicts}
    per_type = {}
    for ct in ConflictType:
        t = {x for x in truth if x[0] == ct.value}
        f = {x for x in found if x[0] == ct.value}
        per_type[ct.value] = prf(len(t & f), len(f - t), len(t - f))
    overall = prf(len(truth & found), len(found - truth), len(truth - found))
    money = sum(c.impact.amount_usd for c in run.conflicts if c.impact)
    return {
        "dataset": {"seed": gt["seed"], "n": gt["n"], "profile": gt.get("profile", "default")},
        "strategy": strategy,
        "per_type": per_type,
        "overall": overall,
        "misses": sorted(truth - found),
        "false_positives": sorted(found - truth),
        "money_at_risk_usd_per_month": round(money, 2),
        "match_methods": run.match.method_counts(),
        "unmatched": {k: len(v) for k, v in run.match.unmatched.items()},
    }


def format_table(result: dict) -> str:
    lines = [f"{'type':<32}{'P':>7}{'R':>7}{'F1':>7}{'TP':>5}{'FP':>5}{'FN':>5}"]
    for name, m in list(result["per_type"].items()) + [("OVERALL", result["overall"])]:
        lines.append(f"{name:<32}{m['precision']:>7.3f}{m['recall']:>7.3f}{m['f1']:>7.3f}"
                     f"{m['tp']:>5}{m['fp']:>5}{m['fn']:>5}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    s = get_settings()
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=s.generated_dir)
    ap.add_argument("--gt", type=Path, default=s.ground_truth)
    ap.add_argument("--strategy", default="default", choices=["default", "name_only"])
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    r = evaluate(args.data, args.gt, args.strategy)
    if args.json:
        print(json.dumps(r, indent=2))
        return
    d = r["dataset"]
    print(f"dataset seed={d['seed']} n={d['n']} profile={d['profile']} strategy={r['strategy']}")
    print(format_table(r))
    print(f"money at risk (USD/month, detected): {r['money_at_risk_usd_per_month']:.2f}")
    print(f"match methods: {r['match_methods']}  unmatched: {r['unmatched']}")
    if r["misses"]:
        print("misses:", r["misses"])
    if r["false_positives"]:
        print("false positives:", r["false_positives"])


if __name__ == "__main__":
    main()
