"""Simulator package: seeded estate (M5/M6) + mock providers (M5/M6)."""

from simulator.cloudflare import MockCloudflareProvider
from simulator.entra import MockEntraProvider
from simulator.estate import (BUGGY_COHORT, BUGGY_TEAMS_VERSION, ESTATE_SIZE,
                              Estate, EstateIdentity, EstateSignin,
                              apply_demo_scenario, generate_estate)
from simulator.intune import MockIntuneProvider
from simulator.nexthink import MockNexthinkProvider
from simulator.tanium import MockTaniumProvider
from simulator.zscaler import MockZscalerProvider

__all__ = ["BUGGY_COHORT", "BUGGY_TEAMS_VERSION", "ESTATE_SIZE", "Estate",
           "EstateIdentity", "EstateSignin", "apply_demo_scenario",
           "generate_estate", "MockCloudflareProvider", "MockEntraProvider",
           "MockIntuneProvider", "MockNexthinkProvider", "MockTaniumProvider",
           "MockZscalerProvider"]
