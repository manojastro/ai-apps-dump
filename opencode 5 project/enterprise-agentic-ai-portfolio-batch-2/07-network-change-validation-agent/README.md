# AI Network Digital Twin & Change Validation Agent

## Executive Summary

This project answers one question before every network change reaches production:
**will it cause an outage, a routing problem, a security violation, or a
reachability regression?**

A deterministic multi-agent pipeline parses the proposed configuration diff,
builds a CANDIDATE digital twin of the network, simulates routing, ACLs,
firewall policy, MTU and bidirectional reachability, compares the candidate
against the CURRENT twin, evaluates declarative intent policies (segmentation,
redundancy, management exposure), performs root-cause analysis on every detected
regression, computes an explainable risk score, proposes and re-validates a
safer configuration when regressions exist, and enforces a human approval gate
before anything is applied. Post-apply verification re-runs the full intent
suite; failed verifications trigger automatic rollback.

On the bundled fault catalog the system achieves 100% detection accuracy
(12/12 injected faults caught with their ground-truth regression classes) with
zero false positives on benign changes.

## Enterprise Problem

Network changes are the leading self-inflicted cause of enterprise outages.
Change windows are risky because:

- Change Advisory Boards review text diffs without understanding reachability impact.
- Pre-production labs never match production; "test in lab" fails silently.
- Routing, security policy, VLAN adjacency and service dependencies interact
  in ways no human can fully simulate mentally.
- Segmentation violations (finance talking to dev, internet reaching databases)
  rarely page anyone — they are discovered during audits or breaches.

## Why It Matters

