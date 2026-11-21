"""The LLM's structured output and the deterministic checks every proposal must pass.

Rules (all deterministic):
- The proposal must parse into `ResolutionProposal` (schema).
- The exception must equal the matcher's primary exception. The only allowed change is an
  escalation to VENDOR_BANK_CHANGE backed by a remittance-change text signal: text can make
  the system more cautious, never less (no downgrades).
- If the text screen raised REMITTANCE_CHANGE_REQUEST, the exception must be
  VENDOR_BANK_CHANGE.
- Every citation must be a chunk retrieved in this case.
- The action must be allowed for the exception (the policy engine re-checks this).
"""

import json
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from invoiceflow.agent.text_screen import REMITTANCE_CHANGE_REQUEST
from invoiceflow.data.models import Action, ExceptionCode, Frozen
from invoiceflow.policy.matrix import ControlMatrix


class ResolutionProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    exception: ExceptionCode
    action: Action
    rationale: str = Field(max_length=2000)
    citations: list[str] = Field(min_length=1, max_length=6)
    text_signals: list[str] = Field(default_factory=list)
    vendor_email_needed: bool = False


def proposal_schema() -> dict[str, Any]:
    return ResolutionProposal.model_json_schema()


class Issue(Frozen):
    code: str
    message: str


def validate_proposal(
    raw: str,
    matcher_primary: ExceptionCode,
    screen_signals: list[str],
    retrieved_ids: set[str],
    matrix: ControlMatrix,
) -> tuple[ResolutionProposal | None, list[Issue]]:
    try:
        proposal = ResolutionProposal.model_validate(json.loads(raw))
    except (json.JSONDecodeError, ValidationError, TypeError) as exc:
        return None, [Issue(code="SCHEMA_INVALID", message=str(exc)[:500])]

    issues: list[Issue] = []
    remittance = REMITTANCE_CHANGE_REQUEST in screen_signals
    if proposal.exception is not matcher_primary:
        escalation = proposal.exception is ExceptionCode.VENDOR_BANK_CHANGE and (
            remittance or REMITTANCE_CHANGE_REQUEST in proposal.text_signals
        )
        if not escalation:
            issues.append(
                Issue(
                    code="EXCEPTION_OVERRIDE",
                    message=f"matcher found {matcher_primary}; proposal says {proposal.exception}. "
                    "Only an evidenced escalation to VENDOR_BANK_CHANGE may differ.",
                )
            )
    if remittance and proposal.exception is not ExceptionCode.VENDOR_BANK_CHANGE:
        issues.append(
            Issue(
                code="SIGNAL_IGNORED",
                message="the invoice text asks to pay a different account (AP-POL §7.1); this must "
                "be escalated as VENDOR_BANK_CHANGE",
            )
        )
    unknown = [c for c in proposal.citations if c not in retrieved_ids]
    if unknown:
        issues.append(
            Issue(
                code="CITATION_NOT_RETRIEVED",
                message=f"citations {unknown} were not retrieved in this case; cite only from "
                f"{sorted(retrieved_ids)[:12]}",
            )
        )
    if proposal.action not in matrix.exceptions[proposal.exception].allowed_actions:
        issues.append(
            Issue(
                code="ACTION_NOT_ALLOWED",
                message=f"{proposal.action} is not allowed for {proposal.exception}",
            )
        )
    return proposal, issues
