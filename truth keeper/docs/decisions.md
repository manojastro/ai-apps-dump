# Design decisions

Each entry is written the way I would explain it in an interview: what, and why, in a few sentences.

### 1. Rules detect, the LLM explains
Whether a conflict exists is decided by deterministic code in `app/core/detector.py`. The LLM only
writes the explanation and picks a fix. Detection then stays testable, repeatable and auditable: the
same data always gives the same conflicts, and a model mistake can never invent or hide a conflict.

### 2. Build the non-AI baseline first and measure it
The detector was scored against planted ground truth before any LLM code existed. That gives a
baseline: the LLM has to add value on top of something that already works and has a number, not
replace it.

### 3. Ground truth is planted, not labelled after the fact
The generator plants each conflict on purpose and writes it to `ground_truth.json` with the expected
fix and ids. Every precision, recall and accuracy figure is then checked against known answers.
Each customer has at most one planted conflict so the truth is unambiguous.

### 4. Noise that must NOT fire is part of the data
Case and space differences, `+tag` email sub-addressing, plan-name casing and aliases, trial accounts
without billing, past-due under (and exactly at) 30 days, and billing records with no CRM reference
are all generated on purpose. Unit tests assert none of them produce a conflict. This tests precision,
not just recall.

### 5. Matching order: id, then email, then fuzzy name + domain
A CRM reference is the strongest signal, then a normalised email. Fuzzy name matching is only allowed
inside the same email domain, and ties are refused rather than guessed. Every link records its method
and confidence, which also appear in the evidence. The `name_only` debugging strategy shows why:
overall precision drops from 1.00 to 0.29 (EMAIL_MISMATCH 0.12, DUPLICATE_CUSTOMER 0.12) because
people with the same name at different companies get merged.

### 6. The LLM picks from an allow-list Enum, checked again by code
`Action` is an Enum. A per-type compatibility table (`app/core/actions.py`) says which actions make
sense for which conflict. Per-action Pydantic models check params, and every id in the params must
appear in that conflict's evidence. The model cannot cancel a subscription it was not shown.

### 7. Validate, retry at most twice, then FAIL loudly
Bad JSON, schema errors, disallowed or incompatible actions, invented ids and long explanations each
have a failure category. The error is fed back for at most two retries. After that the proposal is
stored as FAILED with its reason and raw responses. It is never accepted silently. With no retry
cap, a model that always returns bad JSON would loop forever and burn tokens. The cap keeps the
worst case at 3 calls per conflict.

### 8. Minimum context to the model
The LLM sees only the conflict type and its evidence: no other customers, no database, no impact
numbers. Less data means less leakage, lower cost, and fewer ways for unrelated text to steer the
answer. A test asserts exactly what is sent.

### 9. One LLM module with a MOCK mode
`app/llm/client.py` is the only code that talks to a model. MOCK mode is deterministic, offline and
free, so all 87 tests run in CI without a key. The `noisy` mock profile injects realistic faults so
retries, failure handling, evals and the regression loop can all be exercised for free. Mock numbers
are always labelled as mock: they measure the plumbing, not a model.

### 10. Structured outputs and our own validation
In real mode the client asks the API for JSON-schema-constrained output (`output_config.format`). We
still parse and validate with our own Pydantic models, because the schema cannot express "this id
must be in the evidence" or "this action fits this conflict type". Structured output can be switched
off (`LLM_STRUCTURED_OUTPUT=false`) to measure the raw schema-valid rate.

### 11. Humans approve; approval is a record, not a flag
Approving creates an `approvals` row (who, when, note) and an audit entry. A rejection needs a reason.
The applier refuses anything without both the APPROVED status and an approval row.

### 12. Idempotent applies with a stale check
Applying an already-applied proposal is a no-op, and each action checks the target state first
(cancelling a cancelled subscription changes nothing). Before writing, the applier re-detects the
conflict and compares the evidence with what was approved. If the data changed, the proposal becomes
STALE and nothing is written. A human approved a fix for specific data, not for whatever is there now.

### 13. Append-only audit log, enforced twice
The audit module has only `append` and read functions. SQLite triggers also abort any UPDATE or
DELETE on `audit_log`, so even raw SQL cannot rewrite history. Tests check both.

### 14. Sandbox only
Generated originals live in `data/generated/`. The applier writes only under the sandbox dir and
refuses any other path (`assert_writable`). Resetting the sandbox copies the originals back.

### 15. "Flag for finance review" hands the case to a human queue
Some conflicts (email mismatches, long overdue balances) should not be changed automatically. That
fix writes a `review_flags` row in the billing sandbox, and the detector stops re-reporting a
conflict with an open flag. This is how a real hand-off to another team's queue would work.

### 16. Failures become regression tests
Every FAILED proposal, wrong action (vs ground truth) and human rejection is saved to
`evals/regressions/` with the recorded model responses. `tests/test_regressions.py` replays them in
MOCK mode on every run, and against the real model on demand. The hand-built guard cases from the
debugging exercises live there too.

### 17. Tracing with OpenTelemetry + OpenInference attributes
Every pipeline step and LLM call is a span. LLM spans carry model, prompt version, input, output,
token counts and latency, using OpenInference names so Phoenix shows them as LLM calls. Without an
endpoint, tracing is a no-op, so tests and CI need nothing extra.

### 18. SQLite per system instead of a warehouse
Three SQLite files look like three separate systems and need zero setup. The trade-off is that they
are nothing like real API limits, pagination or eventual consistency. Real connectors (Salesforce,
Stripe and HubSpot sandboxes) are the next step.
