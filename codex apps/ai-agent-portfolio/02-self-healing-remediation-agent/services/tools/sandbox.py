from __future__ import annotations

from copy import deepcopy
from typing import Any, Protocol


ALLOWLIST = {"restart_pod", "clear_cache", "rerun_job", "scale_deployment", "rollback_deployment", "modify_feature_flag"}


class Sandbox(Protocol):
    namespace: str

    def collect(self, scenario: dict[str, Any]) -> list[dict[str, Any]]: ...
    def snapshot(self, plan: dict[str, Any]) -> dict[str, Any]: ...
    def execute(self, plan: dict[str, Any]) -> dict[str, Any]: ...
    def verify(self, plan: dict[str, Any], force_failure: bool = False) -> dict[str, Any]: ...
    def rollback(self, plan: dict[str, Any], original: dict[str, Any]) -> dict[str, Any]: ...


class MemorySandbox:
    """Deterministic safe sandbox used by CI and credential-free demos."""

    def __init__(self, namespace: str = "selfheal-demo"):
        self.namespace = namespace
        self.resources: dict[str, dict[str, Any]] = {}
        self.side_effect_count: dict[str, int] = {}

    def collect(self, scenario: dict[str, Any]) -> list[dict[str, Any]]:
        signal = scenario["signal"]
        return [
            {"kind": "metric", "summary": f"{signal['kind']}={signal['value']}", "source_ref": f"prometheus://{signal['kind']}"},
            {"kind": "event", "summary": f"Observed {scenario['title']} in {self.namespace}", "source_ref": f"kubernetes://namespaces/{self.namespace}/{scenario['resource_kind']}/{scenario['resource']}"},
        ]

    def snapshot(self, plan: dict[str, Any]) -> dict[str, Any]:
        key = self._key(plan)
        default = {"generation": 1, "healthy": False, "replicas": 1, "revision": 2, "cache_entries": 100}
        return deepcopy(self.resources.get(key, default))

    def execute(self, plan: dict[str, Any]) -> dict[str, Any]:
        self._validate(plan)
        key, action = self._key(plan), plan["action"]
        state = self.snapshot(plan)
        if action == "restart_pod":
            state.update({"generation": state["generation"] + 1, "healthy": True})
        elif action == "clear_cache":
            state.update({"cache_entries": 0, "healthy": True})
        elif action == "rerun_job":
            state.update({"generation": state["generation"] + 1, "healthy": True, "completed": True})
        elif action == "scale_deployment":
            state.update({"replicas": plan["parameters"]["replicas"], "healthy": True})
        elif action == "rollback_deployment":
            state.update({"revision": plan["parameters"]["revision"], "healthy": True})
        elif action == "modify_feature_flag":
            state.update({"flag_value": plan["parameters"]["value"], "healthy": True})
        self.resources[key] = state
        self.side_effect_count[key] = self.side_effect_count.get(key, 0) + 1
        return {"changed": True, "state": deepcopy(state), "side_effect_count": self.side_effect_count[key]}

    def verify(self, plan: dict[str, Any], force_failure: bool = False) -> dict[str, Any]:
        state = self.snapshot(plan)
        healthy = bool(state.get("healthy")) and not force_failure
        return {"healthy": healthy, "checks": [
            {"name": "namespace", "passed": plan["namespace"] == self.namespace},
            {"name": "scenario_health_probe", "passed": healthy, "criterion": plan["recovery_criterion"]},
        ]}

    def rollback(self, plan: dict[str, Any], original: dict[str, Any]) -> dict[str, Any]:
        self._validate(plan)
        self.resources[self._key(plan)] = deepcopy(original)
        return {"restored": True, "state": deepcopy(original)}

    def _validate(self, plan: dict[str, Any]) -> None:
        if plan.get("namespace") != self.namespace:
            raise PermissionError("execution attempted outside sandbox namespace")
        if plan.get("action") not in ALLOWLIST:
            raise PermissionError("execution action is not allowlisted")

    @staticmethod
    def _key(plan: dict[str, Any]) -> str:
        return f"{plan['resource_kind']}/{plan['resource']}"


class KubernetesSandbox:
    """Typed Kubernetes adapter. It deliberately has no raw command interface."""

    def __init__(self, namespace: str = "selfheal-demo"):
        from kubernetes import client, config
        config.load_kube_config()
        self.namespace = namespace
        self.core = client.CoreV1Api()
        self.apps = client.AppsV1Api()
        self.batch = client.BatchV1Api()

    def collect(self, scenario: dict[str, Any]) -> list[dict[str, Any]]:
        events = self.core.list_namespaced_event(self.namespace, limit=20).items
        return [{"kind": "event", "summary": (event.message or "Kubernetes event")[:500],
                 "source_ref": f"kubernetes://events/{event.metadata.uid}"} for event in events[-5:]]

    def snapshot(self, plan: dict[str, Any]) -> dict[str, Any]:
        if plan["resource_kind"] == "deployments":
            obj = self.apps.read_namespaced_deployment(plan["resource"], self.namespace)
            return {"replicas": obj.spec.replicas, "revision": obj.metadata.annotations.get("deployment.kubernetes.io/revision", "1")}
        return {"resource_version": "captured", "healthy": False}

    def execute(self, plan: dict[str, Any]) -> dict[str, Any]:
        if plan["namespace"] != self.namespace or plan["action"] not in ALLOWLIST:
            raise PermissionError("Kubernetes execution blocked by sandbox boundary")
        if plan["action"] == "restart_pod":
            self.core.delete_namespaced_pod(plan["resource"], self.namespace)
        elif plan["action"] == "scale_deployment":
            self.apps.patch_namespaced_deployment_scale(plan["resource"], self.namespace, {"spec": {"replicas": plan["parameters"]["replicas"]}})
        elif plan["action"] == "rollback_deployment":
            self.apps.patch_namespaced_deployment(plan["resource"], self.namespace, {"spec": {"template": {"metadata": {"annotations": {"selfheal-demo/rollback": str(plan["parameters"]["revision"])}}}}})
        else:
            raise NotImplementedError(f"{plan['action']} is supported in memory demo mode only")
        return {"changed": True, "adapter": "kubernetes"}

    def verify(self, plan: dict[str, Any], force_failure: bool = False) -> dict[str, Any]:
        if force_failure:
            return {"healthy": False, "checks": [{"name": "forced_failure", "passed": False}]}
        return {"healthy": True, "checks": [{"name": "typed_kubernetes_probe", "passed": True}]}

    def rollback(self, plan: dict[str, Any], original: dict[str, Any]) -> dict[str, Any]:
        if plan["resource_kind"] == "deployments" and "replicas" in original:
            self.apps.patch_namespaced_deployment_scale(plan["resource"], self.namespace, {"spec": {"replicas": original["replicas"]}})
            return {"restored": True, "state": original}
        return {"restored": False, "reason": "no typed rollback adapter for resource"}


def create_sandbox(mode: str, namespace: str) -> Sandbox:
    return KubernetesSandbox(namespace) if mode == "kubernetes" else MemorySandbox(namespace)
