"""Control-plane coded tools (M12+): deterministic wrappers, zero LLM logic.

Not wired into any agent's tools[] — orchestration calls these directly so
agents can never bypass them. ExecuteRemoteAction is single-shot (fresh
seeded estate per call, before/after snapshots returned); session flows
that need verify-after-execute on ONE estate use control_plane.execution
directly (M17).
"""

from __future__ import annotations

from typing import Any

from neuro_san.interfaces.coded_tool import CodedTool


class EvaluatePolicy(CodedTool):
    """Run the policy gate for a proposed action. Returns ALLOW/DENY/REQUIRE_APPROVAL."""

    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        from common.config import load_settings
        from control_plane.policy import PolicyInput, evaluate
        from database.bootstrap import get_connection, init_db

        try:
            at_hour = int(args.get("at_hour", 10))
        except (TypeError, ValueError):
            at_hour = 10
        policy = PolicyInput(
            user_id=str(args.get("user_id", sly_data.get("user_id", ""))),
            user_role=str(args.get("user_role", sly_data.get("user_role", "employee"))),
            device_id=str(args.get("device_id", sly_data.get("device_id", ""))),
            device_group=str(args.get("device_group", "corporate-laptop")),
            device_compliant=bool(args.get("device_compliant", True)),
            action_id=str(args.get("action_id", "")),
            script_hash=str(args.get("script_hash", "")),
            environment=str(args.get("environment", "prod")),
            at_hour=at_hour)
        db_path = str(args.get("db_path", "")) or load_settings(env_file=".env").db_path
        init_db(db_path)
        conn = get_connection(db_path)
        try:
            result = evaluate(conn, policy)
            return {"decision": result.decision,
                    "action_id": policy.action_id,
                    "checks": [{"name": c.name, "passed": c.passed, "detail": c.detail}
                               for c in result.checks]}
        finally:
            conn.close()


class ExecuteRemoteAction(CodedTool):
    """Gate then execute an approved action (single-shot demo semantics)."""

    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        import json

        from common.config import load_settings
        from control_plane.execution import request_execution
        from control_plane.registry import seed_registry
        from database.bootstrap import get_connection, init_db
        from simulator.estate import generate_estate

        try:
            seed = int(args.get("seed", 42))
        except (TypeError, ValueError):
            seed = 42
        params: dict[str, Any] = {}
        raw_params = args.get("params", "")
        if raw_params:
            try:
                params = json.loads(raw_params) if isinstance(raw_params, str) else dict(raw_params)
            except (TypeError, ValueError):
                params = {}
        db_path = str(args.get("db_path", "")) or load_settings(env_file=".env").db_path
        init_db(db_path)
        conn = get_connection(db_path)
        try:
            seed_registry(conn)
            estate = generate_estate(seed=seed)
            result = request_execution(
                conn, estate, str(args.get("case_id", sly_data.get("case_id", ""))),
                str(args.get("action_id", "")), str(args.get("device_id", "DEVICE_001")),
                str(args.get("user_id", sly_data.get("user_id", "USER_001"))),
                params=params)
            return {"status": result.status, "action_id": result.action_id,
                    "run_id": result.run_id, "policy_decision": result.policy_decision,
                    "autonomy": result.autonomy, "approval_id": result.approval_id,
                    "effect": result.effect, "reasons": result.reasons}
        finally:
            conn.close()
