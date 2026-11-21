# BUILD STATE — Digital Workplace Autopilot

## M0 — Framework grounding — COMPLETED (2026-09-06)
- Cloned `cognizant-ai-lab/neuro-san-studio@9cb6965` + `cognizant-ai-lab/neuro-san` (neuro-san==0.7.0) to `C:\Users\manoj\AppData\Local\Temp\opencode\*-ref` for inspection.
- Read: `README.md`, `docs/user_guide.md` (HOCON/agent/tool/middleware/LLM/Gemini/fallback/AAOSA/sly_data/toolbox/MCP), `docs/tutorial.md` (CodedTool, AGENT_TOOL_PATH/MANIFEST), `docs/dev_guide.md`, `docs/examples.md`, `docs/agent_hocon_reference.md` + `docs/manifest_hocon_reference.md` (neuro-san), `registries/manifest.hocon`, `registries/basic/music_nerd.hocon`, `registries/aaosa.hocon`, `config/llm_config.hocon` + `developer_llm_config.hocon`, `coded_tools/basic/accountant.py` + siblings, `neuro_san/interfaces/coded_tool.py`, `.env.example`, `requirements.txt`.
- Created: `docs/FRAMEWORK_FACTS.md` (source of truth), `docs/BUILD_STATE.md` (this file), `docs/DECISIONS.md`.
- Tests: no app code yet; verification = direct file reads + `Test-Json` on `opencode.json`; `python 3.11.15` present, `pip` via `python -m pip`.
- Architecture decisions: see `docs/DECISIONS.md` (D001–D010). Key: real framework wins; Neuro SAN layout preserved; `agents/` folder rejected; `GOOGLE_API_KEY` only; Gemini 3 `temperature:1.0`.
- Pending: M1 repo skeleton per proposed structure below; requires `GOOGLE_API_KEY` in `.env` (user-supplied, never committed).
- Known bugs/risks: `GEMINI_API_KEY` confusion (doc-only, do not use); Windows `;` manifest separator; `AGENT_TOOL_PATH` must include coded tools; Gemini 3 low-temp infinite-loop risk.
- Next: M1 only (skeleton, config, .env.example, logging, SQLite bootstrap). Do NOT start M2+ yet.

## Proposed final repository structure (M0 decision, adapts prompt to framework)
```
digital-workplace-autopilot/
  registries/digital_workplace_autopilot/
    commander.hocon          # 1 network file, 10 LLM agents + coded-tool refs (front-man first)
    manifest.hocon           # included from root registries/manifest.hocon
  coded_tools/digital_workplace/
    endpoint_tools.py  software_tools.py  network_tools.py  identity_tools.py
    rca_tools.py  knowledge_tools.py  security_tools.py  learning_tools.py
    servicenow_tools.py  control_plane_tools.py  fleet_tools.py  evidence_tools.py
  control_plane/  integrations/servicenow/  simulator/  knowledge/  script_registry/  workflow_registry/
  database/  audit/  metrics/  evaluation/scenarios/  demo/  ui/  tests/  docs/
  config/llm_config.hocon  registries/manifest.hocon  .env.example  .gitignore  requirements.txt  README.md
```
- Rationale: Neuro SAN serves ONLY `registries/*.hocon` via `AGENT_MANIFEST_FILE`; tool code resolves via `AGENT_TOOL_PATH`. `agents/` top-level from prompt is rejected (no such convention). `control_plane/*`, `integrations/*`, `simulator/*` are Python packages imported by `coded_tools/*` (keeps `AGENT_TOOL_PATH` small, business logic testable without LLM).
- `config/llm_config.hocon` = single Gemini entry (see DECISIONS D003). Root `registries/manifest.hocon` includes `registries/digital_workplace_autopilot/manifest.hocon`.

## Milestone tracker
- [x] M0 grounding
- [x] M1 skeleton/config/.env/logging/SQLite — COMPLETED (2026-09-06)
- [x] M2 domain models/DB/audit schema — COMPLETED (2026-09-07)
- [x] M3 ServiceNow real connector — COMPLETED (2026-09-07)
- [x] M4 Enterprise connector abstractions — COMPLETED (2026-09-07)
- [x] M5 Mock Nexthink/Tanium/Intune simulation — COMPLETED (2026-09-07)
- [x] M6 Mock Entra/Zscaler/Cloudflare simulation — COMPLETED (2026-09-07)
- [x] M7 10-agent Neuro SAN network — COMPLETED (2026-09-07)
- [x] M8 Intelligent delegation + dynamic tool calling — COMPLETED (2026-09-07)
- [x] M9 Evidence normalization — COMPLETED (2026-09-07)
- [x] M10 Hypothesis-driven RCA + confidence + causal graph — COMPLETED (2026-09-07)
- [x] M11 Knowledge RAG + RBAC/document ACL — COMPLETED (2026-09-07)
- [x] M12 Policy-as-Code control plane — COMPLETED (2026-09-07)
- [x] M13 Approved Script Registry — COMPLETED (2026-09-07)
- [x] M14 AI-generated script validation pipeline — COMPLETED (2026-09-07)
- [x] M15 Risk engine + autonomy levels + approval engine — COMPLETED (2026-09-07)
- [x] M16 Remote execution (policy-gated executor) — COMPLETED (2026-09-07)
- [x] M17 Multi-tool verification + rollback — COMPLETED (2026-09-07)
- [x] M18 Full ServiceNow lifecycle — COMPLETED (2026-09-07)
- [x] M19 Decision trace / audit UI — COMPLETED (2026-09-07)
- [x] M20 Learning agent + pattern recording — COMPLETED (2026-09-07)
- [x] M21 Workflow candidate + promotion pipeline — COMPLETED (2026-09-07)
- [x] M22 Known-workflow replay — COMPLETED (2026-09-07)
- [x] M23 Fleet intelligence — COMPLETED (2026-09-07)
- [x] M24 Proactive fleet healing + Problem management — COMPLETED (2026-09-07)
- [x] M25 Zero-secret / zero-PII proof — COMPLETED (2026-09-07)
- [x] M26 Adversarial RCA benchmark - COMPLETED (2026-09-07)
- [x] M27 KPI dashboard - COMPLETED (2026-09-07)
- [x] M28 End-to-end demos + reset - COMPLETED (2026-09-07)
- [x] M29 Reliability + security gate - COMPLETED (2026-09-07)
- [x] M30 Documentation + acceptance - COMPLETED (2026-09-07)

