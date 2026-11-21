"""MockZscalerProvider (M6): NetworkProvider secure-access view over the estate."""

from __future__ import annotations

from integrations.ports import NetworkHealth, VPNState
from simulator.estate import Estate


class MockZscalerProvider:
    source = "zscaler"

    def __init__(self, estate: Estate) -> None:
        self._estate = estate

    def get_network_health(self, device_id: str) -> NetworkHealth:
        device = self._estate.get(device_id)
        return NetworkHealth(
            device_id=device.device_id, latency_ms=device.net_latency_ms,
            loss_pct=device.net_loss_pct, dns_ok=device.dns_ok,
            proxy_ok=device.proxy_ok, path_ok=device.path_ok,
            summary=(f"zscaler: proxy {'ok' if device.proxy_ok else 'FAIL'} "
                     f"vpn {'up' if device.vpn_connected else 'DOWN'} "
                     f"({device.vpn_last_error or 'no error'})"))

    def get_vpn_state(self, device_id: str) -> VPNState:
        device = self._estate.get(device_id)
        return VPNState(device_id=device.device_id,
                        connected=device.vpn_connected,
                        gateway=device.vpn_gateway,
                        last_error=device.vpn_last_error)
