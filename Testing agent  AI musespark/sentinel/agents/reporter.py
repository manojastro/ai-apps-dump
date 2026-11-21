"""Reporter: real_bug Verdict -> BugReport -> Jira issue (proposal, never auto-merged).

Two halves:
1. Pure assembly + duplicate detection (this module, fully unit-tested).
   A report missing any fix-critical field raises instead of filing thin.
2. HTTP delivery via sentinel.integrations.jira (slice C) — the live Jira
   call needs a real instance; until then delivery raises, assembly doesn't.

Duplicate policy: before filing, score existing issues by title overlap +
error-signature match. On likely duplicate, comment on the existing issue
and record suspected_duplicate_of — never file a second copy.
"""

from __future__ import annotations

import logging
import re

from sentinel.models import BugReport, RunTrace, TestCase, Verdict

logger = logging.getLogger("sentinel.reporter")

# Jaccard overlap at/above this on normalized titles counts as "same conversation".
DUPLICATE_TITLE_THRESHOLD = 0.5

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(text.lower()))


def _first_failing_trace(traces: list[RunTrace]) -> RunTrace:
    for trace in traces:
        if trace.final_state.lower().startswith("fail") or any(not s.succeeded for s in trace.step_results):
            return trace
    raise ValueError("assemble_bug_report needs at least one failing trace")


def error_signature(trace: RunTrace) -> str:
    """Stable fingerprint: failing intent + first console/net evidence, normalized."""
    for step in trace.step_results:
        if not step.succeeded:
            bits = [step.target_description.lower(), (step.error or "").lower().split("\n")[0][:160]]
            if step.console_errors:
                bits.append(step.console_errors[0].lower()[:160])
            for call in step.failed_network_calls:
                bits.append(f"{call.method} {call.url} {call.status or 'fail'}".lower()[:160])
            return " | ".join(b for b in bits if b)
    return f"final_state={trace.final_state}".lower()


def assemble_bug_report(
    *,
    verdict: Verdict,
    test_case: TestCase,
    traces: list[RunTrace],
    environment: str,
    test_data_used: str,
    video_path: str | None = None,
) -> BugReport:
    """Build a developer-ready report. Raises on real_bug mismatch or thin fields."""
    if verdict.classification != "real_bug":
        raise ValueError(
            f"Reporter only files real_bug; got {verdict.classification} for {verdict.test_case_id}. "
            "Flaky/blocked/pass verdicts file nothing."
        )
    if verdict.test_case_id != test_case.id:
        raise ValueError(f"Verdict {verdict.test_case_id} does not match case {test_case.id}")
    failing = _first_failing_trace(traces)
    bad_step = next((s for s in failing.step_results if not s.succeeded), None)

    steps = [f"{i}. {s}" for i, s in enumerate(test_case.steps, 1)]
    if bad_step is not None:
        steps.append(f"{len(steps) + 1}. OBSERVED FAILURE at {bad_step.target_description}: {bad_step.error}")

    console: list[str] = []
    network = []
    for trace in traces:
        for step in trace.step_results:
            console.extend(step.console_errors)
            network.extend(step.failed_network_calls)
    # De-dupe, keep order (three runs repeat the same errors).
    console = list(dict.fromkeys(console))

    gaps = {
        "environment": environment.strip(),
        "test_data_used": test_data_used.strip(),
        "expected_result": test_case.expected_result.strip(),
    }
    missing = sorted(k for k, v in gaps.items() if not v)
    if missing:
        raise ValueError(f"Refusing to file thin bug report; empty: {missing}")

    actual = (
        (f"Step failed: {bad_step.target_description} — {bad_step.error}" if bad_step else failing.final_state)
        + f" (reproduced {verdict.runs_failed}/{verdict.runs_attempted} fresh runs; "
        + f"verifier: {verdict.evidence_summary})"
    )
    return BugReport(
        title=f"[{test_case.id}] {test_case.title}",
        steps_to_reproduce=steps,
        expected=test_case.expected_result,
        actual=actual,
        environment=environment,
        video_path=video_path,
        console_log=console,
        network_log=network,
        test_data_used=test_data_used,
    )


def duplicate_score(title_a: str, sig_a: str, title_b: str, sig_b: str) -> float:
    """0..1. Title Jaccard plus a strong bonus for identical error signatures."""
    ta, tb = _tokens(title_a), _tokens(title_b)
    jaccard = len(ta & tb) / max(len(ta | tb), 1)
    score = 0.4 * jaccard
    if sig_a and sig_a == sig_b:
        score += 0.6
    elif sig_a and sig_b and (sig_a in sig_b or sig_b in sig_a):
        score += 0.3
    return min(score, 1.0)


def find_duplicate(report: BugReport, existing: list[dict], signature: str = "") -> str | None:
    """Return the issue key of a likely duplicate, else None.

    `existing` items: {"key": "SENT-123", "title": ..., "signature": ...}.
    `signature` is error_signature(failing_trace) from the caller — kept as an
    explicit parameter so matching uses the identical fingerprint, not a
    re-derivation from the report text.
    """
    best_key, best_score = None, 0.0
    for issue in existing:
        score = duplicate_score(report.title, signature, issue.get("title", ""), issue.get("signature", ""))
        if score > best_score:
            best_key, best_score = issue.get("key"), score
    if best_key is not None and best_score >= DUPLICATE_TITLE_THRESHOLD:
        logger.info("Likely duplicate of %s (score %.2f)", best_key, best_score)
        return best_key
    return None


def deliver(
    report: BugReport,
    *,
    signature: str,
    project: str,
    search_fn,
    create_fn,
    comment_fn,
) -> tuple[str, str]:
    """Route a report: comment on a likely duplicate, else create a new issue.

    Side-effect functions are injectable so routing is unit-tested with fakes;
    production passes bound JiraClient methods. Returns (issue_key, action)
    where action is "commented" or "created". Human review happens in Jira —
    nothing is auto-closed or auto-deployed, ever.
    """
    existing = search_fn(project, report.title)
    duplicate_of = find_duplicate(report, existing, signature=signature)
    if duplicate_of is not None:
        report.suspected_duplicate_of = duplicate_of
        comment_fn(
            duplicate_of,
            f"Sentinel re-observed this failure ({report.title}). "
            f"Actual: {report.actual} Environment: {report.environment}",
        )
        logger.info("Commented on likely duplicate %s instead of filing", duplicate_of)
        return duplicate_of, "commented"
    key = create_fn(project, report)
    logger.info("Filed new issue %s", key)
    return key, "created"


def report(*args, **kwargs):
    raise NotImplementedError(
        "Live Jira delivery needs a real instance (slice C client + Phase 5 wiring). "
        "Use assemble_bug_report + find_duplicate for the offline-verified path."
    )