## M1 — Repository skeleton / config / .env / logging / SQLite — COMPLETED (2026-09-06)
- Slices (incremental, each verified): S1 requirements/.env.example/.gitignore/pytest.ini → S2 common/{config,logging_setup,redaction} → S3 database/{bootstrap,schema.sql} → S4 Neuro SAN skeleton (config/llm_config.hocon, registries/manifest.hocon + digital_workplace_autopilot/manifest.hocon, coded_tools/control_plane/integrations/simulator/audit/metrics/evaluation/demo/ui/knowledge/script_registry/workflow_registry pkgs) → S5 tests + fixes.
- Files created: requirements.txt, .env.example, .gitignore, pytest.ini, README.md (stub), common/__init__.py + config.py + logging_setup.py + redaction.py, database/__init__.py + bootstrap.py + schema.sql, config/llm_config.hocon, registries/manifest.hocon, registries/digital_workplace_autopilot/manifest.hocon, 17x __init__.py package markers, tests/__init__.py + test_m1_bootstrap.py (10 tests).
- Files modified: common/logging_setup.py (record-factory redaction — logger filters miss propagated child records + caplog), config/llm_config.hocon (drop key NAME from comment so HOCON carries zero secret identifiers).
- Tests: `python -m pytest -q` → 10 passed. First run 8 passed/2 failed (HOCON comment contained key NAME; logging filter missed child propagation); both fixed, rerun green. No skips.
- Decisions: no new D-entries (D002/D003/D006 hold). `data/` runtime-only (gitignored, bootstrap mkdirs); `data/autopilot.db` created during verification then removed.
- Risks: HOCON not yet parsed by `ns check-config` (needs `pip install -r requirements.txt` + network in M7); `GEMINI_API_KEY` alias deliberately absent; Windows manifest separator `;` noted.
- Next: M2 only (domain models, full DB tables, audit-event schema). Do NOT start M3+ yet.

## M2 — Core domain models / database / audit-event schema — COMPLETED (2026-09-07)
- Secure key handling: user-supplied Gemini key NOT persisted/printed/logged/committed per zero-secret rule (D006). Verified `.env` absent, `.env.example` placeholder-only, `.gitignore` covers `.env`/`*.db`. Live-key curl NOT executed by agent (would leak secret to logs); user creates local `.env` with `GOOGLE_API_KEY` themselves. Note: supplied token shape is non-standard (AI Studio keys start `AIza`); verify in AI Studio + `ns check-llm-keys` after env set. M2 needs no live LLM.
- Slices: S1 database/models.py (14 dataclasses, aliased IDs, SUPPORTED/REJECTED/INSUFFICIENT + ALLOW/DENY/REQUIRE_APPROVAL enums-as-str) → S2 database/schema.sql v2 (21 tables + indexes + FKs) + bootstrap SCHEMA_VERSION=2 → S3 audit/logger.py (log_event redacts via redact_text, list_events timeline) → S4 tests + fix.
- Files created: database/models.py, audit/logger.py, tests/test_m2_models.py (6 tests).
- Files modified: database/schema.sql (v1→v2 full domain DDL), database/bootstrap.py (VERSION 1→2), tests/test_m1_bootstrap.py (`==1`→`>=1` for version growth).
- Tests: `python -m pytest -q` → 16 passed (10 M1 + 6 M2). One interim failure (M1 hardcoded version) fixed openly, rerun green.
- Risks: schema v2 additive only (no migration downgrade yet — M29); knowledge content bodies live in knowledge/ files (content_ref), not DB; metrics computed from runs (M27).
- Next: M3 only (ServiceNow Table API: create/read/search/update/work-note/resolve/escalate + problem/link).

## M3 — ServiceNow real connector (Table API) — COMPLETED (2026-09-07)
- Slices: S1 integrations/servicenow/client.py (stdlib urllib, injectable transport, Basic + bearer-ready, 401→AuthError/404→NotFound, logs method/path/status only) → S2 incidents.py (create/get/search/update/work-note/resolve state=6/escalate P1/problem/link + WRITABLE allowlist) + __init__ surface → S3 credential boundary (creds in config-from-env + Authorization header only; incidents.py has zero credential refs) → S4 fake-PDI tests.
- Files created: integrations/servicenow/client.py, incidents.py, tests/test_m3_servicenow.py (8 tests).
- Files modified: integrations/servicenow/__init__.py (public surface, 14 exports).
- Tests: `python -m pytest -q` → 24 passed (16 prior + 8 M3). No failures, no live network.
- Decisions/assumptions: standard `/api/now/table/{incident,problem}` only (no Scripted REST); resolve = `state=6` + close_code/notes (PDI default, enforced non-empty); link = `incident.problem_id` + problem work-note (revisit only if a real PDI proves otherwise); OAuth = bearer_token override, Basic today.
- Risks: live PDI not yet exercised (needs user SERVICENOW_* in local .env, M18 full lifecycle + M28 demo); search query passthrough assumes encoded `sysparm_query` dialect; no retry/backoff yet (M29 hardening).
- Next: M4 only (enterprise connector abstractions: EndpointProvider et al. behind adapter interfaces, mocks implement same).

## M4 — Enterprise connector abstractions — COMPLETED (2026-09-07)
- User constraint: no live ServiceNow creds — mock-first throughout; real client preserved for later swap with zero caller changes.
- Slices: S1 integrations/ports.py (DTOs + 6 runtime_checkable Protocols: Endpoint/Software/Network/Identity/ITSM/RemoteExecutor + Providers bundle) → S2 factory + adapters (real_itsm.py wraps M3 client; simulated_itsm.py deterministic seed-42 in-memory PDI; factory.build_providers auto=mock-first, explicit override, ValueError when forcing real without creds) → S3 six package skeletons (nexthink/tanium/intune/entra/zscaler/cloudflare, interface-only docstrings) → S4 contract tests.
- Files created: integrations/ports.py, factory.py, servicenow/real_itsm.py, servicenow/simulated_itsm.py, 6x system __init__.py, tests/test_m4_ports.py (6 tests).
- Files modified: integrations/factory.py (em-dash→hyphen for Win console).
- Tests: `python -m pytest -q` → 30 passed (24 prior + 6 M4). No failures, no live network.
- Decisions: simulated ITSM numbering INC/PRB0001xxx from seed (demo-deterministic); enterprise observe/execute split (RemoteExecutor separate for M16/M17 control plane); ports.py carries zero credential/simulator references (tested).
- Risks: enterprise mocks unwired (factory endpoint/software/network/identity=None until M5/M6); simulated ITSM work_notes list vs real journal string (DTO hides difference; revisit in M18 if demo surfaces it).
- Next: M5 only (Mock Nexthink/Tanium/Intune simulation + 500-device estate seed).

