"""Runtime-editable policy and simulator settings persisted in ``app_settings``."""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.identity import AppSetting
from app.security.auth import Principal
from app.services.audit import record_audit
from app.services.risk_engine import RiskPolicy

RISK_POLICY_KEY = "risk_policy"
SN_SIM_FAILURE_KEY = "servicenow_sim_failure"


def get_risk_policy(db: Session) -> RiskPolicy:
    row = db.get(AppSetting, RISK_POLICY_KEY)
    return RiskPolicy.model_validate(row.value) if row else RiskPolicy()


def set_risk_policy(db: Session, policy: RiskPolicy, actor: Principal) -> RiskPolicy:
    previous = get_risk_policy(db)
    policy.version = previous.version + 1
    RiskPolicy.model_validate(policy.model_dump())  # re-run validators
    row = db.get(AppSetting, RISK_POLICY_KEY)
    if row is None:
        row = AppSetting(key=RISK_POLICY_KEY, value={})
        db.add(row)
    row.value = policy.model_dump()
    row.updated_by = actor.email
    record_audit(
        db,
        actor=actor,
        action="risk_policy_updated",
        target_type="policy",
        target_id=RISK_POLICY_KEY,
        previous_state={"policy_version": previous.policy_version, "weights": previous.weights},
        new_state={"policy_version": policy.policy_version, "weights": policy.weights},
    )
    return policy


def get_setting(db: Session, key: str, default: dict[str, Any]) -> dict[str, Any]:
    row = db.get(AppSetting, key)
    return dict(row.value) if row else dict(default)


def put_setting(db: Session, key: str, value: dict[str, Any], actor: str) -> None:
    row = db.get(AppSetting, key)
    if row is None:
        db.add(AppSetting(key=key, value=value, updated_by=actor))
    else:
        row.value = value
        row.updated_by = actor
