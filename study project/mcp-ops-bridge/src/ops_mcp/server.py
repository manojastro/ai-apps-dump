"""Minimal JSON-RPC 2.0 MCP server: stdio + Streamable-HTTP-ish bearer stub.

stdio: read one JSON object per line on stdin, write one per line on stdout.
Methods: initialize, tools/list, tools/call, resources/list, resources/read,
prompts/list, prompts/get, ping. Everything else -> -32601.

HTTP: FastAPI app exposing POST /mcp (same dispatch, Bearer auth) + GET /health.
"""

from __future__ import annotations

import json
import sys
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from mock_itsm.db import init_db
from mock_itsm.seed import seed_db
from ops_mcp.config import settings
from ops_mcp.resources import get_prompt, read_resource
from ops_mcp.tools import TOOL_DEFS, call_tool

PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {"name": "ops-mcp", "version": "0.1.0"}
MCP_VERSION_NOTE = "minimal JSON-RPC 2.0 over stdio + HTTP bearer stub (no external MCP SDK; offline slice)"


class RpcError(Exception):
    def __init__(self, code: int, message: str, data: Any = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data


def dispatch(db_path: str, method: str, params: dict[str, Any]) -> Any:
    if method == "initialize":
        return {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}, "resources": {}, "prompts": {}},
            "serverInfo": SERVER_INFO,
            "note": MCP_VERSION_NOTE,
        }
    if method in ("tools/list", "tools.list"):
        return {"tools": TOOL_DEFS}
    if method in ("tools/call", "tools.call"):
        name = str(params.get("name", ""))
        args = dict(params.get("arguments", {}))
        if not name:
            raise RpcError(-32602, "tools/call needs params.name")
        try:
            out = call_tool(db_path, name, args)
        except PermissionError as e:
            raise RpcError(-32000, f"approval required: {e}") from e
        except (ValueError, KeyError) as e:
            raise RpcError(-32602, str(e)) from e
        return {
            "content": [{"type": "text", "text": json.dumps(out, default=str)}],
            "isError": False,
        }
    if method in ("resources/list", "resources.list"):
        return {
            "resources": [
                {"uriTemplate": "incident://{number}", "name": "incident"},
                {"uriTemplate": "kedb://{doc_id}", "name": "kedb"},
            ]
        }
    if method in ("resources/read", "resources.read"):
        uri = str(params.get("uri", ""))
        return read_resource(db_path, uri)
    if method in ("prompts/list", "prompts.list"):
        return {
            "prompts": [
                {
                    "name": "triage_incident",
                    "description": "Triage an incident",
                    "arguments": [{"name": "number", "required": True}],
                }
            ]
        }
    if method in ("prompts/get", "prompts.get"):
        return get_prompt(str(params.get("name", "")), dict(params.get("arguments", {})))
    if method == "ping":
        return {}
    raise RpcError(-32601, f"method not found: {method}")


def handle_message(db_path: str, raw: dict[str, Any]) -> dict[str, Any] | None:
    msg_id = raw.get("id")
    method = str(raw.get("method", ""))
    params = raw.get("params", {})
    if not isinstance(params, dict):
        params = {}
    is_notification = msg_id is None
    try:
        if raw.get("jsonrpc") != "2.0" or not method:
            raise RpcError(-32600, "invalid request: need {jsonrpc:'2.0', id, method, params}")
        result = dispatch(db_path, method, params)
        if is_notification:
            return None
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}
    except RpcError as e:
        if is_notification:
            return None
        err: dict[str, Any] = {"code": e.code, "message": e.message}
        if e.data is not None:
            err["data"] = e.data
        return {"jsonrpc": "2.0", "id": msg_id, "error": err}
    except Exception as e:
        if is_notification:
            return None
        return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": -32603, "message": str(e)}}


def run_stdio(db_path: str) -> None:
    init_db(db_path)
    seed_db(db_path)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as e:
            sys.stdout.write(
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {"code": -32700, "message": f"parse error: {e}"},
                    }
                )
                + "\n"
            )
            sys.stdout.flush()
            continue
        resp = handle_message(db_path, raw)
        if resp is not None:
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()


class McpRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: int | str | None = None
    method: str
    params: dict[str, Any] = {}


def _check_bearer(authorization: str | None) -> None:
    expected = f"Bearer {settings.mcp_bearer_token}"
    if authorization != expected:
        raise HTTPException(status_code=401, detail="invalid bearer token")


def create_http_app(db_path: str | None = None) -> FastAPI:
    path = db_path or settings.itsm_db_path
    app = FastAPI(title="ops-mcp (HTTP bearer stub)")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "server": "ops-mcp"}

    @app.post("/mcp")
    def mcp(req: McpRequest, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        _check_bearer(authorization)
        init_db(path)
        seed_db(path)
        resp = handle_message(path, {"jsonrpc": req.jsonrpc, "id": req.id, "method": req.method, "params": req.params})
        return resp or {}

    return app


http_app = create_http_app()


def main() -> None:
    import argparse

    p = argparse.ArgumentParser(description="ops-mcp: stdio JSON-RPC or HTTP bearer stub")
    p.add_argument("--transport", default=settings.mcp_transport, choices=["stdio", "http"])
    p.add_argument("--db", default=settings.itsm_db_path)
    p.add_argument("--port", type=int, default=8002)
    args = p.parse_args()
    if args.transport == "http":
        import uvicorn

        init_db(args.db)
        seed_db(args.db)
        uvicorn.run(create_http_app(args.db), host="127.0.0.1", port=args.port)
    else:
        run_stdio(args.db)


if __name__ == "__main__":
    main()
