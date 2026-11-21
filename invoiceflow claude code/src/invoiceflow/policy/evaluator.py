"""Policy v1: a deterministic evaluator over the control matrix.

`evaluate` answers "may this proposal execute now?" with ALLOW, REQUIRE_APPROVAL or DENY,
and records which rule produced each part of the answer. Unknown or incompatible actions
are denied by default. `require_allow` is the gate the executor calls before any write.
"""

from collections.abc import Sequence

from invoiceflow.data.models import Action, ExceptionCode, Role
from invoiceflow.policy.matrix import ControlMatrix
from invoiceflow.policy.models import (
    Approval,
    Identity,
    Outcome,
    PolicyDecision,
    PolicyViolationError,
    Proposal,
    RuleResult,
    Verification,
)


class _Results:
    def __init__(self, matrix: ControlMatrix) -> None:
        self._matrix = matrix
        self.items: list[RuleResult] = []

    def add(self, rule_id: str, status: str, message: str) -> None:
        self.items.append(
            RuleResult.model_validate(
                {
                    "rule_id": rule_id,
                    "status": status,
                    "message": message,
                    "source": self._matrix.rule(rule_id).source,
                }
            )
        )

    def has(self, status: str) -> bool:
        return any(item.status == status for item in self.items)


def _can_approve(identity: Identity, matrix: ControlMatrix) -> bool:
    return identity.kind == "human" and identity.role in matrix.approver_hierarchy


def _required_role(proposal: Proposal, matrix: ControlMatrix) -> Role:
    candidates = [matrix.role_for_value(proposal.gross_value)]
    exception_role = matrix.exceptions[proposal.exception].required_role
    if exception_role is not None:
        candidates.append(exception_role)
    action_role = matrix.minimum_role_by_action.get(proposal.action)
    if action_role is not None:
        candidates.append(action_role)
    return max(candidates, key=matrix.rank)


def evaluate(
    proposal: Proposal,
    matrix: ControlMatrix,
    approvals: Sequence[Approval] = (),
    verifications: Sequence[Verification] = (),
) -> PolicyDecision:
    results = _Results(matrix)
    policy = matrix.exceptions[proposal.exception]

    if any(citation.strip() for citation in proposal.citations):
        results.add("CM-08", "pass", f"{len(proposal.citations)} citation(s)")
    else:
        results.add("CM-08", "fail", "the decision cites no policy or contract source")

    if proposal.action in policy.allowed_actions:
        results.add("CM-09", "pass", f"{proposal.action} is allowed for {proposal.exception}")
    else:
        allowed = ", ".join(policy.allowed_actions)
        results.add(
            "CM-09",
            "fail",
            f"{proposal.action} is not allowed for {proposal.exception} (allowed: {allowed})",
        )

    if proposal.action is Action.APPROVE:
        pv = proposal.price_variance
        detail = f"overcharge {pv.overcharge_amount} ({pv.overcharge_pct}%)"
        if pv.within_tolerance:
            results.add("CM-01", "pass", f"{detail} is within tolerance")
        else:
            results.add("CM-01", "fail", f"{detail} is beyond tolerance; APPROVE not allowed")

    if proposal.exception is ExceptionCode.VENDOR_BANK_CHANGE:
        if proposal.action is Action.ESCALATE_FRAUD_REVIEW:
            results.add("CM-03", "pass", "bank change is escalated for fraud review")
        else:
            results.add("CM-03", "fail", f"bank change must be escalated, not {proposal.action}")

    for approval in approvals:
        approver = approval.approver
        if not _can_approve(approver, matrix):
            who = "the agent" if approver.kind == "agent" else f"role {approver.role}"
            results.add("CM-06", "fail", f"{approver.id}: {who} can never approve")
        elif approver.id == proposal.preparer.id:
            results.add("CM-05", "fail", f"{approver.id} prepared this proposal; cannot approve it")

    required: Role | None = None
    needs_verification = False
    if proposal.action in matrix.actions_without_approval:
        results.add("CM-10", "pass", f"{proposal.action} is reversible and needs no approval")
    else:
        required = _required_role(proposal, matrix)
        needs_verification = policy.requires_out_of_band_verification
        valid = [
            a.approver
            for a in approvals
            if _can_approve(a.approver, matrix) and a.approver.id != proposal.preparer.id
        ]
        best = max((matrix.rank(a.role) for a in valid if a.role), default=-1)
        satisfied = best >= matrix.rank(required)
        status = "pass" if satisfied else "pending"
        message = "human approval recorded" if satisfied else "awaiting approval"
        results.add("CM-10", status, message)
        value_rule = "CM-04" if proposal.action in matrix.minimum_role_by_action else "CM-02"
        results.add(value_rule, status, f"requires {required} for gross {proposal.gross_value}")
        if needs_verification:
            verified = any(
                v.performed_by.kind == "human" and v.performed_by.id != proposal.preparer.id
                for v in verifications
            )
            results.add(
                "CM-03",
                "pass" if verified else "pending",
                "out-of-band verification recorded" if verified else "awaiting verification",
            )

    if results.has("fail"):
        outcome = Outcome.DENY
    elif results.has("pending"):
        outcome = Outcome.REQUIRE_APPROVAL
    else:
        outcome = Outcome.ALLOW
    return PolicyDecision(
        outcome=outcome,
        required_role=required,
        requires_out_of_band_verification=needs_verification,
        results=tuple(results.items),
        matrix_version=matrix.version_hash,
    )


def require_allow(decision: PolicyDecision) -> None:
    """CM-07: the executor calls this before every write. Anything but ALLOW stops it."""
    if decision.outcome is not Outcome.ALLOW:
        raise PolicyViolationError(f"execution blocked: policy outcome is {decision.outcome}")