## M5 — Mock Nexthink/Tanium/Intune simulation — COMPLETED (2026-09-07)
- Slices: S1 simulator/estate.py (500 aliased devices+users, seeded RNG, 27-device Teams 3.8.4 cohort DEVICE_001..027, apply_demo_scenario pins DEVICE_001 to CPU94/RAM91/Disk42/Teams 4812.8MB) → S2 simulator/{nexthink,tanium,intune}.py (read-only Endpoint/Software ports; Tanium mem-sorted live view) → S3 factory shares one estate across mocks + Providers.estate (Any-typed, ports stay import-free) + simulator/__init__ exports → S4 tests + 2 open fixes.
- Files created: simulator/estate.py, nexthink.py, tanium.py, intune.py, tests/test_m5_simulation.py (7 tests).
- Files modified: integrations/ports.py (Providers.estate), factory.py (shared-estate mocks; network/identity still M6), simulator/__init__.py (exports), tests/test_m4_ports.py (endpoint None→nexthink/intune — intended M5 progression).
- Tests: `python -m pytest -q` → 37 passed (30 prior + 7 M5). One interim fail (M4 text-guard vs new docstring word) fixed by rewording, rerun green.
- Decisions: cohort exactly 27 pre-seeds fleet demo (M23); mocks read-only (execution M16); no sim logic outside simulator/ (tested — no CodedTool/llm references).
- Risks: network/identity overlays absent until M6 (estate devices carry no vpn/identity state yet); change timestamps fixed per cohort (temporal RCA in M10 uses them as-is).
- Next: M6 only (Mock Entra/Zscaler/Cloudflare + network/identity estate overlays).

## M6 — Mock Entra/Zscaler/Cloudflare simulation — COMPLETED (2026-09-07)
- Slices: S1 estate overlays (per-device net/vpn fields + EstateIdentity/EstateSignin + 500 identities via separate overlay RNG stream so M5 draws never shift; vpn_stale_token pins DEVICE_002/U002: vpn DOWN stale-token, net healthy 35ms/0.1%, identity active+mfa, password_reset success + vpn_auth failed) → S2 simulator/{entra,zscaler,cloudflare}.py (Identity/Network ports; Zscaler secure-access vs Cloudflare path/DNS summaries, identical core numbers) → S3 factory wires network=zscaler + identity=entra (Tanium/Cloudflare caller-built from shared estate) + simulator exports → S4 tests + 1 open fix.
- Files created: simulator/entra.py, zscaler.py, cloudflare.py, tests/test_m6_netident.py (6 tests).
- Files modified: simulator/estate.py (overlays + dual demo hooks), factory.py (network/identity wiring), simulator/__init__.py (exports), tests/test_m4_ports.py (None→zscaler/entra — intended M6 progression).
- Tests: `python -m pytest -q` → 43 passed (37 prior + 6 M6). No failures (M4 expectation updated openly for the intended wiring progression).
- Decisions: overlay RNG stream separated (M5 determinism preserved — demo1/cohort untouched, regression-tested); DEVICE_002 carries both teams_memory + vpn_stale_token (multi-issue realism); no real IPs anywhere (tested).
- Risks: executor still unwired (M16); vpn_last_error free-text matched by agents (M8 tool-selection must not hard-code the string — RCA reads live values).
- Next: M7 only (10-agent Neuro SAN network: commander.hocon front-man + 9 specialists, coded-tool refs, manifest entry).

## M7 — 10-agent Neuro SAN network — COMPLETED (2026-09-07)
- Slices: S1 coded_tools/digital_workplace/_ctx.py (mock-first bundles, id resolution) + observe.py (22 query tools: 6 endpoint incl Tanium cross-check, 5 software incl static catalog, 6 network, 5 identity) → S2 rca.py (7 evidence helpers incl confidence bands + mermaid) + knowledge.py (ACL deny-by-default shape) + security.py (advisory-only + tiers) → S3 commander_tools.py (ranked routing, user/case context, approved-only workflow search) + ops.py (5 SQLite learning tools with forced-candidate + 9 simulated ITSM tools) → S4 registries/digital_workplace_autopilot/commander.hocon (64 entries) + manifest + vendored registries/aaosa.hocon (verbatim Apache, root-relative includes) → S5 tests + 2 open test fixes.
- Files created: coded_tools/digital_workplace/{_ctx,observe,rca,knowledge,security,commander_tools,ops}.py, commander.hocon, tests/test_m7_network.py (11 tests), tests/conftest.py (neuro_san test-only stub mirroring verified §4 signatures).
- Files modified: registries/.../manifest.hocon (serve commander), registries/aaosa.hocon (new, vendored).
- HOCON validity: parsed with repo-root basedir (ns-resolves-includes-root-relative finding documented) → 64 entries, commander first with no params/class, 9 specialists with inquiry params, 54 coded tools, zero dupes, zero dangling refs, gemini-3-flash/1.0 resolved, AAOSA substitutions resolved.
- Tests: `python -m pytest -q` → 54 passed (43 prior + 11 M7). Two interim test-side fails (banned-word vs sample prose; module- vs method-helper) fixed openly.
- Decisions: D11 — specialists use explicit function schemas (not ${aaosa_call} merge) for parse certainty; commander carries 13 down-chains (4 tools + 9 agents, LLM selects per rank); neuro_san absent here so conftest stubs it (real check = ns check-config M28); pip installed pyhocon==0.3.63 (declared dep).
- Risks: agent collaboration unproven without live LLM (M8); knowledge/runbook stores empty until M11; remediation/execution/policy untouched until M12-M17 (agents can only observe + propose today).
- Next: M8 only (intelligent delegation proof: ranked routing + evidence-driven follow-ups + stop rules, no fixed chains).

## M8 — Intelligent delegation + dynamic tool calling — COMPLETED (2026-09-07)
- Slices: S1 orchestration/{__init__,investigate.py} (route → round-1 probes → evidence predicates to fixpoint → RCA score/threshold → 1 bounded follow-up → PROCEED/CONFIRM/ESCALATE/KNOWLEDGE; stops at conf>=90, 8-call budget, name-level dedupe) → S2 tests/test_m8_delegation.py (6 trace tests) → S3 run + state.
- Fixes during build (open): GenerateHypotheses name-matching was too loose (VPN-client app name formed stale-token; healthy Teams formed memory) → threshold triggers (process>=3000MB/UNHEALTHY/disk>=80/DOWN-stale) so red herrings never form; single-pass predicates missed depth (recent_changes) → fixpoint loop; fixpoint infinite-looped on user-scoped tools (tuple-key vs name-key) → called_names set.
- Proven traces (seed 42): slow DEVICE_001 = health→inventory→processes→recent_changes → PROCEED Teams 100 SUPPORTED, no disk/vpn hypotheses, knowledge absent; same text DEVICE_100 = health→follow-up processes → ESCALATE 0% (honest abstention); vpn DEVICE_002 = vpn→network→account→signin→zscaler → PROCEED stale-token, no endpoint tools; reimbursement = knowledge only → KNOWLEDGE.
- Files created: orchestration/__init__.py + investigate.py, tests/test_m8_delegation.py (6 tests).
- Files modified: coded_tools/digital_workplace/rca.py (threshold triggers), orchestration/investigate.py (fixpoint + dedupe).
- Tests: `python -m pytest -q` → 60 passed (54 prior + 6 M8). No skips.
- Decisions: D12 — post-routing selection is numbers-only (_next_tools takes facts, never text); initial text ranking is intent routing, not symptom→script mapping; healthy-device abstention is the correct outcome, not a failure.
- Risks: runner is deterministic scaffolding for the LLM behavior (live agents may pick different-but-valid orders — trace tests pin the coded path, HOCON pins the agent topology); evidence dicts are pre-M9 shape (M9 normalizes to DB).
- Next: M9 only (evidence normalization to SQLite per spec schema).

