<!-- allowed_roles: employee, it, support -->
# Runbook: Teams Memory Regression

## Symptom
Laptop slow with Teams resident memory above 3 GB after a recent Teams
update. CPU and RAM pressure follow the memory growth.

## Evidence
Nexthink device health shows RAM above 85 percent, Tanium lists Teams as
the top process, and Intune shows a recent Teams version change.

## Remediation
Use approved action SCR-018 Clear Teams Cache (LOW risk, autonomy L3).
Verify with fresh Nexthink and Tanium telemetry before resolving.
