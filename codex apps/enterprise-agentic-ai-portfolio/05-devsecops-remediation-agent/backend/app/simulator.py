from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class VulnerabilityScenario:
    name: str
    title: str
    cwe: str
    description: str
    filename: str
    vulnerable_source: str
    fixed_source: str
    vulnerable_line: int
    ground_truth_finding: bool
    ground_truth_exploitability: str
    context: dict[str, bool | str]


SCENARIOS: dict[str, VulnerabilityScenario] = {
    "sql_injection": VulnerabilityScenario(
        name="sql_injection", title="SQL injection in user lookup", cwe="CWE-89",
        description="An API-controlled user ID is interpolated into a SQL statement.",
        filename="user_lookup.py", vulnerable_line=5, ground_truth_finding=True,
        ground_truth_exploitability="LIKELY_EXPLOITABLE",
        context={"reachable": True, "attacker_controlled_input": True, "authentication_required": False},
        vulnerable_source='''"""Inert vulnerable fixture. Never imported by the service."""\n\ndef find_user(cursor, user_id):\n    query = f"SELECT id, email FROM users WHERE id = '{user_id}'"\n    return cursor.execute(query).fetchone()\n''',
        fixed_source='''"""Remediated fixture using parameterized SQL."""\n\ndef find_user(cursor, user_id):\n    query = "SELECT id, email FROM users WHERE id = ?"\n    return cursor.execute(query, (user_id,)).fetchone()\n''',
    ),
    "command_injection": VulnerabilityScenario(
        name="command_injection", title="Shell injection in image conversion", cwe="CWE-78",
        description="User-controlled file paths are concatenated into a shell command.",
        filename="image_tool.py", vulnerable_line=6, ground_truth_finding=True,
        ground_truth_exploitability="CONDITIONALLY_EXPLOITABLE",
        context={"reachable": True, "attacker_controlled_input": True, "authentication_required": True},
        vulnerable_source='''"""Inert vulnerable fixture. Never imported by the service."""\n\nimport subprocess\n\ndef convert_image(input_path, output_path):\n    return subprocess.run(f"convert {input_path} {output_path}", shell=True, check=True)\n''',
        fixed_source='''"""Remediated fixture without a command shell."""\n\nimport subprocess\n\ndef convert_image(input_path, output_path):\n    return subprocess.run(["convert", input_path, output_path], shell=False, check=True)\n''',
    ),
    "hardcoded_secret": VulnerabilityScenario(
        name="hardcoded_secret", title="Hard-coded service credential", cwe="CWE-798",
        description="A production-like bearer token is embedded directly in source.",
        filename="token_store.py", vulnerable_line=3, ground_truth_finding=True,
        ground_truth_exploitability="LIKELY_EXPLOITABLE",
        context={"reachable": True, "attacker_controlled_input": False, "repository_access_required": True},
        vulnerable_source='''"""Inert vulnerable fixture. The token is a nonfunctional example."""\nSERVICE_TOKEN = "demo_prod_token_123456789"\n\ndef auth_header():\n    return {"Authorization": f"Bearer {SERVICE_TOKEN}"}\n''',
        fixed_source='''"""Remediated fixture loading the token from process environment."""\n\nimport os\n\nSERVICE_TOKEN = os.environ["SERVICE_TOKEN"]\n\ndef auth_header():\n    return {"Authorization": f"Bearer {SERVICE_TOKEN}"}\n''',
    ),
}


class SourceAdapter(Protocol):
    def scenario(self, name: str) -> VulnerabilityScenario: ...


class SafeDemoSourceAdapter:
    def scenario(self, name: str) -> VulnerabilityScenario:
        if name not in SCENARIOS:
            raise KeyError(name)
        return SCENARIOS[name]
