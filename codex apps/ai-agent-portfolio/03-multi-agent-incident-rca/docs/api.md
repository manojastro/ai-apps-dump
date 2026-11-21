# API guide

OpenAPI is available at `/docs` and `/openapi.json`. Versioned resources are under `/api/v1`.

| Method | Route | Role | Purpose |
|---|---|---|---|
| GET | `/api/v1/incidents` | viewer | List incidents |
| POST | `/api/v1/incidents` | investigator | Inject/manual incident |
| POST | `/api/v1/incidents/{id}/investigate` | investigator | Run the supervisor workflow |
| GET | `/api/v1/incidents/{id}/investigation` | viewer | Full snapshot and worker status |
| GET | `/api/v1/incidents/{id}/evidence` | viewer | Immutable source observations |
| GET | `/api/v1/incidents/{id}/timeline` | viewer | Correlated timeline |
| GET | `/api/v1/incidents/{id}/hypotheses` | viewer | Ranked candidates and critic |
| GET/PUT | `/api/v1/incidents/{id}/rca` | viewer/investigator | View or citation-gated edit |
| GET | `/api/v1/graph` | viewer | Dependency topology |
| POST | `/api/v1/evaluations/run` | admin | Run all 60 cases |
| GET | `/api/v1/evaluations/summary` | viewer | Evaluation metrics |
| GET | `/api/v1/audit` | admin | Security audit log |

The POC uses `X-User` and `X-Role` headers (`viewer`, `investigator`, `admin`) to demonstrate authorization boundaries. Replace this adapter with verified SSO/JWT claims in production.

Example:

```bash
curl -X POST http://localhost:8003/api/v1/incidents/INC-DEMO-06/investigate \
  -H "X-User: demo" -H "X-Role: investigator"
```

