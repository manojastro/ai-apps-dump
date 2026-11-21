param([ValidateSet('crashloop','unhealthy_pod','excessive_latency','replica_shortage','bad_deployment','failing_job','unsafe_no_remediation')][string]$Scenario='crashloop',[switch]$ForceVerificationFailure)
$ErrorActionPreference = 'Stop'
$namespace = 'selfheal-demo'
switch ($Scenario) {
  'crashloop' { kubectl -n $namespace set image deployment/checkout app=invalid.local/crashloop:demo }
  'unhealthy_pod' { kubectl -n $namespace delete pod -l app=checkout --wait=false }
  'replica_shortage' { kubectl -n $namespace scale deployment/worker --replicas=1 }
  'bad_deployment' { kubectl -n $namespace annotate deployment/payments selfheal-demo/bad-revision=true --overwrite }
  'failing_job' { kubectl -n $namespace delete job reconcile --ignore-not-found; kubectl -n $namespace create job reconcile --image=busybox:1.36 -- sh -c 'exit 1' }
  'excessive_latency' { kubectl -n $namespace annotate deployment/checkout selfheal-demo/cache-pressure=high --overwrite }
  'unsafe_no_remediation' { kubectl -n $namespace annotate deployment/payments selfheal-demo/volume-corruption=suspected --overwrite }
}
$body = @{scenario=$Scenario;force_verification_failure=[bool]$ForceVerificationFailure} | ConvertTo-Json
$headers = @{Authorization='Bearer demo-operator-token';'X-CSRF-Token'='demo-csrf-token'}
Invoke-RestMethod -Method Post -Uri 'http://localhost:8002/api/incidents' -Headers $headers -ContentType 'application/json' -Body $body

