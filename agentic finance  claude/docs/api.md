# API

Engine base URL `http://127.0.0.1:8000`. Interactive OpenAPI docs: `/docs`. The web app calls these through
`/api/engine/*` (BFF adds the bearer token from the httpOnly cookie). All decimals are JSON **strings**.
Errors: `{"detail": …, "correlation_id": …}`. Other tenants' records answer **404**, insufficient role **403**.

## Auth
| Method | Path | Notes |
|---|---|---|
| POST | `/api/auth/login` | `{email, password}` → `{token, user}` |
| POST | `/api/auth/logout` | |
| GET | `/api/me` | user + workspaces with roles |
| POST | `/api/workspaces` | create workspace (creator becomes admin) |

## Workspace, companies, documents
| Method | Path | Role |
|---|---|---|
| GET | `/api/workspaces/{ws}/dashboard` | analyst |
| POST | `/api/workspaces/{ws}/companies` | analyst |
| GET | `/api/companies/{id}` | analyst — documents, revisions, runs, spreads |
| POST | `/api/companies/{id}/documents` | analyst — multipart `file` (PDF/XLSX), optional `title`; integrity checked; duplicate/revision detection; starts a run |
| GET | `/api/documents/{dv}` | analyst — status, runs + tasks, metadata questions, statements, document-level exceptions |
| GET | `/api/documents/{dv}/file` | analyst — original file (audited) |
| GET | `/api/documents/{dv}/pages/{n}?dpi=` | analyst — PNG page render; headers `X-Page-Width-Pt`, `X-Page-Height-Pt` |
| GET | `/api/documents/{dv}/sheet?name=&cell=` | analyst — worksheet cells around a reference |
| DELETE | `/api/documents/{dv}` | admin — deletes file + derived data, recomputes spreads |
| POST | `/api/questions/{id}/answer` | analyst — `{answer}`; resumes the run when all are answered |
| GET | `/api/runs/{id}` | analyst — workflow trace: tasks, agent executions, tools, artifacts, tokens, cost |
| POST | `/api/runs/{id}/retry` | analyst — retry the failed stage (same run; not a new revision) |

## Spreads and review
| Method | Path | Role |
|---|---|---|
| GET | `/api/spreads/{id}` | detail, versions, decisions, blocking reasons |
| GET | `/api/spreads/{id}/grid` | statements (original + standardised labels, per-period cells with state, confidence, validation), metrics, taxonomy |
| GET | `/api/observations/{id}` | full evidence: source location, raw text, transformations, mapping, note, adjustment history, other sources |
| GET | `/api/spreads/{id}/validations?version=` | rule results of a version |
| GET | `/api/spreads/{id}/exceptions` | review queue (spread + document level) |
| POST | `/api/spreads/{id}/actions` | `{action, reason, …}` — `correct_value`, `change_mapping`, `accept_mapping`, `reject_mapping`, `confirm_unit`, `confirm_period`, `mark_unresolved`, `add_adjustment`, `accept_exception`, `request_reextraction` |
| GET | `/api/spreads/{id}/adjustments` | history |
| POST | `/api/spreads/{id}/submit` | preparer submits current version |
| POST | `/api/spreads/{id}/approve` | reviewer; `{version}` must equal current; four-eyes; blocked by open critical exceptions; creates approved snapshot + files |
| POST | `/api/spreads/{id}/reopen` | reviewer |
| POST | `/api/spreads/{id}/exports` | draft export (labelled unreviewed) |
| GET | `/api/spreads/{id}/exports`, `/api/exports/{id}`, `/api/exports/{id}/download/{xlsx|pdf}` | downloads carry `X-Snapshot-Hash`, `X-Snapshot-Stale` |

## Operations
`GET /api/health` (mode, OCR provider, versions) · `GET /api/taxonomy` · `GET /api/workspaces/{ws}/metrics` ·
`GET /api/workspaces/{ws}/audit` (reviewer) · `GET /api/workspaces/{ws}/exports` · `GET /api/workspaces/{ws}/adjustments` ·
`POST /api/workspaces/{ws}/retention/purge` (admin).

## Internal agent tools (eve → engine)
`/internal/tools/*` require `Authorization: Bearer $SPREADLENS_AGENT_TOOL_TOKEN` **and** `X-SpreadLens-Scope`
(HMAC-signed, expiring, names workspace + run). Read-only: taxonomy, row context, note, calculation, quote check.

## eve agents (live mode)
Each agent exposes eve's `/eve/v1` API (`POST /eve/v1/session` with `message`, `outputSchema`, `clientContext`;
NDJSON stream). Only the engine's service bearer token (or the local dev TUI) is admitted.
