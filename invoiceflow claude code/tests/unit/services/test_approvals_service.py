"""Approval service: identity from the token only, server-side role checks, and OIDC."""

import time
from pathlib import Path
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from invoiceflow.adapters.llm.stub import StubChatModel
from invoiceflow.agent.runner import AgentRunner, sqlite_checkpointer
from invoiceflow.agent.wiring import build_deps
from invoiceflow.config import Settings
from invoiceflow.data.dataset import Dataset
from invoiceflow.data.models import Role, Split
from invoiceflow.policy.models import Identity
from invoiceflow.services.approvals.app import create_app
from invoiceflow.services.approvals.auth import AuthError, DevTokenAuth, OidcAuth

TOKENS = {
    "tok-clerk": Identity(id="u-clerk-1", kind="human", role=Role.AP_CLERK),
    "tok-manager": Identity(id="u-manager-1", kind="human", role=Role.AP_MANAGER),
    "tok-fc": Identity(id="u-fc-1", kind="human", role=Role.FINANCE_CONTROLLER),
    "tok-audit": Identity(id="u-audit-1", kind="human", role=Role.AUDITOR),
    "tok-admin": Identity(id="u-admin-1", kind="human", role=Role.PLATFORM_ADMIN),
}


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def service(tmp_path: Path, dataset: Dataset) -> tuple[TestClient, AgentRunner, Dataset]:
    deps = build_deps(Settings(_env_file=None), tmp_path, dataset, StubChatModel())
    deps.kill_switch = lambda: False
    runner = AgentRunner(deps, sqlite_checkpointer(tmp_path / "cp.db"))
    return TestClient(create_app(runner, DevTokenAuth(TOKENS))), runner, dataset


def start(runner: AgentRunner, dataset: Dataset, scenario: str, role: str | None = None) -> str:
    for label in dataset.labels(Split.DEV):
        approver = label.expected_required_approver
        if label.scenario == scenario and (role is None or (approver and approver.value == role)):
            runner.start(label.invoice_id)
            return label.invoice_id
    raise LookupError(scenario)


def test_requests_without_a_valid_token_are_rejected(service: Any) -> None:
    client, _, _ = service
    assert client.get("/api/cases").status_code == 401
    assert client.get("/api/cases", headers=auth("nope")).status_code == 401


def test_inbox_lists_cases_awaiting_approval(service: Any) -> None:
    client, runner, dataset = service
    case_id = start(runner, dataset, "price_over_pct")
    cases = client.get("/api/cases", headers=auth("tok-manager")).json()
    assert [c["case_id"] for c in cases] == [case_id]
    assert client.get("/", headers={}).status_code == 200


def test_auditor_can_read_but_not_decide(service: Any) -> None:
    client, runner, dataset = service
    case_id = start(runner, dataset, "price_over_pct")
    assert client.get(f"/api/cases/{case_id}", headers=auth("tok-audit")).status_code == 200
    response = client.post(
        f"/api/cases/{case_id}/decision", json={"decision": "approve"}, headers=auth("tok-audit")
    )
    assert response.status_code == 403


def test_admin_cannot_even_read_cases(service: Any) -> None:
    client, _, _ = service
    assert client.get("/api/cases", headers=auth("tok-admin")).status_code == 403


def test_role_in_the_body_is_ignored(service: Any) -> None:
    client, runner, dataset = service
    case_id = start(runner, dataset, "clean_exact", role="AP_MANAGER")
    response = client.post(
        f"/api/cases/{case_id}/decision",
        json={"decision": "approve", "role": "FINANCE_CONTROLLER"},
        headers=auth("tok-clerk"),
    )
    assert response.status_code == 422  # unknown field rejected outright


def test_insufficient_authority_is_refused_server_side(service: Any) -> None:
    client, runner, dataset = service
    case_id = start(runner, dataset, "clean_exact", role="AP_MANAGER")
    response = client.post(
        f"/api/cases/{case_id}/decision", json={"decision": "approve"}, headers=auth("tok-clerk")
    )
    assert response.status_code == 403
    ok = client.post(
        f"/api/cases/{case_id}/decision", json={"decision": "approve"}, headers=auth("tok-manager")
    )
    assert ok.json()["status"] == "EXECUTED"
    again = client.post(
        f"/api/cases/{case_id}/decision", json={"decision": "approve"}, headers=auth("tok-manager")
    )
    assert again.status_code == 409


def test_bank_change_needs_the_callback_flag(service: Any) -> None:
    client, runner, dataset = service
    case_id = start(runner, dataset, "bank_change_structured")
    first = client.post(
        f"/api/cases/{case_id}/decision", json={"decision": "approve"}, headers=auth("tok-fc")
    ).json()
    assert first["status"] == "AWAITING_APPROVAL"
    done = client.post(
        f"/api/cases/{case_id}/decision",
        json={"decision": "approve", "verification_performed": True},
        headers=auth("tok-fc"),
    ).json()
    assert done["status"] == "EXECUTED"


# --- OIDC (v2) with a locally generated key; nothing is created in Entra ID -------------


class StaticJwks:
    def __init__(self, key: Any) -> None:
        self._key = key

    def get_signing_key_from_jwt(self, token: str) -> Any:
        return type("K", (), {"key": self._key})()


def make_token(private: Any, **claims: Any) -> str:
    base = {
        "iss": "https://login.example/tenant/v2.0",
        "aud": "api://invoiceflow",
        "exp": int(time.time()) + 300,
        "oid": "user-123",
        "roles": ["AP.Manager"],
    }
    return jwt.encode({**base, **claims}, private, algorithm="RS256")


def test_oidc_maps_app_roles_and_validates_the_token() -> None:
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    oidc = OidcAuth(
        "https://login.example/tenant/v2.0", "api://invoiceflow", StaticJwks(private.public_key())
    )
    identity = oidc.identify(f"Bearer {make_token(private)}")
    assert (identity.id, identity.role, identity.kind) == ("user-123", Role.AP_MANAGER, "human")
    with pytest.raises(AuthError, match="invalid"):
        oidc.identify(f"Bearer {make_token(private, aud='api://someone-else')}")
    with pytest.raises(AuthError, match="invalid"):
        oidc.identify(f"Bearer {make_token(private, exp=int(time.time()) - 10)}")
    with pytest.raises(AuthError, match="app role"):
        oidc.identify(f"Bearer {make_token(private, roles=['Other.Role'])}")
    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    with pytest.raises(AuthError, match="invalid"):
        oidc.identify(f"Bearer {make_token(other)}")  # signed by the wrong key


def test_dev_tokens_are_created_once_and_random(tmp_path: Path) -> None:
    path = tmp_path / "tokens.json"
    first = DevTokenAuth.load_or_create(path)
    second = DevTokenAuth.load_or_create(path)
    assert first._tokens.keys() == second._tokens.keys()
    assert all(len(token) >= 24 for token in first._tokens)
