"""Hardened outbound HTTP for integrations.

* Only hosts on an explicit allowlist can be contacted (model output can never pick a URL).
* TLS verification is always on; timeouts and bounded retries are mandatory.
"""

from __future__ import annotations

import logging
import time
from urllib.parse import urlparse

import httpx

log = logging.getLogger("aegis.http")

STATIC_ALLOWED_HOSTS = {
    "www.cisa.gov",
    "api.first.org",
    "services.nvd.nist.gov",
    "login.microsoftonline.com",
    "api.securitycenter.microsoft.com",
    "api.security.microsoft.com",
    "api-eu.securitycenter.microsoft.com",
    "api-us.securitycenter.microsoft.com",
    "api-uk.securitycenter.microsoft.com",
    "api.anthropic.com",
    "api.openai.com",
    "generativelanguage.googleapis.com",
}


class EgressDenied(Exception):
    pass


def allowed_hosts() -> set[str]:
    """Static allowlist plus hosts the operator configured explicitly via environment."""
    from app.core.config import get_settings

    s = get_settings()
    hosts = set(STATIC_ALLOWED_HOSTS)
    for url in (s.servicenow_instance_url, s.ai_base_url, s.defender_api_base, s.langfuse_host):
        if url:
            host = urlparse(url).hostname
            if host:
                hosts.add(host.lower())
    return hosts


def check_egress(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme != "https" and parsed.hostname not in {"localhost", "127.0.0.1"}:
        raise EgressDenied(f"Only HTTPS egress is permitted (got {parsed.scheme}://)")
    host = (parsed.hostname or "").lower()
    if host not in allowed_hosts():
        raise EgressDenied(f"Host '{host}' is not on the integration egress allowlist")


def request_with_retry(
    method: str,
    url: str,
    *,
    attempts: int = 3,
    timeout: float = 20.0,
    backoff: float = 1.0,
    retry_statuses: tuple[int, ...] = (429, 500, 502, 503, 504),
    client: httpx.Client | None = None,
    **kwargs: object,
) -> httpx.Response:
    """Allowlisted request with bounded exponential backoff for transient failures."""
    check_egress(url)
    own_client = client is None
    c = client or httpx.Client(timeout=timeout, verify=True, follow_redirects=False)
    try:
        last_exc: Exception | None = None
        for attempt in range(1, attempts + 1):
            try:
                resp = c.request(method, url, **kwargs)  # type: ignore[arg-type]
                if resp.status_code in retry_statuses and attempt < attempts:
                    log.warning("retryable status %s from %s (attempt %s)", resp.status_code, urlparse(url).hostname, attempt)
                    time.sleep(backoff * 2 ** (attempt - 1))
                    continue
                return resp
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                last_exc = exc
                if attempt < attempts:
                    time.sleep(backoff * 2 ** (attempt - 1))
        assert last_exc is not None
        raise last_exc
    finally:
        if own_client:
            c.close()
