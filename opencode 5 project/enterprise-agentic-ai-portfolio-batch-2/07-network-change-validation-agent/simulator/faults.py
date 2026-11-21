"""Deterministic fault injection scenarios with tagged ground-truth expectations."""
from __future__ import annotations

from pydantic import BaseModel, Field


class ExpectedRegression(BaseModel):
    kind: str
    detail_contains: list[str] = Field(default_factory=list)


class FaultSpec(BaseModel):
    name: str
    title: str
    description: str
    category: str
    diff_text: str
    expected_regressions: list[ExpectedRegression]
    benign: bool = False


class FaultCatalog:
    def __init__(self) -> None:
        self._faults: dict[str, FaultSpec] = {}
        for spec in self._build():
            self._faults[spec.name] = spec

    @staticmethod
    def _build() -> list[FaultSpec]:
        return [
            FaultSpec(
                name="acl_blackhole",
                title="ACL blackholes app-to-db traffic",
                description="New extended ACL denies tcp/5432 from prod-app to prod-db inbound on fw-01 Vlan210.",
                category="acl",
                diff_text=(
                    "device fw-01\n"
                    "+ip access-list APP-DB-GUARD\n"
                    "+ deny tcp 10.30.0.0/24 10.30.1.0/24 eq 5432\n"
                    "+ permit ip any any\n"
                    "interface Vlan210\n"
                    "+ ip access-group APP-DB-GUARD in\n"
                ),
                expected_regressions=[
                    ExpectedRegression(kind="INTENT_MUST_REACH_BROKEN",
                                       detail_contains=["app-tier-to-postgres"]),
                    ExpectedRegression(kind="ACL_BLACKHOLE", detail_contains=["APP-DB-GUARD"]),
                ],
            ),
            FaultSpec(
                name="bgp_route_missing",
                title="BGP backup advertisement withdrawn",
                description="core-01 loses one of two BGP routes to branch prefix 10.80.0.0/24.",
                category="routing",
                diff_text=(
                    "device core-01\n"
                    "router bgp 65000\n"
                    "- neighbor 10.200.3.5 advertised-prefixes 10.80.0.0/24\n"
                ),
                expected_regressions=[
                    ExpectedRegression(kind="ROUTE_MISSING", detail_contains=["10.80.0.0/24"]),
                    ExpectedRegression(kind="INTENT_ROUTE_MISSING",
                                       detail_contains=["branch-primary-and-backup"]),
                ],
            ),
            FaultSpec(
                name="bgp_route_leak",
                title="Internal dev prefix leaked to WAN edge",
                description="wan-edge-01 advertises internal prefix 10.50.20.0/24 toward core via BGP, hijacking traffic into a routing loop.",
                category="routing",
                diff_text=(
                    "device core-01\n"
                    "router bgp 65000\n"
                    "+ neighbor 10.200.2.1 advertised-prefixes 10.50.20.0/24\n"
                ),
                expected_regressions=[
                    ExpectedRegression(kind="ROUTE_HIJACK", detail_contains=["10.50.20.0/24"]),
                    ExpectedRegression(kind="INTENT_MUST_REACH_BROKEN",
                                       detail_contains=["ops-reach-dev"]),
                ],
            ),
            FaultSpec(
                name="missing_route",
                title="dev-vlan withdrawn from OSPF",
                description="access-dev-01 stops advertising 10.50.20.0/24 into OSPF; dev subnet vanishes from the routing domain.",
                category="routing",
                diff_text=(
                    "device access-dev-01\n"
                    "router ospf 1\n"
                    "- network 10.50.20.0/24 area 0\n"
                ),
                expected_regressions=[
                    ExpectedRegression(kind="NO_ROUTE", detail_contains=["10.50.20.66"]),
                    ExpectedRegression(kind="HOST_ISOLATED", detail_contains=["dev-vm-01"]),
                    ExpectedRegression(kind="INTENT_MUST_REACH_BROKEN",
                                       detail_contains=["ops-reach-dev"]),
                ],
            ),
            FaultSpec(
                name="asymmetric_routing",
                title="Static route pins forward path off the symmetric path",
                description="More-specific static route on core-01 forwards dev-bound traffic via dist-01 while return traffic follows OSPF via dist-02.",
                category="routing",
                diff_text=(
                    "device core-01\n"
                    "+ip route 10.50.20.0/24 10.200.1.1\n"
                ),
                expected_regressions=[
                    ExpectedRegression(kind="ASYMMETRIC_ROUTE", detail_contains=[]),
                ],
            ),
            FaultSpec(
                name="vlan_mismatch",
                title="Finance gateway VLAN membership mismatch",
                description="access-fin-01 SVI moves to vlan 111 while fin-app-01 stays in vlan 110, breaking L2 adjacency to the gateway.",
                category="l2",
                diff_text=(
                    "device access-fin-01\n"
                    "interface Vlan110\n"
                    "+ switchport access vlan 111\n"
                ),
                expected_regressions=[
                    ExpectedRegression(kind="GATEWAY_UNREACHABLE", detail_contains=["fin-app-01"]),
                    ExpectedRegression(kind="HOST_ISOLATED", detail_contains=["fin-app-01"]),
                    ExpectedRegression(kind="INTENT_MUST_REACH_BROKEN",
                                       detail_contains=["finance-to-dns"]),
                ],
            ),
            FaultSpec(
                name="overlapping_subnet",
                title="Overlapping mgmt subnet on WAN edge",
                description="wan-edge-01 is configured with a duplicate 10.99.0.1/24 address overlapping the management subnet and gateway IP.",
                category="addressing",
                diff_text=(
                    "device wan-edge-01\n"
                    "interface Ethernet1/3\n"
                    "+ no shutdown\n"
                    "+ ip address 10.99.0.1/24\n"
                    "+ switchport access vlan 10\n"
                ),
                expected_regressions=[
                    ExpectedRegression(kind="SUBNET_OVERLAP", detail_contains=["10.99.0.0/24"]),
                    ExpectedRegression(kind="INTENT_MUST_NOT_REACH_VIOLATED",
                                       detail_contains=["mgmt-jump-restricted"]),
                ],
            ),
            FirewallFault(),
            DnsServiceFault(),
            MtuMismatchFault(),
            WrongGatewayFault(),
            SegmentationViolationFault(),
            BenignChange(),
        ]

    def names(self) -> list[str]:
        return sorted(self._faults)

    def get(self, name: str) -> FaultSpec:
        if name not in self._faults:
            raise KeyError(name)
        return self._faults[name]

    def all_faults(self) -> dict[str, FaultSpec]:
        return dict(self._faults)