## M9 — Evidence normalization — COMPLETED (2026-09-07)
- Slices: S1 evidence/{__init__,normalize.py} (12 spec fields in order; source map incl static-catalog; confidence 0.9/0.95/0.5; units %/MB/ms/s; measurement names + value formats UNCHANGED for RCA stability; value/entity/summary/raw all redacted) → S2 evidence/store.py (ensure_case, save with stable CASE-E001 ids + OR REPLACE idempotence, list ordered; IntegrityError without parent documents the FK contract) → S3 investigate refactor (normalize replaces _evidence_from, +case_id/db_path params, persist at verdict returns, stored_ids on trace) → S4 tests.
- Files created: evidence/__init__.py + normalize.py + store.py, tests/test_m9_evidence.py (7 tests).
- Files modified: orchestration/investigate.py (normalize + persist; _evidence_from deleted).
- Tests: `python -m pytest -q` → 67 passed (60 prior + 7 M9). M8 traces byte-identical after the swap (verified PROCEED path pre/post).
- Decisions: persist is single-batch at verdict (stable ids, reruns converge); KNOWLEDGE path stores nothing (no telemetry); hostile-value redaction defense-in-depth (estate is secret-free by construction, normalizer assumes nothing).
- Risks: raw_reference truncated 500 chars (M25 proof reads full prompts elsewhere); multi-batch same-case appends not yet needed (single investigation = single batch).
- Next: M10 only (hypothesis-driven RCA with DB persistence + abstention + causal graph).

## M10 — Hypothesis-driven RCA + confidence + causal graph — COMPLETED (2026-09-07)
- Slices: S1 orchestration/rca.py (propose/refuting_for/score/confidence_band/correlate/temporal_links/missing_evidence/find_conflicts/causal_graph/diagnose + RcaResult; thresholds 90/70; teams-vs-disk conflict pair; missing keys map to tools) → S2 rca.py wrappers delegate (identical I/O) + store.save/list_hypotheses (CASE-H01 stable ids) → S3 investigate rca_round replaced by diagnose(); follow-up now RCA-driven via missing→tool map (+ thoroughness rule); thresholds single-sourced → S4 tests + 1 open test fix.
- Files created: orchestration/rca.py, tests/test_m10_rca.py (8 tests).
- Files modified: coded_tools/digital_workplace/rca.py (thin wrappers, zero logic), evidence/store.py (+hypotheses fns), orchestration/investigate.py (diagnose + missing-driven follow-up; PROCEED_AT/CONFIRM_AT removed).
- Tests: `python -m pytest -q` → 75 passed (67 prior + 8 M10). One interim test-side fail (expected ESCALATE for no-candidate+gap; engine correctly abstains INSUFFICIENT with named gap) fixed openly. M8 traces re-verified identical post-refactor.
- Decisions: D13 — contradicted candidates stay visible as REJECTED (never silently dropped); vpn-domain never conflicts with performance-domain (different fault planes); INSUFFICIENT (nothing to judge) vs ESCALATE (judged-unsafe) both block autonomy, mapped at the trace layer.
- Risks: conflict pairs hand-listed (teams-vs-disk only — M26 benchmark may demand more; adversarial red-team cases will extend); temporal links are entity-overlap heuristics (LLM weighs them live).
- Next: M11 only (knowledge RAG seeding + ACL enforcement + permission-aware retrieval).

