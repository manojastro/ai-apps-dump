# Build Log

## 2026-08-24 — Portfolio initialization

- Created a new portfolio root to preserve the existing `ai-agent-portfolio` and `datanalyis agent` directories.
- Chose independently runnable Python/FastAPI services with project-local SQLite defaults and adapter boundaries. PostgreSQL-compatible configuration remains an expansion path; SQLite keeps every demo credential-free.
- Chose deterministic mock reasoning as the default so each investigation is reproducible without an LLM key. OpenAI-compatible provider settings are exposed for later expansion.
- Started all five projects as independent vertical slices rather than completing one project before scaffolding the others.

## 2026-08-24 — Project 4 first vertical slice

- Implemented seven labeled streaming failure scenarios behind a `StreamingAdapter` interface and a deterministic, evidence-bound `ReasoningProvider` fallback.
- Initial validation tests exposed eager construction of every scenario's check dictionary; unrelated after-state fields raised `KeyError`. Changed validation to scenario-specific branching.
- Initial Windows tests exposed unclosed SQLite handles. Replaced raw connection context use with an explicit commit/rollback/close context manager.
- Verification after fixes: 7/7 automated tests passed; the seven-scenario demo produced 7/7 exact RCA matches and seven `VALIDATED` outcomes.
- A live Uvicorn smoke test returned `200` for health/dashboard/metrics, `409` for execution before approval, and `VALIDATED` after explicit approval and synthetic execution.
- `docker compose config -q` passed. Image build could not start because the local Docker Desktop Linux engine pipe was unavailable. No Docker success is claimed.
- Independent acceptance review found that validation returned a canned healthy fixture even for a wrong allow-listed action. Replaced it with incident-specific, action-aware simulator execution and independent state recollection.
- Added atomic conditional state transitions, explicit retryable `EXECUTION_FAILED` and `VALIDATION_FAILED` states, persisted adapter failure evidence, wrong-action and transient-failure negative tests, schema migration versioning, and labeled lag-detection/MTTD/MTTR metrics.
- Added exact action-parameter matching and role-separated secure mode with distinct viewer, approver, and executor keys; approval identity is server-derived in secure mode.
- Re-verification after the audit fixes: 11/11 tests passed; the seven-scenario benchmark again produced 7/7 RCA matches and seven validated remediations.

## 2026-08-24 — Project 2 first vertical slice

- Implemented a synthetic AWS adapter with a 31-day workload replay. The cheapest static recommendation is blocked as `CRITICAL` because the monthly peak projects 134% CPU and 487 ms latency against a 250 ms SLO.
- A safer bounded change passes shadow guardrails, produces inert Terraform text, requires approval, and records $113.50/month realized simulated savings.
- Verification: 13/13 tests passed, compilation passed, and a live port 8102 workflow finished `VERIFIED` with `unsafe_prevented=true` and validation passing.
- Docker Compose configuration passed; image build was blocked by the unavailable Docker Desktop Linux engine.

## 2026-08-24 — Project 3 first vertical slice

- Implemented operational and silent logical pipeline-failure simulations, eight data-quality metrics, lineage, evidence-based RCA, bounded dbt-style SQL proposals, and shadow before/after validation.
- A live silent-failure run preserved the pipeline's operational `SUCCESS` signal while detecting the logical incident; shadow quality improved from 0.9194 to 1.0 and the approved simulated deployment resolved the incident.
- Verification: 11/11 tests passed, compilation passed, live health/readiness/dashboard/metrics and approval-gated workflow checks passed on port 8103.
- Docker Compose configuration passed; image build was blocked by the unavailable Docker Desktop Linux engine.

## 2026-08-24 — Project 1 first vertical slice

- Implemented nine deterministic agent scenarios and thirteen rule findings spanning loops, cost waste, wrong tools, hallucinated success, partial completion, latency, unsafe action, and retrieval failure.
- Added independent claimed/expected/verified outcome checks, typed evidence-linked RCA, immutable audit triggers, approval-gated allow-listed execution, shadow validation, and a current-versus-candidate release gate.
- Verification: 15/15 tests passed, compilation passed, and a live port 8101 smoke test confirmed pre-approval execution is blocked and a regressed candidate release is blocked.
- Interactive dashboard QA confirmed approval/execution and release-block flows with no browser console errors.
- Docker Compose configuration passed; image build was blocked by the unavailable Docker Desktop Linux engine.

