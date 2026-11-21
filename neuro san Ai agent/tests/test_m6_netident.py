"""M6 tests: network/identity overlays + Entra/Zscaler/Cloudflare mocks."""

from __future__ import annotations

import re

import pytest

from integrations import ports
from simulator.estate import generate_estate


def test_identities_present_and_deterministic() -> None:
    a = generate_estate(seed=42)
    b = generate_estate(seed=42)
    assert len(a.identities) == 500
    assert set(a.identities) == {f"USER_{i:03d}" for i in range(1, 501)}
    assert (a.devices["DEVICE_050"].vpn_last_error ==
            b.devices["DEVICE_050"].vpn_last_error)
    assert a.get_identity("USER_050").mfa_ok == b.get_identity("USER_050").mfa_ok
    with pytest.raises(LookupError):
        a.get_identity("USER_999")


def test_demo2_vpn_stale_token_exact() -> None:
    estate = generate_estate(seed=42)
    device = estate.get("DEVICE_002")
    assert not device.vpn_connected
    assert device.vpn_last_error == "stale cached token after password change"
    assert (device.net_latency_ms, device.net_loss_pct) == (35.0, 0.1)
    assert device.dns_ok and device.proxy_ok and device.path_ok
    assert "vpn_stale_token" in device.issues

    identity = estate.get_identity("USER_002")
    assert identity.account_state == "active"
    assert identity.mfa_ok and not identity.locked
    events = [(s.event, s.result) for s in identity.signins]
    assert ("password_reset", "success") in events
    assert ("vpn_auth", "failed") in events


def test_demo1_untouched_by_overlays() -> None:
    estate = generate_estate(seed=42)
    device = estate.get("DEVICE_001")
    assert (device.cpu_pct, device.ram_pct, device.disk_pct) == (94.0, 91.0, 42.0)
    assert len(estate.devices_with_teams_version("3.8.4")) == 27


def test_mocks_satisfy_ports_and_agree() -> None:
    from simulator.cloudflare import MockCloudflareProvider
    from simulator.entra import MockEntraProvider
    from simulator.zscaler import MockZscalerProvider

    estate = generate_estate(seed=42)
    entra, zscaler, cloudflare = (MockEntraProvider(estate),
                                  MockZscalerProvider(estate),
                                  MockCloudflareProvider(estate))
    assert isinstance(entra, ports.IdentityProvider)
    assert isinstance(zscaler, ports.NetworkProvider)
    assert isinstance(cloudflare, ports.NetworkProvider)
    assert (entra.source, zscaler.source, cloudflare.source) == (
        "entra", "zscaler", "cloudflare")

    identity = entra.get_identity("USER_002")
    assert (identity.account_state, identity.mfa_ok, identity.locked) == (
        "active", True, False)
    history = entra.get_signin_history("USER_002")
    assert any(h["event"] == "password_reset" and h["result"] == "success"
               for h in history)

    health_z = zscaler.get_network_health("DEVICE_002")
    health_c = cloudflare.get_network_health("DEVICE_002")
    assert (health_z.latency_ms, health_z.loss_pct) == (35.0, 0.1)
    assert (health_c.latency_ms, health_c.loss_pct) == (35.0, 0.1)
    assert health_z.summary != health_c.summary
    assert not zscaler.get_vpn_state("DEVICE_002").connected
    assert (cloudflare.get_vpn_state("DEVICE_002").last_error ==
            "stale cached token after password change")

    with pytest.raises(LookupError):
        zscaler.get_network_health("DEVICE_999")
    with pytest.raises(LookupError):
        entra.get_identity("USER_999")


def test_factory_wires_network_identity() -> None:
    from common.config import load_settings
    from integrations.factory import build_providers

    providers = build_providers(load_settings(env_file="nonexistent-m6"))
    assert providers.network is not None and providers.identity is not None
    assert providers.network.source == "zscaler"  # type: ignore[union-attr]
    assert providers.identity.source == "entra"  # type: ignore[union-attr]
    assert providers.network.get_vpn_state("DEVICE_002").last_error  # type: ignore[union-attr]
    assert "seed=42" in providers.notes


def test_no_real_ips_or_llm_refs() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    estate_text = (root / "simulator" / "estate.py").read_text(encoding="utf-8")
    assert not re.search(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", estate_text)
    for rel in ("simulator/entra.py", "simulator/zscaler.py",
                "simulator/cloudflare.py"):
        text = (root / rel).read_text(encoding="utf-8").lower()
        assert "codedtool" not in text
        assert "llm_config" not in text
