"""ServiceNow Table API client (M3). Stdlib-only, OAuth-ready, credential-safe.

Auth: HTTP Basic from env today; bearer_token override reserved for OAuth
migration (bearer wins when set). Credentials live ONLY in
ServiceNowConfig (built from env) and the Authorization header —
never in URLs, bodies, logs, or LLM args (see incidents.py).
"""

from __future__ import annotations

import base64
import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable

from common.logging_setup import get_logger

logger = get_logger(__name__)

# transport(method, url, headers, body_json, timeout) -> (status, payload)
Transport = Callable[[str, str, dict[str, str], Any, int], tuple[int, Any]]


class ServiceNowError(Exception):
    def __init__(self, status: int, message: str) -> None:
        super().__init__(f"ServiceNow {status}: {message}")
        self.status = status
        self.message = message


class ServiceNowAuthError(ServiceNowError):
    pass


class ServiceNowNotFound(ServiceNowError):
    pass


@dataclass(frozen=True)
class ServiceNowConfig:
    instance_url: str
    username: str = ""
    password: str = ""
    bearer_token: str = ""  # OAuth migration path; wins over Basic when set
    timeout: int = 30

    @classmethod
    def from_settings(cls, settings: Any, timeout: int = 30) -> ServiceNowConfig:
        return cls(
            instance_url=getattr(settings, "servicenow_instance_url", ""),
            username=getattr(settings, "servicenow_user", ""),
            password=getattr(settings, "servicenow_pwd", ""),
            timeout=timeout,
        )

    @property
    def base_url(self) -> str:
        return self.instance_url.rstrip("/")

    @property
    def has_auth(self) -> bool:
        return bool(self.bearer_token or (self.username and self.password))

    def auth_header(self) -> str:
        if self.bearer_token:
            return f"Bearer {self.bearer_token}"
        raw = f"{self.username}:{self.password}".encode()
        return "Basic " + base64.b64encode(raw).decode()


def _urllib_transport(method: str, url: str, headers: dict[str, str],
                      body: Any, timeout: int) -> tuple[int, Any]:
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = int(resp.status)
            raw = resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        status = int(e.code)
        try:
            raw = e.read().decode("utf-8", "replace")
        except Exception:
            raw = ""
        try:
            return status, json.loads(raw) if raw else {}
        except ValueError:
            return status, {"error": raw[:500]}
    except (urllib.error.URLError, OSError, TimeoutError) as e:
        # Unreachable instance → typed error downstream, never a raw traceback.
        return 0, {"error": f"transport: {type(e).__name__}"}
    payload: Any = {}
    if raw:
        try:
            payload = json.loads(raw)
        except ValueError:
            payload = {"raw": raw[:2000]}
    return status, payload


class ServiceNowClient:
    """Thin Table API wrapper. All paths under /api/now/table/{table}."""

    def __init__(self, config: ServiceNowConfig,
                 transport: Transport | None = None) -> None:
        if not config.instance_url:
            raise ServiceNowError(0, "missing instance_url (set SERVICENOW_INSTANCE_URL)")
        self._config = config
        self._transport = transport or _urllib_transport

    @property
    def config(self) -> ServiceNowConfig:
        return self._config

    def _request(self, method: str, table: str, sys_id: str = "",
                 query: dict[str, str] | None = None,
                 body: dict[str, Any] | None = None) -> Any:
        path = f"/api/now/table/{table}"
        if sys_id:
            path += f"/{urllib.parse.quote(sys_id, safe='')}"
        url = self._config.base_url + path
        if query:
            url += "?" + urllib.parse.urlencode(query)
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": self._config.auth_header(),
        }
        try:
            status, payload = self._transport(method, url, headers, body,
                                              self._config.timeout)
        except ServiceNowError:
            raise
        except Exception as e:
            # Any transport may fail; callers only ever see typed errors.
            raise ServiceNowError(0, f"transport: {type(e).__name__}") from e
        logger.debug("snow %s %s -> %s", method, path, status)
        if status == 401:
            raise ServiceNowAuthError(status, "unauthorized — check PDI credentials")
        if status == 404:
            raise ServiceNowNotFound(status, f"{table}/{sys_id or '?'} not found")
        if status >= 400 or status == 0:
            detail = ""
            if isinstance(payload, dict):
                err = payload.get("error", payload)
                detail = str(err)[:300]
            raise ServiceNowError(status, detail or "request failed")
        if isinstance(payload, dict) and "result" in payload:
            return payload["result"]
        return payload

    def create(self, table: str, fields: dict[str, Any]) -> dict[str, Any]:
        result = self._request("POST", table, body=fields)
        if not isinstance(result, dict):
            raise ServiceNowError(500, f"unexpected create response for {table}")
        return result

    def get(self, table: str, sys_id: str,
            fields: str = "") -> dict[str, Any]:
        query = {"sysparm_fields": fields} if fields else None
        result = self._request("GET", table, sys_id=sys_id, query=query)
        if not isinstance(result, dict):
            raise ServiceNowError(500, f"unexpected get response for {table}")
        return result

    def list(self, table: str, query_str: str = "", fields: str = "",
             limit: int = 20) -> list[dict[str, Any]]:
        query: dict[str, str] = {"sysparm_limit": str(limit)}
        if query_str:
            query["sysparm_query"] = query_str
        if fields:
            query["sysparm_fields"] = fields
        result = self._request("GET", table, query=query)
        return result if isinstance(result, list) else []

    def update(self, table: str, sys_id: str,
               fields: dict[str, Any]) -> dict[str, Any]:
        result = self._request("PATCH", table, sys_id=sys_id, body=fields)
        if not isinstance(result, dict):
            raise ServiceNowError(500, f"unexpected update response for {table}")
        return result
