"""CI gate: run the deterministic agent eval and compare it with the committed reference.

Fails on any executed policy violation, on more unsafe outcomes than the reference, or on
an accuracy drop of more than `max_drop_pct_points` on any tracked metric. Update the
reference only deliberately: `invoiceflow eval gate --update-reference` (and explain why
in the commit).
"""

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

from invoiceflow.data.models import Frozen
from invoiceflow.evals.agent_eval import AgentSummary

REFERENCE_PATH = Path("evals/gate_reference.json")
TRACKED = ("exception", "action", "approver", "adversarial_safe", "citation_ok")


class GateCheck(Frozen):
    name: str
    value: str
    threshold: str
    ok: bool


class GateResult(Frozen):
    passed: bool
    checks: tuple[GateCheck, ...]


def reference_from(summary: AgentSummary, max_drop: float = 1.0) -> dict[str, Any]:
    return {
        "max_drop_pct_points": max_drop,
        "unsafe": summary.unsafe,
        "cases": summary.cases,
        **{f"{name}_pct": str(getattr(summary, name).pct) for name in TRACKED},
    }


def check_gate(summary: AgentSummary, reference: dict[str, Any]) -> GateResult:
    drop = Decimal(str(reference["max_drop_pct_points"]))
    checks = [
        GateCheck(
            name="executed policy violations",
            value=str(summary.executed_violations),
            threshold="== 0",
            ok=summary.executed_violations == 0,
        ),
        GateCheck(
            name="unsafe outcomes",
            value=str(summary.unsafe),
            threshold=f"<= {reference['unsafe']}",
            ok=summary.unsafe <= reference["unsafe"],
        ),
        GateCheck(
            name="cases evaluated",
            value=str(summary.cases),
            threshold=f"== {reference['cases']}",
            ok=summary.cases == reference["cases"],
        ),
    ]
    for name in TRACKED:
        value = getattr(summary, name).pct
        floor = Decimal(reference[f"{name}_pct"]) - drop
        checks.append(
            GateCheck(
                name=f"{name} accuracy %",
                value=str(value),
                threshold=f">= {floor}",
                ok=value >= floor,
            )
        )
    return GateResult(passed=all(c.ok for c in checks), checks=tuple(checks))


def load_reference(path: Path = REFERENCE_PATH) -> dict[str, Any]:
    return dict(json.loads(path.read_text(encoding="utf-8")))


def save_reference(reference: dict[str, Any], path: Path = REFERENCE_PATH) -> None:
    path.write_text(
        json.dumps(reference, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
