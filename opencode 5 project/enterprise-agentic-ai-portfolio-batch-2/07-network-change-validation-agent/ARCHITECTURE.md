# ARCHITECTURE

## System Overview

The system is a vertical-slice implementation of a network change validation
control plane. A FastAPI service owns a persistent digital twin of the lab
network. Every proposed change is expressed as a unified configuration diff,
compiled into structured operations, applied to a copy of the CURRENT twin, and
analyzed by a deterministic agent pipeline. Nothing mutates the CURRENT twin
without passing the approval state machine.

## Module Map

```
simulator/
  models.py     pydantic twin schema: Device, Interface, Vlan, SubnetDef, Acl,
                StaticRoute, BgpProcess/BgpNeighbor, FirewallDef, ServiceDef,
                TwinPayload (the serializable truth), CIDR helpers
  lab.py        deterministic seeded topology (15 devices) + SEED_INTENTS
  configs.py    config renderer (Cisco-flavored), unified-diff parser
                (context-state machine), op applier with change journal
  faults.py     FaultCatalog: 12 fault specs + 1 benign spec, each with
                ExpectedRegression ground truth

backend/app/
  services/twin.py       TwinRuntime: segment index, ip-owner index, routing
                         tables (connected/static/ospf/bgp) with memoization,
                         recursive next-hop resolution, ACL and firewall
                         evaluators, flow simulator, reachability matrix,
                         matrix differ
  services/intents.py    IntentDef -> IntentOutcome evaluators:
                         must_reach, must_not_reach, route_exists,
                         only_from_subnet
  services/validation.py orchestrator: seed_network, run_validation,
                         submit/approve/reject/apply/rollback, KPI snapshots
  services/state_machine.py ALLOWED_TRANSITIONS + IllegalTransition
  services/llm.py        LlmAdapter: mock narration default; live mode via
                         OpenAI-compatible httpx call; narration only
  services/metrics.py    in-process counters/gauges + Prometheus rendering
  tools/base.py          BaseTool (schema validation, permission gate, timeout
                         thread, tool_calls audit), ToolRegistry
  tools/network_tools.py the 7 registered tools
  agents/base.py         AgentContext (pipeline blackboard), StepReport,
                         BaseAgent timing contract
  agents/network_agents.py   perception agents
  agents/analysis_agents.py  impact/RCA/remediation/validation agents
  models/entities.py     SQLAlchemy schema (20 tables)
  repositories/repo.py   Snapshot/Change/Run/Intent/Audit/Investigation/Diff/Kpi repos
  api/                   deps.py, observability.py, network.py, changes.py, v1.py
```

## Twin Engine Design

- **Segments** are derived from interfaces: every enabled interface with a CIDR
  joins the broadcast domain keyed by its normalized network address. VLAN
  compatibility is enforced between adjacent interfaces when both declare a
  VLAN, which is what makes `vlan_mismatch` detectable.
- **Routing tables** per device combine connected routes (distance 0), statics
  (distance configurable), eBGP-learned routes from neighbor advertisements
  (distance 20) and OSPF-learned routes (distance 110). OSPF runs a Dijkstra
  over router nodes using per-interface directed costs; each router learns other
  routers' OSPF-enabled subnets through its first hop.
- **Route lookup**: longest prefix, then administrative distance, then cost,
  then next-hop tie-break — deterministic and unit-tested.
- **Forwarding simulation** walks devices hop-by-hop: ingress ACL check, ingress
  MTU check, firewall policy evaluation on firewall devices, route lookup,
  recursive next-hop resolution, egress ACL and MTU checks, TTL guard for
  routing loops. Every drop records the reason and the dropping device.
- **Firewall semantics** are stateful-in-spirit: a rule port matches destination
  or source port, so reply traffic of an allowed session passes; unmatched
  cross-zone traffic hits default deny.
- **Reachability matrix** probes 7 endpoint hosts x 6 remote endpoints x 4
  protocol/port tuples (168 flows) plus bidirectional asymmetry analysis.

## Pipeline Data Flow

`AgentContext` is the shared blackboard. The orchestrator fills it with parsed
ops, the apply journal, both runtimes' matrices, the matrix diff, the routing
table diff and intent results; agents append regressions, findings, hypotheses,
risk, RCA and the remediation proposal. Each agent returns a StepReport that is
persisted as an Investigation with Evidence and Hypotheses rows.

## Risk Formula

```
score = min(100, routing_impact + reachability_impact + security_violations
              + blast_radius + rollback_complexity + confidence_penalty)
routing_impact      = 5 x removed routes            (cap 25)
reachability_impact = 10 x broken intents
                      + 3 x blocked flows
                      + 5 x newly opened flows      (cap 35)
security_violations = 15 x violations
                      + 15 x affected critical svcs (cap 30)
blast_radius        = 1 x touched devices + 3 x apps (cap 15)
rollback_complexity = 2 / 5 / 9 by op count bands
confidence_penalty  = 10 x (1 - confidence)
bands: LOW <20 <= MEDIUM <40 <= HIGH <65 <= CRITICAL
```

## Approval State Machine

Transitions are encoded in one map and enforced everywhere; violations raise
HTTP 409. Re-validation loops (`AWAITING_APPROVAL -> VALIDATING`) are allowed so
operators can iterate; approval, execution and verification gates are not
skippable. Mutating tools independently refuse unapproved invocations.

## Persistence

SQLite via SQLAlchemy 2 with WAL journaling and busy timeouts; full twin state
lives in `network_snapshots.payload` JSON while normalized child tables mirror
the current snapshot for queryability. Candidate snapshots are versioned rows;
rollback points at archived pre-change payloads.

## Frontend

Single-file dark dashboard consuming only the public JSON API: SVG topology
layout by role/zone, change queue with approve/reject actions, diff viewer with
remediation overlay, matrix diff grid, regression table, risk gauge, intent
results and RCA panel, and a fault launcher for incident simulation.
