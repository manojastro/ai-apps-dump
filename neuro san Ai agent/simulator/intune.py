"""MockIntuneProvider (M5): SoftwareProvider over the shared estate."""

from __future__ import annotations

from integrations.ports import ChangeEntry, SoftwareItem
from simulator.estate import Estate


class MockIntuneProvider:
    source = "intune"

    def __init__(self, estate: Estate) -> None:
        self._estate = estate

    def get_inventory(self, device_id: str) -> list[SoftwareItem]:
        device = self._estate.get(device_id)
        return [SoftwareItem(s.app_id, s.name, s.version, s.healthy)
                for s in device.software]

    def get_recent_changes(self, device_id: str) -> list[ChangeEntry]:
        device = self._estate.get(device_id)
        return [ChangeEntry(c.change_id, c.target, c.kind, c.at, c.summary)
                for c in device.recent_changes
                if c.kind in ("update", "install", "uninstall")]

    def get_patch_history(self, device_id: str) -> list[ChangeEntry]:
        device = self._estate.get(device_id)
        return [ChangeEntry(c.change_id, c.target, c.kind, c.at, c.summary)
                for c in device.patch_history]
