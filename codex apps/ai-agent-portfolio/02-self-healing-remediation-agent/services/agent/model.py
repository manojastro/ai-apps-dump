from __future__ import annotations

from typing import Any, Protocol


class DiagnosticModel(Protocol):
    provider: str
    model: str

    def hypothesize(self, scenario: dict[str, Any], evidence: list[dict[str, Any]], runbook: dict[str, Any]) -> list[dict[str, Any]]: ...


class DeterministicDiagnosticModel:
    """CI model: structured output only and no command-generation capability."""

    provider = "deterministic"
    model = "rules-v1"

    def hypothesize(self, scenario: dict[str, Any], evidence: list[dict[str, Any]], runbook: dict[str, Any]) -> list[dict[str, Any]]:
        refs = [item["source_ref"] for item in evidence] + [f"runbook://{runbook['id']}@{runbook['version']}"]
        return [{
            "statement": scenario["diagnosis"],
            "confidence": 0.96,
            "evidence_refs": refs,
        }]


def create_model(provider: str) -> DiagnosticModel:
    # Provider boundary is explicit; external providers can be added without changing policy or tools.
    # The safe local build deliberately defaults to deterministic structured diagnostics.
    return DeterministicDiagnosticModel()

