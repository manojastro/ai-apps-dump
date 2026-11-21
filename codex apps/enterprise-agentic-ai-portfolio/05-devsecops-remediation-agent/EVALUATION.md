# Evaluation

ForgeGuard scores deterministic outcomes against authored scenario ground truth.

| Metric | Definition |
|---|---|
| Finding validity | confirmed true findings / investigations |
| Exploitability accuracy | exact predicted classification / ground-truth classification |
| Remediation success | validations passed / remediations attempted |
| Security regression | remediation introduced an obvious new high-risk pattern |
| Test regression | syntax, exact signature, import/call, or top-level policy failed |
| Release risk | deterministic score before and after remediation |

## Benchmark fixtures

| Scenario | CWE | Ground truth | Before decision | Expected after |
|---|---|---|---|---|
| SQL interpolation | CWE-89 | LIKELY_EXPLOITABLE | BLOCK | parameterized query, zero findings |
| Shell interpolation | CWE-78 | CONDITIONALLY_EXPLOITABLE | BLOCK | argument vector, `shell=False` |
| Embedded example token | CWE-798 | LIKELY_EXPLOITABLE | BLOCK | environment-backed secret boundary |

A successful validation requires every independent static check, one before finding, zero
after findings, and release risk `10 / ALLOW_WITH_REVIEW`. The vulnerable risk is
derived from severity and exploitability and remains `BLOCK`. A validator outage is
recorded as an attempted but unsuccessful remediation, not as a fabricated security or
test regression. Failed checks record only the regression dimensions actually observed,
and the attempted patch is rolled back before the outcome transaction commits.

## Reproduce

```bash
python -m pytest
```

Finding prediction is derived from scanner output and compared with the stored expected
label. Exploitability is derived only from reachability, attacker-control,
authentication, and repository-access evidence, then compared with a separate label.
Mutating ground truth therefore changes accuracy, not the prediction.

Run each scenario through the dashboard or API, then query
`/api/v1/evaluations/summary`. Small authored fixtures measure workflow correctness,
not scanner recall across arbitrary codebases. Expand the benchmark before generalizing
accuracy claims.