## 2026-08-24 — Project 5 first vertical slice

- Implemented three inert source fixtures, deterministic findings and exploitability, typed release risk, exact allow-listed remediation, reviewed-source/workspace hash verification, and static/AST-only validation without executing fixture or generated code.
- Added explicit operator authorization, approval gating, immutable audit triggers, schema migration tracking, a domain dashboard, and objective finding/remediation/regression evaluation.
- Verification: 16/16 tests and compilation passed. A live port 8105 workflow blocked remediation before approval and viewer approval, then removed the finding (1 to 0), reduced simulated release risk from 92 to 10, and reached `VALIDATED` with zero security/test regressions.
- Docker Compose configuration passed; image build was not attempted because the Docker Desktop Linux engine was already known unavailable.

## 2026-08-24 — Cross-project adversarial acceptance review

- Reopened Project 2 because workload/shadow evidence and realized savings were partly predetermined rather than derived from the selected action and observed synthetic history.
- Reopened Project 3 because predicted RCA reused ground truth, shadow validation bypassed the proposed SQL artifact, and missing credentials defaulted to an authorized role.
- Reopened Project 5 because caller-controlled/missing roles could authorize changes, approvals were not bound to the reviewed fixed-source hash, AST checks allowed unreviewed side effects, and exploitability evaluation reused its label.
- These green-test/false-success findings are treated as release blockers. Status remains in progress until evidence-derived implementations and reproducing negative tests pass.

## 2026-08-24 — Project 2 acceptance fixes

- Replaced predetermined analysis with adapter-sourced workload history, threshold-driven anomaly detection, computed rate-card/capacity projections, and selection of the lowest-cost proposal that passes a real 31-day daily shadow profile.
- The static cheapest option is now computed and blocked at 336% capacity demand and 1000 ms projected latency; the scheduled-elastic option is selected at an 84% peak with $118.68 estimated savings.
- Simulated apply independently observes $160.99 post-change cost and derives $119.01 realized savings plus 0.997219 savings accuracy. Observed SLO failures now roll back and fail evaluation.
- Acceptance verification: 19/19 tests, compilation, Docker Compose configuration, and a live port 8102 `VERIFIED` workflow all passed.

## 2026-08-24 — Project 3 acceptance fixes

- Decoupled RCA prediction from stored ground truth; the deterministic reasoner now predicts from persisted evidence before evaluation compares the separate label.
- Bound approval to the exact SQL hash, execute that artifact in isolated in-memory SQLite, profile its actual output, and independently rerun the deployment against fresh source state.
- Closed anonymous/default-operator mutations with credential-derived roles, gated on every quality dimension, and calculated referential integrity from transformed output.
- Acceptance verification: 19/19 tests, compilation, Docker Compose configuration, and a live port 8103 workflow with auth denials and final `RESOLVED` state all passed.

## 2026-08-24 — Project 5 acceptance fixes

- Replaced caller-supplied/missing roles with separate verified approver and executor credentials; the same identity cannot perform both operations.
- Approval now immutably binds the action ID, patch SHA-256, and fixed-source SHA-256. Execution rechecks approval, input, workspace, and output hashes.
- Strengthened AST validation to enforce exact signatures, allow-listed imports/calls, and no executable top-level statements. Scanner and exploitability predictions are now derived without reading their evaluation labels.
- Acceptance verification: 23/23 tests, compilation, Docker Compose configuration, and a live port 8105 flow passed. Negative tests cover credential bypass, identity overlap, changed patches, immutable approvals, top-level side effects, signature drift, and label mutation.

## 2026-08-24 — Project 1 adversarial review

- Reopened Project 1 because the outcome verifier trusted state embedded in the same trace, post-action policy validation was unconditional, approvals were not payload-hash-bound, the evaluator could pass with a critical detector disabled, and the version gate compared canned profiles instead of executing both versions.
- Adversarial probes demonstrated forged/stale/missing artifact state passing, wrong allow-listed payload mutation after approval, loop-detection accuracy of zero with an overall passing benchmark, and a candidate runner failure that did not affect the release gate.
- Acceptance now requires separate artifact-state collection, generic server-owned outcome contracts, causal policy application/observation, immutable approval binding, per-class gates, and same-dataset executed version comparisons.

## 2026-08-24 — Project 4 acceptance re-audit

