# API examples

The generated OpenAPI UI at `/docs` is authoritative. A minimal incident lifecycle is:

```text
POST /api/v1/scenarios/consumer_slowdown/inject
POST /api/v1/incidents/{incident_id}/approval
POST /api/v1/incidents/{incident_id}/execute
GET  /api/v1/incidents/{incident_id}
```

Approval body:

```json
{
  "approved": true,
  "approved_by": "local-operator",
  "reason": "Evidence, blast radius, and rollback reviewed"
}
```

With `AUTH_MODE=api_key`, use the viewer key for read/injection calls, the approver key for approval, and the distinct executor key for execution. The server derives approval identity in this mode. Health, readiness, metrics, dashboard assets, and OpenAPI remain unauthenticated for local orchestration and inspection.
