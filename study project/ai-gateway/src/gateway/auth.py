"""Tenant keys: generate once, store sha256 hash, verify in constant time."""

from __future__ import annotations

import hashlib
import hmac
import secrets


def generate_api_key(prefix: str = "sk-gw-") -> str:
    """Create a new tenant API key shown to the tenant exactly once."""
    return prefix + secrets.token_urlsafe(32)


def hash_key(raw_key: str) -> str:
    """SHA-256 hex digest of a raw key (what we store in the DB)."""
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def verify_key(raw_key: str, stored_hash: str) -> bool:
    """Constant-time comparison so timing does not leak which key is closer."""
    candidate = hash_key(raw_key)
    return hmac.compare_digest(candidate, stored_hash)
