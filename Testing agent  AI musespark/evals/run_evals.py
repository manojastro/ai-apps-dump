"""Golden harness runner: scenarios -> agent -> EvalReport.

Same injectable pattern as the Verifier: `run_golden(scenarios, agent_fn)`
takes `agent_fn(scenario) -> AgentOutcome`, so the full pipeline (load,
execute, score, render) is proven offline with a scripted fake agent. The
live `salesforce_agent_fn` (browser + model + judge) needs the org and keys;
`main()` refuses to run live until every prerequisite is present and says
exactly which are missing.
"""

from __future__ import annotations

import logging
import os
import shutil
import sys
from dataclasses import dataclass

from pydantic import BaseModel, Field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evals.metrics import EvalReport, EvalResult, compute_metrics, render_markdown
from sentinel.models import VerdictLabel

logger = logging.getLogger("sentinel.evals")


class GoldenScenario(BaseModel):
    id: str = Field(..., min_length=1)
    flow: str = Field(..., min_length=1, description="What the agent must do.")
    setup: str = Field(default="", description="Org mutation establishing ground truth.")
    expected: VerdictLabel


@dataclass
class AgentOutcome:
    predicted: VerdictLabel
    cost_usd: float = 0.0
    steps: int = 0
    bug_quality: int | None = None


def load_scenarios(path: str) -> list[GoldenScenario]:
    try:
        import yaml  # deepeval pulls PyYAML; kept import-local to that fact
    except ImportError as exc:
        raise RuntimeError("PyYAML not installed (expected via deepeval)") from exc
    with open(path, encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)
    if not isinstance(raw, list):
        raise ValueError(f"{path}: expected a YAML list of scenarios")
    scenarios = [GoldenScenario(**item) for item in raw]
    ids = [s.id for s in scenarios]
    if len(set(ids)) != len(ids):
        raise ValueError(f"{path}: duplicate scenario ids")
    return scenarios


def run_golden(scenarios: list[GoldenScenario], agent_fn) -> EvalReport:
    results: list[EvalResult] = []
    for scenario in scenarios:
        try:
            outcome: AgentOutcome = agent_fn(scenario)
        except Exception as exc:
            logger.warning("Scenario %s: agent crashed: %s", scenario.id, exc)
            outcome = AgentOutcome(predicted="blocked")
        results.append(EvalResult(scenario_id=scenario.id, expected=scenario.expected,
                                  predicted=outcome.predicted, cost_usd=outcome.cost_usd,
                                  steps=outcome.steps, bug_quality=outcome.bug_quality))
    report = compute_metrics(results)
    logger.info("Eval complete: n=%d precision=%.3f recall=%.3f FAR=%.3f",
                report.n, report.precision, report.recall, report.false_alarm_rate)
    return report


def live_prerequisites() -> list[str]:
    missing = []
    if not os.getenv("ANTHROPIC_API_KEY"):
        missing.append("ANTHROPIC_API_KEY")
    if shutil.which("sf") is None:
        missing.append("sf CLI on PATH (+ `sf org login web`)")
    if not os.getenv("SALESFORCE_INSTANCE_URL"):
        missing.append("SALESFORCE_INSTANCE_URL")
    return missing


def main() -> int:
    missing = live_prerequisites()
    if missing:
        print("Live evals refusing to run. Missing prerequisites:")
        for item in missing:
            print(f"  - {item}")
        print("Offline path (tested): run_golden(scenarios, agent_fn) with any agent_fn.")
        return 2
    raise NotImplementedError(
        "Live salesforce_agent_fn lands with Phase 2 acceptance (browser runner).")


if __name__ == "__main__":
    raise SystemExit(main())
