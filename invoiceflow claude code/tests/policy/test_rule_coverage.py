"""Meta-test: every rule in the control matrix has at least one allow and one deny test.

Reads the `@pytest.mark.rule(...)` decorators in test_rules.py with `ast`, so adding a
rule to the YAML without tests fails CI.
"""

import ast
from pathlib import Path

from invoiceflow.policy.matrix import load_matrix

RULE_TESTS = Path(__file__).with_name("test_rules.py")


def covered() -> set[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    for node in ast.walk(ast.parse(RULE_TESTS.read_text(encoding="utf-8"))):
        if not isinstance(node, ast.FunctionDef):
            continue
        for decorator in node.decorator_list:
            if (
                isinstance(decorator, ast.Call)
                and isinstance(decorator.func, ast.Attribute)
                and decorator.func.attr == "rule"
                and len(decorator.args) == 2
                and all(isinstance(a, ast.Constant) for a in decorator.args)
            ):
                rule_id, kind = (a.value for a in decorator.args)  # type: ignore[attr-defined]
                pairs.add((str(rule_id), str(kind)))
    return pairs


def test_every_rule_has_allow_and_deny_tests() -> None:
    pairs = covered()
    missing = [
        f"{rule.id} {kind}"
        for rule in load_matrix().rules
        for kind in ("allow", "deny")
        if (rule.id, kind) not in pairs
    ]
    assert missing == [], f"rules without tests: {missing}"


def test_tests_only_reference_rules_that_exist() -> None:
    known = {rule.id for rule in load_matrix().rules}
    unknown = sorted({rule_id for rule_id, _ in covered()} - known)
    assert unknown == []
