"""Red-team eval (offline): runs guardrail input checks over attack + benign sets.

Writes reports/redteam.json with block rate, false-positive rate, overhead ms.
No network calls. All data synthetic (Acme Retail Ltd).
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gateway import guardrails as guards  # noqa: E402


def read_jsonl(path: Path) -> list[dict[str, object]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="strict")
    ap.add_argument("--attacks", default=str(ROOT / "suites/redteam/attacks.jsonl"))
    ap.add_argument("--benign", default=str(ROOT / "suites/redteam/benign.jsonl"))
    ap.add_argument("--out", default=str(ROOT / "reports/redteam.json"))
    args = ap.parse_args()

    profiles = guards.load_profiles(str(ROOT / "config/guardrail_profiles.yaml"))
    profile = profiles[args.profile]
    attacks = read_jsonl(Path(args.attacks))
    benign = read_jsonl(Path(args.benign))

    attack_lat, benign_lat = [], []
    blocked = 0
    blocked_ids = []
    for row in attacks:
        t0 = time.perf_counter()
        res = guards.check_input(str(row["prompt"]), profile)
        attack_lat.append((time.perf_counter() - t0) * 1000.0)
        if not res.allowed:
            blocked += 1
            blocked_ids.append(row["id"])

    fps = 0
    fp_ids = []
    for row in benign:
        t0 = time.perf_counter()
        res = guards.check_input(str(row["prompt"]), profile)
        benign_lat.append((time.perf_counter() - t0) * 1000.0)
        if not res.allowed:
            fps += 1
            fp_ids.append(row["id"])

    all_lat = sorted(attack_lat + benign_lat)
    p50 = statistics.median(all_lat)
    p95 = all_lat[max(0, int(len(all_lat) * 0.95) - 1)]
    report = {
        "synthetic": True,
        "profile": args.profile,
        "n_attacks": len(attacks),
        "n_benign": len(benign),
        "blocked_attacks": blocked,
        "block_rate": round(blocked / len(attacks), 4),
        "false_positives": fps,
        "false_positive_rate": round(fps / len(benign), 4),
        "overhead_ms_p50": round(p50, 3),
        "overhead_ms_p95": round(p95, 3),
        "blocked_ids": blocked_ids,
        "fp_ids": fp_ids,
        "max_usd_per_run": float(os.getenv("MAX_USD_PER_RUN", "5")),
        "cost_usd": 0.0,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
