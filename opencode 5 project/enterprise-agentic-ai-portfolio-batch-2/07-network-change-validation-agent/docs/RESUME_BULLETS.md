# RESUME BULLETS

- Built an AI Network Digital Twin & Change Validation Agent that simulates
  every proposed network change (routing, ACLs, firewall policy, VLAN adjacency,
  MTU, asymmetric routing) against a deterministic digital twin before
  production, catching 12/12 injected fault scenarios with zero false positives.

- Designed a multi-agent validation pipeline (9 deterministic agents: config
  analysis, topology, routing, reachability, security policy, impact scoring,
  root-cause analysis, remediation, verdict) with persisted investigations,
  evidence chains and hypothesis tracking for full auditability.

- Implemented a graph-based reachability engine with longest-prefix route
  selection across static/OSPF/BGP sources, recursive next-hop resolution,
  per-hop ACL/firewall/MTU evaluation, and forward-vs-reverse asymmetric-path
  detection over 168 endpoint x port probes.

- Enforced a change-safety state machine (PROPOSED to COMPLETED/ROLLED_BACK)
  with approval-gated mutating tools, justification requirements for high-risk
  changes, automatic post-apply verification and rollback; illegal transitions
  rejected at the API contract level (HTTP 409).

- Created a declarative intent-policy language (must-reach, isolation,
  route-redundancy, management-exposure) converted into deterministic checks
  with baseline-relative evaluation to eliminate false positives.

- Shipped a typed tool framework with pydantic schemas, safe/mutating permission
  classes, timeouts and per-call audit persistence; FastAPI service exposing 20+
  endpoints including Prometheus metrics, plus a dark-mode operations dashboard
  with SVG topology, matrix diffs and approval queue.

- Delivered an evaluation harness reporting detection accuracy, recall,
  precision, unsafe-change prevention rate and validation latency; authored 79
  passing tests spanning engine mathematics, tool contracts, API behavior,
  workflow lifecycle and end-to-end demo parity.
