"""Secret redaction for zero-secret architecture (M1 minimal, extended in M25)."""

from __future__ import annotations

import os
import re

# Patterns mirror studio front-man PII middleware (see FRAMEWORK_FACTS §7).
_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("GOOGLE_API_KEY", re.compile(r"AIza[0-9A-Za-z_\-]{35}")),
    ("OPENAI_KEY", re.compile(r"sk-(proj-)?[A-Za-z0-9_\-]+")),
    ("ANTHROPIC_KEY", re.compile(r"sk-ant-[A-Za-z0-9_\-]+")),
    ("AWS_KEY", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("GITHUB_TOKEN", re.compile(r"gh[pousr]_[A-Za-z0-9]+")),
    ("SLACK_TOKEN", re.compile(r"xox[baprs]-[A-Za-z0-9\-]+")),
    ("BEARER", re.compile(r"Bearer\s+[A-Za-z0-9._~+/=\-]{20,}")),
    ("HOCON_ENV_REF", re.compile(r"\$\{[^}]+\}")),
)

_PLACEHOLDER = "[REDACTED]"


def _env_secret_values() -> list[str]:
    values: list[str] = []
    for key in ("GOOGLE_API_KEY", "SERVICENOW_PWD", "SERVICENOW_PASSWORD",
                "SERVICENOW_USER", "SERVICENOW_USERNAME"):
        val = os.environ.get(key, "")
        if val and val != f"YOUR_{key}" and "YOUR_" not in val and len(val) >= 8:
            values.append(val)
    return values


def redact_text(text: str, extra_secrets: tuple[str, ...] = ()) -> str:
    """Replace known secret shapes (and live env secret values) with [REDACTED]."""
    redacted = text
    for _, pattern in _PATTERNS:
        redacted = pattern.sub(_PLACEHOLDER, redacted)
    for secret in list(_env_secret_values()) + [s for s in extra_secrets if s]:
        if secret and secret in redacted:
            redacted = redacted.replace(secret, _PLACEHOLDER)
    return redacted


def scan_prompt_for_secrets(prompt: str) -> list[str]:
    """Return sorted names of secret patterns found in prompt (empty = clean)."""
    found = [name for name, pattern in _PATTERNS if pattern.search(prompt)]
    for val in _env_secret_values():
        if val and val in prompt and "ENV_VALUE" not in found:
            found.append("ENV_VALUE")
    return sorted(found)
