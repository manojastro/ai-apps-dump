# Progress report — milestones, verification, limitations

Environment: Windows 11, Python 3.12 (uv), Node 24, embedded PostgreSQL 16 (Docker Desktop failed to start on this
machine, so Compose files are provided but were not run). Nothing was deployed.

## M1 — Deterministic foundation ✅
* **Works:** canonical schema (Alembic `0001`), taxonomy v1 (63 items), Decimal parser (Indian/international
  grouping, parentheses, trailing minus, distinct value states), exact scale factors, rules R01–R10 with
  precision-derived tolerance, metrics with special-interpretation handling, 14 synthetic fixtures + ground truth.
* **Verified:** `tests/test_numeric.py`, `tests/test_rules.py` (incl. proofs that insufficient data never becomes a
  pass/fail and that zero/negative denominators are not reported as ordinary numbers).
* **Learned / fixed:** the residual sign convention is `observed − expected`; "not presented at all" (not applicable)
  is distinguished from "presented but unusable" (insufficient data).

## M2 — First complete workflow ✅
* **Works:** upload → integrity → extraction → mapping → normalization → checks → evidence → correction → export.
* **Verified:** `tests/test_workflow_e2e.py` (source page + bbox for each figure, exact base-unit values as strings).

## M3 — Complete spreading ✅
* **Works:** three statements, multiple periods, multi-page continuation, XLSX (multiple sheets, cell refs, cached
  values only), local OCR with word-boundary restoration, notes linked to rows, standalone/consolidated separation,
  restatements, duplicates.
* **Verified:** `tests/test_fixtures_behaviour.py` (12 scenarios), `tests/test_ocr.py`.
* **Fixed along the way:** pdfium is not thread-safe (render under a lock); the bundled OCR model drops spaces
  (dictionary segmentation, characters untouched); garbled figures under a value column are kept as unreadable cells
  instead of merging into the label; formula-text labels in XLSX are kept as untrusted text.

## M4 — Agent coordination ✅
* **Works:** five agents with typed artifacts and execution records; coordinator with fixed transitions and a
  metadata gate; durable leased tasks; idempotent enqueue; bounded retries with backoff; targeted re-extraction;
  per-document budgets; extraction cache; eve workspace (5 agents, typed tools, service auth, signed tool scope,
  default tools disabled).
* **Verified:** `tests/test_durability.py` (crash after writes but before commit → lease expiry → exactly one
  retry → completed; idempotent replay; 3 documents in parallel; failed stage shown as `partial`, retried in the same
  run). eve: `eve info` ready with 0 errors for all five agents; `eve build` OK; a built agent started, rejected
  unauthenticated calls (401), accepted the engine's token, and with no model credentials the engine raised
  `LiveAgentError` (no demo fallback).
* **Fixed:** a race creating the same reporting entity from parallel documents (advisory lock).

## M5 — Analyst workflow ✅
* **Works:** exception queue with fingerprints across versions (auto-resolve, reopen when inputs change), all review
  actions with before/after, version invalidation of approvals and exports, preparer/reviewer four-eyes sign-off on a
  specific version, approval blocked by open critical exceptions, approved/draft snapshot exports.
* **Verified:** e2e test (approved XLSX value = snapshot value; hash in workbook and PDF; later correction locked until
  reopen, then approval stale and export stale), Playwright `web/tests/review-flow.spec.ts` (2 passed).

## M6 — Operational readiness ✅
* **Works:** workspace roles, server-side authz (other tenants get 404 and the denial is audited), protected files,
  upload limits (size, pages, encryption, zip bomb, macro formats), redacted JSON logs, OpenTelemetry spans,
  correlation IDs across web → engine → worker → eve, metrics events, cost view, retention purge, evaluation harness,
  documentation, Compose and Dockerfiles.
* **Verified:** `tests/test_security.py` (10 tests), `tests/test_eval_regression.py`; final run **64 passed** (+1 OCR).

## Definition of done — status
| # | Item | Status |
|---|---|---|
| 1 | Fresh checkout starts with documented setup | ✅ option A verified here; Compose not run (Docker unavailable) |
| 2 | Deterministic demo without paid credentials | ✅ |
| 3 | Real extraction independent of fixtures | ✅ generic layout/OCR/XLSX parsers; real-world accuracy unmeasured |
| 4 | Each figure has a source reference | ✅ citation coverage 1.0 |
| 5 | Unreadable/missing stay unresolved | ✅ |
| 6 | Agents exchange typed, auditable artifacts | ✅ |
| 7 | Numerical checks deterministic | ✅ |
| 8 | Correct a figure and inspect recalculation | ✅ |
| 9 | Corrections invalidate approvals and stale exports | ✅ |
| 10 | Sign-off applies to a specific immutable snapshot | ✅ |
| 11 | Excel and PDF match the snapshot | ✅ |
| 12 | Security, integration, numerical regression tests pass | ✅ |
| 13 | UI distinguishes processing / failure / unresolved / draft / approved | ✅ |
| 14 | Unsupported cases documented | ✅ [cost-and-limitations.md](cost-and-limitations.md) |

Remaining limitations: see [cost-and-limitations.md](cost-and-limitations.md). The biggest are unmeasured real-world
extraction accuracy, live-mode answer quality (no gateway key here), and Docker Compose not exercised on this machine.
