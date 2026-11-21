"""Network egress guard applied to every browser context.

Only explicitly configured supplier origins (plus inline data: resources) may be requested.
Redirects, subresources, new tabs and downloads all pass through the same check. Link-local
metadata endpoints and unrelated private networks are never permitted, even if misconfigured.
"""

from __future__ import annotations

import ipaddress
from dataclasses import dataclass, field
from urllib.parse import urlsplit

ALWAYS_BLOCKED_HOSTS = {"169.254.169.254", "metadata.google.internal", "metadata", "100.100.100.200", "fd00:ec2::254"}


def origin_of(url: str) -> str | None:
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        return None
    port = parts.port or (443 if parts.scheme == "https" else 80)
    default = (parts.scheme == "https" and port == 443) or (parts.scheme == "http" and port == 80)
    host = parts.hostname
    return f"{parts.scheme}://{host}" + ("" if default else f":{port}")


def _is_link_local(host: str) -> bool:
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False
    return ip.is_link_local or ip.is_multicast or ip.is_unspecified


@dataclass
class EgressGuard:
    allowed_origins: set[str]
    blocked: list[dict[str, str]] = field(default_factory=list)

    def check(self, url: str) -> tuple[bool, str]:
        if url.startswith(("data:", "about:blank", "blob:")):
            return True, "inline"
        parts = urlsplit(url)
        host = (parts.hostname or "").lower()
        if host in ALWAYS_BLOCKED_HOSTS or _is_link_local(host):
            return False, "metadata_or_link_local"
        origin = origin_of(url)
        if origin is None:
            return False, "unsupported_scheme"
        if origin.rstrip("/") not in self.allowed_origins:
            return False, "origin_not_allowed"
        return True, "allowed"

    def record(self, url: str, reason: str, kind: str) -> None:
        self.blocked.append({"url": url[:300], "reason": reason, "kind": kind})

    def install(self, context) -> None:
        """Attach to a Playwright BrowserContext (sync API)."""

        def handle(route, request):
            ok, reason = self.check(request.url)
            if ok:
                route.continue_()
            else:
                self.record(request.url, reason, request.resource_type)
                route.abort("blockedbyclient")

        context.route("**/*", handle)

        def on_page(page):
            # Pages are opened only by our own code; any other tab (window.open, target=_blank) is closed.
            if getattr(context, "_procnav_primary", None) is not None and page is not context._procnav_primary:
                self.record(page.url or "about:blank", "new_tab_closed", "popup")
                page.close()

        context.on("page", on_page)
