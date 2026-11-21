from __future__ import annotations

import json
from typing import Any, Protocol
from uuid import uuid4

from .database import Database
from .schemas import ProposedAction, utc_now


POLICY_SPECS: dict[str, dict[str, Any]] = {
    "quarantine_agent_version": {"tool": "policy_registry", "policy_key": "agent.quarantined", "value": {"enabled": True}},
    "require_outcome_attestation": {"tool": "evaluation_policy", "policy_key": "outcome.attestation", "value": {"required": True}},
    "enforce_step_budget": {"tool": "runtime_policy", "policy_key": "runtime.step_budget", "value": {"max_steps": 8}},
    "enforce_cost_budget": {"tool": "runtime_policy", "policy_key": "runtime.cost_budget", "value": {"max_cost_usd": 0.15}},
    "enable_context_compaction": {"tool": "runtime_policy", "policy_key": "runtime.context_compaction", "value": {"enabled": True, "max_tokens": 120000}},
    "restrict_tool_routing": {"tool": "evaluation_policy", "policy_key": "tools.task_allowlist", "value": {"strict": True}},
    "require_retrieval_evidence": {"tool": "evaluation_policy", "policy_key": "retrieval.evidence", "value": {"required": True}},
    "add_bounded_retry": {"tool": "runtime_policy", "policy_key": "runtime.retry_budget", "value": {"max_retries": 2}},
    "enforce_latency_budget": {"tool": "runtime_policy", "policy_key": "runtime.latency_budget", "value": {"max_latency_ms": 12000}},
    "require_completion_contract": {"tool": "evaluation_policy", "policy_key": "outcome.completion_contract", "value": {"required": True}},
}


class PolicyStateProvider(Protocol):
    """Read-only policy state boundary, independent of the change adapter."""

    def read(self, policy_key: str) -> dict[str, Any]: ...


class SQLitePolicyStateProvider:
    def __init__(self, database: Database):
        self.__database = database

    def read(self, policy_key: str) -> dict[str, Any]:
        row = self.__database.query_one("SELECT * FROM policy_state WHERE policy_key = ?", (policy_key,))
        if not row:
            return {"policy_key": policy_key, "version": 0, "value": {}}
        return {"policy_key": policy_key, "version": row["version"], "value": json.loads(row["value_json"])}


class SyntheticPolicyRegistry:
    """Persistent local policy adapter with separately readable post-action state."""

    def __init__(self, database: Database, fault_mode: str | None = None):
        self.database = database
        self.fault_mode = fault_mode
        self._state_provider = SQLitePolicyStateProvider(database)

    def observe(self, policy_key: str) -> dict[str, Any]:
        return self._state_provider.read(policy_key)

    def apply(self, action: ProposedAction) -> tuple[dict[str, Any], dict[str, Any]]:
        spec = POLICY_SPECS[action.action_type]
        before = self.observe(spec["policy_key"])
        expected = {
            "policy_key": spec["policy_key"],
            "version": before["version"] + 1,
            "value": spec["value"],
        }
        written = dict(expected)
        if self.fault_mode == "wrong_state":
            written = {**expected, "value": {"unexpected": True}}
        self.database.execute(
            """INSERT INTO policy_state(policy_key,version,value_json,updated_at) VALUES(?,?,?,?)
               ON CONFLICT(policy_key) DO UPDATE SET version=excluded.version,value_json=excluded.value_json,updated_at=excluded.updated_at""",
            (written["policy_key"], written["version"], json.dumps(written["value"], sort_keys=True), utc_now()),
        )
        if self.fault_mode == "raise_after_write":
            raise RuntimeError("synthetic policy adapter failed after write")
        return before, expected

    def rollback(self, before: dict[str, Any]) -> dict[str, Any]:
        if before["version"] == 0:
            self.database.execute("DELETE FROM policy_state WHERE policy_key = ?", (before["policy_key"],))
        else:
            self.database.execute(
                """INSERT INTO policy_state(policy_key,version,value_json,updated_at) VALUES(?,?,?,?)
                   ON CONFLICT(policy_key) DO UPDATE SET version=excluded.version,value_json=excluded.value_json,updated_at=excluded.updated_at""",
                (before["policy_key"], before["version"], json.dumps(before["value"], sort_keys=True), utc_now()),
            )
        return self.observe(before["policy_key"])

    def record_execution(
        self, action_id: str, status: str, before: dict[str, Any], after: dict[str, Any], rollback: dict[str, Any]
    ) -> str:
        execution_id = f"pex_{uuid4().hex[:12]}"
        self.database.execute(
            "INSERT INTO policy_executions(execution_id,action_id,status,before_json,after_json,rollback_json,created_at) VALUES(?,?,?,?,?,?,?)",
            (execution_id, action_id, status, json.dumps(before), json.dumps(after), json.dumps(rollback), utc_now()),
        )
        return execution_id
