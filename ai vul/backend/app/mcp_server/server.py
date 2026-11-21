"""Internal MCP server exposing narrowly scoped AegisRemediate tools.

* Transport: stdio (the MCP client launches this process locally; no network listener).
* Identity: every call runs as the active application user named by ``MCP_ACTOR_EMAIL``;
  the same role permissions apply as in the web UI.
* Allowlist: ``MCP_ALLOWED_TOOLS`` (comma separated, ``*`` = all registered tools).
* Every call is schema-validated, permission-checked, time-limited, redacted and recorded in
  ``tool_calls``; mutating calls are additionally written to the audit log.
* The only mutating tool (``remediation_request_approval``) submits a plan to the human
  approval engine - it can never approve, write to ServiceNow, or execute anything.

Run:  python -m app.mcp_server
"""

from __future__ import annotations

import inspect
import logging
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations
from sqlalchemy import select

from app.core.config import get_settings
from app.core.db import session_scope
from app.models.identity import User
from app.security.auth import Principal
from app.services.audit import record_audit
from app.tools import catalog as _catalog  # noqa: F401  (registers tools)
from app.tools.registry import ToolContext, ToolError, ToolSpec, registry

log = logging.getLogger("aegis.mcp")
TOOL_TIMEOUT_SECONDS = 20
_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="aegis-mcp")


def _principal() -> Principal:
    email = get_settings().mcp_actor_email
    with session_scope() as db:
        user = db.scalar(select(User).where(User.email == email))
        if user is None or not user.is_active:
            raise PermissionError(f"MCP actor '{email}' is not an active AegisRemediate user")
        return Principal.from_user(user)


def allowed_tools() -> set[str]:
    raw = get_settings().mcp_allowed_tools.strip()
    names = {s.name for s in registry.specs()}
    return names if raw in ("", "*") else {t.strip() for t in raw.split(",")} & names


def _invoke(spec: ToolSpec, args: dict[str, Any]) -> dict[str, Any]:
    principal = _principal()
    with session_scope() as db:
        ctx = ToolContext(db, principal, "mcp")
        result = registry.call(spec.name, args, ctx, allowed_tools())
        if spec.mutating:
            record_audit(
                db,
                actor=principal,
                action=f"mcp_{spec.name}",
                target_type="mcp_tool",
                target_id=spec.name,
                details={"arguments": args},
            )
        return result


def _make_handler(spec: ToolSpec):
    fields = spec.input_model.model_fields

    def handler(**kwargs: Any) -> dict[str, Any]:
        args = {k: v for k, v in kwargs.items() if v is not None}
        future = _pool.submit(_invoke, spec, args)
        try:
            return future.result(timeout=TOOL_TIMEOUT_SECONDS)
        except FutureTimeout:
            return {"error": f"tool timed out after {TOOL_TIMEOUT_SECONDS}s"}
        except (ToolError, PermissionError) as exc:
            return {"error": str(exc)}

    params = [
        inspect.Parameter(
            name,
            inspect.Parameter.KEYWORD_ONLY,
            default=inspect.Parameter.empty if f.is_required() else f.default,
            annotation=f.annotation,
        )
        for name, f in fields.items()
    ]
    handler.__signature__ = inspect.Signature(params, return_annotation=dict[str, Any])  # type: ignore[attr-defined]
    handler.__annotations__ = {n: f.annotation for n, f in fields.items()} | {"return": dict[str, Any]}
    handler.__name__ = spec.name
    handler.__doc__ = spec.description
    return handler


def build_server() -> MCPServer:
    server = MCPServer(
        name="aegisremediate",
        title="AegisRemediate AI",
        instructions=(
            "Read-only access to vulnerability, asset, threat-intelligence and remediation data. "
            "Remediation can only be submitted for human approval; approvals and ServiceNow writes are not exposed."
        ),
    )
    permitted = allowed_tools()
    for spec in registry.specs():
        if spec.name not in permitted:
            continue
        server.add_tool(
            _make_handler(spec),
            name=spec.name,
            description=spec.description,
            annotations=ToolAnnotations(
                readOnlyHint=not spec.mutating, destructiveHint=False, idempotentHint=not spec.mutating, openWorldHint=False
            ),
        )
    return server


def main() -> None:
    logging.basicConfig(level=logging.WARNING)  # stdout is the MCP channel: keep logs on stderr
    build_server().run("stdio")


if __name__ == "__main__":
    main()
