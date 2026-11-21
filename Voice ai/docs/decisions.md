# Design decisions (interview-ready, 2-3 sentences each)

**Multiple agents instead of one big prompt.** Each agent gets a small prompt and a short tool allow-list, so it is
easier to test and a mistake has a small blast radius. Roles also map cleanly onto permissions.

**RBAC in a gateway, not in prompts.** A prompt can be bypassed by a clever input; a check in code on every call
cannot. Denied calls are returned as errors and audited, so attempts are visible.

**Patient scoping at the gateway.** A task is tied to one patient id and any tool call touching another patient is
denied. That turns "show me other patients' data" from a prompt-following problem into a code-enforced one.

**Thresholds in code; the flag tool re-checks them.** Clinical judgement is never automated: fixed numbers flag and
a human decides. The tool recomputes the thresholds itself, so a model can neither create nor suppress a flag.

**Summaries are validated, with a fixed fallback.** The LLM writes a neutral summary that is checked for diagnosis,
urgency and reassurance wording. If it fails twice the check-in is still flagged using a template, and the failure is
recorded, so a bad model can never hide a flagged case.

**SQLite outbox as the queue.** It is durable, transactional, and easy to inspect. A claim is a single
`UPDATE ... RETURNING`, so two workers never get the same event. A lease timeout returns events from crashed
workers (at-least-once delivery) and retries back off exponentially up to 5 attempts, then DEAD.

**At-least-once delivery + idempotency keys = effectively-once effects.** Events may be redelivered, so every
state-changing tool call carries a deterministic key (workflow, step, attempt). A replay returns the stored result
instead of repeating the action. The model never picks the key; the agent loop injects it.

**Persist the transition after the step, guard with a version.** A crash between "work done" and "state saved"
re-runs an idempotent step on resume. Optimistic versioning rejects two workers advancing the same workflow.

**Crash tests kill at every crash point.** The engine exposes a fault hook after each step and after each event;
the test runs a clean workflow, then re-runs it crashing at each point in turn, and requires the final state to be
identical. That is the evidence for "survives a restart", not just one lucky kill.

**Timers are events.** A timer is an outbox event with a future `available_at`, so it survives restarts like
everything else. A simulated clock lets tests jump 3 days.

**Approvals expire, one re-draft only.** Rejection (with a required reason) or expiry triggers exactly one
re-draft; the second time the workflow stops or escalates to staff. This bounds cost and avoids endless loops.

**Mock LLM with a "gullible" mode.** Offline tests cost nothing and are deterministic. A simulated compromised
model that obeys any patient text lets the evals test the *system* defences. It does not say anything about how a
real model behaves, and the README says so.

**Plain Python agent loop before any framework.** The loop is ~100 lines (prompt, tool call, gateway, result,
step limit), which makes the security boundary obvious. Frameworks would hide exactly the parts being demonstrated.

**How this would map to an agent framework.** With Google ADK, each agent becomes an `LlmAgent` with a tool list and
the gateway becomes a tool wrapper or `before_tool_callback`; the orchestrator's state machine could become a
`SequentialAgent`/custom workflow agent with session state. With LangGraph, each workflow is a graph, the persisted
workflow row becomes a checkpointer, and approvals are `interrupt` nodes. In both, the RBAC gateway, idempotency
keys and approval service would stay as they are, because they are the parts that must not live in the framework.

**Console escapes everything.** Patient free text is shown to staff; Jinja2 autoescaping (tested with a script tag)
prevents stored XSS from injected text.
