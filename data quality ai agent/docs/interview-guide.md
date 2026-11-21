# Interview guide

**What problem does this solve?** Monitoring supplies a failed-pipeline incident. RecoveryGraph
collects supporting evidence and tests a recovery proposal before releasing it for review.

**Why a graph?** Independent evidence sources run concurrently, join before synthesis, and route
through explicit confidence, validation, risk and approval boundaries. State and dependencies are
visible, unlike a single opaque agent call.

**How is parallelism proven?** The graph test uses a barrier requiring all five branches to arrive.
A sequential implementation cannot complete it. Runtime timings also record each branch.

**Why a loop?** The first proposal can be incorrect. Failed expected/actual data checks produce
feedback; the next candidate is tested on fresh input. Three attempts are allowed by default.

**What stops the loop?** Complete mandatory validation, exhausted budget or a terminal risk/error.
Verifier rejection cannot create an endless self-reflection loop.

**Why not let an LLM validate itself?** Numeric correctness, duplicates, schema and contract checks
are deterministic. Confidence or persuasive text cannot establish or override those invariants.

**What is independent about verification?** It is a separate rule-based component receiving only
public incident fields, evidence, hypothesis, candidate and validation results. Worker reasoning,
scenario labels and golden answers are excluded.

**How does state survive restart?** LangGraph checkpoints persist per incident. SQLAlchemy tables
project evidence, attempts, validations and approvals for queries. Restart tests restore a paused
checkpoint on a new connection and resume it with a human decision.

**What does approval do?** It releases a proposal artifact after risk policy review and fresh
post-validation. It does not modify a production system. Shared-token identity is a demo limitation.

**Why RAG?** Runbooks and business rules support incident reasoning. Retrieval filters pipeline and
environment before ranking. Offline feature hashing is a lexical vector baseline; learned semantic
embeddings are optional. Retrieved text cannot add tools or bypass validators.

**What tools can an agent call?** Explicit role-based allowlists. Investigators are read-only;
remediation is restricted to simulator operations. No arbitrary shell or SQL execution is exposed.

**What did evaluation show?** All 15 synthetic expected outcomes matched, including five intended
exhaustions. Ten incorrect-candidate probes produced zero false acceptances. This does not establish
generalization or live-model quality. Online evaluation is separate and opt-in.

**What is observable?** Node spans, structured workflow events, persisted audit records, duration,
attempt and validation counts, model token usage and optional configured cost estimates. No invented
detection speed is claimed because detection happens upstream.

**How are failures handled?** Model correction and transient API retries are bounded. Business
validation returns feedback. Insufficient evidence interrupts for manual review. Exhaustion and
unrecoverable errors terminate safely and withhold artifacts.

**What limits scaling?** One backend worker and process-local task locks. Introduce a durable queue,
distributed execution leases and idempotent adapter operations before increasing replicas. Move
migrations to a controlled deployment job and add retention policies for checkpoints/audit data.

**What are the main tradeoffs?** A reproducible simulator demonstrates control flow and correctness
boundaries without cloud credentials, but does not prove vendor integration reliability. A deterministic
verifier is auditable but only as complete as its rules. The console favors inspection over broad SaaS features.

**How would adapters extend?** Implement the protocols in `backend/app/adapters/protocols.py` for
Airflow/Dagster pipeline metadata and replay, database read evidence, observability, Git source changes,
or isolated sandbox operations. Preserve evidence contracts and add real integration tests per vendor.