- Reproduced and passed wrong-action, wrong-parameter, transient execution/validation retry, legacy migration, role separation, and lag/MTTD/MTTR probes.
- Fixed stale state-machine/security documentation, configured bare pytest discovery, and added in-memory viewer/approver/executor key inputs so the dashboard remains usable in secure mode without persisting credentials.
- Final re-audit verification: 11/11 tests passed through both the documented unittest script and bare pytest discovery.

## 2026-08-24 — Project 2 acceptance re-audit

- Reopened Project 2 again after a targeted workload probe showed the shadow replay used the observed peak while generated Terraform still hard-coded day 28, allowing artifact/simulation divergence and drifting peaks.
- A stateful adapter probe also showed `ROLLED_BACK` was a status assertion without a restore call or post-rollback observation, and subsequent runs returned a cached incident before reevaluating current thresholds.
- Acceptance now additionally requires workload-bound schedule artifacts, refusal of non-recurring peak schedules, executed and independently observed rollback with corrected savings, and per-event history reevaluation.

## 2026-08-24 — Project 3 acceptance re-audit

- Reopened Project 3 after a legacy-schema probe showed migration backfilled an approval hash from the current SQL, which could bless a post-approval mutation instead of requiring review.
- A fresh adapter probe also showed deployment profiling forced operational `SUCCESS`, allowing fresh operational failure to resolve when cached rows still scored well.
- Acceptance now additionally requires legacy approvals to be invalidated for reapproval and fresh operational success to be an explicit deployment validation gate.
- Fixed migration to invalidate legacy approvals instead of backfilling trust, and made fresh `SUCCESS` status mandatory before deployment can resolve. Fresh failure/timeout results are persisted and audited.
- Re-verification: 22/22 tests, compilation, Docker Compose configuration, and an authenticated live port 8103 workflow passed.

## 2026-08-24 — Project 1 acceptance fixes

- Split trace production from a genuinely read-only artifact-state provider and moved acceptance criteria to a server-owned contract covering every required key, artifact identity, checksum/size, and freshness interval.
- Added a persistent action-specific policy simulator with observed before/after versions, failure/rollback behavior, and independently calculated post-action validation.
- Bound approvals to canonical SHA-256 payloads and enforced catalog/incident/risk/tool consistency. Added per-critical-class evaluation gates and same-dataset execution of current and candidate versions through an injectable runner.
- Corrected duplicated/mislabeled metrics and added adversarial cases for forged/stale/missing artifacts, contract weakening, payload mutation, failed rollback, missing loop detection, and failed/incomplete candidate runners.
- Acceptance verification: 31/31 tests, compilation, Docker Compose configuration, and a live port 8101 smoke passed. Policy version advanced 0 to 1 only after bound approval and observed validation; the regressed candidate was blocked.

## 2026-08-24 — Project 2 re-audit fixes

- Bound the typed plan, simulator, and Terraform cron to the workload-derived recurring `peak_day`, added plan/Terraform SHA-256 alignment checks, and made drifting peaks reject scheduled elasticity in favor of the safe retain-current option.
- Every run now reloads histories and reevaluates thresholds before content-fingerprint deduplication.
- Added adapter restore plus independent post-rollback observation. `ROLLED_BACK` is recorded only after baseline is verified; otherwise the outcome is blocked/rollback-failed, with final-state savings and evaluation corrected.
- Re-verification: 22/22 tests, compilation, Docker Compose configuration, diff checks, and a live port 8102 `VERIFIED` workflow passed. Negative cases cover day-15 binding, drifting peaks, stateful rollback with zero savings, and a fresh below-threshold event after a previous incident.

## 2026-08-24 — Project 5 acceptance re-audit

- Reopened Project 5 because AST checks allowed extra destructive SQL/curl behavior beside an allow-listed call, secret-environment exfiltration with a safe string hidden in a docstring, and failed/crashed validation left the patch applied.
- The displayed patch preview was not itself verified against its attested hash, and fail-closed legacy approvals were left in an unrecoverable `APPROVED` state.
- Acceptance now additionally requires exact scenario AST structure/arguments, exact displayed-patch binding, rollback on every validation failure/exception, and explicit reapproval-required legacy migration.

## 2026-08-24 — Project 3 final trust-boundary review

