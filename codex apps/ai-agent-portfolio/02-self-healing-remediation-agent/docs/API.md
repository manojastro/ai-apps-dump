# API

OpenAPI is generated at `/docs`. Read routes require a viewer or operator bearer token. Mutation routes require operator role and `X-CSRF-Token`.

| Method | Route | Purpose |
|---|---|---|
| GET | `/health/live`, `/health/ready` | liveness and DB readiness |
| GET | `/api/scenarios` | certified fault catalog |
| GET | `/api/incidents` | incident queue |
| GET | `/api/incidents/{id}` | full evidence, policy, action, verification, rollback, audit |
| POST | `/api/incidents` | inject and run one certified incident |
| POST | `/api/incidents/{id}/approval` | approve/reject a pending MEDIUM plan with comment |
| GET | `/api/dashboard` | operational aggregates and timeline |
| GET | `/api/audit` | latest safe audit events |
| POST | `/api/admin/seed` | reset and seed the local demo |
| GET | `/metrics` | Prometheus text exposition |

Pydantic rejects unknown decisions, oversized comments, and malformed incident payloads. Unknown scenario IDs cannot be used to invent arbitrary tools.

