"""MockCloudflareProvider (M6): NetworkProvider path/DNS view over the estate."""

from __future__ import annotations

from integrations.ports import NetworkHealth, VPNState
from simulator.estate import Estate


class MockCloudflareProvider:
    source = "cloudflare"

    def __init__(self, estate: Estate) -> None:
        self._estate = estate

    def get_network_health(self, device_id: str) -> NetworkHealth:
        device = self._estate.get(device_id)
        return NetworkHealth(
            device_id=device.device_id, latency_ms=device.net_latency_ms,
            loss_pct=device.net_loss_pct, dns_ok=device.dns_ok,
            proxy_ok=device.proxy_ok, path_ok=device.path_ok,
            summary=(f"cloudflare: dns {'ok' if device.dns_ok else 'FAIL'} "
                     f"path {'ok' if device.path_ok else 'FAIL'} "
                     f"latency {device.net_latency_ms}ms"))

    def get_vpn_state(self, device_id: str) -> VPNState:
        device = self._estate.get(device_id)
        return VPNState(device_id=device.device_id,
                        connected=device.vpn_connected,
                        gateway=device.vpn_gateway,
                        last_error=device.vpn_last_error)
