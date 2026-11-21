# Demo runbook

## Start

```powershell
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8105 --no-server-header
```

Open `http://localhost:8105`.

## Guided demo

1. Choose **SQL injection in user lookup**. The scanner records a CWE-89 finding and
   source hash without importing or executing the fixture.
2. Review reachability: unauthenticated attacker input reaches constructed SQL, so the
   release decision is `BLOCK`.
3. Inspect the exact parameterization diff, blast radius, and rollback plan.
4. Click **Apply exact patch & validate** before approval if demonstrating the API:
   remediation returns HTTP 409.
5. Click **Approve remediation**. A demo-approver credential attests the action ID,
   displayed patch hash, and fixed-source hash but performs no change.
6. Click **Apply exact patch & validate**. A separate demo-executor credential invokes
   the change. ForgeGuard rechecks all approved hashes and both source snapshots,
   writes only the allow-listed fixed text, compares its complete canonical AST,
   rescans, and checks regressions. Explain that any failed check or validator outage
   restores the original workspace before recording `VALIDATION_FAILED`.
7. Show the result: one finding to zero, risk approximately 92 to 10, status
   `VALIDATED`, decision `ALLOW_WITH_REVIEW`, and zero regressions.
8. Open the append-only activity table, `/api/v1/evaluations/summary`, `/metrics`, and
   `/docs`.

## Scripted demo

```powershell
.\scripts\demo.ps1
```

Expected: unauthenticated remediation HTTP 403, authenticated pre-approval remediation
HTTP 409, final status `VALIDATED`, zero findings, and after-risk 10.

## Alternative cases

Repeat with shell injection to show removal of `shell=True`, or the hard-coded example
credential to show migration to `os.environ`. These remain inert source strings and
are never run.
