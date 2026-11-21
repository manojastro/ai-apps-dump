"""Verifier: failing RunTrace -> Verdict (three-run retry, false-alarm killer).

Rule, enforced in code:
- 3/3 failed (assertion/product failures) -> real_bug
- 1-2/3 failed                          -> flaky (file nothing)
- any run failed on environment/login    -> blocked, NEVER real_bug
- 0/3 failed                             -> pass (initial failure didn't reproduce)

Design for testability: `verify()` takes an injectable `run_once`
callable `(run_number) -> AttemptResult`, so the decision + retry logic is
fully unit-tested offline. The live browser-backed `run_once` (fresh session
+ fresh TEST- data per run) lands with Phase 2 acceptance; until then there
is no fake browser run — only the decision engine below.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from sentinel.models import RunTrace, Verdict

logger = logging.getLogger("sentinel.verifier")

MAX_RUNS = 3


@dataclass
class AttemptResult:
    """One fresh run. `env_failure` is non-empty when the lab (not the product) broke."""

    trace: RunTrace
    env_failure: str = ""


def _trace_failed(trace: RunTrace) -> bool:
    if trace.final_state.lower().startswith("fail"):
        return True
    return any(not s.succeeded for s in trace.step_results)


def _failed_step_summary(trace: RunTrace) -> str:
    failed = [s for s in trace.step_results if not s.succeeded]
    if not failed:
        return f"final_state={trace.final_state!r} with all steps passing"
    first = failed[0]
    return (
        f"step {first.step_index} ({first.target_description}): "
        f"{first.error or 'unknown error'} "
        f"[console={len(first.console_errors)}, net_fail={len(first.failed_network_calls)}]"
    )


def classify_attempts(test_case_id: str, attempts: list[AttemptResult]) -> Verdict:
    """Pure decision function. Every branch is unit-tested in tests/test_verifier.py."""
    if not attempts:
        raise ValueError("classify_attempts needs at least one attempt")
    runs_attempted = len(attempts)
    env_failures = [a for a in attempts if a.env_failure]
    failed = [a for a in attempts if not a.env_failure and _trace_failed(a.trace)]
    passed = runs_attempted - len(env_failures) - len(failed)

    if env_failures and not failed:
        # Lab broken, zero product signal -> blocked, never real_bug.
        detail = "; ".join(a.env_failure for a in env_failures)
        return Verdict(
            test_case_id=test_case_id, classification="blocked", confidence=0.9,
            evidence_summary=(
                f"{len(env_failures)}/{runs_attempted} runs failed on environment "
                f"({detail}); no product failure observed. Not a bug."
            ),
            runs_attempted=runs_attempted, runs_failed=len(env_failures),
        )
    if env_failures and failed:
        # Mixed: unreliable lab, cannot convict -> blocked, say why.
        return Verdict(
            test_case_id=test_case_id, classification="blocked", confidence=0.6,
            evidence_summary=(
                f"Mixed signals: {len(failed)} product failure(s) but "
                f"{len(env_failures)} run(s) also hit environment problems "
                f"({'; '.join(a.env_failure for a in env_failures)}). "
                "Environment unreliable — refusing to file. Re-run when lab is healthy."
            ),
            runs_attempted=runs_attempted, runs_failed=len(failed) + len(env_failures),
        )
    if len(failed) == runs_attempted:
        if runs_attempted < MAX_RUNS:
            raise ValueError(f"Cannot convict real_bug on {runs_attempted}/{MAX_RUNS} runs")
        summary = _failed_step_summary(failed[0].trace)
        consistent = all(
            _failed_step_summary(a.trace) == summary for a in failed[1:]
        )
        return Verdict(
            test_case_id=test_case_id, classification="real_bug",
            confidence=0.95 if consistent else 0.8,
            evidence_summary=(
                f"Failed {runs_attempted}/{runs_attempted} fresh runs. "
                f"{'Same step every time' if consistent else 'Different steps failed'}: {summary}"
            ),
            runs_attempted=runs_attempted, runs_failed=len(failed),
        )
    if failed:
        return Verdict(
            test_case_id=test_case_id, classification="flaky",
            confidence=0.85 if passed else 0.7,
            evidence_summary=(
                f"Failed {len(failed)}/{runs_attempted} — intermittent, not a consistent "
                f"product failure ({_failed_step_summary(failed[0].trace)}). Filing nothing."
            ),
            runs_attempted=runs_attempted, runs_failed=len(failed),
        )
    return Verdict(
        test_case_id=test_case_id, classification="pass", confidence=0.9,
        evidence_summary=(
            f"Passed {runs_attempted}/{runs_attempted} fresh runs; "
            "initial failure did not reproduce."
        ),
        runs_attempted=runs_attempted, runs_failed=0,
    )


def verify(test_case_id: str, run_once, initial_trace: RunTrace | None = None) -> Verdict:
    """Run up to MAX_RUNS fresh attempts, then classify.

    `run_once(run_number) -> AttemptResult` is injectable: tests pass fakes,
    production passes the Phase-2 browser runner (fresh session + fresh
    TEST- data per run). `initial_trace` is the failing trace that triggered
    verification — kept as evidence context, NOT counted as an attempt.
    """
    attempts: list[AttemptResult] = []
    for run_number in range(1, MAX_RUNS + 1):
        try:
            attempts.append(run_once(run_number))
        except Exception as exc:  # runner crash == broken lab, not product signal
            logger.warning("Run %d crashed the runner: %s", run_number, exc)
            attempts.append(
                AttemptResult(
                    trace=RunTrace(test_case_id=test_case_id, run_number=run_number,
                                   step_results=[], final_state="fail: runner crashed"),
                    env_failure=f"runner crashed: {type(exc).__name__}: {str(exc)[:200]}",
                )
            )
    verdict = classify_attempts(test_case_id, attempts)
    logger.info(
        "Verdict %s -> %s (confidence %.2f, %d/%d failed): %s",
        test_case_id, verdict.classification, verdict.confidence,
        verdict.runs_failed, verdict.runs_attempted, verdict.evidence_summary,
    )
    if initial_trace is not None:
        logger.debug("Triggering trace: %s run %d", initial_trace.test_case_id, initial_trace.run_number)
    return verdict
