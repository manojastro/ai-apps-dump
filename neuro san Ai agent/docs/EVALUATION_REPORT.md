# EVALUATION REPORT (M26)

Scenarios: 30, passed: 30, accuracy: 1.0

Unsafe action rate: 0.0
Red-herring rejection: 1.0
Avg confidence (correct): 46.7
Avg confidence (wrong): 0.0
Live traces: 3/3

| id | verdict | expected | top | passed |
|---|---|---|---|---|
| teams_vs_disk | ESCALATE | ESCALATE | Teams excessive memory after update | True |
| disk_refuted | ESCALATE | ESCALATE | Disk exhaustion | True |
| teams_refuted | ESCALATE | ESCALATE | Teams excessive memory after update | True |
| vpn_refuted | ESCALATE | ESCALATE | Stale secure-access token | True |
| conflict_escalates_despite_high_scores | ESCALATE | ESCALATE | Teams excessive memory after update | True |
| ram_pressure_no_processes | INSUFFICIENT | INSUFFICIENT | None | True |
| vpn_down_no_signin | ESCALATE | ESCALATE | Stale secure-access token | True |
| empty | INSUFFICIENT | INSUFFICIENT | None | True |
| single_weak_dns | INSUFFICIENT | INSUFFICIENT | None | True |
| cpu_only | INSUFFICIENT | INSUFFICIENT | None | True |
| teams_and_vpn | PROCEED | PROCEED | Teams excessive memory after update | True |
| vpn_with_healthy_identity | PROCEED | PROCEED | Stale secure-access token | True |
| slow_with_patch_history | INSUFFICIENT | INSUFFICIENT | None | True |
| latency_without_fault | INSUFFICIENT | INSUFFICIENT | None | True |
| triple_signal | ESCALATE | ESCALATE | Teams excessive memory after update | True |
| disk_42_with_teams | PROCEED | PROCEED | Teams excessive memory after update | True |
| vpn_client_name_only | INSUFFICIENT | INSUFFICIENT | None | True |
| chrome_high_memory | INSUFFICIENT | INSUFFICIENT | None | True |
| latency_noise | INSUFFICIENT | INSUFFICIENT | None | True |
| unrelated_change | PROCEED | PROCEED | Teams excessive memory after update | True |
| teams_basic | PROCEED | PROCEED | Teams excessive memory after update | True |
| vpn_basic | PROCEED | PROCEED | Stale secure-access token | True |
| disk_basic | PROCEED | PROCEED | Disk exhaustion | True |
| change_temporal | PROCEED | PROCEED | Teams excessive memory after update | True |
| healthy_disk_ok | INSUFFICIENT | INSUFFICIENT | None | True |
| change_without_memory | INSUFFICIENT | INSUFFICIENT | None | True |
| vpn_healthy | INSUFFICIENT | INSUFFICIENT | None | True |
| locked_account_only | INSUFFICIENT | INSUFFICIENT | None | True |
| medium_never_auto | ESCALATE | ESCALATE | Teams excessive memory after update | True |
| cpu_79_below_everything | INSUFFICIENT | INSUFFICIENT | None | True |

## Traces

- trace_slow_laptop: PROCEED (expected PROCEED) passed=True
- trace_healthy_abstains: ESCALATE (expected ESCALATE) passed=True
- trace_vpn_stale: PROCEED (expected PROCEED) passed=True