- **Outage prevention**: intent tests encode business guarantees ("app tier MUST
  reach postgres", "branch prefix has primary AND backup path") and fail loudly
  when a change breaks them.
- **Security enforcement**: forbidden-flow intents catch changes that silently
  open east-west paths.
- **Explainability**: every regression carries evidence, hypotheses, a root
  cause, and a recommended remediation — reviewers see *why*, not just *what*.
- **Safety**: nothing mutates the twin without passing the approval state
  machine; post-apply verification auto-rolls back harmful changes.
- **Auditability**: every tool call, agent investigation, hypothesis,
  approval decision and KPI snapshot is persisted.

## Architecture

```
frontend/index.html          dark operations dashboard (SVG topology, matrix, gates)
backend/app/
  api/            FastAPI routers: /api/v1/*, health, readiness, metrics, dashboard
  agents/         deterministic AgentPipeline: 9 agents (see below)
  tools/          typed tool framework + 7 network tools (safe | mutating)
  services/       twin engine, intent evaluator, validation orchestrator,
                  approval state machine, LLM adapter, metrics
  models/         SQLAlchemy entities (SQLite via create_all)
  schemas/        Pydantic v2 API contracts incl. exact RootCauseAnalysis model
  repositories/   data-access layer over sessions
simulator/        normalized multi-vendor-flavored network model, seeded lab,
                  config renderer/parser/applier, fault injection catalog
scripts/          inject_bad_network_change.py demo, evaluate.py harness
tests/            pytest suite (unit, tools, agents, api, workflow, validation,
                  failure-injection ground truth, e2e)
```

## Agent Architecture

All agents are deterministic (no LLM in the decision loop). Each persists an
Investigation with duration_ms, Evidence items and Hypotheses:

| Agent | Responsibility |
|---|---|
| ConfigAnalysisAgent | parses unified diff into structured ops; classifies riskiness |
| TopologyAgent | interface/VLAN/addressing diffs, duplicate IPs, overlapping subnets |
| RoutingAgent | per-device routing table diff; route removals; internal-prefix hijacks |
| ReachabilityAgent | endpoint x port matrix diff; blocked flows; asymmetry; host isolation |
| SecurityPolicyAgent | must_not_reach / only_from_subnet / redundancy intent violations |
| ChangeImpactAgent | deterministic weighted risk score -> LOW/MEDIUM/HIGH/CRITICAL |
| RCAAgent | observations, confirmed/rejected hypotheses, root cause, confidence, actions |
| RemediationAgent | inverts implicated ops into a safer config and re-simulates it |
| ValidationAgent | assembles verdict PASS/FAIL, stages, narration |

The LLM adapter (`services/llm.py`) renders human-readable narration of already
computed results. `LLM_MODE=live` calls any OpenAI-compatible endpoint; the LLM
never controls control flow.

## Workflow

1. Submit change (unified config diff) -> parse diff -> build CANDIDATE twin.
2. Topology impact -> routing diff -> reachability matrix diff vs CURRENT.
3. Intent/security policy suite on candidate vs baseline results.
4. Regressions aggregated -> RCA (hypotheses, rejected hypotheses, root cause).
5. Risk score from deterministic formula (routing + reachability + security +
   blast radius + rollback complexity - confidence).
6. Safer-config proposal -> re-simulation -> adopted as effective candidate.
7. Validation report -> human approval gate (justification required for HIGH/CRITICAL).
8. Apply -> promote candidate to CURRENT -> post-apply verification ->
   COMPLETED, or automatic rollback on verification failure.

Approval state machine:
`PROPOSED -> VALIDATING -> AWAITING_APPROVAL -> APPROVED -> EXECUTING ->
VERIFYING -> COMPLETED | FAILED -> ROLLED_BACK` (+ REJECTED terminal).
Illegal transitions return HTTP 409.

## Tools

Typed framework (`tools/base.py`): pydantic input/output schemas, permission
class (`safe` | `mutating`), timeout thread, every invocation audited into
`tool_calls`. No shell execution anywhere.

| Tool | Permission |
|---|---|
| parse_config_diff_tool | safe |
| build_candidate_topology_tool | safe |
| reachability_matrix_tool | safe |
| routing_table_diff_tool | safe |
| policy_check_tool | safe |
| apply_change_tool | mutating (approval-gated) |
| rollback_tool | mutating |

## Data Model

Persisted tables: devices, interfaces, vlans, subnets, acl_rules, routes,
bgp_neighbors, firewall_policies, network_snapshots (CURRENT/CANDIDATE versions
with full JSON payload), changes, diffs, validation_runs, intent_tests +
intent_test_results, regressions, investigations, evidence, hypotheses,
rca_records, approvals, audit_events, tool_calls, kpi_snapshots.

## Safety Model

- Mutating tools refuse to run outside the approval gate.
- Applying requires APPROVED status; HIGH/CRITICAL risk requires written justification.
- Candidate snapshots are versioned; rollback restores the archived pre-change CURRENT snapshot.
- Post-apply verification re-runs the intent suite; failure triggers auto-rollback.
- The LLM is narration-only; all gating is deterministic code.

## Validation

Declarative JSON intents are converted to deterministic checks against the twin:
representative-host flow probes, port sweeps for isolation intents, distinct
next-hop counting for route redundancy, and source-subnet enumeration for
management exposure. Baseline compliance must be 100% before a change is judged;
only *new* violations count as regressions (zero false positives on a clean twin).

## Evaluation

`python scripts/evaluate.py` prints the harness table: detection accuracy over
all injected faults, recall, precision, false-positive rate on the benign change,
unsafe-change prevention (apply-before-approval returns HTTP 409), and average
validation duration. Ground truth is tagged per fault in `simulator/faults.py`.

## Tech Stack

Python 3.11, FastAPI, Pydantic v2, SQLAlchemy 2 (SQLite), Uvicorn, httpx,
pytest. No external network dependencies at runtime.

## Local Setup

```
cd "07-network-change-validation-agent"
python -m pip install fastapi uvicorn "pydantic>=2" "sqlalchemy>=2" httpx pytest
copy .env.example .env
python -m pytest -q
python scripts/inject_bad_network_change.py
uvicorn app.main:app --host 127.0.0.1 --port 8612   # from backend/, or set PYTHONPATH
```

Docker: `docker compose up --build` then open http://localhost:8612/dashboard

## Demo

`python scripts/inject_bad_network_change.py` runs the full story against a
fresh database: seeds the twin, submits an ACL blackhole change, prints every
pipeline stage, the detected `app->db tcp/5432 BLOCKED` regression, the RCA,
the HIGH risk breakdown, the proposed safer config, its clean re-simulation,
the approval gate, apply, and post-apply verification. Exit code 0.

## API

| Method | Path |
|---|---|
| GET | /health, /readiness, /metrics, /dashboard |
| POST/GET | /api/v1/network/snapshot |
| GET | /api/v1/network/faults |
| POST | /api/v1/network/faults/{name} |
| GET | /api/v1/topology, /api/v1/reachability, /api/v1/intents, /api/v1/kpis (?change_id=) |
| POST | /api/v1/changes |
| GET | /api/v1/changes, /api/v1/changes/{id}, /api/v1/changes/{id}/validation |
| POST | /api/v1/changes/{id}/validate, /propose-fix, /approve, /reject, /apply, /rollback |

## Dashboard

Dark operations console at `/dashboard`: SVG topology by role/zone, KPI strip,
proposed-change queue with approve/reject buttons, configuration diff viewer
(+/- highlighting plus the proposed safer fix), reachability matrix diff grid,
routing change list, detected-regression table, risk gauge with component
breakdown and blast radius, intent test results, RCA panel, and a fault
injection launcher.

## Metrics

Prometheus text at `/metrics`: `http_requests_total{method,path,status}`,
`validations_total{verdict}`, `regressions_detected_total`,
`tool_calls_total{tool}`, `llm_calls_total{mode}`,
`last_validation_duration_ms`, `process_uptime_seconds`.

## Failure Scenarios

12 seeded faults, each with tagged ground truth: `acl_blackhole`,
`bgp_route_missing`, `bgp_route_leak`, `missing_route`, `asymmetric_routing`,
`vlan_mismatch`, `overlapping_subnet`, `firewall_blocks_required_traffic`,
`dns_service_failure`, `mtu_mismatch`, `wrong_gateway`,
`segmentation_violation`, plus one benign change that must produce zero findings.

## Limitations

See LIMITATIONS.md. Highlights: single-threaded simulation semantics, simplified
stateful-firewall abstraction, no live device telemetry (everything simulated),
OSPF modeled as link-state SPF without LSA flooding detail.

## Production Architecture

Replace the simulator's truth source with telemetry (NetBox/IPAM as inventory,
sflow/NetFlow for observed flows, napalm/pyATS for device config collection),
persist twins in Postgres, run the pipeline as a queue worker (change events
from ITSM webhooks), keep the deterministic agents identical, add OIDC-backed
approval identities, ship metrics via OpenTelemetry, and execute approved
changes through your existing automation layer (Ansible/Nornir) rather than
direct SSH.

## Future Enhancements

Multi-vendor syntax packs, what-if scenario batching, ML-assisted anomaly
scoring trained on historical validations, streaming updates via SSE, RBAC on
the approval queue, scheduled drift detection between twin and production.

## Interview Talking Points

See docs/INTERVIEW_GUIDE.md and docs/RESUME_BULLETS.md.
