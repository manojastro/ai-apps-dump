# InvoiceFlow policy v2: the control matrix in Rego (OPA 1.x).
#
# Same rules as the Python evaluator (src/invoiceflow/policy/evaluator.py); a parity test
# runs both over the same generated cases (tests/policy/test_opa_parity.py).
#
# data.matrix  : policy/control_matrix.yaml as JSON (synthetic example values)
# input        : {"proposal": {...}, "approvals": [...], "verifications": [...]}
# result       : data.invoiceflow.policy.decision -> {outcome, required_role, failed}
package invoiceflow.policy

import rego.v1

matrix := data.matrix

proposal := input.proposal

exc := matrix.exceptions[proposal.exception]

approvals := object.get(input, "approvals", [])

verifications := object.get(input, "verifications", [])

can_approve(identity) if {
	identity.kind == "human"
	identity.role in matrix.approver_hierarchy
}

rank(role) := i if {
	some i, r in matrix.approver_hierarchy
	r == role
}

# --- rules that deny ------------------------------------------------------------------

has_citation if {
	some c in proposal.citations
	trim_space(c) != ""
}

failed contains "CM-08" if not has_citation

failed contains "CM-09" if not proposal.action in exc.allowed_actions

failed contains "CM-01" if {
	proposal.action == "APPROVE"
	not proposal.price_variance.within_tolerance
}

failed contains "CM-03" if {
	proposal.exception == "VENDOR_BANK_CHANGE"
	proposal.action != "ESCALATE_FRAUD_REVIEW"
}

failed contains "CM-06" if {
	some a in approvals
	not can_approve(a.approver)
}

failed contains "CM-05" if {
	some a in approvals
	can_approve(a.approver)
	a.approver.id == proposal.preparer.id
}

# --- who must approve -----------------------------------------------------------------

exempt if proposal.action in matrix.actions_without_approval

eligible_limits contains i if {
	some i, limit in matrix.approval_limits
	limit.max_gross_value == null
}

eligible_limits contains i if {
	some i, limit in matrix.approval_limits
	limit.max_gross_value != null
	to_number(proposal.gross_value) <= to_number(limit.max_gross_value)
}

candidate_roles contains matrix.approval_limits[min(eligible_limits)].role

candidate_roles contains exc.required_role if exc.required_role != null

candidate_roles contains matrix.minimum_role_by_action[proposal.action]

required_rank := max({rank(r) | some r in candidate_roles})

required_role := matrix.approver_hierarchy[required_rank]

approver_ranks contains rank(a.approver.role) if {
	some a in approvals
	can_approve(a.approver)
	a.approver.id != proposal.preparer.id
}

approved if max(approver_ranks) >= required_rank

needs_verification if {
	not exempt
	exc.requires_out_of_band_verification == true
}

verified if {
	some v in verifications
	v.performed_by.kind == "human"
	v.performed_by.id != proposal.preparer.id
}

complete if {
	approved
	not needs_verification
}

complete if {
	approved
	verified
}

# --- outcome --------------------------------------------------------------------------

outcome := "DENY" if count(failed) > 0

outcome := "ALLOW" if {
	count(failed) == 0
	exempt
}

outcome := "ALLOW" if {
	count(failed) == 0
	not exempt
	complete
}

outcome := "REQUIRE_APPROVAL" if {
	count(failed) == 0
	not exempt
	not complete
}

decision := {
	"outcome": outcome,
	"required_role": role_or_null,
	"failed": sort([r | some r in failed]),
}

role_or_null := null if exempt

role_or_null := required_role if not exempt

# Batch form used by the parity test: one OPA call for many cases.
decisions := [d | some c in input.cases; d := decision with input as c]
