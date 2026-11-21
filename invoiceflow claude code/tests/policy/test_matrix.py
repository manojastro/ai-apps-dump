from decimal import Decimal as D
from pathlib import Path
from typing import Any

import pytest
import yaml
from pydantic import ValidationError

from invoiceflow.core.findings import Finding, FindingReason
from invoiceflow.data.models import Action, ExceptionCode, Role
from invoiceflow.policy.matrix import DEFAULT_MATRIX_PATH, ControlMatrix, load_matrix


def raw() -> dict[str, Any]:
    data = yaml.safe_load(DEFAULT_MATRIX_PATH.read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def test_matrix_loads_and_is_marked_synthetic() -> None:
    matrix = load_matrix()
    assert matrix.synthetic is True
    assert set(matrix.exceptions) == set(ExceptionCode)


def test_version_hash_is_stable_and_tracks_content(tmp_path: Path) -> None:
    first, second = load_matrix(), load_matrix()
    assert first.version_hash == second.version_hash
    assert len(first.version_hash) == 64

    changed = raw()
    changed["tolerance"]["price_variance_max_pct"] = "2.50"
    path = tmp_path / "matrix.yaml"
    path.write_text(yaml.safe_dump(changed), encoding="utf-8")
    assert load_matrix(path).version_hash != first.version_hash


@pytest.mark.parametrize(
    ("gross", "role"),
    [
        ("0.00", Role.AP_CLERK),
        ("100000.00", Role.AP_CLERK),
        ("100000.01", Role.AP_MANAGER),
        ("1000000.00", Role.AP_MANAGER),
        ("1000000.01", Role.FINANCE_CONTROLLER),
    ],
)
def test_role_for_value_boundaries(gross: str, role: Role) -> None:
    assert load_matrix().role_for_value(D(gross)) is role


def test_default_action_can_depend_on_the_finding_reason() -> None:
    matrix = load_matrix()

    def qty(reason: FindingReason) -> tuple[Finding, ...]:
        return (Finding(code=ExceptionCode.QTY_OVERBILLED, reason=reason, message="t"),)

    assert (
        matrix.default_action(ExceptionCode.QTY_OVERBILLED, qty(FindingReason.QTY_EXCEEDS_RECEIVED))
        is Action.HOLD_FOR_GRN
    )
    assert (
        matrix.default_action(ExceptionCode.QTY_OVERBILLED, qty(FindingReason.QTY_EXCEEDS_ORDERED))
        is Action.REQUEST_CREDIT_NOTE
    )


def test_match_params_come_from_the_matrix() -> None:
    params = load_matrix().match_params()
    assert params.tolerance.max_pct == D("2.00")
    assert params.tolerance.max_amount == D("5000.00")
    assert params.near_duplicate_window_days == 7


def broken(mutate: Any) -> dict[str, Any]:
    data = raw()
    mutate(data)
    return data


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda d: d["exceptions"].pop("PO_CLOSED"), "missing"),
        (lambda d: d["exceptions"]["CLEAN"].update(default_action="HOLD_FOR_GRN"), "allowed"),
        (lambda d: d.update(surprise="field"), "Extra inputs"),
        (lambda d: d["rules"].append(dict(d["rules"][0])), "unique"),
        (lambda d: d["rules"][0].update(id="RULE-1"), "pattern"),
        (lambda d: d["approval_limits"][0].update(max_gross_value="2000000.00"), "increase"),
        (lambda d: d["approval_limits"][2].update(max_gross_value="5000000.00"), "unlimited"),
        (lambda d: d.update(never_approve=["AP_CLERK"]), "both"),
        (lambda d: d.update(synthetic=False), "synthetic"),
    ],
)
def test_invalid_matrices_fail_loudly(mutate: Any, message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        ControlMatrix.model_validate(broken(mutate))
