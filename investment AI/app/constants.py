from __future__ import annotations

from datetime import timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

try:
    IST = ZoneInfo("Asia/Kolkata")
except ZoneInfoNotFoundError:
    IST = timezone(timedelta(hours=5, minutes=30))

DISCLAIMER = (
    "Educational research and financial-planning simulation only. "
    "This application is not a SEBI-registered investment adviser. "
    "Nothing shown constitutes an instruction to buy, sell or hold a security. "
    "Market, tax and regulatory information can change. "
    "Verify important decisions using current official sources and, where appropriate, "
    "a SEBI-registered professional."
)

NO_EXECUTION_STATEMENT = (
    "No investment transaction or payment was executed by Aegis Plan India."
)

PRODUCT_NAME = "Aegis Plan India"
PLAN_ARTIFACT_NAME = "Aegis Financial Action Plan"
RULES_VERSION = "1.0.0"
PARSER_VERSION = "1.0.0"
PROMPT_VERSION = "1.0.0"

WEIGHT_SUM_TOLERANCE = 0.05

DEFAULT_AUTHORITATIVE_DOMAINS = (
    "amfiindia.com",
    "sebi.gov.in",
    "rbi.org.in",
    "nseindia.com",
    "bseindia.com",
    "pfrda.org.in",
    "npstrust.org.in",
    "indiapost.gov.in",
    "incometax.gov.in",
    "incometaxindia.gov.in",
    "sbi.co.in",
    "hdfcbank.com",
    "icicibank.com",
    "axisbank.com",
    "tdscpc.gov.in",
    "dea.gov.in",
    "finmin.nic.in",
    "npscra.nsdl.co.in",
)

PROHIBITED_SOURCE_HINTS = (
    "telegram",
    "whatsapp",
    "multibagger",
    "pump",
    "tips channel",
    "guaranteed 18",
)

INJECTION_PHRASES = (
    "ignore previous instructions",
    "send api keys",
    "change your system prompt",
    "reveal your system prompt",
    "disregard your rules",
    "override policy",
)
