"""M4 contract tests: ports, mock-first factory, ITSM interchangeability."""

from __future__ import annotations

import pytest

from integrations import ports
from integrations.factory import build_providers
from integrations.servicenow.real_itsm import RealServiceNowITSM
from integrations.servicenow.simulated_itsm import SimulatedITSM


def test_protocols_satisfied_by_both_itsm_impls() -> None:
    from integrations.servicenow.client import ServiceNowClient, ServiceNowConfig

    calls: list[str] = []

    def fake_transport(method: str, url: str, headers: dict, body, timeout: int):
        calls.append(method)
        if method == "POST" and url.endswith("/table/incident"):
            return 201, {"result": {"sys_id": "s1", "number": "INC001",
                                    "state": "New", "short_description": "t"}}
        raise AssertionError(url)

    cfg = ServiceNowConfig(instance_url="https://x/", username="u", password="p")
    real = RealServiceNowITSM(ServiceNowClient(cfg, transport=fake_transport))
    sim = SimulatedITSM(seed=7)
    assert isinstance(real, ports.ITSMProvider)
    assert isinstance(sim, ports.ITSMProvider)
    assert real.source == "servicenow-table-api"
    assert sim.source == "simulated-servicenow"
    assert real.create_incident("t").number == "INC001"
    assert sim.create_incident("t").number.startswith("INC")


def test_factory_auto_selects_simulated_without_creds(monkeypatch) -> None:
    from common.config import load_settings

    for k in ("SERVICENOW_INSTANCE_URL", "SERVICENOW_INSTANCE",
              "SERVICENOW_USER", "SERVICENOW_USERNAME",
              "SERVICENOW_PWD", "SERVICENOW_PASSWORD"):
        monkeypatch.delenv(k, raising=False)
    providers = build_providers(load_settings(env_file="nonexistent-m4"))
    assert providers.itsm is not None
    assert providers.itsm.source == "simulated-servicenow"  # type: ignore[union-attr]
    # M5 wired enterprise mocks (was None in M4)
    assert providers.endpoint is not None
    assert providers.endpoint.source == "nexthink"  # type: ignore[union-attr]
    assert providers.software is not None
    assert providers.software.source == "intune"  # type: ignore[union-attr]
    # M6 wired network/identity (were None in M4/M5)
    assert providers.network is not None
    assert providers.network.source == "zscaler"  # type: ignore[union-attr]
    assert providers.identity is not None
    assert providers.identity.source == "entra"  # type: ignore[union-attr]


def test_factory_explicit_mock_and_real_paths(monkeypatch) -> None:
    from common.config import load_settings

    for k in ("SERVICENOW_INSTANCE_URL", "SERVICENOW_INSTANCE",
              "SERVICENOW_USER", "SERVICENOW_USERNAME",
              "SERVICENOW_PWD", "SERVICENOW_PASSWORD"):
        monkeypatch.delenv(k, raising=False)
    s = load_settings(env_file="nonexistent-m4")
    assert build_providers(s, use_mock=True).itsm.source == "simulated-servicenow"  # type: ignore[union-attr]
    with pytest.raises(ValueError):
        build_providers(s, use_mock=False)

    monkeypatch.setenv("SERVICENOW_INSTANCE_URL", "https://pdi.service-now.com/")
    monkeypatch.setenv("SERVICENOW_USER", "admin")
    monkeypatch.setenv("SERVICENOW_PWD", "pw")
    live = load_settings(env_file="nonexistent-m4")
    assert live.has_servicenow
    real_providers = build_providers(live, use_mock=False)
    assert real_providers.itsm.source == "servicenow-table-api"  # type: ignore[union-attr]


def test_simulated_lifecycle_and_determinism() -> None:
    a = SimulatedITSM(seed=42)
    b = SimulatedITSM(seed=42)
    assert a.create_incident("slow").number == b.create_incident("slow").number
    sim = SimulatedITSM(seed=1)
    inc = sim.create_incident("Teams freezing")
    assert sim.get_incident(inc.sys_id).number == inc.number
    assert sim.search_incidents(f"number={inc.number}")[0].sys_id == inc.sys_id
    sim.add_work_note(inc.sys_id, "note")
    assert sim.resolve_incident(inc.sys_id, "fixed").state == "6"
    with pytest.raises(ValueError):
        sim.resolve_incident(inc.sys_id, "  ")
    assert sim.escalate_incident(inc.sys_id, "vip").state == "6"  # stays resolved-state
    prb = sim.create_problem("regression")
    assert prb.number.startswith("PRB")
    linked = sim.link_incident_to_problem(inc.sys_id, prb.sys_id)
    assert linked.sys_id == inc.sys_id
    with pytest.raises(LookupError):
        sim.get_incident("NOPE")
    with pytest.raises(ValueError):
        sim.update_incident(inc.sys_id, {"sys_created_by": "x"})


def test_no_credentials_in_dtos() -> None:
    sim = SimulatedITSM(seed=3)
    inc = sim.create_incident("t", caller_id="USER_001")
    assert "pw" not in str(inc) and "password" not in str(inc).lower()


def test_system_packages_importable_and_interface_only() -> None:
    import importlib
    from pathlib import Path

    for pkg in ("nexthink", "tanium", "intune", "entra", "zscaler", "cloudflare"):
        assert importlib.import_module(f"integrations.{pkg}") is not None
    text = (Path(__file__).resolve().parents[1] / "integrations" / "ports.py").read_text()
    assert "simulator" not in text
    assert "password" not in text.lower()
