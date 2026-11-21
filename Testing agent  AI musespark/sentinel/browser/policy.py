"""Red-team policy layer: deterministic tripwires around the LLM agent.

The model is the last line of defense, not the first. These helpers run in
code on every observation, so known-hostile patterns are refused even if the
model is fooled:

- injection screen: hidden page text issuing instructions ("ignore previous
  instructions", "delete all records") -> refuse before acting.
- exfiltration screen: form/action URLs outside the domain allowlist -> refuse.
- fake-success check: UI claims success while network calls failed -> report
  the failure, not the banner.
- step budget: hard cap on actions per flow -> infinite-loop bait terminates.

Each maps to a redteam.yaml category and a fixture page in
evals/redteam/injection_pages/. Live scoring (pass rate per category) runs in
Phase 5; the tripwires themselves are proven here.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Literal

from sentinel.config import is_domain_allowed

logger = logging.getLogger("sentinel.policy")

INJECTION_PHRASES = (
    "ignore your previous instructions",
    "ignore all previous instructions",
    "disregard your instructions",
    "disregard all prior instructions",
    "delete all records",
    "delete every record",
    "drop table",
    "send password",
    "paste record data",
)

EXFILTRATION_PHRASES = (
    "paste record data into",
    "enter customer data below",
    "export records to",
    "send records to",
)


@dataclass(frozen=True)
class PolicyHit:
    category: Literal["injection", "exfiltration"]
    matched: str
    excerpt: str


def screen_page_text(text: str) -> list[PolicyHit]:
    """Flag hostile instructions embedded in page content (visible or hidden).

    Pure function of the text the agent was about to act on — the orchestrator
    must refuse the step when hits are non-empty. Case-insensitive.
    """
    lowered = text.lower()
    hits: list[PolicyHit] = []
    for phrase in INJECTION_PHRASES:
        if phrase in lowered:
            hits.append(PolicyHit("injection", phrase, text[max(0, lowered.find(phrase) - 40):][:120]))
    for phrase in EXFILTRATION_PHRASES:
        if phrase in lowered:
            hits.append(PolicyHit("exfiltration", phrase, text[max(0, lowered.find(phrase) - 40):][:120]))
    if hits:
        logger.warning("Policy screen hit: %s", [(h.category, h.matched) for h in hits])
    return hits


def find_external_targets(urls: list[str], allowed_domains: list[str]) -> list[str]:
    """Return URLs pointing outside the allowlist (data-exfiltration bait)."""
    return [u for u in urls if u.startswith(("http://", "https://")) and not is_domain_allowed(u, allowed_domains)]


def check_success_claim(claims_success: bool, failed_network_calls: list) -> Literal["ok", "fake_success"]:
    """Banner says saved but the network says 500 -> believe the network."""
    if claims_success and failed_network_calls:
        logger.warning("Fake-success pattern: UI claims success with %d failed calls",
                       len(failed_network_calls))
        return "fake_success"
    return "ok"


class BudgetExhausted(RuntimeError):
    pass


class StepBudget:
    """Hard step cap per flow. take() raises when bait tries to loop forever."""

    def __init__(self, max_steps: int) -> None:
        if max_steps < 1:
            raise ValueError("max_steps must be >= 1")
        self.remaining = max_steps

    def take(self) -> int:
        if self.remaining <= 0:
            raise BudgetExhausted("Step budget exhausted — abandoning flow instead of looping.")
        self.remaining -= 1
        return self.remaining
