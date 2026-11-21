"""Change lifecycle state machine: PROPOSED -> ... -> COMPLETED | ROLLED_BACK."""
from __future__ import annotations

ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    "PROPOSED": {"VALIDATING"},
    "VALIDATING": {"AWAITING_APPROVAL", "FAILED"},
    "AWAITING_APPROVAL": {"APPROVED", "REJECTED", "VALIDATING"},
    "APPROVED": {"EXECUTING"},
    "EXECUTING": {"VERIFYING"},
    "VERIFYING": {"COMPLETED", "FAILED", "ROLLED_BACK"},
    "FAILED": {"ROLLED_BACK"},
    "COMPLETED": {"ROLLED_BACK"},
    "REJECTED": set(),
    "ROLLED_BACK": set(),
}


class IllegalTransition(Exception):
    def __init__(self, from_status: str, to_status: str) -> None:
        super().__init__(
            f"illegal status transition {from_status} -> {to_status}"
        )
        self.from_status = from_status
        self.to_status = to_status


def transition(current: str, target: str) -> str:
    allowed = ALLOWED_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise IllegalTransition(current, target)
    return target
