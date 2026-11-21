from copy import deepcopy

from .schemas import RiskTier, Scenario


SCENARIOS: dict[str, Scenario] = {
    "crashloop": Scenario(
        id="crashloop", title="Checkout CrashLoopBackOff",
        signal={"kind": "kube_pod_container_status_waiting_reason", "value": "CrashLoopBackOff"},
        diagnosis="checkout pod is repeatedly failing its startup probe",
        runbook_id="RB-001", action="restart_pod", resource_kind="pods",
        resource="checkout-0", parameters={"pod": "checkout-0"}, expected_risk=RiskTier.LOW,
        recovery_criterion="replacement pod Ready=true for two probes",
    ),
    "unhealthy_pod": Scenario(
        id="unhealthy_pod", title="Unhealthy catalog pod",
        signal={"kind": "kube_pod_status_ready", "value": "0"},
        diagnosis="catalog pod is not Ready while its deployment remains available",
        runbook_id="RB-002", action="restart_pod", resource_kind="pods",
        resource="catalog-0", parameters={"pod": "catalog-0"}, expected_risk=RiskTier.LOW,
        recovery_criterion="pod readiness probe returns success",
    ),
    "excessive_latency": Scenario(
        id="excessive_latency", title="API latency from stale demo cache",
        signal={"kind": "http_request_duration_p95_ms", "value": "1850"},
        diagnosis="synthetic cache saturation correlates with elevated API p95 latency",
        runbook_id="RB-003", action="clear_cache", resource_kind="application_cache",
        resource="demo-api-cache", parameters={"cache": "demo-api-cache"}, expected_risk=RiskTier.LOW,
        recovery_criterion="p95 latency below 500ms for two probes",
    ),
    "replica_shortage": Scenario(
        id="replica_shortage", title="Worker replica shortage",
        signal={"kind": "kube_deployment_status_replicas_available", "value": "1/3"},
        diagnosis="worker deployment has fewer available replicas than its safe target",
        runbook_id="RB-004", action="scale_deployment", resource_kind="deployments",
        resource="worker", parameters={"deployment": "worker", "replicas": 3}, expected_risk=RiskTier.LOW,
        recovery_criterion="three worker replicas are Ready",
    ),
    "bad_deployment": Scenario(
        id="bad_deployment", title="Bad payments deployment",
        signal={"kind": "deployment_error_rate", "value": "0.42"},
        diagnosis="error rate increased immediately after payments revision 2",
        runbook_id="RB-005", action="rollback_deployment", resource_kind="deployments",
        resource="payments", parameters={"deployment": "payments", "revision": 1}, expected_risk=RiskTier.MEDIUM,
        recovery_criterion="revision 1 is available and error rate below 2%",
    ),
    "failing_job": Scenario(
        id="failing_job", title="Failed reconciliation job",
        signal={"kind": "kube_job_status_failed", "value": "1"},
        diagnosis="reconciliation job failed once with an approved transient dependency error",
        runbook_id="RB-006", action="rerun_job", resource_kind="jobs",
        resource="reconcile", parameters={"job": "reconcile"}, expected_risk=RiskTier.LOW,
        recovery_criterion="replacement reconciliation job completes successfully",
    ),
    "unsafe_no_remediation": Scenario(
        id="unsafe_no_remediation", title="Suspected namespace data corruption",
        signal={"kind": "persistent_volume_corruption", "value": "suspected"},
        diagnosis="signal suggests a destructive recovery may be required; no safe demo action exists",
        runbook_id="RB-007", action="delete_namespace", resource_kind="namespaces",
        resource="selfheal-demo", parameters={"namespace": "selfheal-demo"}, expected_risk=RiskTier.HIGH,
        recovery_criterion="external change process completes forensic review", allowed=False,
    ),
}


RUNBOOKS = {
    "RB-001": {"id": "RB-001", "title": "Restart a crash-looping demo pod", "incident_type": "crashloop", "action": "restart_pod", "version": "1.2", "content": "Confirm CrashLoopBackOff and deployment health, restart only the named pod, then require two successful readiness probes."},
    "RB-002": {"id": "RB-002", "title": "Recover one unhealthy demo pod", "incident_type": "unhealthy_pod", "action": "restart_pod", "version": "1.0", "content": "When one named pod is NotReady, restart it and verify readiness without changing other resources."},
    "RB-003": {"id": "RB-003", "title": "Clear synthetic application cache", "incident_type": "excessive_latency", "action": "clear_cache", "version": "1.1", "content": "Clear only the demo application cache when cache pressure and p95 latency are correlated; verify p95 below 500ms."},
    "RB-004": {"id": "RB-004", "title": "Restore safe deployment replicas", "incident_type": "replica_shortage", "action": "scale_deployment", "version": "2.0", "content": "Scale the named deployment no higher than the configured maximum and verify all replicas become Ready."},
    "RB-005": {"id": "RB-005", "title": "Rollback a bad demo revision", "incident_type": "bad_deployment", "action": "rollback_deployment", "version": "1.4", "content": "After operator approval, rollback the named deployment one known revision and verify availability plus error rate."},
    "RB-006": {"id": "RB-006", "title": "Re-run a transiently failed demo job", "incident_type": "failing_job", "action": "rerun_job", "version": "1.0", "content": "Create one replacement of the named failed demo job and confirm completion. Never loop retries."},
    "RB-007": {"id": "RB-007", "title": "Escalate possible persistent-data corruption", "incident_type": "unsafe_no_remediation", "action": "external_change", "version": "1.0", "content": "Do not mutate volumes or namespaces. Preserve evidence and escalate to the external change process."},
}


def get_scenario(scenario_id: str) -> Scenario:
    if scenario_id not in SCENARIOS:
        raise KeyError(scenario_id)
    return SCENARIOS[scenario_id].model_copy(deep=True)


def get_runbook(runbook_id: str) -> dict:
    return deepcopy(RUNBOOKS[runbook_id])
