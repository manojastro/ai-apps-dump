# Evaluation methodology

`packages/evaluation/catalog.py` defines 48 stable cases: 16 fault diagnoses, 8 healthy/misleading correlations, 8 evidence-quality failures, 6 connector failures, 6 integrity/tool-authorization cases, and 4 lifecycle cases. Cases are synthetic and **unreviewed**. The catalog marks every fourth case as held out; no prompt tuning or automated human review is claimed.

The fixed script and deliberately regressed script receive identical snapshots and a 12-call tool budget. Each trial launches the agent in a separate Python process with only visible telemetry and permitted controller probes. Expected labels and grading stay in the controller. Four lifecycle cases use a fresh database and actual API/worker/executor code, including a different interpreter for restart recovery.

This is **deterministic plumbing evaluation**. It is not a real-model reasoning benchmark. Single-call LLM and iterative-agent comparisons are not yet implemented in the benchmark runner. Live model and full end-to-end collector-backed evaluations remain required before release.

Scoring is calculated in code with denominators. Diagnosis accuracy covers the 16 diagnosis cases. Every case has explicit assertions; failures and execution errors remain visible. Restart/approval checks are distinct from diagnosis quality. Semantic claim support is not assessed because cases have not been reviewed. Token usage is zero for scripts, and dollar cost is null, not a fabricated estimate.

The release policy is versioned in `packages/evaluation/policy.json`: minimum diagnosis accuracy 85%, regression allowance 2 percentage points, per-case latency limit 10 seconds, and zero prohibited effects. These are initial project choices, not industry standards. Missing critical execution, human review or real-model evaluation gives insufficient evidence. Explicit regression or quality failures give fail. A finite suite never proves universal safety.

Repeated trials are supported (1–3). Single-case reruns preserve inspectable outputs and do not satisfy the full mandatory suite. Reports preserve method, commit identity when available, prompt/source hash, tool-contract hash, model, generation settings, runtime limits and lock hash. Do not compare older and newer benchmark reports as one identical experiment after code changes.
