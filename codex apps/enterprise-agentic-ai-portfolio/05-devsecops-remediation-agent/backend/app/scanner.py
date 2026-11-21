from __future__ import annotations

import ast
import hashlib
import re
from typing import Protocol
from uuid import uuid4

from .models import Evidence, ExploitabilityAssessment, RemediationPlan, ReleaseRisk, SecurityFinding, Severity
from .simulator import SCENARIOS, VulnerabilityScenario


def source_hash(source: str) -> str:
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


class SecurityScanner(Protocol):
    def scan(self, scenario: VulnerabilityScenario, source: str) -> list[SecurityFinding]: ...


class DeterministicSecurityScanner:
    """Small transparent ruleset for the authored safe fixtures."""

    def scan(self, scenario: VulnerabilityScenario, source: str) -> list[SecurityFinding]:
        matched = False
        rule_id = ""
        if scenario.name == "sql_injection":
            matched = bool(re.search(r'query\s*=\s*f["\']SELECT', source)) and "execute(query," not in source
            rule_id = "PY-SQL-INTERPOLATION"
        elif scenario.name == "command_injection":
            matched = "shell=True" in source and "subprocess.run(f" in source
            rule_id = "PY-SHELL-USER-INPUT"
        elif scenario.name == "hardcoded_secret":
            matched = bool(re.search(r'SERVICE_TOKEN\s*=\s*["\']demo_prod_token_', source))
            rule_id = "PY-HARDCODED-SECRET"
        if not matched:
            return []
        evidence = Evidence(
            evidence_id=f"ev-{uuid4().hex[:10]}", source="deterministic-static-scanner",
            claim=f"{scenario.cwe} rule matched the authored vulnerable pattern",
            value={"rule_id": rule_id, "source_sha256": source_hash(source)}, line=scenario.vulnerable_line,
        )
        return [SecurityFinding(
            finding_id=f"finding-{uuid4().hex[:10]}", rule_id=rule_id, cwe=scenario.cwe,
            title=scenario.title, severity=Severity.high, file=scenario.filename,
            line=scenario.vulnerable_line, evidence=[evidence],
        )]


class ExploitabilityAgent:
    def assess(self, scenario: VulnerabilityScenario, finding: SecurityFinding) -> ExploitabilityAssessment:
        reachable = bool(scenario.context.get("reachable"))
        attacker_input = bool(scenario.context.get("attacker_controlled_input"))
        authentication_required = bool(scenario.context.get("authentication_required"))
        repository_access = bool(scenario.context.get("repository_access_required"))
        if reachable and attacker_input and not authentication_required:
            classification, score = "LIKELY_EXPLOITABLE", 0.92
        elif reachable and attacker_input:
            classification, score = "CONDITIONALLY_EXPLOITABLE", 0.72
        elif reachable and repository_access:
            classification, score = "LIKELY_EXPLOITABLE", 0.84
        else:
            classification, score = "UNLIKELY_EXPLOITABLE", 0.25
        preconditions = [key.replace("_", " ") for key, value in scenario.context.items() if value is True]
        return ExploitabilityAssessment(
            classification=classification, score=score,
            reachable=reachable, attacker_controlled_input=attacker_input,
            preconditions=preconditions,
            rationale="Classification combines a valid static finding with the fixture's explicit reachability context.",
            evidence_ids=[item.evidence_id for item in finding.evidence],
        )


class RemediationAgent:
    def propose(self, scenario: VulnerabilityScenario) -> RemediationPlan:
        summaries = {
            "sql_injection": "Replace SQL interpolation with a parameterized query",
            "command_injection": "Replace shell command construction with an argument vector",
            "hardcoded_secret": "Load the credential from an environment-backed secret boundary",
        }
        patch_preview = self._diff(scenario.vulnerable_source, scenario.fixed_source)
        return RemediationPlan(
            action_id=f"action-{uuid4().hex[:10]}", summary=summaries[scenario.name],
            patch_preview=patch_preview, patch_sha256=source_hash(patch_preview),
            fixed_source_sha256=source_hash(scenario.fixed_source),
            risk=Severity.medium, blast_radius=f"one function in {scenario.filename}",
            reversibility="Original source hash and content remain stored with the incident",
            expected_benefit=f"Remove the detected {scenario.cwe} pattern without changing the public function contract",
            confidence=0.98, required_approval=True, rollback_plan="Restore the incident's immutable before-source",
        )

    @staticmethod
    def _diff(before: str, after: str) -> str:
        before_lines, after_lines = before.splitlines(), after.splitlines()
        removed = [line for line in before_lines if line not in after_lines]
        added = [line for line in after_lines if line not in before_lines]
        return "\n".join([*(f"- {line}" for line in removed), *(f"+ {line}" for line in added)])


