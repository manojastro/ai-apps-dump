# EVALUATION

## Method

`scripts/evaluate.py` replays the full fault catalog through the public API
against a fresh database and grades every run against the ground truth tagged
in `simulator/faults.py`. A fault passes when all its expected regression kinds
appear in the validation report; the benign scenario passes only with zero
detected regressions.

## Latest Results

```
scenario                               ok   risk      regs  ms
------------------------------------------------------------------------------
acl_blackhole                          PASS HIGH      2     ~600
asymmetric_routing                     PASS MEDIUM    3     ~580
benign_ntp_addition                    PASS LOW       0     ~280
bgp_route_leak                         PASS HIGH     15     ~770
bgp_route_missing                      PASS MEDIUM    2     ~660
dns_service_failure                    PASS CRITICAL 25     ~600
firewall_blocks_required_traffic       PASS HIGH      2     ~800
missing_route                          PASS CRITICAL 21     ~800
mtu_mismatch                           PASS CRITICAL  7     ~690
overlapping_subnet                     PASS CRITICAL  9     ~880
segmentation_violation                 PASS HIGH      2     ~780
vlan_mismatch                          PASS HIGH      4     ~690
wrong_gateway                          PASS HIGH      4     ~640
```

| Metric | Value |
|---|---|
| Detection accuracy | 100% (13/13 scenarios) |
| Recall on faults | 100% (12/12) |
| False positives | 0 (benign change yields zero regressions) |
| Precision | 100% |
| Unsafe-change prevention | apply-before-approval blocked with HTTP 409 |
| Avg validation duration | ~650-900 ms per full pipeline run |

## What Each Fault Proves

| Fault | Capability exercised |
|---|---|
| acl_blackhole | ACL-layer flow blocking, intent breakage, critical-service impact, remediation |
| bgp_route_missing | routing-table diff, redundancy intent (primary AND backup) |
| bgp_route_leak | internal-prefix hijack detection via BGP advertisement analysis |
| missing_route | OSPF withdrawal -> NO_ROUTE propagation, host isolation |
| asymmetric_routing | bidirectional path comparison, warning-class findings without outage |
| vlan_mismatch | VLAN adjacency semantics, gateway unreachability |
| overlapping_subnet | duplicate IP / zone-conflict topology analysis |
| firewall_blocks_required_traffic | firewall policy shadowing of permitted flows |
| dns_service_failure | service endpoint health mapping to multiple intents |
| mtu_mismatch | per-interface MTU checks along real paths |
| wrong_gateway | host configuration validation against subnet math |
| segmentation_violation | forbidden-flow detection when ACLs are removed |
| benign_ntp_addition | false-positive resistance to no-op config lines |

## Test Suite Coverage

79 tests across nine files: twin engine mathematics (LPM, admin distance, ACL
first-match, MTU, asymmetry, OSPF costs), tool framework contracts and audit,
agent behavior and exact RCA model contract, API surface including 409/422
error contracts, lifecycle workflows incl. auto-rollback, validation/intent
math, fault ground truth, and end-to-end demo parity.

Reproduce: `python -m pytest -q`
