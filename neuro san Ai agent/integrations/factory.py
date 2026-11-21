"""Provider factory (M6): mock-first selection with an audit-friendly note.

- Enterprise endpoint/software/network/identity: shared-estate mocks.
  Executor wires in M16.
- ITSM: real PDI iff live creds present AND use_mock is False;
  otherwise deterministic SimulatedITSM (user: no ServiceNow creds).
"""

from __future__ import annotations

from typing import Any

from integrations.ports import Providers
from integrations.servicenow.real_itsm import RealServiceNowITSM
from integrations.servicenow.client import ServiceNowClient, ServiceNowConfig
from integrations.servicenow.simulated_itsm import SimulatedITSM
from simulator.entra import MockEntraProvider
from simulator.estate import generate_estate
from simulator.intune import MockIntuneProvider
from simulator.nexthink import MockNexthinkProvider
from simulator.zscaler import MockZscalerProvider


def build_providers(settings: Any, use_mock: bool | None = None,
                    seed: int = 42) -> Providers:
    """Build one shared-estate bundle. Explicit use_mock wins; None = auto."""
    has_live = bool(getattr(settings, "has_servicenow", False))
    if use_mock is None:
        use_mock = not has_live
    estate = generate_estate(seed=seed)
    endpoint = MockNexthinkProvider(estate)
    software = MockIntuneProvider(estate)
    network = MockZscalerProvider(estate)
    identity = MockEntraProvider(estate)
    # NOTE: MockTaniumProvider/MockCloudflareProvider share the same estate;
    # callers needing cross-source verification build them from
    # providers.estate directly.
    if use_mock:
        reason = ("no live ServiceNow creds - simulated ITSM"
                  if not has_live else "explicit use_mock=True")
        return Providers(endpoint=endpoint, software=software,
                         network=network, identity=identity,
                         itsm=SimulatedITSM(seed=seed),
                         notes=f"itsm=simulated ({reason}); "
                               f"endpoint=nexthink network=zscaler "
                               f"identity=entra shared estate seed={seed}",
                         estate=estate)
    if not has_live:
        raise ValueError("use_mock=False requires SERVICENOW_* in env")
    config = ServiceNowConfig.from_settings(settings)
    client = ServiceNowClient(config)
    providers = Providers(endpoint=endpoint, software=software,
                          network=network, identity=identity,
                          itsm=RealServiceNowITSM(client),
                          notes=f"itsm=real (servicenow-table-api); "
                                f"shared estate seed={seed}",
                          estate=estate)
    return providers
