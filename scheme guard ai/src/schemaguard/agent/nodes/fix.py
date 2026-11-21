"""Nodes 8-11 + escalate: plan_fix, generate_patch, run_tests, check_tests, escalate."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from schemaguard.agent.guardrails import check_patch, wrap_untrusted
from schemaguard.agent.llm_calls import BudgetExceeded, call_llm, dumps, prompt
from schemaguard.agent.state import AgentState, Deps
from schemaguard.lineage.model import column_id
from schemaguard.llm.base import LLMError
from schemaguard.sandbox import run_sandbox
from schemaguard.sandbox.patching import make_unified_diff
from schemaguard.schemas.avro import parse_schema

STRATEGIES = {
    "update_sql_transform",
    "add_coalesce_default",
    "add_compat_view",
    "update_data_test",
    "pin_schema_version",
}
TESTS_FILE = "tests/data_tests.yaml"


def _edit_targets(deps: Deps, state: AgentState) -> dict[str, list[str]]:
    """Files that directly consume each changed field (first SQL hop), plus the data tests file."""
    lg = deps.lineage
    topic = state["schema_diff"]["topic"]
    targets: dict[str, list[str]] = {}
    raw_tables = (
        [
            t.split(":", 1)[1]
            for task, _ in lg.out(f"topic:{topic}", "CONSUMED_BY")
            for t, _ in lg.out(task, "WRITES")
        ]
        if lg.has(f"topic:{topic}")
        else []
    )
    for c in state["schema_diff"]["changes"]:
        files: set[str] = set()
        for raw in raw_tables:
            rc = column_id(raw, c["field"])
            if lg.has(rc):
                for _child, data in lg.inn(rc, "DERIVES_FROM"):
                    if data.get("sql_file"):
                        files.add(data["sql_file"])
        if c["kind"] == "enum_symbols_added":
            files.add(TESTS_FILE)
        targets[c["field"]] = sorted(files)
    return targets


def _read_files(deps: Deps, paths: set[str]) -> dict[str, str]:
    out = {}
    for p in sorted(paths):
        f = (deps.pipeline_dir / p).resolve()
        if deps.pipeline_dir.resolve() in f.parents and f.exists():
            out[p] = f.read_text(encoding="utf-8")
    return out


def _old_types(state: AgentState) -> dict[str, str]:
    return {f.name: f.duckdb_type for f in parse_schema(state["old_schema"]).fields}


def _failing_tests(state: AgentState) -> list[str]:
    return sorted(
        a["asset"].removeprefix("test:")
        for a in state.get("assessments", [])
        if a["type"] == "DataTest" and a["verdict"] == "breaking"
    )


def make_plan_fix(deps: Deps):
    def plan_fix(state: AgentState) -> dict[str, Any]:
        targets = _edit_targets(deps, state)
        files = _read_files(deps, {p for ps in targets.values() for p in ps})
        impacted = [a for a in state.get("assessments", []) if a["verdict"] != "safe"]
        changed_fields = {a["change"].split(":", 1)[1] for a in impacted if a.get("change")}
        changes = [c for c in state["schema_diff"]["changes"] if c["field"] in changed_fields]
        previous = state.get("attempts", [])
        ctx = {
            "topic": state["schema_diff"]["topic"],
            "changes": changes,
            "assessments": impacted,
            "edit_targets": targets,
            "files": files,
            "previous_attempts": previous,
            "allowed_paths": list(deps.settings.patch_allowed_paths),
        }
        user = prompt(
            "plan_fix",
            allowed_paths=", ".join(deps.settings.patch_allowed_paths),
            changes_json=dumps(changes),
            assessments_json=dumps(impacted[:60]),
            edit_targets_json=dumps(targets),
            previous_json=dumps(previous),
            files="\n".join(wrap_untrusted(p, t) for p, t in files.items()),
        )
        try:
            plan, ct = call_llm(deps, state, "plan_fix", user, ctx)
        except BudgetExceeded as exc:
            return {"route_reason": f"budget: {exc}", "errors": [str(exc)]}
        except LLMError as exc:
            return {"route_reason": f"llm_error: {exc}", "errors": [f"plan_fix: {exc}"]}
        strategy = plan.get("strategy")
        allowed_files = {p for ps in targets.values() for p in ps}
        problems = []
        if strategy not in STRATEGIES:
            problems.append(f"unknown strategy {strategy!r}")
        for e in plan.get("edits", []):
            bad = [f for f in e.get("files", []) if f not in allowed_files]
            if bad:
                problems.append(f"plan edits files outside edit targets: {bad}")
            e["files"] = [f for f in e.get("files", []) if f in allowed_files]
        plan["problems"] = problems
        out: dict[str, Any] = {"fix_plan": plan, "cost_tracking": ct, "route_reason": ""}
        if strategy == "pin_schema_version":
            out["route_reason"] = "plan: pin_schema_version (no safe code fix)"
        elif problems:
            out["route_reason"] = "plan rejected by guardrails: " + "; ".join(problems)
        return out

    return plan_fix


def route_after_plan(state: AgentState) -> str:
    r = state.get("route_reason", "")
    if r.startswith(("budget", "llm_error", "plan:")):
        return "escalate"
    if r.startswith("plan rejected"):
        return "escalate"
    return "generate_patch"


def make_generate_patch(deps: Deps):
    def generate_patch(state: AgentState) -> dict[str, Any]:
        plan = state["fix_plan"]
        paths = {f for e in plan.get("edits", []) for f in e.get("files", [])}
        files = _read_files(deps, paths)
        ctx = {
            "plan": plan,
            "files": files,
            "old_types": _old_types(state),
            "failing_tests": _failing_tests(state),
            "previous_attempts": state.get("attempts", []),
        }
        user = prompt(
            "generate_patch",
            allowed_paths=", ".join(deps.settings.patch_allowed_paths),
            plan_json=dumps(plan),
            types_json=dumps(ctx["old_types"]),
            previous_json=dumps(ctx["previous_attempts"]),
            files="\n".join(wrap_untrusted(p, t) for p, t in files.items()),
        )
        attempt = len(state.get("attempts", [])) + 1
        try:
            data, ct = call_llm(deps, state, "generate_patch", user, ctx)
        except BudgetExceeded as exc:
            return {
                "route_reason": f"budget: {exc}",
                "errors": [str(exc)],
                "patch": {"attempt": attempt, "diff": "", "check": {"ok": False, "violations": [str(exc)]}},
            }
        except LLMError as exc:
            data, ct = {"files": {}}, state.get("cost_tracking", {})
            state_err = [f"generate_patch: {exc}"]
        else:
            state_err = []
        new_files = {p: c for p, c in (data.get("files") or {}).items() if isinstance(c, str)}
        outside = sorted(set(new_files) - paths)
        # Diff only against files the plan named; anything else is reported as a violation.
        diff = make_unified_diff(files, {p: c for p, c in new_files.items() if p in paths})
        chk = check_patch(diff, deps.settings.patch_allowed_paths, deps.settings.patch_max_lines)
        violations = chk.violations + [f"model edited a file the plan did not name: {p}" for p in outside]
        return {
            "patch": {
                "attempt": attempt,
                "diff": diff,
                "files": chk.files,
                "summary": str(data.get("summary", ""))[:500],
                "check": {"ok": not violations, "violations": violations, "changed_lines": chk.changed_lines},
            },
            "cost_tracking": ct,
            "errors": state_err,
        }

    return generate_patch


def make_run_tests(deps: Deps):
    def run_tests(state: AgentState) -> dict[str, Any]:
        patch = state["patch"]
        run_dir = deps.settings.sandbox_root / state["run_id"]
        topic = state["schema_diff"]["topic"]
        out: dict[str, Any] = {}
        if not state.get("baseline_results"):
            base = run_sandbox(
                deps.pipeline_dir,
                run_dir / "baseline",
                "",
                topic,
                state["new_schema"],
                deps.settings.sandbox_timeout_s,
            )
            out["baseline_results"] = _summarise(base)
        if not patch["check"]["ok"]:
            res = {
                "ok": False,
                "skipped": True,
                "failures": ["guardrail: " + v for v in patch["check"]["violations"]],
                "tasks": [],
                "tests": [],
            }
        else:
            res = run_sandbox(
                deps.pipeline_dir,
                run_dir / f"attempt-{patch['attempt']}",
                patch["diff"],
                topic,
                state["new_schema"],
                deps.settings.sandbox_timeout_s,
            )
        summary = _summarise(res)
        attempts = list(state.get("attempts", [])) + [
            {
                "attempt": patch["attempt"],
                "strategy": state["fix_plan"].get("strategy"),
                "ok": summary["ok"],
                "failures": summary["failures"][:10],
                "files": patch.get("files", []),
            }
        ]
        out.update({"test_results": summary, "attempts": attempts})
        return out

    return run_tests


def _summarise(res: dict[str, Any]) -> dict[str, Any]:
    tests = res.get("tests", [])
    return {
        "ok": bool(res.get("ok")),
        "failures": list(res.get("failures", [])),
        "tasks": [
            {"task_id": t["task_id"], "status": t["status"], "rows": t.get("rows", 0)}
            for t in res.get("tasks", [])
        ],
        "tests": [{"name": t["name"], "passed": t["passed"], "detail": t["detail"]} for t in tests],
        "tests_passed": sum(1 for t in tests if t["passed"]),
        "tests_total": len(tests),
        "duration_s": res.get("duration_s"),
        "skipped": bool(res.get("skipped")),
    }


def make_check_tests(deps: Deps):
    def check_tests(state: AgentState) -> dict[str, Any]:
        res = state["test_results"]
        if res["ok"]:
            return {"route_reason": "tests passed"}
        retries = state.get("retry_count", 0) + 1
        if retries >= deps.settings.max_fix_retries:
            return {"retry_count": retries, "route_reason": f"tests failed after {retries} attempts"}
        return {"retry_count": retries, "route_reason": "retry"}

    return check_tests


def route_after_check(state: AgentState) -> str:
    if state["test_results"]["ok"]:
        return "human_approval"
    if state.get("route_reason") == "retry":
        return "plan_fix"
    return "escalate"


def make_escalate(deps: Deps):
    def escalate(state: AgentState) -> dict[str, Any]:
        reason = state.get("route_reason") or "escalated"
        return {"status": "escalated", "escalation_reason": reason, "approval_status": "not_requested"}

    return escalate


def artifacts_dir(deps: Deps, run_id: str) -> Path:
    d = deps.settings.artifacts_dir / run_id
    d.mkdir(parents=True, exist_ok=True)
    return d
