from __future__ import annotations

from urllib.parse import urlparse

from app.constants import DEFAULT_AUTHORITATIVE_DOMAINS


def hostname_of(url: str) -> str | None:
    try:
        parsed = urlparse(url)
    except Exception:
        return None
    host = (parsed.hostname or "").lower().rstrip(".")
    if not host or parsed.scheme not in {"http", "https"}:
        return None
    return host


def is_allowlisted(url: str, extra_domains: tuple[str, ...] = ()) -> bool:
    """Hostname-based allowlist. Rejects evil-rbi.org.in and rbi.org.in.attacker.com."""
    host = hostname_of(url)
    if not host:
        return False
    allowed = tuple(d.lower() for d in (*DEFAULT_AUTHORITATIVE_DOMAINS, *extra_domains))
    for domain in allowed:
        if host == domain or host.endswith("." + domain):
            return True
    return False


def assert_no_ssrf(url: str) -> None:
    host = hostname_of(url)
    if not host:
        raise ValueError("invalid url")
    blocked = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}
    if host in blocked or host.endswith(".local") or host.endswith(".internal"):
        raise ValueError("ssrf blocked")
    if host.startswith("10.") or host.startswith("192.168.") or host.startswith("169.254."):
        raise ValueError("ssrf blocked")
