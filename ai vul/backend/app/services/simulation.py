"""Simulation console: actions taken by the *simulated outside world* (ops team, ServiceNow users).

These controls exist only for the simulated environment and are clearly labelled in the UI.
They let a demo show realistic lifecycles: an implementer advancing a change in ServiceNow,
an engineer patching a host, or the ServiceNow API failing.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.types import utcnow
from app.integrations.servicenow.base import CHANGE_STATE_FLOW, CHANGE_STATES
from app.integrations.servicenow.mock import FAILURE_MODES, MockServiceNowClient
from app.models.servicenow import ServiceNowRecord
from app.models.simulation import SimDevice, SimDeviceSoftware
from app.security.auth import Principal
from app.services.audit import record_audit
from app.services.policy_store import SN_SIM_FAILURE_KEY, get_setting, put_setting


class SimulationError(Exception):
    pass


def _require_mock() -> None:
    if get_settings().servicenow_mode != "mock":
        raise SimulationError("ServiceNow simulation controls are disabled in real mode")


def set_failure_mode(db: Session, mode: str, remaining: int, actor: Principal) -> dict[str, Any]:
    _require_mock()
    if mode not in FAILURE_MODES:
        raise SimulationError(f"mode must be one of {FAILURE_MODES}")
    value = {"mode": mode, "remaining": remaining if mode != "none" else 0}
    put_setting(db, SN_SIM_FAILURE_KEY, value, actor.email)
    record_audit(db, actor=actor, action="simulation_failure_mode", target_type="servicenow_simulator", details=value)
    db.commit()
    return value


def failure_mode(db: Session) -> dict[str, Any]:
    return get_setting(db, SN_SIM_FAILURE_KEY, {"mode": "none", "remaining": 0})


def advance_change(
    db: Session, record_id: str, actor: Principal, target_state: str | None = None, close_code: str = "successful"
) -> dict[str, Any]:
    """Simulate a ServiceNow user moving the change through its lifecycle."""
    _require_mock()
    rec = db.get(ServiceNowRecord, record_id)
    if rec is None or not rec.sys_id or rec.table_name != "change_request":
        raise SimulationError("Select a synchronised change_request record")
    client = MockServiceNowClient(actor=f"sim.{actor.email.split('@')[0]}")
    remote = client.get(rec.table_name, rec.sys_id)
    if remote is None:
        raise SimulationError("Record not found in simulator")
    current = str(remote.get("state"))
    if target_state is None:
        if current not in CHANGE_STATE_FLOW or current == "3":
            raise SimulationError(f"Change is {CHANGE_STATES.get(current, current)}; nothing to advance")
        target_state = CHANGE_STATE_FLOW[CHANGE_STATE_FLOW.index(current) + 1]
    if target_state not in CHANGE_STATES:
        raise SimulationError("Unknown change state")
    fields: dict[str, Any] = {"state": target_state}
    if target_state == "-3":
        fields["approval"] = "approved"
    if target_state == "3":
        fields |= {"close_code": close_code, "close_notes": f"Closed in simulator by {actor.email}"}
    client.update(rec.table_name, rec.sys_id, fields)
    record_audit(
        db,
        actor=actor,
        action="simulation_change_advanced",
        target_type="servicenow_record",
        target_id=rec.id,
        previous_state={"state": CHANGE_STATES.get(current)},
        new_state={"state": CHANGE_STATES.get(target_state)},
    )
    db.commit()
    return {"number": rec.number, "from": CHANGE_STATES.get(current), "to": CHANGE_STATES.get(target_state)}


def apply_patch(db: Session, device_id: str, vendor: str, product: str, version: str, actor: Principal) -> dict[str, Any]:
    """Simulate an engineer installing a new software version on a Defender-managed device."""
    sw = db.scalar(
        select(SimDeviceSoftware).where(
            SimDeviceSoftware.device_id == device_id,
            func.lower(SimDeviceSoftware.vendor) == vendor.lower(),
            func.lower(SimDeviceSoftware.product) == product.lower(),
        )
    )
    if sw is None:
        raise SimulationError("Software not installed on this simulated device")
    if not version or len(version) > 64:
        raise SimulationError("Provide the version that was deployed")
    previous = sw.version
    sw.version = version.strip()
    sw.updated_at = utcnow()
    device = db.get(SimDevice, device_id)
    record_audit(
        db,
        actor=actor,
        action="simulation_patch_applied",
        target_type="sim_device",
        target_id=device_id,
        previous_state={"product": product, "version": previous},
        new_state={"product": product, "version": sw.version},
        details={"hostname": device.computer_dns_name if device else None},
    )
    db.commit()
    return {"device_id": device_id, "product": sw.display_name, "from": previous, "to": sw.version}
