# DEMO

## Quick Start

```
python scripts/inject_bad_network_change.py
```

The script resets the database, seeds the baseline twin and drives the entire
story through the public API (no ports bound). Exit code 0 on success.

## Storyboard

**Stage 0 - Baseline.** Seeds the 15-device lab (core/distribution/access/
firewall/WAN edges/hosts across mgmt, finance, dev, prod-app, prod-db, branch,
transit zones) and confirms 11/11 intent policies compliant.

**Stage 1 - Bad change submitted.** A realistic-looking hardening diff adds an
`APP-DB-GUARD` ACL to fw-01 denying tcp/5432 from prod-app to prod-db and binds
it inbound on the app-facing VLAN. The pipeline runs: parse -> build candidate
-> topology -> routing -> reachability matrix -> security intents -> impact ->
RCA -> remediation -> verdict.

**Stage 2 - Regressions caught.** Report shows FAIL with risk HIGH:

```
[HIGH] ACL_BLACKHOLE
    app-01->db-01 tcp/5432 BLOCKED [denied_acl] APP-DB-GUARD seq 10 ...
[HIGH] INTENT_MUST_REACH_BROKEN
    intent policy 'app-tier-to-postgres' violated: app-01(10.30.0.0/24)
    ->10.30.1.21/tcp:5432 blocked ...
```

**Stage 3 - RCA.** Confirms the implicated config operations as root cause,
records rejected hypotheses (including the latent/pre-existing hypothesis),
confidence score and recommended actions.

**Stage 4 - Risk breakdown.** Component table (routing, reachability,
security, blast radius, rollback complexity, confidence penalty) ending in a
HIGH band; narration rendered by the LLM adapter.

**Stage 5 - Safer config proposed and re-simulated.** The RemediationAgent
inverts the implicated ops into a fix diff; re-simulation against the twin is
clean (`fix_validated=True`).

**Stage 6 - Approval gate.** Approve with justification (required for HIGH risk).

**Stage 7 - Apply + verify.** Candidate promoted to CURRENT; post-apply
verification re-runs the intent suite; status COMPLETED.

**Stage 8 - Health.** Final KPIs and 100% intent compliance.

## Interactive Demo

```
uvicorn app.main:app --host 127.0.0.1 --port 8612   # PYTHONPATH=backend:.
```

Open http://localhost:8612/dashboard — pick any fault in the launcher
(dns outage, BGP leak, overlapping subnet, ...), watch regressions, RCA and
risk appear, approve or reject from the queue.

## API Walkthrough

```
curl localhost:8612/health
curl -X POST localhost:8612/api/v1/network/snapshot -H "content-type: application/json" -d "{}"
curl -X POST localhost:8612/api/v1/network/faults/acl_blackhole -H "content-type: application/json" -d "{}"
curl localhost:8612/api/v1/changes/1/validation
curl -X POST localhost:8612/api/v1/changes/1/approve -H "content-type: application/json" \
     -d '{"approver":"me","justification":"reviewed"}'
curl -X POST localhost:8612/api/v1/changes/1/apply
curl localhost:8612/metrics
```
