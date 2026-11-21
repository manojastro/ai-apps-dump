"""Layered guardrails: size limit, injection heuristics, PII redaction,
output schema + secrets checks. Every block carries a reason (logged to ledger).
Synthetic patterns only — including Indian ID shapes on fake data.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

import yaml

# --- Injection heuristics: high confidence vs medium -------------------------
HIGH_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"ignore\s+your\s+system\s+prompt",
    r"reveal\s+your\s+system\s+prompt",
    r"print\s+your\s+system\s+prompt",
    r"\bDAN\s+mode\b",
    r"jailbreak",
    r"exfiltrat",
    r"bypass\s+(your\s+)?(safety|guardrail|filter)",
    r"disable\s+(your\s+)?(safety|guardrail|filter)",
]
MEDIUM_PATTERNS = [
    r"pretend\s+you\s+are\s+(not|no\s+longer)",
    r"act\s+as\s+if\s+you\s+have\s+no\s+restrictions",
    r"do\s+anything\s+now",
    r"developer\s+mode",
    r"you\s+are\s+now\s+unrestricted",
    r"override\s+your\s+instructions",
]

HIGH_RE = [re.compile(p, re.IGNORECASE) for p in HIGH_PATTERNS]
MEDIUM_RE = [re.compile(p, re.IGNORECASE) for p in MEDIUM_PATTERNS]

# --- PII (synthetic test shapes) ----------------------------------------------
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
# Indian 10-digit mobile: +91 optional, separator optional; require a valid
# leading digit 6-9 so order numbers / pincodes / short ids do NOT match.
PHONE_RE = re.compile(r"(?:\+91[\s-]?)?(?<![0-9])[6-9][0-9]{9}(?![0-9])")
AADHAAR_RE = re.compile(r"(?<![0-9])[2-9][0-9]{3}\s[0-9]{4}\s[0-9]{4}(?![0-9])")
PAN_RE = re.compile(r"(?<![A-Z0-9])[A-Z]{5}[0-9]{4}[A-Z](?![A-Z0-9])")

# --- Output secrets -------------------------------------------------------------
SECRET_RES = [
    (re.compile(r"sk-[A-Za-z0-9]{8,}"), "api_key_leak"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "aws_key_leak"),
    (re.compile(r"(?i)(password|passwd|api[_-]?key)\s*[:=]\s*\S+"), "credential_leak"),
]


@dataclass
class GuardrailResult:
    allowed: bool
    reason: str = ""
    redacted_text: str = ""
    pii_found: list[str] | None = None


def load_profiles(path: str) -> dict[str, dict[str, object]]:
    return dict(yaml.safe_load(Path(path).read_text(encoding="utf-8")))


def injection_level(text: str) -> str:
    """Return 'high', 'medium', or 'none'."""
    for rx in HIGH_RE:
        if rx.search(text):
            return "high"
    for rx in MEDIUM_RE:
        if rx.search(text):
            return "medium"
    return "none"


def redact_pii(text: str) -> tuple[str, list[str]]:
    """Redact emails / phones / Aadhaar / PAN shapes. Returns (text, found)."""
    found: list[str] = []

    def _sub(rx: re.Pattern[str], label: str, token: str, s: str) -> str:
        def repl(m: re.Match[str]) -> str:
            found.append(f"{label}:{m.group(0)[:4]}...")
            return token

        return rx.sub(repl, s)

    # Order matters: structured IDs first so phone regex never eats Aadhaar parts
    # (Aadhaar starts with 2-9 and is space-separated, phone needs 10 contiguous).
    text = _sub(AADHAAR_RE, "aadhaar", "[REDACTED_AADHAAR]", text)
    text = _sub(PAN_RE, "pan", "[REDACTED_PAN]", text)
    text = _sub(EMAIL_RE, "email", "[REDACTED_EMAIL]", text)
    text = _sub(PHONE_RE, "phone", "[REDACTED_PHONE]", text)
    return text, found


def check_input(text: str, profile: dict[str, object]) -> GuardrailResult:
    max_chars = int(str(profile.get("max_input_chars", 8000)))
    if len(text) > max_chars:
        return GuardrailResult(False, "input_too_large", text, [])
    level = injection_level(text)
    mode = str(profile.get("block_injection", "high_only"))
    if level == "high" or (level == "medium" and mode == "medium_and_high"):
        return GuardrailResult(False, f"injection_{level}", text, [])
    redacted, found = redact_pii(text)
    return GuardrailResult(True, "", redacted, found)


def check_output(text: str, profile: dict[str, object],
                 expect_json: bool = False) -> GuardrailResult:
    if expect_json or bool(profile.get("output_json_check", False)) and expect_json:
        try:
            json.loads(text)
        except json.JSONDecodeError:
            return GuardrailResult(False, "output_schema_invalid", text, [])
    if bool(profile.get("block_output_secrets", True)):
        for rx, reason in SECRET_RES:
            if rx.search(text):
                return GuardrailResult(False, reason, text, [])
    _, found = redact_pii(text)  # detect PII leak shape in output
    if found and str(profile.get("redact_pii", True)).lower() != "false":
        return GuardrailResult(False, "output_pii_leak", text, found)
    return GuardrailResult(True, "", text, [])
