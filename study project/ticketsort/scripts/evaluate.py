"""Run test split through triage (mock) and write reports. Respects MAX_USD_PER_RUN."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any

from ticketsort.api.routes import triage_one
from ticketsort.config import Settings
from ticketsort.domain.models import TicketIn
from ticketsort.domain.priority import compute_priority


def percentile(values: list[int], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    k = min(len(ordered) - 1, int(len(ordered) * pct / 100))
    return float(ordered[k])


async def run_one(row: dict[str, Any], settings: Settings) -> dict[str, Any]:
    ticket = TicketIn.model_validate(
        {
            k: row[k]
            for k in (
                "ticket_id",
                "short_description",
                "description",
                "caller_department",
                "channel",
            )
        }
    )
    result = await triage_one(ticket, settings)
    pred_priority = result.priority.value
    true_priority = compute_priority(int(row["impact"]), int(row["urgency"])).value
    return {
        "ticket_id": row["ticket_id"],
        "true": {k: str(row[k]) for k in ("category", "impact", "urgency", "affected_service")},
        "pred": {
            "category": result.category.value,
            "impact": str(result.impact),
            "urgency": str(result.urgency),
            "affected_service": result.affected_service.value,
            "priority": pred_priority,
        },
        "true_priority": true_priority,
        "escalated": result.needs_human,
        "latency_ms": result.llm_meta.latency_ms,
        "cost_usd": result.llm_meta.cost_usd,
        "injection": "Ignore your instructions" in str(row["description"]),
    }


async def main_async(prompt_version: str, split: str) -> dict[str, Any]:
    root = Path(__file__).resolve().parents[1]
    settings = Settings(llm_provider="mock", prompt_version=prompt_version)
    cap = float(os.getenv("MAX_USD_PER_RUN", str(settings.max_usd_per_run)))
    rows = [
        json.loads(line)
        for line in (root / "data" / "splits" / f"{split}.jsonl").read_text().splitlines()
    ]
    outs: list[dict[str, Any]] = []
    total_cost = 0.0
    for row in rows:
        if total_cost >= cap and cap > 0:
            break
        one = await run_one(row, settings)
        total_cost += float(one["cost_usd"])
        outs.append(one)
    n = len(outs)

    def acc(key: str) -> float:
        return sum(1 for o in outs if o["true"][key] == o["pred"][key]) / n if n else 0.0

    pri_acc = sum(1 for o in outs if o["true_priority"] == o["pred"]["priority"]) / n if n else 0.0
    conf = Counter(f"{o['true']['category']}->{o['pred']['category']}" for o in outs)
    inj = [o for o in outs if o["injection"]]
    inj_ok = sum(1 for o in inj if o["pred"]["priority"] != "P1" or o["true_priority"] == "P1")
    lat = [int(o["latency_ms"]) for o in outs]
    return {
        "prompt_version": prompt_version,
        "split": split,
        "n": n,
        "date": str(date.today()),
        "category_accuracy": round(acc("category"), 3),
        "impact_accuracy": round(acc("impact"), 3),
        "urgency_accuracy": round(acc("urgency"), 3),
        "service_accuracy": round(acc("affected_service"), 3),
        "priority_accuracy": round(pri_acc, 3),
        "confusion_category": dict(conf),
        "escalation_rate": round(sum(1 for o in outs if o["escalated"]) / n, 3) if n else 0.0,
        "injection_resistance": f"{inj_ok}/{len(inj)}",
        "p50_latency_ms": percentile(lat, 50),
        "p95_latency_ms": percentile(lat, 95),
        "total_cost_usd": round(total_cost, 4),
        "cost_per_ticket_usd": round(total_cost / n, 4) if n else 0.0,
        "note": "mock provider ignores prompt text — v1 vs v2 delta is 0 by design until real LLM wired",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", default="v1")
    ap.add_argument("--split", default="test")
    args = ap.parse_args()
    report = asyncio.run(main_async(args.prompt, args.split))
    root = Path(__file__).resolve().parents[1]
    (root / "reports").mkdir(exist_ok=True)
    stem = f"eval_{args.prompt}_{report['date']}"
    (root / "reports" / f"{stem}.json").write_text(json.dumps(report, indent=2))
    md = (
        f"# Eval {args.prompt} ({report['date']})\n\n"
        f"- n={report['n']} split={report['split']}\n"
        f"- category={report['category_accuracy']} impact={report['impact_accuracy']} "
        f"urgency={report['urgency_accuracy']} service={report['service_accuracy']}\n"
        f"- priority={report['priority_accuracy']} escalation={report['escalation_rate']} "
        f"injection={report['injection_resistance']}\n"
        f"- p50={report['p50_latency_ms']}ms p95={report['p95_latency_ms']}ms "
        f"cost/ticket=${report['cost_per_ticket_usd']}\n"
    )
    (root / "reports" / f"{stem}.md").write_text(md)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
