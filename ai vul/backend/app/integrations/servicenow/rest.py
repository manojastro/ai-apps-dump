"""ServiceNow Table API adapter for a real instance (e.g. a Personal Developer Instance).

Authentication (in order of preference):
1. OAuth 2.0 client credentials  (SERVICENOW_CLIENT_ID / SERVICENOW_CLIENT_SECRET)
2. OAuth 2.0 password grant      (client id/secret + SERVICENOW_USERNAME / SERVICENOW_PASSWORD)
3. Basic auth                    (SERVICENOW_USERNAME / SERVICENOW_PASSWORD, PDI convenience)

Writes are only ever invoked by ``ServiceNowSyncService`` after the deterministic approval
gate passes, and only to tables configured by the operator.
"""

from __future__ import annotations

import logging
import time
from typing import Any
from urllib.parse import urlparse

import httpx

from app.core.config import Settings
from app.integrations.http import check_egress
from app.integrations.servicenow.base import (
    ServiceNowAuthError,
    ServiceNowClient,
    ServiceNowError,
    ServiceNowPermissionError,
    ServiceNowSchemaError,
    ServiceNowServerError,
    ServiceNowTimeout,
)

log = logging.getLogger("aegis.servicenow.rest")


class RestServiceNowClient(ServiceNowClient):
    mode = "real"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.base = settings.servicenow_instance_url.rstrip("/")
        self.instance_label = urlparse(self.base).hostname or self.base
        self._token: str | None = None
        self._token_exp = 0.0
        self._schema_cache: dict[str, set[str] | None] = {}
        check_egress(self.base)

    # ------------------------------------------------------------------ auth
    def _auth_kwargs(self) -> dict[str, Any]:
        s = self.settings
        if s.servicenow_client_id and s.servicenow_client_secret.get_secret_value():
            return {"headers": {"Authorization": f"Bearer {self._oauth_token()}"}}
        if s.servicenow_username and s.servicenow_password.get_secret_value():
            return {"auth": (s.servicenow_username, s.servicenow_password.get_secret_value())}
        raise ServiceNowAuthError("No ServiceNow credentials configured")

    def _oauth_token(self) -> str:
        if self._token and time.time() < self._token_exp - 60:
            return self._token
        s = self.settings
        data = {"client_id": s.servicenow_client_id, "client_secret": s.servicenow_client_secret.get_secret_value()}
        if s.servicenow_username and s.servicenow_password.get_secret_value():
            data |= {
                "grant_type": "password",
                "username": s.servicenow_username,
                "password": s.servicenow_password.get_secret_value(),
            }
        else:
            data |= {"grant_type": "client_credentials"}
        try:
            resp = httpx.post(f"{self.base}/oauth_token.do", data=data, timeout=self.settings.servicenow_timeout_seconds)
        except httpx.TimeoutException as exc:
            raise ServiceNowTimeout("OAuth token request timed out") from exc
        if resp.status_code != 200:
            raise ServiceNowAuthError(f"OAuth token request failed (HTTP {resp.status_code})", resp.status_code)
        body = resp.json()
        self._token = body["access_token"]
        self._token_exp = time.time() + int(body.get("expires_in", 1800))
        return self._token

    # ------------------------------------------------------------------ transport
    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        url = f"{self.base}{path}"
        check_egress(url)
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        auth = self._auth_kwargs()
        headers |= auth.pop("headers", {})
        try:
            resp = httpx.request(
                method, url, headers=headers, timeout=self.settings.servicenow_timeout_seconds, verify=True, **auth, **kwargs
            )
        except httpx.TimeoutException as exc:
            raise ServiceNowTimeout(f"{method} {path} timed out") from exc
        except httpx.TransportError as exc:
            # The request may or may not have reached the instance.
            err = ServiceNowTimeout(f"{method} {path} transport error: {type(exc).__name__}")
            raise err from exc
        if resp.status_code == 401:
            self._token = None
            raise ServiceNowAuthError("ServiceNow rejected credentials (401)", 401)
        if resp.status_code == 403:
            raise ServiceNowPermissionError("ServiceNow ACL denied the operation (403)", 403)
        if resp.status_code == 404:
            return {}
        if resp.status_code >= 500 or resp.status_code == 429:
            raise ServiceNowServerError(f"ServiceNow HTTP {resp.status_code}", resp.status_code)
        if resp.status_code >= 400:
            detail = (
                resp.json().get("error", {}).get("message", "")
                if resp.headers.get("content-type", "").startswith("application/json")
                else ""
            )
            raise ServiceNowError(f"ServiceNow HTTP {resp.status_code}: {detail[:200]}", resp.status_code)
        return resp.json() if resp.content else {}

    # ------------------------------------------------------------------ contract
    def query(self, table: str, query: str = "", fields: list[str] | None = None, limit: int = 100) -> list[dict[str, Any]]:
        params: dict[str, Any] = {
            "sysparm_query": query,
            "sysparm_limit": min(limit, 1000),
            "sysparm_exclude_reference_link": "true",
        }
        if fields:
            params["sysparm_fields"] = ",".join(fields)
        return self._request("GET", f"/api/now/table/{table}", params=params).get("result", [])

    def get(self, table: str, sys_id: str) -> dict[str, Any] | None:
        body = self._request("GET", f"/api/now/table/{table}/{sys_id}", params={"sysparm_exclude_reference_link": "true"})
        return body.get("result") or None

    def create(self, table: str, fields: dict[str, Any]) -> dict[str, Any]:
        self._verify_fields(table, fields)
        return self._request("POST", f"/api/now/table/{table}", json=fields).get("result", {})

    def update(self, table: str, sys_id: str, fields: dict[str, Any]) -> dict[str, Any]:
        self._verify_fields(table, fields)
        result = self._request("PATCH", f"/api/now/table/{table}/{sys_id}", json=fields).get("result")
        if not result:
            raise ServiceNowError(f"{table}/{sys_id} not found", 404)
        return result

    def table_fields(self, table: str) -> set[str] | None:
        """Read the real schema from sys_dictionary (includes parent-table fields such as task.*)."""
        if table in self._schema_cache:
            return self._schema_cache[table]
        names: set[str] = set()
        try:
            tables = [table]
            # Walk the table hierarchy (change_request extends task) via sys_db_object.
            current = table
            for _ in range(5):
                rows = self.query("sys_db_object", f"name={current}", ["super_class.name"], 1)
                parent = rows[0].get("super_class.name") if rows else None
                if not parent:
                    break
                tables.append(parent)
                current = parent
            for t in tables:
                for row in self.query("sys_dictionary", f"name={t}^elementISNOTEMPTY", ["element"], 1000):
                    names.add(row["element"])
        except ServiceNowPermissionError:
            log.warning("cannot read sys_dictionary for %s; schema verification unavailable", table)
            self._schema_cache[table] = None
            return None
        self._schema_cache[table] = names
        return names

    def _verify_fields(self, table: str, fields: dict[str, Any]) -> None:
        known = self.table_fields(table)
        if known is None:
            raise ServiceNowSchemaError(f"Cannot verify schema of '{table}' (sys_dictionary not readable); refusing to write")
        if not known:
            raise ServiceNowSchemaError(f"Table '{table}' does not exist or is not accessible")
        unknown = set(fields) - known
        if unknown:
            raise ServiceNowSchemaError(f"Fields not present on '{table}': {sorted(unknown)}")

    def test_connection(self) -> dict[str, Any]:
        try:
            self.query(self.settings.servicenow_change_table, "", ["sys_id"], 1)
            schema = self.table_fields(self.settings.servicenow_change_table)
            return {
                "ok": True,
                "instance": self.instance_label,
                "mode": self.mode,
                "detail": "Authenticated; change table readable"
                + ("; schema verified" if schema else "; schema NOT readable (writes will be refused)"),
            }
        except ServiceNowError as exc:
            return {"ok": False, "instance": self.instance_label, "mode": self.mode, "detail": str(exc)}

    def record_url(self, table: str, sys_id: str) -> str | None:
        return f"{self.base}/nav_to.do?uri={table}.do?sys_id={sys_id}"
