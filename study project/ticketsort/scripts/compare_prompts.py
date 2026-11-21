"""Compare two eval report JSONs and print deltas."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

KEYS = ["category_accuracy", "impact_accuracy", "urgency_accuracy", "service_accuracy", "priority_accuracy", "escalation_rate", "p95_latency_ms", "cost_per_ticket_usd"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("a", type=Path)
    ap.add_argument("b", type=Path)
    args = ap.parse_args()
    ra = json.loads(args.a.read_text())
    rb = json.loads(args.b.read_text())
    print(f"compare {args.a.name} -> {args.b.name}")
    for k in KEYS:
        va, vb = float(ra.get(k, 0)), float(rb.get(k, 0))
        flag = "  <-- REGRESSION" if (k != "escalation_rate" and "accuracy" in k and vb < va) else ""
        print(f"{k}: {va} -> {vb} (delta {vb - va:+.3f}){flag}")


if __name__ == "__main__":
    main()
