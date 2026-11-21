"""M5 tests: estate determinism + Nexthink/Tanium/Intune mocks + factory."""

from __future__ import annotations

import re

import pytest

from integrations import ports
from simulator.estate import (BUGGY_TEAMS_VERSION, apply_demo_scenario,
                              generate_estate)


def test_estate_size_and_aliases() -> None:
    estate = generate_estate(seed=42)
    assert len(estate.devices) == 500
    assert len(estate.users) == 500
    assert set(estate.devices) == {f"DEVICE_{i:03d}" for i in range(1, 501)}
    assert set(estate.users) == {f"USER_{i:03d}" for i in range(1, 501)}
    for device_id in estate.devices:
        assert re.fullmatch(r"DEVICE_\d{3}", device_id)
        assert "." not in device_id  # no real hostnames


def test_estate_deterministic_and_seed_sensitive() -> None:
    a = generate_estate(seed=42)
    b = generate_estate(seed=42)
    assert a.devices["DEVICE_100"].cpu_pct == b.devices["DEVICE_100"].cpu_pct
    assert a.devices["DEVICE_250"].ram_pct == b.devices["DEVICE_250"].ram_pct
    other = generate_estate(seed=7)
    assert other.devices["DEVICE_100"].cpu_pct != a.devices["DEVICE_100"].cpu_pct


def test_demo_device_exact_values() -> None:
    estate = generate_estate(seed=42)
    device = estate.get("DEVICE_001")
    assert (device.cpu_pct, device.ram_pct, device.disk_pct) == (94.0, 91.0, 42.0)
    teams = next(p for p in device.processes if p.name == "Teams")
    assert teams.mem_mb == 4812.8
    teams_sw = next(s for s in device.software if s.app_id == "APP_TEAMS")
    assert teams_sw.version == BUGGY_TEAMS_VERSION
    assert not teams_sw.healthy
    assert any("3.8.4" in c.summary for c in device.recent_changes)
    assert "teams_memory" in device.issues
    with pytest.raises(ValueError):
        apply_demo_scenario(estate, "nope")
    with pytest.raises(LookupError):
        estate.get("DEVICE_999")


def test_buggy_cohort_is_27() -> None:
    estate = generate_estate(seed=42)
    cohort = estate.devices_with_teams_version(BUGGY_TEAMS_VERSION)
    assert len(cohort) == 27
    assert {d.device_id for d in cohort} == {f"DEVICE_{i:03d}" for i in range(1, 28)}


def test_mocks_satisfy_ports_and_agree() -> None:
    from simulator.intune import MockIntuneProvider
    from simulator.nexthink import MockNexthinkProvider
    from simulator.tanium import MockTaniumProvider

    estate = generate_estate(seed=42)
    nexthink, tanium, intune = (MockNexthinkProvider(estate),
                                MockTaniumProvider(estate),
                                MockIntuneProvider(estate))
    assert isinstance(nexthink, ports.EndpointProvider)
    assert isinstance(tanium, ports.EndpointProvider)
    assert isinstance(intune, ports.SoftwareProvider)
    assert (nexthink.source, tanium.source, intune.source) == (
        "nexthink", "tanium", "intune")

    health_n = nexthink.get_device_health("DEVICE_001")
    health_t = tanium.get_device_health("DEVICE_001")
    assert (health_n.cpu_pct, health_n.ram_pct) == (94.0, 91.0)
    assert (health_t.cpu_pct, health_t.ram_pct) == (94.0, 91.0)

    procs = tanium.get_processes("DEVICE_001")
    mems = [p.mem_mb for p in procs]
    assert mems == sorted(mems, reverse=True)
    assert procs[0].name == "Teams"

    inventory = intune.get_inventory("DEVICE_001")
    teams = next(s for s in inventory if s.app_id == "APP_TEAMS")
    assert teams.version == BUGGY_TEAMS_VERSION and not teams.healthy
    assert intune.get_patch_history("DEVICE_001")

    for provider in (nexthink, tanium, intune):
        method = ("get_inventory" if provider.source == "intune"
                  else "get_device_health")
        with pytest.raises(LookupError):
            getattr(provider, method)("DEVICE_999")


def test_factory_shares_one_estate() -> None:
    from common.config import load_settings
    from integrations.factory import build_providers
    from simulator.tanium import MockTaniumProvider

    providers = build_providers(load_settings(env_file="nonexistent-m5"))
    assert providers.estate is not None
    assert len(providers.estate.devices) == 500
    assert providers.endpoint is not None and providers.software is not None
    tanium = MockTaniumProvider(providers.estate)
    assert (tanium.get_device_health("DEVICE_001").cpu_pct ==
            providers.endpoint.get_device_health("DEVICE_001").cpu_pct)
    assert "seed=42" in providers.notes


def test_simulation_has_no_llm_layer() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    for rel in ("simulator/estate.py", "simulator/nexthink.py",
                "simulator/tanium.py", "simulator/intune.py"):
        text = (root / rel).read_text(encoding="utf-8").lower()
        assert "codedtool" not in text
        assert "llm_config" not in text
        assert "instructions" not in text
