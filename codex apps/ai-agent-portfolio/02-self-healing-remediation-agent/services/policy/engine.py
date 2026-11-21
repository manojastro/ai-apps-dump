from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from app.repository import Repository
from app.schemas import PolicyDecision, RiskTier


class PolicyEngine:
    """Deterministic authorization boundary; model output is never trusted here."""

    def __init__(self, policy_path: str | Path, repository: Repository):
        self.config: dict[str, Any] = yaml.safe_load(Path(policy_path).read_text(encoding="utf-8"))
        self.repository = repository

    def evaluate(self, plan: dict[str, Any]) -> PolicyDecision:
        reasons: list[str] = []
        action = plan.get("action", "")
        namespace = plan.get("namespace", "")
        resource_kind = plan.get("resource_kind", "")
        parameters = plan.get("parameters", {})

        if namespace != self.config["allowed_namespace"]:
            reasons.append("namespace is outside the dedicated sandbox")
        if resource_kind not in self.config["allowed_resources"]:
            reasons.append("resource kind is outside the allowlist")
        action_policy = self.config["allowed_actions"].get(action)
        if not action_policy:
            return PolicyDecision(allowed=False, risk_tier=RiskTier.HIGH,
                                  approval_required=True,
                                  reasons=reasons + ["action is outside the explicit allowlist"])

        risk = RiskTier(action_policy["risk"])
        if action == "scale_deployment":
            replicas = parameters.get("replicas")
            if not isinstance(replicas, int) or replicas < 1:
                reasons.append("replica count must be a positive integer")
                risk = RiskTier.HIGH
            elif replicas > int(self.config["max_replicas"]):
                reasons.append("replica count exceeds the configured maximum")
                risk = RiskTier.HIGH
            elif replicas > int(self.config["normal_scale_max"]):
                risk = RiskTier.MEDIUM

        window = self.config.get("maintenance_window", {})
        if window.get("enabled"):
            hour = datetime.now(UTC).hour
            if not int(window["start_hour_utc"]) <= hour < int(window["end_hour_utc"]):
                reasons.append("current time is outside the maintenance window")

        destructive = {"delete_namespace", "delete_volume", "wipe_data"}
        if action in destructive and not self.config.get("destructive_actions_enabled", False):
            reasons.append("destructive actions are disabled")
            risk = RiskTier.HIGH

        allowed = not reasons and risk != RiskTier.HIGH
        approval_required = bool(action_policy.get("approval_required")) or risk in {RiskTier.MEDIUM, RiskTier.HIGH}
        return PolicyDecision(
            allowed=allowed,
            risk_tier=risk,
            approval_required=approval_required,
            reasons=reasons or ["plan satisfies sandbox, resource, action, and parameter policy"],
        )

    @property
    def cooldown_seconds(self) -> int:
        return int(self.config.get("cooldown_seconds", 60))

