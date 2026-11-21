# FINAL ACCEPTANCE (M30) — checkbox to evidence

- [x] Gemini API powers Neuro SAN agents — `config/llm_config.hocon`
  (`gemini-3-flash`, temp 1.0); live loop needs `GOOGLE_API_KEY` + `ns run`.
- [x] Commander dynamically delegates — `test_m7_network.py` (ranked routing),
  `test_m8_delegation.py` (per-request agent sets).
- [x] Specialists collaborate — traces span endpoint+software / network+identity.
- [x] Intelligent tool choice — M8: same text, different telemetry, different
  tools; predicates take facts, never text.
- [x] Multi-system correlation — `correlate` groups + `temporal_links`.
- [x] Competing hypotheses + evidence + calibrated confidence — `test_m10_rca.py`,
  bands 90/70, `docs/EVALUATION_REPORT.md` (30/30, unsafe 0.0).
- [x] Low confidence escalates — abstention tests + healthy-device trace.
- [x] Policy cannot be bypassed — import boundary (`test_m29_gate.py`), executor
  orchestration-only, HOCON has no control-plane tools.
- [x] Approved registry required; hash/version validated — M13/M16 tamper tests.
- [x] Risk classification, autonomy levels, human approval — M15 engine + gates.
- [x] Remote simulated execution; before/after captured — M16 snapshots.
- [x] Verification required; rollback/escalation on failure — M17 tests.
- [x] Real ServiceNow lifecycle — Table API client (M3) + composer (M18);
  sim path green, live path needs PDI creds (contract-tested).
- [x] Knowledge respects permissions — M11 deny tests + demo-4.
- [x] Learning detects patterns; no self-promotion; reusable; policy re-checked —
  M20/M21/M22 tests.
- [x] Fleet finds related devices; proactivity only where permitted; Problem
  record; prevented metric — M23/M24 tests (27/26/PRB).
- [x] Zero exposures — `docs/ZERO_SECRET_PROOF.md` (113 prompts, all 0, PASS).
- [x] Full audit trace — M19 timeline + card tests.
- [x] Benchmark runs; red herrings rejected — M26 (1.0 rejection).
- [x] Metrics derived from runs — M27 move-with-data test.
- [x] Reset works; primary demo repeats — M28 determinism + reset tests.

Suite: `python -m pytest -q` — 155 tests green (see BUILD_STATE per milestone).
Live gaps (need keys, nothing hidden): Gemini live loop, PDI live calls.
