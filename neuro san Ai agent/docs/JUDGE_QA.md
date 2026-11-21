# JUDGE Q&A

**Why 10 agents?** Each owns one evidence domain with its own tools. One agent
with 54 tools picks worse tools; ten specialists with six each stay sharp, and
the commander only wakes the relevant ones (a slow laptop never pages knowledge).

**Why not one LLM?** Separation of powers: LLMs propose, deterministic code
disposes. Policy, risk, autonomy, approvals, execution, and verification are
plain Python with no LLM dependency — an LLM cannot authorize itself.

**How do you prevent hallucinated actions?** Agents request `action_id`, never
shell. The id must exist, be approved, hash-verify, clear policy/risk/autonomy,
and pass approvals. Anything else refuses without touching the estate.

**Can agents bypass policy?** No. `control_plane/` imports zero agent code
(boundary-tested); the executor is orchestration-only and invisible in HOCON;
every refusal and execution is audited.

**What if Gemini is unavailable?** Fallback chain in `llm_config` plus the
deterministic runner keeps diagnosing; low confidence escalates instead of
guessing. No silent automation.

**How are secrets protected?** Env-only, aliases natively, deep redaction,
server-side vault, prompt corpus scanned. `docs/ZERO_SECRET_PROOF.md`: 113
prompts, all counts 0, PASS.

**How do you verify a fix?** Fresh provider telemetry through independent
sources against per-action postconditions with before/after per check. A 200
OK from execution proves nothing here.

**What if remediation makes things worse?** Failed postconditions trigger
snapshot-restore rollback, reproven, with failure+rollback counted (which
demotes autonomy). No rollback path means immediate escalation.

**How are AI-generated scripts controlled?** Seven automated stages (syntax,
forbidden-scan, secrets, privilege, sandbox, staging policy, risk) plus human
review before versioning, hashing, and registry insert. The registry never
self-writes.

**How does workflow learning work?** Resolution snapshots (not chat) with
success/reopen/approval data; repeated human-touched successes become
candidates; simulation+tests+human approval promote at L1.

**Can workflows self-approve?** No — promotion raises awaiting-approval until
a named human approves; the engine enforces it, tests prove it.

**How is ServiceNow integrated?** Standard Table API (no Scripted REST),
isolated adapter, simulated ITSM behind the same interface when no PDI creds.

**Why simulated Nexthink/Tanium/etc?** No production credentials for a
hackathon. Mocks implement the exact provider interfaces, so real connectors
drop in with zero caller changes.

**How do you replace mocks?** Implement the protocol in `integrations/<system>/`,
flip the factory on env creds. Callers, tests shapes, and HOCON stay.

**How do you measure RCA correctness?** 30-scenario adversarial benchmark
(`docs/EVALUATION_REPORT.md`): 30/30 accuracy, 0.0 unsafe-action rate, 1.0
red-herring rejection, plus 3 live traces.

**How do you prevent incorrect fleet-wide automation?** Per-device policy
re-evaluation at act time, EARLY/AT_RISK never auto-heal, blocked devices
reported untouched, tampered registry fails the whole wave safe.
