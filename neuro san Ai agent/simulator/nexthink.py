"""MockNexthinkProvider (M5): EndpointProvider over the shared estate."""

from __future__ import annotations

from integrations.ports import ChangeEntry, DeviceHealth, ProcessEntry
from simulator.estate import Estate


class MockNexthinkProvider:
    source = "nexthink"

    def __init__(self, estate: Estate) -> None:
        self._estate = estate

    def get_device_health(self, device_id: str) -> DeviceHealth:
        device = self._estate.get(device_id)
        return DeviceHealth(
            device_id=device.device_id, cpu_pct=device.cpu_pct,
            ram_pct=device.ram_pct, disk_pct=device.disk_pct,
            boot_secs=device.boot_secs,
            compliant=device.compliance_state == "compliant",
            summary=(f"nexthink experience: cpu {device.cpu_pct}% ram "
                     f"{device.ram_pct}% disk {device.disk_pct}%"))

    def get_processes(self, device_id: str) -> list[ProcessEntry]:
        device = self._estate.get(device_id)
        return [ProcessEntry(p.name, p.mem_mb, p.cpu_pct) for p in device.processes]

    def get_recent_changes(self, device_id: str) -> list[ChangeEntry]:
        device = self._estate.get(device_id)
        return [ChangeEntry(c.change_id, c.target, c.kind, c.at, c.summary)
                for c in device.recent_changes]
