$ErrorActionPreference = 'Stop'
$BaseUri = 'http://127.0.0.1:8105'
$Incident = Invoke-RestMethod -Method Post -Uri "$BaseUri/api/v1/scenarios/sql_injection/scan"
$IncidentId = $Incident.incident_id
$BeforeApprovalStatus = 0
try {
    Invoke-RestMethod -Method Post -Uri "$BaseUri/api/v1/incidents/$IncidentId/remediate" -ErrorAction Stop | Out-Null
} catch {
    $BeforeApprovalStatus = [int]$_.Exception.Response.StatusCode
}
$Approval = @{ approved = $true; reason = 'Reviewed exact patch hashes and rollback plan' } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "$BaseUri/api/v1/incidents/$IncidentId/approval" -Headers @{ 'X-API-Key' = 'forgeguard-local-demo-approver' } -ContentType 'application/json' -Body $Approval | Out-Null
$Result = Invoke-RestMethod -Method Post -Uri "$BaseUri/api/v1/incidents/$IncidentId/remediate" -Headers @{ 'X-API-Key' = 'forgeguard-local-demo-executor' }
[pscustomobject]@{
    Incident = $IncidentId
    Finding = $Incident.investigation.finding.cwe
    ReleaseRiskBefore = $Incident.investigation.release_risk_before.score
    PreApprovalStatus = $BeforeApprovalStatus
    FinalStatus = $Result.status
    FindingsAfter = $Result.validation.result.findings_after
    ReleaseRiskAfter = $Result.validation.result.release_risk_after.score
}
