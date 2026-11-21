# DEMO SCRIPT — 3-minute primary hackathon demonstration

Setup (before the clock): `pip install -r requirements.txt`, `.env` with
`GOOGLE_API_KEY`, `python -m demo.reset_demo`.

## 0:00–0:20 — The ticket

> "My laptop is extremely slow and Teams keeps freezing."

Run: `python -m demo.demo --scenario laptop_teams_memory --seed 42`

Say: "One user reported a problem. Watch the agents work it — nobody told
them which tools to call."

## 0:20–1:00 — Think, observe, argue

Point at the tool sequence: device health → software inventory → processes →
recent changes. CPU 94, RAM 91, Teams 4.7 GB, updated yesterday. RCA weighs
Teams-memory 100% SUPPORTED against disk and token hypotheses — the disk
reading (42%, healthy) never even forms a hypothesis; red herrings die with
citations.

## 1:00–1:40 — Authorize, execute, verify

Policy gate: RBAC, compliance, approved script SCR-018, hash, deny-list,
LOW, L3 → ALLOW. Execution runs. Then — the important slide — verification
re-queries Nexthink AND Tanium: 94→22, 91→54, 4.7 GB→640 MB. Only then does
the ServiceNow incident resolve.

## 1:40–2:30 — Learn and heal the fleet

The resolution snapshots to a pattern. Fleet scan: 500 devices, 27 matching
the Teams 3.8.4 signature. Policy per device. All 27 auto-eligible here:
healed and verified one by one. Problem record created, incident linked.

## 2:30–3:00 — The winning moment

> "One user reported a problem. The agents solved it safely, learned the
> root cause, found the same emerging issue across the enterprise, and
> prevented the next 26 incidents before users noticed."

Backup one-liners: `vpn_stale_token` (identity+network isolation, human
approval shown), `learning_loop` (earn L3 on camera), `knowledge_security`
(payroll snooping denied). Reset anytime: `python -m demo.reset_demo`.