class SafePatchExecutor:
    """Applies only the exact pre-authored transformation for the matching input hash."""

    def apply(
        self,
        scenario: VulnerabilityScenario,
        current_source: str,
        *,
        approved_action_id: str,
        expected_action_id: str,
        approved_patch_sha256: str,
        expected_patch_sha256: str,
        approved_fixed_source_sha256: str,
        expected_fixed_source_sha256: str,
    ) -> str:
        if source_hash(current_source) != source_hash(scenario.vulnerable_source):
            raise ValueError("source changed after investigation; refusing to apply")
        current_patch = RemediationAgent._diff(scenario.vulnerable_source, scenario.fixed_source)
        bindings = {
            "action_id": approved_action_id == expected_action_id,
            "patch_sha256": (
                approved_patch_sha256 == expected_patch_sha256 == source_hash(current_patch)
            ),
            "fixed_source_sha256": (
                approved_fixed_source_sha256
                == expected_fixed_source_sha256
                == source_hash(scenario.fixed_source)
            ),
        }
        if not all(bindings.values()):
            raise ValueError("approved remediation artifact changed; refusing to apply")
        return scenario.fixed_source


class ValidationAgent:
    def __init__(self, scanner: SecurityScanner):
        self.scanner = scanner

    def validate(self, scenario: VulnerabilityScenario, before: str, after: str) -> dict[str, bool]:
        try:
            before_tree = ast.parse(before)
            tree = ast.parse(after)
            expected_tree = ast.parse(SCENARIOS[scenario.name].fixed_source)
            syntax_valid = True
        except SyntaxError:
            before_tree = ast.Module(body=[], type_ignores=[])
            tree = ast.Module(body=[], type_ignores=[])
            expected_tree = ast.Module(body=[], type_ignores=[])
            syntax_valid = False
        original_removed = len(self.scanner.scan(scenario, after)) == 0
        function_name = {"sql_injection": "find_user", "command_injection": "convert_image",
                         "hardcoded_secret": "auth_header"}[scenario.name]
        before_functions = [node for node in before_tree.body if isinstance(node, ast.FunctionDef) and node.name == function_name]
        functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == function_name]
        expected_functions = [
            node for node in expected_tree.body
            if isinstance(node, ast.FunctionDef) and node.name == function_name
        ]
        public_contract_preserved = (
            len(before_functions) == 1
            and len(functions) == 1
            and len(expected_functions) == 1
            and ast.dump(before_functions[0].args, include_attributes=False)
            == ast.dump(functions[0].args, include_attributes=False)
            == ast.dump(expected_functions[0].args, include_attributes=False)
        )
        exact_scenario_structure = (
            syntax_valid
            and ast.dump(tree, include_attributes=False)
            == ast.dump(expected_tree, include_attributes=False)
        )
        allow_list_policy = self._allow_list_policy(tree, expected_tree)
        no_top_level_side_effects = self._no_top_level_side_effects(tree, expected_tree)
        safe_construct = self._safe_construct(functions, expected_functions)
        no_new_high_risk_pattern = exact_scenario_structure
        return {
            "syntax_valid": syntax_valid,
            "original_finding_removed": original_removed,
            "public_contract_preserved": public_contract_preserved,
            "exact_scenario_structure": exact_scenario_structure,
            "allow_list_policy": allow_list_policy,
            "no_top_level_side_effects": no_top_level_side_effects,
            "safe_construct_present": safe_construct,
            "no_obvious_new_high_risk_pattern": no_new_high_risk_pattern,
            "source_changed": source_hash(before) != source_hash(after),
        }

    @staticmethod
    def _allow_list_policy(tree: ast.Module, expected_tree: ast.Module) -> bool:
        """Require the exact approved import and call structures, including arguments."""
        actual = [
            node for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom, ast.Call))
        ]
        expected = [
            node for node in ast.walk(expected_tree)
            if isinstance(node, (ast.Import, ast.ImportFrom, ast.Call))
        ]
        return [ast.dump(node, include_attributes=False) for node in actual] == [
            ast.dump(node, include_attributes=False) for node in expected
        ]

    @staticmethod
    def _no_top_level_side_effects(tree: ast.Module, expected_tree: ast.Module) -> bool:
        actual = [node for node in tree.body if not isinstance(node, ast.FunctionDef)]
        expected = [node for node in expected_tree.body if not isinstance(node, ast.FunctionDef)]
        return [ast.dump(node, include_attributes=False) for node in actual] == [
            ast.dump(node, include_attributes=False) for node in expected
        ]

    @staticmethod
    def _safe_construct(
        functions: list[ast.FunctionDef], expected_functions: list[ast.FunctionDef]
    ) -> bool:
        if len(functions) != 1 or len(expected_functions) != 1:
            return False
        return [ast.dump(node, include_attributes=False) for node in functions[0].body] == [
            ast.dump(node, include_attributes=False) for node in expected_functions[0].body
        ]


def release_risk_before(finding: SecurityFinding, assessment: ExploitabilityAssessment) -> ReleaseRisk:
    score = min(100, round(55 + assessment.score * 40))
    return ReleaseRisk(score=score, decision="BLOCK", reasons=[
        f"Unresolved {finding.severity.value} {finding.cwe} finding",
        f"Exploitability classified {assessment.classification}",
    ])


def release_risk_after(checks: dict[str, bool]) -> ReleaseRisk:
    if all(checks.values()):
        return ReleaseRisk(score=10, decision="ALLOW_WITH_REVIEW", reasons=[
            "Original finding removed", "Static regression contract passed", "Human review remains required",
        ])
    return ReleaseRisk(score=90, decision="BLOCK", reasons=["One or more remediation validations failed"])