## M11 — Knowledge RAG + RBAC/document ACL — COMPLETED (2026-09-07)
- Slices: S1 knowledge/{HR,Finance,IT,Security,Applications,Runbooks}/ (11 docs, line-1 ACL comments; payroll_admin_sop restricted; runbooks for both demos) → S2 retrieval upgrade (_sections on ## headers skipping H1/ACL, _score term-overlap, top-5 chunks with section+excerpt+confidence, answer=top excerpt; role filter still BEFORE scoring) → S3 demo-4 tests → S4 run + state.
- Fixes during build (open): ACL parser kept "-->" suffix on single-role lines (payroll_admin never matched — deny-by-default masked it; tests now cover) → strip comment close; H1 leaked into first chunk → skipped as metadata.
- Proven: reimbursement as employee → internet_reimbursement + How-to-Claim citation; payroll-info as employee → payroll_admin_sop absent + ACCESS DENIED; payroll_admin role → full access; no-ACL doc invisible; teams runbook found.
- Files created: 11 knowledge docs, tests/test_m11_knowledge.py (6 tests).
- Files modified: coded_tools/digital_workplace/knowledge.py (retrieval), tests/test_m7_network.py (payroll expectation → exclusion-based, intended M11 progression).
- Tests: `python -m pytest -q` → 81 passed (75 prior + 6 M11). No skips.
- Decisions: D14 — keyword retrieval (no vectors; deterministic, testable, sufficient for 11-doc base; revisit only past hundreds of docs) + ACL as line-1 HTML comment (human-editable, grep-able, parsed before content read).
- Risks: substring term matching (no stemming — "reimburse" vs "reimbursement" both present in docs so demo works; M26 phrasing variants may need stemming); excerpts capped 300 chars.
- Next: M12 only (deterministic Policy-as-Code control plane: ALLOW/DENY/REQUIRE_APPROVAL).

## M12 — Policy-as-Code control plane — COMPLETED (2026-09-07)
- Slices: S1 control_plane/registry.py (lookup/is_approved/verify_hash; tamper-mismatch DENIES, empty defers to execution) + policy.py (10 ordered checks: role/group/compliance/approval/hash/deny-list/risk/autonomy/hours/rollback; DENY wins, then APPROVAL, else ALLOW; record_decision persists) → S2 coded_tools/digital_workplace/control.py EvaluatePolicy wrapper (NOT wired to any agent tools[] yet — orchestration-only until M15/M16) → S3 tests.
- Proven: spec example SCR-018/DEVICE_038 → ALLOW with all 10 PASS; DENY on unknown script, tamper hash, non-compliant, bad group, unknown role, deny-list; REQUIRE_APPROVAL on L2/L1, HIGH risk, off-hours MEDIUM; deny-list precedence over approval-softening; decisions only ever ALLOW/DENY/REQUIRE_APPROVAL.
- Files created: control_plane/registry.py + policy.py, coded_tools/digital_workplace/control.py, tests/test_m12_policy.py (6 tests).
- Files modified: none (registry seeding is M13; scripts table read as-is, empty = deny).
- Tests: `python -m pytest -q` → 87 passed (81 prior + 6 M12). No failures.
- Decisions: D15 — engine is import-isolated from neuro_san/dotenv/os.environ (boundary-tested; LLM cannot reach it); hash-mismatch hard-DENIES while empty-hash defers (agents propose action_id only per D005); off-hours gates non-LOW risk; no-rollback gates non-LOW risk.
- Risks: production scripts table empty until M13 seed (ALLOW unprovable outside tests until then); business-hours UTC fixed (localize in M29 hardening); record_decision ids time-based (audit only).
- Next: M13 only (Approved Script Registry seed + governance: SCR-018 etc. with hash/version/rollback metrics).

## M13 — Approved Script Registry — COMPLETED (2026-09-07)
- Slices: S1 control_plane/registry.py extended (canonical sha256 over id/version/platform/name, verify_stored_hash, idempotent seed_registry with 8 governed scripts + preset histories, get_approved_action trust gate, find_approved_action keyword map, record_execution accounting) → S2 tests.
- Seed (all approved except last): SCR-018 Clear Teams Cache 3.2 LOW L3 rollback (95/94 = 98.9%, spec example), SCR-VPN-RECONNECT 1.4 MEDIUM L2, SCR-INSTALL 2.0 MEDIUM L2, SCR-RESTART-APP 1.1 LOW L3, SCR-CLEAR-TEMP 1.0 LOW L3, SCR-DISK-CLEANUP 1.2 LOW L3, SCR-FIREWALL 1.0 HIGH L1 approved, SCR-DISABLE-PROTECTION CRITICAL L0 unapproved + deny-listed.
- Proven: idempotent seed; tampered hash → get_approved_action None; teams/vpn/disk mapping + unknown None; execution math (96/95 = 99.0, failure/rollback/reopen counting); policy ALLOW on seeded SCR-018 + REQUIRE_APPROVAL on SCR-VPN-RECONNECT (closes M12's empty-registry risk note).
- Files created: tests/test_m13_registry.py (5 tests).
- Files modified: control_plane/registry.py (seed + ops; M12 read API unchanged).
- Tests: `python -m pytest -q` → 92 passed (87 prior + 5 M13). No failures.
- Decisions: D16 — hash recomputable from the row alone (no external body to lose); AI-generated intake stays M14 (registry never self-writes from LLM output).
- Risks: keyword action map is a starting heuristic (M16 remediation may rank multiple candidates); preset histories are illustrative baselines (live metrics overwrite via record_execution).
- Next: M14 only (AI-generated script validation pipeline: propose → scan → sandbox → review → register).

## M14 — AI-generated script validation pipeline — COMPLETED (2026-09-07)
- Slices: S1 database/schema.sql + script_proposals table (status machine proposed/validated/in_review/approved/denied/registered) + bootstrap v3 + control_plane/script_intake.py (7 automated stages + review transitions) → S2 review/approve/register (staging-savepoint policy gate, version 1.0 + canonical hash, approvals row) → S3 tests + 1 open test fix.
- Stages enforced: syntax (schema/allowlisted primitives/groups) → forbidden-command regex scan → secret-shape detection → privilege matrix (L4 never at intake, claimed within risk cap) → sandbox dry-run on scratch device copy (source estate provably untouched) → staging policy gate (rollback savepoint, no residue) → risk classification (claimed covers computed max) → human review → register.
- Proven: happy path 7/7 → in_review → registered with valid hash + executable via get_approved_action; denied on forbidden primitive, leaked key shape, L4 claim, risk under-claim; no skipping (validate→review→approve order enforced, rejected never registers); bad ids rejected.
- Files created: control_plane/script_intake.py, tests/test_m14_intake.py (4 tests).
- Files modified: database/schema.sql (+script_proposals), database/bootstrap.py (v2→v3).
- Tests: `python -m pytest -q` → 96 passed (92 prior + 4 M14). One interim test-side fail (validate returns denied-status, never raises) fixed openly.
- Decisions: D17 — primitives allowlist is the executable vocabulary (anything else fails syntax before deeper stages); staging policy uses post-approval shape (review grants approval; gate tests the rest); sandbox asserts source-copy isolation inline.
- Risks: forbidden regex list is heuristic (M29 red-team extends); human review is an approvals row today (M15 approval engine generalizes); version always 1.0 at intake (upgrades later).
- Next: M15 only (risk engine + autonomy levels + approval engine + earned promotion/demotion).

## M15 — Risk engine + autonomy levels + approval engine — COMPLETED (2026-09-07)
- Slices: S1 control_plane/risk.py (registry → primitives-max → HIGH default) + autonomy.py (L0-L4, promotion ladder L1→L2 on 2 approvals / L2→L3 on 10+ runs ≥95% ≤5% rb/ro + zero DENY / L3→L4 on 50+ ≥98% ≤2% + rollback; demotion on ≥3/10 recent failures or DENY at L3+, L0 terminal; scripts+workflows via shared metric columns) → S2 approvals.py (request reuse, approve/deny with terminal immutability + named approver, expire_stale timeout) → S3 tests.
- Proven: risk sources incl safe HIGH defaults; L1 holds then promotes on 2 approvals (applied to L2); seeded SCR-VPN-RECONNECT eligible L3; 3 recent failures demote seeded SCR-018 L3→L2 and persist; L0 terminal; unknown starts L1; approval reuse/double-decide guard/expiry (49h-old → EXPIRED).
- Files created: control_plane/risk.py + autonomy.py + approvals.py, tests/test_m15_autonomy.py (6 tests).
- Files modified: none.
- Tests: `python -m pytest -q` → 102 passed (96 prior + 6 M15). No failures.
- Decisions: D18 — autonomy reads live metrics only (remediation_runs/workflow_runs windows + approvals/policy_decisions counts); approvals.script_id convention holds the gated entity id for both scripts and workflows; expiry default 24h.
- Risks: promotion thresholds are constants (tune after M26 calibration data); workflow-side promotion unexercised until M21 reuses the engine.
- Next: M16 only (policy-gated remote execution controller + ExecuteRemoteAction tool).

## M16 — Remote execution (policy-gated executor) — COMPLETED (2026-09-07)
- Slices: S1 simulator/actions.py (SCR-018/VPN/DISK/TEMP/RESTART/INSTALL transitions + snapshots; demo-exact numbers) → S2 control_plane/execution.py (registry→device→policy→autonomy→approval→execute→record; stored level governs, earned changes via apply_autonomy only; real device group/compliance from estate) + approvals.latest_for + ExecuteRemoteAction single-shot wrapper → S3 tests + 2 open fixes.
- Proven: L3 SCR-018 executes (94→22/91→54/4812→640, issues cleared) with run row (before/after), metrics+1, audit event, policy row; 6 refusal classes touch nothing (unknown/tampered/L1/L0/unknown-device/non-compliant); L2 pauses→denied refuses→re-requested→approved executes; missing app param refuses; wrapper single-shot shape.
- Files created: simulator/actions.py, control_plane/execution.py, tests/test_m16_execution.py (4 tests).
- Files modified: control_plane/approvals.py (+latest_for), coded_tools/digital_workplace/control.py (+ExecuteRemoteAction).
- Tests: `python -m pytest -q` → 106 passed (102 prior + 4 M16). Interim: helper-tuple bug + denied-retry returning AWAITING (real gate bug — DENIED now refuses) fixed openly.
- Decisions: D19 — execution success ≠ resolution (success=executed-ok; M17 decides resolved); estate injected per call (no globals; wrapper builds fresh seed estate and returns snapshots); HOCON untouched (agents never see the executor; orchestration calls it).
- Risks: wrapper estate is throwaway (session verify-after-execute uses Python API on one estate — M17 wires this); no retry on effect failure (M29 hardening).
- Next: M17 only (multi-tool verification on fresh telemetry + rollback/escalate).

## M17 — Multi-tool verification + rollback — COMPLETED (2026-09-07)
- Slices: S1 control_plane/verification.py (capture_state via Nexthink+Tanium+Zscaler/Cloudflare/Intune providers; per-action postconditions; before/after per check; INSTALL app-targeted via params) → S2 control_plane/rollback.py (snapshot restore, verify_rollback equality, verify_and_recover composer with failure metrics + dual audit) → S3 tests.
- Proven: SCR-018 verified on fresh telemetry (nexthink 22 + tanium 640); sabotage → 3 named failed postconditions → rollback restores before snapshot → rollback_run linked + failure/rollback counted (feeds M15 demotion) + verification/rollback audit present; rollback_available=0 → escalate_required with support-queue target; unknown run raises.
- Files created: control_plane/verification.py + rollback.py, tests/test_m17_recovery.py (4 tests).
- Files modified: none (no wrappers — verify/rollback need the session estate, so Python API only; documented).
- Tests: `python -m pytest -q` → 110 passed (106 prior + 4 M17). No failures.
- Decisions: D20 — verification reads provider telemetry, never run rows or effect returns; rollback is snapshot-restore (generic across actions); refused/awaiting executions never reach verification (nothing to verify).
- Risks: postcondition thresholds mirror RCA triggers by hand (a shared constants module can unify in M29); escalation is a payload for M18, not an ITSM call yet.
- Next: M18 only (ServiceNow lifecycle on live-or-sim ITSM: resolve only when verified, escalate on recovery failure).

## M18 — Full ServiceNow lifecycle — COMPLETED (2026-09-07)
- Slices: S1 integrations/servicenow/lifecycle.py (open idempotent + ensure_case, note_investigation trace notes, resolve_verified hard gate, escalate_recovery with trail, open_problem + incident links; any ITSMProvider) → S2 chains + 1 open schema fix.
- Proven: open twice = one row; resolve refuses unverified (incident stays New); happy chain execute→verified→Resolved(6) with row sync; fail chain rolled_back→escalated P1 with trail; problem PRB links 2 incidents. Fix: incidents FK requires parent case — open_incident now ensures it (real contract bug, not test-side).
- Files created: integrations/servicenow/lifecycle.py, tests/test_m18_lifecycle.py (4 tests).
- Files modified: none beyond the fix above.
- Tests: `python -m pytest -q` → 114 passed (110 prior + 4 M18). No skips.
- Decisions: D21 — lifecycle runs on the provider interface (sim today, PDI tomorrow, zero caller change); local incidents rows mirror ITSM for dashboard/audit; resolve gate raises (never soft-skips).
- Risks: live PDI still unexercised (user has no creds; M28 demo runs sim path, live path covered by M3 client tests + RealServiceNowITSM contract test).
- Next: M19 only (decision trace / audit timeline UI data + rendering).

## M19 — Decision trace / audit UI — COMPLETED (2026-09-07)
- Slices: S1 audit/timeline.py (build_timeline merges 7 record types with tz-safe sort; scan_timeline re-scans on read; render_timeline_markdown; build_final_card spec shape, fleet fields M23/M24) → S2 investigate audit logging (routing + per-tool durations + rca verdict + final verdict rows, case-gated, closed on all returns) → S3 tests.
- Proven: full tmp-DB story (investigate→incident→execute→verified→resolved) yields 10+ ordered entries across audit/policy/execution/rca/itsm/evidence; card shows Teams RCA 100%, ALLOW, SCR-018, 94/91/4812→22/54/640, PASS, INC number, RESOLVED; hostile key logged anywhere still scans clean; caseless runs write zero rows/files.
- Files created: audit/timeline.py, tests/test_m19_trace.py (4 tests).
- Files modified: orchestration/investigate.py (audit hooks only; traces unchanged — full suite confirms).
- Tests: `python -m pytest -q` → 118 passed (114 prior + 4 M19). No failures.
- Decisions: D22 — timeline merges at read time (no duplicate store); verdicts AND tool durations are audit rows (latency analysis free); card fleet keys reserved for M23/M24.
- Risks: mixed timestamp formats sorted via parser (all writers should converge on one format in M29); card before/after keys limited to cpu/ram/teams (extend per action in M27).
- Next: M20 only (learning agent: resolution-pattern recording → governed candidates).

## M20 — Learning agent + pattern recording — COMPLETED (2026-09-07)
- Slices: S1 resolution_patterns table (schema v4: signature/evidence-pattern/root-cause/action/policy/approval/verification/success/reopen/correction) + learning.record/detect/propose → S2 promote_candidate gauntlet (simulate on scratch estate + security + policy + workflow test, human-approval gate, register approved at L1) → S3 ops tools delegate + tests + 2 open test fixes.
- Proven: 3 APPROVED successes → candidate (never approved at birth, always L1); reopened excluded from occurrences while dragging the rate; all-auto patterns never propose (human-touch gate); promote raises awaiting → human approves → approved; deny-listed action refuses even after approval; ops Record tool now returns pattern_id too.
- Files created: control_plane/learning.py, tests/test_m20_learning.py (5 tests).
- Files modified: database/schema.sql (+resolution_patterns) + bootstrap.py (v3→v4), coded_tools/digital_workplace/ops.py (learning tools delegate; M7 shapes preserved incl caller workflow_id).
- Tests: `python -m pytest -q` → 123 passed (118 prior + 5 M20). Two interim test-side fails (rate math with poisoned mix; vacuous assert) fixed openly.
- Decisions: D23 — patterns are snapshots, never history text; rate denominator includes every row (relapses poison); promotion simulates on scratch devices (source estate untouched); earned autonomy stays M15's job post-approval.
- Risks: scratch simulation targets fixed demo devices (fine for seeded actions; novel actions need target mapping — M21); reopen marking is caller-reported (M22 replay sets it on recurrence).
- Next: M21 only (workflow promotion pipeline generalization + registry lifecycle).

## M21 — Workflow registry lifecycle — COMPLETED (2026-09-07)
- Note: M20 already shipped propose/promote; M21 is the registry-side lifecycle around it.
- Added to control_plane/learning.py: get_workflow, snapshot_version (definition freeze per approval), record_workflow_run (reuse metrics + rate + last_updated), recheck_workflow (fresh policy verdict per reuse), sync_autonomy (M15 engine on workflows). promote_candidate now snapshots on approval. Repaired one bad edit that had renamed propose_candidate (caught by signature check, fixed openly).
- Proven: 3 reuses → 3/2/66.7%; recheck ALLOW vs DENY on posture flip; version rows accumulate (manual + promotion); 3 failed runs demote L3→L2 and persist.
- Files created: tests/test_m21_lifecycle.py (3 tests).
- Files modified: control_plane/learning.py (+5 functions, +1 snapshot call in promote).
- Tests: `python -m pytest -q` → included in the 136 below.
- Decisions: D24 — reuse metrics live on the workflow row AND workflow_runs (both, no single-source disputes); every reuse re-evaluates policy (recheck_workflow is the choke point M22 must call).
- Risks: version strings stay 1.0 (bump policy when definitions change — M29); reopen on recurrence still caller-reported.
- Next: M22 only (known-workflow replay shortcut in orchestration).

## M22 — Known-workflow replay — COMPLETED (2026-09-07)
- orchestration/replay.py: match_signature (0.5 overlap hit) → find_matching_workflow (approved only) → try_known_workflow (recheck → autonomy branch → request_execution → verify_and_recover → record_workflow_run). L3/L4 auto with HUMAN NONE; L2 pauses for approval (no metrics recorded on pause — outcome unknown yet); L0/L1/DENY abort to full investigation with reasons; unknown device misses cleanly.
- Proven: WF-023 L3 replays slow-laptop on DEVICE_005 → verified, healed, 1/1/100%; reimbursement text misses; non-compliant posture aborts pre-execution (device untouched); L2 VPN pauses → human approves → verified + APPROVED intervention recorded.
- Files created: orchestration/replay.py, tests/test_m22_replay.py (5 tests).
- Files modified: none.
- Tests: included in the 136 below.
- Decisions: D25 — replay matches on request text (pre-evidence shortcut is the point); policy re-check uses live device posture (never the cached verdict); awaiting pauses record nothing (metrics only on outcomes).
- Risks: signature overlap is lexical (M26 paraphrase variants will stress it); replay bypasses investigation evidence (by design — the workflow IS the compiled evidence).

## M23 — Fleet intelligence — COMPLETED (2026-09-07)
- orchestration/fleet.py: derive_failure_signature (title keywords + version context) → search_fleet_for_signature (AFFECTED ≥3000MB/80%/stale-DOWN; EARLY warning bands; AT_RISK same-version symptomless) → classify_fleet (per-device policy + stored autonomy → auto/approval/blocked; persists fleet_matches; mutates nothing) → scan_fleet composer.
- Truthful counts (seed 42, teams_memory@3.8.4): 500 scanned, 27 matching (all AFFECTED), 27 auto-eligible, 0 approval, 0 blocked — the cohort is fully compliant, so no theatrical 20/5/2. Blocked/approval paths proven via posture-flip (compliant→blocked moves buckets) and unit states. Dashboard MUST show computed counts (M27 enforces).
- Proven: 27-cohort exact; DEVICE_100 absent; DEVICE_002 vpn-AFFECTED; determinism; buckets partition matches; blocked ⟺ non-compliant; flip test proves per-device evaluation (no caching).
- Files created: orchestration/fleet.py, tests/test_m23_fleet.py (5 tests).
- Files modified: none.
- Tests: `python -m pytest -q` → 136 passed (123 prior + 13 across M21/M22/M23). One repaired bad edit (propose→promote rename) caught before running.
- Decisions: D26 — states are threshold bands on live readings (not stored labels); buckets combine state × policy × autonomy (EARLY/AT_RISK never auto even when ALLOW); counts are always computed.
- Risks: AT_RISK needs version context (unknown without evidence — M24 passes RCA evidence through); EARLY bands are heuristic (M26 calibration).
- Next: M24 only (proactive per-device remediation + Problem record + prevented-ticket math).

## M24 — Proactive fleet healing + Problem management — COMPLETED (2026-09-07)
- orchestration/heal.py heal_fleet: M23 scan → per-device request_execution (re-gated at act time) → verify_and_recover → fleet_matches verified flags; approval bucket files human gates untouched; blocked reported never forced; Problem created with scanned/matching/healed/approval/blocked/prevented + originating incident linked; prevented = verified-healed minus originating device.
- Truthful seed-42 run: 500 scanned, 27 matching, 27 healed verified, 0 approval, 0 blocked, 26 prevented, PRB filed, 0.1s. VPN/L2 run: 16 matching → 15 approvals + 1 blocked, zero touched. Tampered registry: 27 failed, 0 healed, problem still recorded.
- Files created: orchestration/heal.py, tests/test_m24_heal.py (5 tests).
- Files modified: none.
- Tests: `python -m pytest -q` → 141 passed (136 prior + 5 M24). Interim: helper-tuple + stale assertions fixed openly (incl. real distribution 15+1 replacing guessed all-approval).
- Decisions: D27 — execution re-gates per device (classify-then-act never assumed); prevented counts verified-healed others only; problem records even on total failure (the pattern is real).
- Risks: mass-heal is fast on mocks (27 devices, 0.1s) — real endpoints need batching/rate limits (M29 hardening); no approval expiry sweep inside heal (M15 expire_stale covers on read).
- Next: M25 only (zero-secret/zero-PII proof: prompt capture + scanner + report).

## M25 — Zero-secret / zero-PII proof — COMPLETED (2026-09-07)
- control_plane/privacy.py (sanitize_for_llm deep-redact + server-side SecureContext) + evaluation/scan_secrets.py (122 files, 74 HOCON prompt blocks, 39-corpus trace layer; locations-only findings; placeholder-aware FQDN/email/allowlist rules).
- Fixes during build (open): scanner ate its own def line (repaired openly); self-matches on example.com/logger.info (allowlisted documented fixtures).
- Result: docs/ZERO_SECRET_PROOF.md — 113 prompts inspected, all six counts 0, PASS.
- Files created: control_plane/privacy.py, evaluation/__init__.py + scan_secrets.py, docs/ZERO_SECRET_PROOF.md, tests/test_m25_privacy.py (3 tests).
- Tests: `python -m pytest -q` → included in the 155 below.
- Decisions: D28 — findings never carry values (locations only); fixtures/placeholders allowlisted by name in code.
- Risks: live-LLM prompt layer is the same strings via ns run (harness captures the tool/context layer deterministically).
- Next: M26 only (adversarial RCA benchmark).

## M26 — Adversarial RCA benchmark — COMPLETED (2026-09-07)
- evaluation/scenarios/ (6 files × 5 = 30: straightforward, multi-domain, missing, conflicting, red-herring, unsafe-denied) + evaluation/run_benchmark.py (grade + calibrate + write docs/EVALUATION_REPORT.md) + 3 live traces.
- The benchmark caught a real engine bug (Chrome memory framing Teams → entity-gated triggers) and one over-strict scenario (fixed openly); final: 30/30 accuracy, 0.0 unsafe, 1.0 red-herring rejection, 3/3 traces.
- Files created: 6 scenario files, evaluation/run_benchmark.py, docs/EVALUATION_REPORT.md, tests/test_m26_benchmark.py (2 tests).
- Files modified: orchestration/rca.py (Teams-entity trigger gate).
- Tests: included in the 155 below.
- Decisions: D29 — scenarios test the contract, not luck (incomplete-but-principled inputs must escalate); unsafe PROCEED rate is the headline metric (0.0 required).
- Risks: lexical replay matching untested by paraphrase (known M22 limit); benchmark is engine-level (live-LLM variance outside harness).
- Next: M27 only (KPI dashboard).

## M27 — KPI dashboard — COMPLETED (2026-09-07)
- metrics/compute.py (21 KPIs from live tables; engineer-minutes/cost clearly-labeled estimates) + render_markdown + record_case_metrics; heal_fleet now records healed/prevented/matching rows; build_final_card gains fleet_matching/healed/prevented.
- Honest findings during build (open): knowledge cases need their own cases row (investigate now ensures it); already-fixed originator scans AT_RISK not AFFECTED (26 healed + 1 approval watch — the better story, tests assert it).
- Files created: metrics/compute.py, tests/test_m27_metrics.py (3 tests).
- Files modified: orchestration/investigate.py (KNOWLEDGE ensure_case), orchestration/heal.py (metric rows), audit/timeline.py (fleet card fields).
- Tests: included in the 155 below.
- Decisions: D30 — estimates multiply real counts by documented rates (never staged totals); anti-hardcode test (metrics must move with data).
- Risks: card before/after keys still cpu/ram/teams-centric; RCA accuracy KPI is supported-share (benchmark accuracy lives in its report).
- Next: M28 only (demos + reset).

## M28 — End-to-end demos + reset — COMPLETED (2026-09-07)
- demo/demo.py (laptop/vpn/learning/knowledge scenarios, --scenario/--seed/--db; composition only) + demo/reset_demo.py (clears data/*.db*, code baselines preserved). Verified runs: laptop PROCEED→SCR-018→26 healed/26 prevented/PRB; vpn with labeled demo-human approval; learning earns L3 on camera (approvals→runs→replay HUMAN NONE); knowledge answers + denies.
- Fixes during build (open): `from typing Any` syntax slip; missing conftest stub in smoke script.
- Files created: demo/demo.py + reset_demo.py, tests/test_m28_demo.py (3 tests).
- Tests: included in the 155 below (determinism twice + reset scoping).
- Decisions: D31 — demos compose tested blocks (no demo-only logic); the human role is played explicitly and labeled when autonomy demands it.
- Risks: demo DB defaults to ./data (gitignored runtime); ns-flow live UI path unexercised here.
- Next: M29 only (reliability + security gate).

## M29 — Reliability + security gate — COMPLETED (2026-09-07)
- Hardening (open fixes from failing tests): investigate degrades unknown-device telemetry to ESCALATE (never crashes); ServiceNow transport failures (any layer) surface as typed ServiceNowError, including status-0 mapping.
- tests/test_m29_gate.py (3 tests): unknown-device escalation, typed transport errors, full spec security checklist (import boundaries on all 11 control_plane modules, refuse classes, approval pause, no-runs-on-abstention, no-resolve-without-verify, KB deny, proof PASS present).
- Files created: tests/test_m29_gate.py.
- Files modified: orchestration/investigate.py (try/except in run_tool), integrations/servicenow/client.py (transport wrap + status-0 mapping).
- Tests: included in the 155 below.
- Decisions: D32 — degraded beats dead (gaps reach RCA as missing evidence); typed errors at every I/O boundary.
- Risks: no retry/backoff yet (documented production hardening); approval expiry is on-read (no sweeper).

## M30 — Documentation + acceptance — COMPLETED (2026-09-07)
- Full README (all required sections incl. Mermaid, limitations, integration path, hardening), docs/DEMO_SCRIPT.md (3-minute run), docs/JUDGE_QA.md (17 answers), docs/ACCEPTANCE.md (checkbox-to-evidence map with two honest live gaps: Gemini loop + PDI calls need keys).
- Files created: README.md (full rewrite), docs/DEMO_SCRIPT.md + JUDGE_QA.md + ACCEPTANCE.md.
- Tests: `python -m pytest -q` → 155 passed. No failures, no skips.
- Decisions: D33 — docs claim only what tests prove; live gaps named, not hidden.
- Risks: none open — see README limitations + M29 hardening notes for production.
- Post-M30 local-run fixes (2026-09-07): neuro_san stub moved to common/neuro_stub.py so demo/demo.py runs outside pytest (tests/conftest.py delegates; suite re-greened); timeline "opened" line no longer shows current state (was rendering "(6)" post-resolution).
- Next: ship it. Run `python -m demo.demo --scenario laptop_teams_memory --seed 42`.