- Reopened Project 3 because changing proposal SQL, its hash, and the approval binding together could bypass application-level equality checks; approved artifacts need database-level immutability.
- Also found that the no-key configuration still allowed the demo POST route to mutate workflow state despite documentation claiming mutation routes were locked.
- Final acceptance requires immutable approved proposal/approval records plus fail-closed no-key mutation behavior with reproducing tests.
- Added ordered migration 004 and SQLite triggers that prevent update/delete of approved proposal SQL/hashes and bound approval records, while preserving append-only reapproval after legacy invalidation.
- Demo/bootstrap POST mutations now require configured verified credentials; no-key mode is read-only.
- Re-verification: 23/23 tests, compilation, Docker Compose configuration, live authenticated workflow, migrations 001–004, and direct database tamper probes all passed.

## 2026-08-24 — Project 5 re-audit fixes

- Replaced permissive call-name/string checks with exact canonical AST policies covering module shape, signatures, imports, call counts/arguments, function bodies, and return semantics for each scenario.
- Bound the persisted/displayed patch-preview bytes at approval and execution. Legacy approvals now migrate to `REAPPROVAL_REQUIRED` and accept a new immutable attestation.
- Failed or crashed validation now atomically records failure/audit/evaluation state and restores both workspace and persisted source to the reviewed before-state.
- Re-verification: 31/31 tests, compilation, Docker Compose configuration, and a live port 8105 workflow with role denials, separate approval/execution, structural validation, and final `VALIDATED` state passed.
- Independent narrow replay found no remaining P1/P2 issue: 31/31 full tests and 8/8 former-blocker probes passed, including extra SQL/curl/environment exfiltration rejection, patch-preview mutation, validation failure/exception rollback, and legacy reapproval.

## 2026-08-24 — Project 2 final approval-integrity review

- Reopened Project 2 after a narrow replay changed both the validated plan and Terraform schedule from day 15 to day 28 before approval; approval and execution still succeeded because reviewed artifact hashes were not stored in the approval record.
- Final acceptance requires immutable approval attestation of the exact plan and Terraform hashes, execution-time recomputation, protected validated/approved artifacts, and legacy reapproval migration.
- Added version-2 approval bindings for exact action/recommendation/validation/reviewer identity plus action, plan, and Terraform SHA-256 attestations. Approval and execution both recompute them.
- Database triggers protect validation/approval rows and validated recommendation artifacts; legacy approvals become `REAPPROVAL_REQUIRED` without backfilling trust. Generation-based reset preserves governed history.
- Re-verification: 29/29 tests, compilation, Docker Compose configuration, and live port 8102 health/reset/demo/approval/apply/dashboard passed with matching hashes, `BOUND` attestation, `SUCCEEDED`, and $119.01 observed savings.

## 2026-08-24 — Project 1 final authority fixes

- Persisted server-observed verification windows so trace-supplied timing cannot widen artifact freshness checks.
- Rollback now uses a separate read-only SQLite policy provider for authoritative state readback; a lying/no-op adapter yields `ROLLBACK_FAILED`.
- Version comparison now issues server nonces and case/run specifications, consumes raw traces/artifact snapshots, verifies requested agent version and unique run/case IDs plus version/run digests, and reconstructs metrics server-side. Baseline evidence replay/relabel is blocked.
- Legacy blank-hash approvals migrate to `REAPPROVAL_REQUIRED`; canonical action bindings are backfilled and a fresh bound approval can execute.
- Final verification: 35/35 tests, compilation, Docker Compose configuration, diff checks, and live port 8101 workflows passed. The regressed candidate blocked; the safe candidate passed with 18 unique version-run IDs.
- A deeper replay demonstrated that an untrusted runner could rewrite the full evidence envelope and recompute public hashes. Public hashes prove consistency, not execution provenance. Final POC acceptance therefore requires the exact server-owned registered benchmark executor; external runners must fail closed until signed runner attestation exists.
- Also reopened approval persistence because legacy approval rows could be mutated back to `APPROVED`; append-only database immutability is required.
- The POC now accepts only the exact server-registered built-in benchmark executor; injected, subclassed, or separately instantiated runners block before invocation. Version artifact digests and raw case/run binding remain checked, while documentation explicitly reserves remote runners for a future signed-attestation integration.
- Migration 004 makes `APPROVED` and `REAPPROVAL_REQUIRED` approval rows immutable; fresh reapproval is append-only.
- Final re-verification: 37/37 tests, compilation, focused trust probes, Docker Compose configuration, and live port 8101 smoke passed. The safe candidate passed with `trusted_runner=true`; the regressed candidate blocked.
