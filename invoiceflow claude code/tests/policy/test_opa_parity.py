"""Python evaluator and the Rego policy must agree on every generated case.

Needs the `opa` binary (on PATH in CI via setup-opa, or tools/opa.exe locally); skipped
otherwise, and the skip is visible in the test report.
"""

import itertools
import json
import subprocess
from decimal import Decimal as D
from pathlib import Path

import pytest

from invoiceflow.core.tolerance import PriceVariance
from invoiceflow.data.models import Action, ExceptionCode, Role
from invoiceflow.policy.evaluator import evaluate
from invoiceflow.policy.matrix import load_matrix
from invoiceflow.policy.models import Approval, Identity, Proposal, Verification
from invoiceflow.policy.opa import REGO_DIR, OpaCli, find_opa, matrix_data, opa_input

OPA = find_opa()
pytestmark = pytest.mark.skipif(OPA is None, reason="opa binary not installed")
MATRIX = load_matrix()

AGENT = Identity(id="agent-invoiceflow", kind="agent")
PEOPLE = {
    "none": (),
    "clerk": (Identity(id="u-clerk-1", kind="human", role=Role.AP_CLERK),),
    "manager": (Identity(id="u-manager-1", kind="human", role=Role.AP_MANAGER),),
    "fc": (Identity(id="u-fc-1", kind="human", role=Role.FINANCE_CONTROLLER),),
    "agent": (AGENT,),
    "auditor": (Identity(id="u-audit-1", kind="human", role=Role.AUDITOR),),
    "self": (Identity(id="u-prep", kind="human", role=Role.AP_MANAGER),),
}
GROSS = ("100000.00", "100000.01", "1000000.00", "1000000.01")


def cases() -> list[tuple[Proposal, tuple[Approval, ...], tuple[Verification, ...]]]:
    out: list[tuple[Proposal, tuple[Approval, ...], tuple[Verification, ...]]] = []
    for exception, action, gross, who, within, callback, cited in itertools.product(
        ExceptionCode, Action, GROSS, PEOPLE, (True, False), (False, True), (True, False)
    ):
        if not cited and (who != "clerk" or gross != GROSS[0]):
            continue  # keep the case count manageable; citations are orthogonal
        preparer = PEOPLE["self"][0] if who == "self" else AGENT
        proposal = Proposal(
            invoice_id="INV-1",
            exception=exception,
            action=action,
            gross_value=D(gross),
            price_variance=PriceVariance(
                overcharge_amount=D("0"),
                base_amount=D("1"),
                overcharge_pct=D("0"),
                within_tolerance=within,
            ),
            citations=("AP-POL:§4.1",) if cited else (),
            preparer=preparer,
        )
        approvals = tuple(Approval(approver=p) for p in PEOPLE[who])
        verifications = (
            (Verification(kind="BANK_DETAILS_CALLBACK", performed_by=PEOPLE["clerk"][0]),)
            if callback
            else ()
        )
        out.append((proposal, approvals, verifications))
    return out


def test_python_and_opa_agree_on_every_case() -> None:
    generated = cases()
    opa = OpaCli(MATRIX, OPA).decide_many([opa_input(*c) for c in generated])
    mismatches = []
    for (proposal, approvals, verifications), rego in zip(generated, opa, strict=True):
        py = evaluate(proposal, MATRIX, approvals, verifications)
        expected_role = py.required_role.value if py.required_role else None
        if (py.outcome.value, expected_role) != (rego["outcome"], rego["required_role"]):
            mismatches.append(
                (
                    proposal.exception,
                    proposal.action,
                    str(proposal.gross_value),
                    py.outcome.value,
                    rego["outcome"],
                    expected_role,
                    rego["required_role"],
                )
            )
    assert len(generated) > 1000
    assert mismatches == []


def test_rego_unit_tests_pass(tmp_path: Path) -> None:
    data = tmp_path / "matrix.json"
    data.write_text(json.dumps(matrix_data(MATRIX)), encoding="utf-8")
    result = subprocess.run(  # noqa: S603 - fixed arguments
        [str(OPA), "test", str(REGO_DIR), str(data), "-v"],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "FAIL" not in result.stdout
