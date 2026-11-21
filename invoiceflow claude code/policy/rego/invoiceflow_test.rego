# Run through `uv run pytest tests/policy/test_opa_parity.py`, which writes the control
# matrix as JSON (data.matrix) and calls `opa test`. One allow and one deny case per rule
# family; the parity test covers the full combination space.
package invoiceflow.policy_test

import rego.v1

import data.invoiceflow.policy

agent := {"id": "agent-invoiceflow", "kind": "agent"}

clerk := {"id": "u-clerk-1", "kind": "human", "role": "AP_CLERK"}

manager := {"id": "u-manager-1", "kind": "human", "role": "AP_MANAGER"}

fc := {"id": "u-fc-1", "kind": "human", "role": "FINANCE_CONTROLLER"}

base := {
	"exception": "CLEAN", "action": "APPROVE", "gross_value": "50000.00",
	"price_variance": {"within_tolerance": true}, "citations": ["AP-POL:§4.1"],
	"preparer": agent,
}

test_clean_approve_with_clerk_is_allowed if {
	d := policy.decision with input as {"proposal": base, "approvals": [{"approver": clerk}]}
	d.outcome == "ALLOW"
	d.required_role == "AP_CLERK"
}

test_cm01_approve_beyond_tolerance_is_denied if {
	p := object.union(base, {"price_variance": {"within_tolerance": false}})
	d := policy.decision with input as {"proposal": p, "approvals": [{"approver": clerk}]}
	d.outcome == "DENY"
	"CM-01" in d.failed
}

test_cm02_limit_boundary if {
	p := object.union(base, {"gross_value": "100000.01"})
	d := policy.decision with input as {"proposal": p, "approvals": [{"approver": clerk}]}
	d.outcome == "REQUIRE_APPROVAL"
	d.required_role == "AP_MANAGER"
}

test_cm03_bank_change_needs_controller_and_callback if {
	p := object.union(base, {"exception": "VENDOR_BANK_CHANGE", "action": "ESCALATE_FRAUD_REVIEW"})
	waiting := policy.decision with input as {"proposal": p, "approvals": [{"approver": fc}]}
	waiting.outcome == "REQUIRE_APPROVAL"
	cb := {"kind": "BANK_DETAILS_CALLBACK", "performed_by": manager}
	done := policy.decision with input as {"proposal": p, "approvals": [{"approver": fc}], "verifications": [cb]}
	done.outcome == "ALLOW"
}

test_cm03_bank_change_cannot_be_approved if {
	p := object.union(base, {"exception": "VENDOR_BANK_CHANGE"})
	d := policy.decision with input as {"proposal": p, "approvals": [{"approver": fc}]}
	d.outcome == "DENY"
	"CM-03" in d.failed
}

test_cm05_self_approval_is_denied if {
	p := object.union(base, {"preparer": clerk})
	d := policy.decision with input as {"proposal": p, "approvals": [{"approver": clerk}]}
	"CM-05" in d.failed
}

test_cm06_agent_cannot_approve if {
	p := object.union(base, {"preparer": clerk})
	d := policy.decision with input as {"proposal": p, "approvals": [{"approver": agent}]}
	"CM-06" in d.failed
}

test_cm08_no_citation_is_denied if {
	p := object.union(base, {"citations": [" "]})
	d := policy.decision with input as {"proposal": p, "approvals": [{"approver": clerk}]}
	"CM-08" in d.failed
}

test_cm09_and_cm10_hold_needs_no_approval if {
	p := object.union(base, {"exception": "MISSING_GRN", "action": "HOLD_FOR_GRN"})
	d := policy.decision with input as {"proposal": p}
	d.outcome == "ALLOW"
	d.required_role == null
}

test_cm09_approve_for_missing_grn_is_denied if {
	p := object.union(base, {"exception": "MISSING_GRN"})
	d := policy.decision with input as {"proposal": p, "approvals": [{"approver": fc}]}
	"CM-09" in d.failed
}
