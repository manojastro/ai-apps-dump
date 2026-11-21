"""Policy v2 client: evaluate the Rego policy with OPA.

Two transports: the `opa` binary (`opa eval`, used in tests and CI) and an OPA server's
REST API (`POST /v1/data/invoiceflow/policy/decision`, the production sidecar pattern).
Both take the same input as the Python evaluator and return {outcome, required_role,
failed}. The Python evaluator stays the reference; the parity test keeps them equal.
"""

import json
import shutil
import subprocess
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import httpx

from invoiceflow.policy.matrix import ControlMatrix
from invoiceflow.policy.models import Approval, Proposal, Verification

REGO_DIR = Path(__file__).resolve().parents[3] / "policy" / "rego"


def find_opa() -> str | None:
    local = Path(__file__).resolve().parents[3] / "tools" / "opa.exe"
    return shutil.which("opa") or (str(local) if local.exists() else None)


def matrix_data(matrix: ControlMatrix) -> dict[str, Any]:
    return {"matrix": matrix.model_dump(mode="json")}


def opa_input(
    proposal: Proposal,
    approvals: Sequence[Approval] = (),
    verifications: Sequence[Verification] = (),
) -> dict[str, Any]:
    return {
        "proposal": proposal.model_dump(mode="json"),
        "approvals": [a.model_dump(mode="json") for a in approvals],
        "verifications": [v.model_dump(mode="json") for v in verifications],
    }


class OpaCli:
    def __init__(self, matrix: ControlMatrix, opa: str | None = None) -> None:
        binary = opa or find_opa()
        if binary is None:
            raise FileNotFoundError("opa binary not found (install OPA or put it in tools/)")
        self._opa = binary
        self._data = matrix_data(matrix)

    def _eval(self, query: str, value: dict[str, Any]) -> Any:
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            data_path, input_path = Path(tmp) / "matrix.json", Path(tmp) / "input.json"
            data_path.write_text(json.dumps(self._data), encoding="utf-8")
            input_path.write_text(json.dumps(value), encoding="utf-8")
            result = subprocess.run(  # noqa: S603 - fixed binary and arguments
                [
                    self._opa,
                    "eval",
                    "--format",
                    "json",
                    "-d",
                    str(REGO_DIR),
                    "-d",
                    str(data_path),
                    "-i",
                    str(input_path),
                    query,
                ],
                capture_output=True,
                text=True,
                check=True,
                timeout=120,
            )
        return json.loads(result.stdout)["result"][0]["expressions"][0]["value"]

    def decide(self, case: dict[str, Any]) -> dict[str, Any]:
        return dict(self._eval("data.invoiceflow.policy.decision", case))

    def decide_many(self, cases: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
        return list(self._eval("data.invoiceflow.policy.decisions", {"cases": list(cases)}))


class OpaRest:
    """Against an OPA server that already has the policy and `data.matrix` loaded."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    def decide(self, case: dict[str, Any]) -> dict[str, Any]:
        response = self._client.post("/v1/data/invoiceflow/policy/decision", json={"input": case})
        response.raise_for_status()
        return dict(response.json()["result"])
