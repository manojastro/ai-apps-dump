# Data dictionary

All tables carry `workspace_id` (tenant isolation). IDs are 32-char hex. Money is `NUMERIC(28,6)`; ratios `NUMERIC(28,10)`.
Schema: `engine/migrations/versions/0001_initial_schema.py`; models: `engine/spreadlens/models/`.

## Tenancy and governance
| Table | Purpose |
|---|---|
| `organizations`, `workspaces` | workspace has `retention_days`, `materiality_pct` (analyst materiality, separate from rounding tolerance) |
| `users`, `memberships` | role per workspace: `analyst` (preparer), `reviewer`, `admin` |
| `auth_sessions` | SHA-256 of opaque session tokens, expiry |
| `audit_events` | action, target, outcome (`ok`/`denied`/`error`), correlation ID; never document content |
| `metric_events` | operational counters (stage durations, OCR pages, retries, failures, mapping coverage, export failures) |

## Documents and extraction
| Table | Key fields |
|---|---|
| `companies` | `supported`, `unsupported_reason` |
| `reporting_entities` | company + name + `scope` (standalone/consolidated) |
| `documents` / `document_versions` | a new upload of the same title = new `version_no` (revision); `sha256`, `storage_key`, `integrity_status`, `duplicate_of_id`, `processing_status`, `metadata_json` (confirmed answers) |
| `statements` | per document version: type, scope, currency, scale, framework, pages/sheet, `columns` (period end, duration, restated), sign convention, method, parser version |
| `extracted_rows` | original label, section path, level, header/total flags, `parent_total_row_id` (hierarchy), note ref, unit type, page/bbox |
| `extracted_cells` | **immutable**: raw text, value state, parsed Decimal, decimals (precision), parse notes, page/bbox or sheet/cell, method, OCR confidence |
| `note_sections` | note ref, title, text |
| `extraction_cache` | (workspace, sha256, parser version, config hash) → raw extraction artifact |
| `reporting_periods` | entity, period end, duration, start |

## Financial model
| Table | Key fields |
|---|---|
| `canonical_line_items` | taxonomy version, code, label, statement, unit type, period type, sign, total |
| `mapping_proposals` | row, proposed code (null = unmapped), rationale, confidence, score, alternatives, evidence, status (`proposed/accepted/changed/rejected/unresolved`), decided code, agent execution |
| `spreads` | review unit = entity + scope + currency; `current_version_no`, `review_status` |
| `spread_versions` | immutable version (= statement-set version) with content hash, per-statement hashes, reason |
| `observations` | see below |
| `calculation_results` | rule/metric per spread version: rule id+version, inputs, expression, expected, observed, exact difference, tolerance + basis, severity, status, explanation, limitations |
| `validation_exceptions` | review queue: fingerprint (stable across versions), category, severity, status (`open/explained/resolved/superseded`), agent explanation, resolution, first/last seen version |
| `analyst_adjustments` | action, field, before, after, reason, user, version before/after |
| `review_decisions` | `submit_for_review/approve/reopen`, version, user, role, stale flag + reason, snapshot |
| `export_snapshots` | frozen snapshot JSON, content hash, status (`draft/approved`), file keys, render status |

### Observation fields (every financial observation)
unique `id`; `document_version_id` + `source_sha256`; `entity_id`; `statement_type`; `scope`; `framework` (as
reported or `unknown`); `period_start`/`period_end`; `duration` (`annual`, `point_in_time`, `quarterly`, `ytd`);
`original_label`; `canonical_code`; `raw_text`; `parsed_value`; `original_currency`; `original_scale`;
`normalized_value` + `normalized_scale`; `current_value`/`current_state` (after corrections); `origin`
(`reported`/`adjusted`; derived values live in calculation results and snapshot lines marked `derived`);
`version_kind` (`original`/`comparative`/`restated`); `is_preferred`; page + bbox or sheet + cell; `extraction_method`;
`confidence` (mapping, OCR, parse); `review_status`; `transformations` (ordered history).

### Value states (kept distinct everywhere)
`value`, `zero` (reported zero), `missing` (blank), `unreadable`, `not_applicable` ("n/a"), `dash_ambiguous`
(a dash whose meaning the document does not define).

## Workflow
| Table | Purpose |
|---|---|
| `workflow_runs` | kind (`initial/retry/reextraction`), agent mode, state, status (`running/awaiting_input/completed/failed/partial`), budget, usage (model calls, tokens, cost, OCR pages), correlation ID |
| `workflow_tasks` | stage, unique idempotency key, payload, status, attempts/max, lease owner/until, available_at, duration, error |
| `artifacts` | typed agent outputs: type, schema version, producer, content hash, payload |
| `agent_executions` | agent, mode, model, tools used, input/output artifacts, status, retries, tokens, cost, duration, eve session |
| `metadata_questions` | field, statement, question, options, evidence, answer, who/when |
