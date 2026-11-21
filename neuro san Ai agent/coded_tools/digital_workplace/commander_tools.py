"""Commander coded tools (M7): routing + context. The LLM decides; these inform.

RouteRequest returns RANKED specialists with reasons — never a fixed chain.
"""

from __future__ import annotations

from typing import Any

from neuro_san.interfaces.coded_tool import CodedTool

from coded_tools.digital_workplace._ctx import get_bundle

_SIGNALS = (
    ("endpoint_agent", ("slow", "cpu", "ram", "memory", "disk", "freeze",
                        "freezing", "boot", "laptop", "process")),
    ("software_agent", ("install", "software", "version", "update", "app ",
                        "application", "teams", "vs code", "patch")),
    ("network_agent", ("vpn", "network", "dns", "proxy", "wifi", "unstable",
                       "connect", "gateway", "zscaler")),
    ("identity_agent", ("password", "login", "log in", "mfa", "auth",
                        "account", "sign-in", "signin", "locked")),
    ("knowledge_agent", ("policy", "policies", "leave", "reimburs",
                         "how do i", "how to", "process", "request software",
                         "sap access", "travel")),
)


class RouteRequest(CodedTool):
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        text = str(args.get("request_text", "")).lower()
        ranked = []
        for agent, keywords in _SIGNALS:
            hits = [kw for kw in keywords if kw in text]
            if hits:
                ranked.append({"agent": agent, "score": len(hits),
                               "reason": f"matched: {', '.join(hits[:3])}"})
        ranked.sort(key=lambda r: r["score"], reverse=True)
        ranked.append({"agent": "rca_agent", "score": 0,
                       "reason": "always available for evidence fusion"})
        return {"ranked": ranked}


class GetUserContext(CodedTool):
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        user_id = str(args.get("user_id", sly_data.get("user_id", "USER_001")))
        bundle = get_bundle(42)
        estate = bundle.estate
        user = estate.users.get(user_id, {"user_id": user_id})
        device_id = str(args.get("device_id", sly_data.get("device_id", "")))
        if not device_id:
            num = "".join(c for c in user_id if c.isdigit()) or "001"
            device_id = f"DEVICE_{int(num):03d}"
        return {"user_id": user_id, "device_id": device_id,
                "role": user.get("role", "employee"),
                "department": user.get("department", ""),
                "user_role": user.get("role", "employee")}


class GetCaseContext(CodedTool):
    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        from common.config import load_settings
        from database.bootstrap import get_connection, init_db
        case_id = str(args.get("case_id", sly_data.get("case_id", "")))
        if not case_id:
            return {"case": {}, "note": "no case_id in context yet"}
        db_path = load_settings(env_file=".env").db_path
        init_db(db_path)
        conn = get_connection(db_path)
        try:
            row = conn.execute("SELECT * FROM cases WHERE case_id=?",
                               (case_id,)).fetchone()
            return {"case": dict(row) if row else {}}
        finally:
            conn.close()


class SearchKnownWorkflows(CodedTool):
    """Approved reusable workflows only (candidates excluded). M21 owns promotion."""

    async def async_invoke(self, args: dict[str, Any], sly_data: dict[str, Any]) -> Any:
        from common.config import load_settings
        from database.bootstrap import get_connection, init_db
        signature = str(args.get("failure_signature", ""))
        db_path = load_settings(env_file=".env").db_path
        init_db(db_path)
        conn = get_connection(db_path)
        try:
            rows = conn.execute(
                "SELECT workflow_id, name, version, action_id, autonomy_level "
                "FROM workflows WHERE approval_state='approved' AND "
                "(failure_signature LIKE ? OR ?='')",
                (f"%{signature}%", signature)).fetchall()
            return {"workflows": [dict(r) for r in rows]}
        finally:
            conn.close()
