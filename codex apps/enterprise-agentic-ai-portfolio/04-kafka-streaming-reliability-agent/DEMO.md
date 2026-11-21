# Demonstration Runbook

## Dashboard path

1. Run `docker compose up --build` and wait for the health check.
2. Open <http://localhost:8104>.
3. Inject `malformed_message`.
4. Explain why the evidence supports a poison message rather than consumer under-capacity: the same event fails repeatedly and lag is isolated to partition 3.
5. Review risk and rollback, approve, then execute.
6. Show that the incident becomes `VALIDATED` only after lag, error, and DLQ checks pass.
7. Inject `partition_imbalance` and show the different evidence and partition-key remediation.
8. Open `/api/v1/activity`, `/api/v1/evaluations/summary`, `/metrics`, and `/docs`.

## API-only path

```powershell
$created = Invoke-RestMethod -Method Post http://localhost:8104/api/v1/scenarios/malformed_message/inject
$id = $created.incident_id
Invoke-RestMethod -Method Post -ContentType application/json -Body '{"approved":true,"approved_by":"demo-operator","reason":"evidence and rollback reviewed"}' "http://localhost:8104/api/v1/incidents/$id/approval"
Invoke-RestMethod -Method Post "http://localhost:8104/api/v1/incidents/$id/execute"
Invoke-RestMethod http://localhost:8104/api/v1/evaluations/summary
```

## Safety proof

Before approval, call the execute endpoint and show its `409` response. Inspect `workflow.py` to show the explicit allow-list and `SyntheticKafkaAdapter` to show that no real cluster call exists. Rejecting an action also prevents execution.