class FirewallFault(FaultSpec):
    def __init__(self) -> None:
        super().__init__(
            name="firewall_blocks_required_traffic",
            title="Firewall policy blocks required app-to-db flow",
            description="Explicit deny inserted at seq 5 on fw-01 shadows the permit for app-to-postgres.",
            category="firewall",
            diff_text=(
                "device fw-01\n"
                "+firewall policy 5 deny 10.30.0.0/24 10.30.1.0/24 tcp eq 5432 label shadow-deny\n"
            ),
            expected_regressions=[
                ExpectedRegression(kind="INTENT_MUST_REACH_BROKEN",
                                   detail_contains=["app-tier-to-postgres"]),
                ExpectedRegression(kind="FW_BLOCKED_FLOW", detail_contains=["shadow-deny"]),
            ],
        )


class DnsServiceFault(FaultSpec):
    def __init__(self) -> None:
        super().__init__(
            name="dns_service_failure",
            title="DNS service interface shutdown",
            description="dns-01 eth0 administratively down; DNS resolution paths fail across zones.",
            category="service",
            diff_text=(
                "device dns-01\n"
                "interface eth0\n"
                "+ shutdown\n"
            ),
            expected_regressions=[
                ExpectedRegression(kind="SERVICE_UNREACHABLE", detail_contains=["dns"]),
                ExpectedRegression(kind="INTENT_MUST_REACH_BROKEN", detail_contains=["app-to-dns"]),
                ExpectedRegression(kind="INTENT_MUST_REACH_BROKEN",
                                   detail_contains=["finance-to-dns"]),
                ExpectedRegression(kind="INTENT_MUST_REACH_BROKEN", detail_contains=["branch-to-dns"]),
            ],
        )


class MtuMismatchFault(FaultSpec):
    def __init__(self) -> None:
        super().__init__(
            name="mtu_mismatch",
            title="MTU mismatch on firewall app-facing VLAN",
            description="fw-01 Vlan210 MTU lowered to 1300; standard 1500-byte packets from app tier are dropped.",
            category="mtu",
            diff_text=(
                "device fw-01\n"
                "interface Vlan210\n"
                "+ mtu 1300\n"
            ),
            expected_regressions=[
                ExpectedRegression(kind="MTU_VIOLATION", detail_contains=["Vlan210"]),
                ExpectedRegression(kind="INTENT_MUST_REACH_BROKEN",
                                   detail_contains=["app-tier-to-postgres"]),
            ],
        )


class WrongGatewayFault(FaultSpec):
    def __init__(self) -> None:
        super().__init__(
            name="wrong_gateway",
            title="Finance host default gateway misconfigured",
            description="fin-app-01 default gateway points at unused address 10.40.10.254; finance subnet is isolated.",
            category="host",
            diff_text=(
                "device fin-app-01\n"
                "+ip default-gateway 10.40.10.254\n"
            ),
            expected_regressions=[
                ExpectedRegression(kind="GATEWAY_UNREACHABLE", detail_contains=["fin-app-01"]),
                ExpectedRegression(kind="HOST_ISOLATED", detail_contains=["fin-app-01"]),
                ExpectedRegression(kind="INTENT_MUST_REACH_BROKEN",
                                   detail_contains=["finance-to-dns"]),
            ],
        )


class SegmentationViolationFault(FaultSpec):
    def __init__(self) -> None:
        super().__init__(
            name="segmentation_violation",
            title="Segmentation ACL removed between dev and finance",
            description="The dev-to-finance deny line is deleted from SEG-ISOLATE-FIN, opening forbidden east-west traffic.",
            category="security",
            diff_text=(
                "device access-fin-01\n"
                "ip access-list SEG-ISOLATE-FIN\n"
                "- deny ip 10.50.20.0/24 10.40.10.0/24\n"
            ),
            expected_regressions=[
                ExpectedRegression(kind="INTENT_MUST_NOT_REACH_VIOLATED",
                                   detail_contains=["dev-isolated-from-finance"]),
                ExpectedRegression(kind="SEGMENTATION_VIOLATION", detail_contains=[]),
            ],
        )


class BenignChange(FaultSpec):
    def __init__(self) -> None:
        super().__init__(
            name="benign_ntp_addition",
            title="Add NTP server reference on core",
            description="Unmodeled cosmetic change adding an NTP server statement; must produce zero regressions.",
            category="benign",
            benign=True,
            diff_text=(
                "device core-01\n"
                "+ntp server 10.99.0.24 prefer\n"
            ),
            expected_regressions=[],
        )


FAULT_CATALOG = FaultCatalog()
