# Graph engineering

`backend/app/graph/workflow.py` compiles a typed LangGraph StateGraph. Intake loads the incident
fixture; context retrieval supplies metadata-filtered runbooks. Five independent edges fan out
to schema, quality, infrastructure, dependency and change investigators. A list-valued join edge
waits for every branch before evidence aggregation.

Each investigator owns a read-only evidence source and records an allowlisted tool call. State
reducers append branch evidence, timings and audit events. The aggregator deduplicates evidence
IDs before synthesis. Raw models are retained in state; prompts are constructed at provider
boundaries. `backend/tests/test_graph.py` includes a shared barrier test: a sequential implementation
cannot satisfy it.

Confidence below 0.75 requests one additional evidence round, then interrupts for manual
investigation if still insufficient. The risk gate blocks critical operations. Validation failure
routes to another plan while the attempt budget remains. Verification routes to rejection, approval
or artifact generation. These are explicit graph edges, not model-selected arbitrary tool calls.

Application projections live in SQLAlchemy tables; LangGraph checkpoints separately store execution
state under the incident's thread ID. SQLite supports native development and PostgreSQL supports
Compose. Pydantic types have a reconstruction allowlist; pickle is disabled. Approval uses LangGraph
`interrupt` and `Command(resume=...)`. Restart tests close the connection and restore the paused
workflow through a new graph instance before accepting a decision.

After a process interruption, the API run endpoint can resume a checkpoint with pending nodes;
human interrupts must use approval/rejection endpoints. Running incidents are not automatically
redispatched at startup. Exactly-once production side effects are not promised. All transformations
operate on fresh local copies, which makes replay appropriate for this demonstration.

A sequential script could implement the same business checks, but would hide dependency boundaries,
prevent concurrent evidence collection, and require custom persistence and approval state handling.
The graph makes these responsibilities visible and testable. For horizontal scale, first introduce
a durable queue, database-backed execution ownership and idempotent adapter operations; keep one
backend worker until then.
