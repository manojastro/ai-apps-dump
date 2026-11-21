# Architecture

## Why LangGraph

The flow Planner → Explorer → Verifier → Reporter → TestWriter is a fixed QA pipeline with retries in exactly one place (Verifier, 3 runs). LangGraph gives an explicit state machine (`sentinel/graph.py: SentinelState`) with typed edges instead of a free-form agent loop: each node input/output is a Pydantic model, failures are routable (blocked → stop, flaky → stop, real_bug → report), and the trace is replayable for evals. An AutoGPT-style loop cannot guarantee "never file on flaky".

## Why the accessibility tree

Salesforce Lightning hides internals behind Shadow DOM, generates dynamic IDs, and ships 3 releases/year that break selectors. Screenshots are pixels; the accessibility tree is intent ("button Save opportunity"). Explorer (Phase 2) observes the a11y tree primarily, screenshots only on failure for the bug report — cheaper in tokens and robust to DOM churn.

## Why the three-run verifier

A tool that cries wolf gets switched off. 3/3 fails → real_bug, 1–2/3 → flaky, env/login failure → blocked (never real_bug). Reasoning is logged per verdict so false alarms are auditable.

## Why deepeval

Python-native (matches uv/pytest stack), pytest-integrated, built-in LLM-as-judge for the 1–5 bug-report reproducibility rubric. promptfoo would split the repo into Node + Python for no gain.

## Guardrails (code, not prompt)

Domain allowlist, production block (sandbox/Dev only, fail loudly), blocked-action deny list, TEST- disposable data with finally-cleanup, token/$ kill switch, human reviews every issue/PR.
