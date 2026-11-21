from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.agents.graph import run_pipeline  # noqa: E402
from app.models.profile import Holding, HouseholdProfile  # noqa: E402
from app.pdf.renderer import render_plan_pdf  # noqa: E402


def main() -> int:
    data = json.loads((ROOT / "evals" / "households.json").read_text(encoding="utf-8"))
    failures = 0
    for row in data["households"]:
        profile = HouseholdProfile.model_validate(row["profile"])
        raw = row.get("pasted_holdings")
        if raw:
            from app.engine.holdings import parse_holdings_text

            holdings, _ = parse_holdings_text(raw)
        else:
            holdings = [Holding.model_validate(h) for h in profile.existing_holdings]
        plan = run_pipeline(profile, holdings, conflict=row["id"] == "11")
        names = {s.name for s in plan.scenarios}
        print(f"fixture {row['id']}: {row['label']} status={plan.risk_status} scenarios={names}")
        if row["id"] == "2":
            render_plan_pdf(plan, ROOT / "data" / "pdfs" / "eval-fixture-2.pdf")
        if row["id"] == "9":
            if any(s.international_pct > 0.05 or s.alternatives_pct > 0.05 for s in plan.scenarios):
                print("  FAIL constraint leak")
                failures += 1
        if row["id"] == "6" and not any("chit" in v.message.lower() or v.code == "FORBIDDEN_PRODUCT" for v in plan.vetoes):
            print("  FAIL chit not vetoed")
            failures += 1
    return failures


if __name__ == "__main__":
    raise SystemExit(main())
