# RecoveryGraph architecture

RecoveryGraph starts with a reported pipeline incident. It produces a reviewed recovery artifact,
never a production mutation. The implementation follows the supplied master specification.

## Execution boundary

FastAPI owns lifecycle and incident execution. A typed LangGraph StateGraph fans out to five read-only
investigators, joins their evidence, diagnoses a cause, and enters a bounded plan/apply/replay/validate
loop. Ten mandatory deterministic validators inspect actual transformed rows. A separate verifier
receives only an explicit public evidence package. Risk rules can block an action or interrupt for
human approval. Approval releases an artifact, not deployment permission.

## Data boundary

Six adapter protocols isolate pipeline, database, observability, source control, sandbox, and knowledge.
The simulator replays fixture rows under an allowlisted transformation configuration. It does not
execute generated Python, SQL, shell commands, or user-selected filesystem paths. Golden labels stay
outside worker/verifier input. Every attempt starts with a fresh copy of the original data.

## Persistence and local operation

SQLAlchemy relational records store incidents, events, evidence, hypotheses, attempts, validation
results, verifications, approvals, audit entries, knowledge and evaluation results. LangGraph's
supported checkpointers separately store execution state per incident thread. SQLite supports a
zero-service local demo; Docker uses PostgreSQL + pgvector and PostgreSQL checkpoints. Versioned
Alembic migrations own application tables. One backend worker is supported; horizontal queue-based
execution is an explicit future hardening requirement.

## Retrieval and providers

Knowledge uses pipeline/environment filters and hybrid retrieval. Local feature-hash embeddings
provide a deterministic lexical vector baseline; optional OpenAI-compatible embeddings enable real
semantic retrieval. pgvector stores and ranks vectors in Postgres. The local substitute uses the same
cosine scoring. Model providers return Pydantic-validated structured hypotheses and candidates. A
deterministic provider makes all five scenarios reproducible without credentials.

## Delivery order

1. Simulator and contracts, validated by broken and recovered replay tests.
2. Validators, graph, bounded loop, isolated verifier, interruption and persistence tests.
3. Retrieval, provider adapters, API, audit and measured telemetry.
4. React investigation console with actual graph/evidence/attempt/approval data.
5. Golden evaluation, containers, CI, Kubernetes, documentation and browser verification.

The root pyproject and uv.lock own Python dependencies for backend, simulator and evaluations so
the three packages cannot drift. Individual backend modules remain under backend/app.
