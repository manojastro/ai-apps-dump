# API Guide

Interactive OpenAPI is available at `/docs`.

## Platform

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | process liveness |
| GET | `/ready` | database readiness and current mode |
| GET | `/metrics` | Prometheus text exposition |
| GET | `/api/v1/platform` | runtime, persistence, and auth mode |
| GET | `/api/v1/agents` | role, tools, boundary, failure behavior |

## Runs and investigations

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/scenarios` | labelled scenario catalog |
| POST | `/api/v1/demo/run` | execute one scenario through the full workflow |
| GET | `/api/v1/runs` | list trace summaries |
| GET | `/api/v1/runs/{run_id}` | retrieve typed trace |
| GET | `/api/v1/incidents` | list incidents |
| GET | `/api/v1/incidents/{incident_id}` | RCA, detections, actions, validations |

## Governance and evaluation

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/actions` | approval queue |
| POST | `/api/v1/actions/{id}/approval` | approve/reject and bind the canonical payload hash/version |
| POST | `/api/v1/actions/{id}/execute` | catalog-bound synthetic policy update, readback, validation, and rollback |
| GET | `/api/v1/audit` | immutable-style activity view |
| POST | `/api/v1/evaluations/run` | run labelled detector benchmark |
| GET | `/api/v1/evaluations` | stored evaluation results |
| POST | `/api/v1/regression/compare` | execute current/candidate benchmarks with the server-registered built-in executor and derive the release gate |
| GET | `/api/v1/dashboard` | fleet aggregate view model |

If `API_KEY` is configured, include `X-API-Key` on state-changing requests.

The local regression endpoint does not accept a runner in its request. Programmatic constructor injection is also fail-closed: unregistered runners return a persisted `BLOCK` result with `error: UntrustedBenchmarkRunner`. Production remote execution requires signed attestation verification and is not implemented by this POC.
