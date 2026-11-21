"""Symmetric encryption for stored browser authentication state."""

from __future__ import annotations

import base64
import hashlib
from functools import lru_cache

from cryptography.fernet import Fernet

from .config import get_settings


@lru_cache
def _fernet() -> Fernet:
    s = get_settings()
    key = s.credentials_key
    if not key:
        # Development only (production requires CREDENTIALS_KEY): derive a stable key from the session secret.
        key = base64.urlsafe_b64encode(hashlib.sha256(("browser-state:" + s.session_secret).encode()).digest()).decode()
    return Fernet(key.encode())


def encrypt(data: bytes) -> bytes:
    return _fernet().encrypt(data)


def decrypt(token: bytes) -> bytes:
    return _fernet().decrypt(token)
