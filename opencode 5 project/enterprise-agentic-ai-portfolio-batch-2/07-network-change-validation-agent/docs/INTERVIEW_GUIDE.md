# INTERVIEW GUIDE

## The 30-second pitch

"Before any network change reaches production, my agents rebuild the network as
a digital twin from the proposed diff, simulate routing, ACLs, firewall policy,
MTU and bidirectional reachability, check declarative business intents, and
block or remediate anything that would cause an outage or a security violation.
On a seeded fault catalog it catches 12 of 12 injected failure modes with zero
false positives on benign changes."

## Likely questions and strong answers

**Why deterministic agents instead of an LLM agent loop?**
Reliability and auditability. Network change gating must be reproducible: the
same diff always yields the same verdict. The LLM only narrates results; every
decision path is plain code that can be unit-tested — the RCA model, risk
formula and state machine all have exact contracts covered by tests.

**How does the reachability engine work?**
It derives broadcast segments from interface addressing (with VLAN compatibility
checks), builds per-device routing tables from connected, static, OSPF-SPF and
BGP sources with longest-prefix/admin-distance/cost selection, then walks flows
hop-by-hop evaluating ingress/egress ACLs, firewall policies, MTU on both
directions, recursive next-hop resolution and TTL guards. Forward and reverse
paths are compared for asymmetry.

**How do you avoid false positives?**
Baseline-first evaluation: intents are evaluated against CURRENT before judging
the candidate, so only *new* violations count. A benign change catalog entry
must produce zero findings and is part of the test suite.

**What happens if someone approves a dangerous change anyway?**
Post-apply verification re-runs the intent suite against the promoted twin;
any failure triggers automatic rollback to the archived pre-change snapshot,
and the whole sequence is in the audit log.

**How is risk scored?**
A transparent weighted formula over routing removals, broken intents, blocked/
opened flows, security violations, affected critical services, blast radius and
rollback complexity, discounted by pipeline confidence. Bands are LOW/MEDIUM/
HIGH/CRITICAL; HIGH+ requires written approval justification.

**What did you learn about agentic design?**
The agent framework value here is structure: typed tools with permissions and
audit, a shared evidence/hypothesis blackboard, persisted investigations with
durations, and clear separation between perception agents (what changed), analysis
agents (what it means) and the safety gate (what may happen next).

## Deep-dive anchors

- Twin engine math: `backend/app/services/twin.py` (route selection, ACL first-match)
- Ground truth harness: `simulator/faults.py` + `tests/test_failure_injection.py`
- Safety gate: `backend/app/services/state_machine.py`, `backend/app/tools/base.py`
- Remediation inversion: `agents/analysis_agents.py::invert_journal`
