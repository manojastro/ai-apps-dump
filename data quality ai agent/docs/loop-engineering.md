# Loop engineering

The objective is an evidence-supported recovery candidate whose replay passes all ten mandatory
checks. The provider proposes an allowlisted configuration, never arbitrary executable code.
The simulator starts each attempt from a fresh copy, applies the candidate, and replays the pipeline.

Validators inspect schema, row count, null rate, duplicates, freshness, types, business rules,
transformation correctness, downstream contract and pipeline completion. Their expected/actual
values and evidence are persisted with each attempt. `all_passed` checks the complete mandatory
inventory, so missing checks cannot become a pass.

Failures become structured feedback for the next planner call. The default budget is three
attempts, configurable within the validated 1–10 range. Exhaustion, critical risk or unrecoverable
errors terminate safely. Passing validation enters the separate verifier, whose rejection does
not trigger an endless self-review loop. Medium/high risk requires durable human approval.

The scripted schema-drift demo sets `demo_force_first_fix_fail=true`:

1. Attempt 1 repairs identifier mapping but applies incorrect currency units.
2. TransformationValidator compares per-transaction amounts with the reference ledger and rejects it.
3. Feedback reaches the planner; attempt 2 corrects units and passes all mandatory checks.
4. The independent verifier checks grounding, check inventory, permissions and risk.
5. A fresh replay passes post-validation before the artifact is released.

This switch is explicit for the demo; normal backend configuration defaults to false. The console
labels its checked demo option. Rejected attempt evidence remains available after success.

LLM self-reflection cannot establish these numeric invariants or override a failed check. A model
may explain a failure, but acceptance belongs to the deterministic boundary. Online provider retries
are separately bounded to three structured-output attempts; this is distinct from the remediation
budget. Live provider behavior remains an unverified integration until tested with credentials.
