from collections.abc import Awaitable, Callable
from enum import StrEnum
from typing import Any

from app.models.domain import Candidate, Operation, Risk

BRANCHES = ("schema", "quality", "infrastructure", "dependency", "change")
CONTROLLED_OPERATIONS = {
    Operation.MAP_CUSTOMER,
    Operation.RESTORE_CUSTOMER,
    Operation.DEDUPLICATE,
    Operation.CORRECT_AMOUNT,
    Operation.RETRY_DEPENDENCY,
}


class Role(StrEnum):
    INVESTIGATOR = "investigator"
    SANDBOX = "sandbox"


def risk_for(candidate: Candidate) -> Risk:
    operations = set(candidate.operations)
    if operations & {Operation.DELETE, Operation.REWRITE}:
        return Risk.CRITICAL
    if Operation.SCHEMA in operations:
        return Risk.HIGH
    if operations & {Operation.RETRY_DEPENDENCY, Operation.CONFIGURATION}:
        return Risk.MEDIUM
    return Risk.LOW


def authorize(role: Role, tool: str) -> None:
    allowed = {
        Role.INVESTIGATOR: {f"read_{b}" for b in BRANCHES},
        Role.SANDBOX: {"sandbox_apply", "pipeline_replay"},
    }
    if tool not in allowed[role]:
        raise PermissionError(f"{role} cannot invoke {tool}")


async def invoke_tool(
    role: Role, name: str, call: Callable[[], Awaitable[Any]], audit: Callable[..., Awaitable[None]]
) -> Any:
    try:
        authorize(role, name)
    except PermissionError:
        await audit("tool_denied", name, {"role": role})
        raise
    await audit("tool_called", name, {"role": role})
    return await call()
