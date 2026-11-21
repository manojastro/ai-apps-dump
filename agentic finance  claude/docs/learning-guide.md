# Learning guide (plain English)

## Why each agent exists

* **Document Understanding** — before trusting any number we must know whose numbers they are, which statement,
  which year, which currency and unit, and whether they are standalone or consolidated. Getting one of these
  wrong silently corrupts everything after it, so this agent shows its evidence and asks when unsure.
* **Table Extraction** — turns a page or worksheet into rows and cells while remembering *exactly* where each
  cell came from (page + box, or sheet + cell). Without that, nobody can check a figure later.
* **Financial Mapping** — companies call the same thing different names. Mapping to one taxonomy is what makes
  two companies (or two years) comparable. It explains each choice and leaves doubtful rows unmapped.
* **Reconciliation** — when a total does not add up, someone needs a hint about *why*. This agent runs the
  checks (through ordinary code) and suggests causes, but it is not allowed to change a number.
* **Analyst Pack** — reviewers need a short narrative. Every number in it must point to a stored record, and a
  checker throws out sentences whose numbers it cannot find.

## Which tasks use AI and which use ordinary code

| Ordinary code (always) | AI (live mode only, optional) |
|---|---|
| reading PDFs, OCR, reading spreadsheets | confirming document metadata *with quotes* |
| parsing "(1,234.50)" into an exact Decimal | flagging layout problems in suspicious rows |
| converting lakhs/crores exactly | choosing a mapping among offered candidates |
| every validation rule and ratio | suggesting causes for failed checks |
| deciding the workflow's next step, gates, approvals | drafting narrative sentences (then verified) |

In demo mode every AI step is replaced by a deterministic adapter, so the whole product runs without credentials.

## How source evidence follows a figure

1. The extractor records, for a cell: raw text (`2,670.70`), page, bounding box in PDF points (or worksheet + cell),
   method (`pdf_text`, `ocr_local`, `xlsx_cells`) and OCR confidence. This row in `extracted_cells` never changes.
2. Normalization creates an `observation` that copies that location and adds the parsed value, scale, normalized
   base-unit value, canonical code and a `transformations` list (parse → scale ×10,000,000 → any sign flip).
3. Every rule result lists its input observation IDs; every metric does too; every narrative claim lists record IDs.
4. Clicking a figure in the grid calls `/api/observations/{id}`; the UI renders the page and draws the box.
5. The Excel "Source References" sheet repeats the raw text, document, location and transformations.

## How one uploaded document moves through the application

`upload` → integrity checked immediately (type, size, pages, encryption) → file stored under the workspace →
`workflow_run` + first task. The worker then runs, one durable task each:
`integrity → understand → extract → map → await_metadata → normalize → reconcile`.
If metadata is ambiguous the run waits at `await_metadata` ("awaiting confirmation"); the analyst answers in the
UI and the run resumes. At the end the document is "ready for review" and its figures appear in the spread.

## How a correction triggers recalculation

Analyst enters `422.80` with a reason → `analyst_adjustments` row (who, when, why, before, after) →
`observation.current_value` updated (original kept) → `recompute(spread)`: rebuild facts from current values →
rerun every rule and metric → hash differs → new immutable spread version with new results → exceptions re-synced
(new failures opened, fixed ones auto-resolved, previously *explained* ones reopened if their inputs changed) →
older approvals marked stale → older exports shown as stale.

## How durable execution recovers after interruption

Each stage is a row in `workflow_tasks`. A worker claims a row with `SELECT … FOR UPDATE SKIP LOCKED` and sets a
lease. All of the stage's database writes, the "succeeded" mark and the insert of the next task are committed in
one transaction. If the worker dies mid-stage, nothing is committed; when the lease expires another worker claims
the task again (attempt + 1, up to `max_attempts`). Enqueueing uses a unique idempotency key, so replaying a stage
never creates a duplicate next stage, and handlers replace their own earlier output. `test_durability.py`
simulates a crash after all writes but before commit and proves the run finishes correctly.

## How tests detect invented or incorrectly mapped values

* Every numeric observation's raw text must appear in the extracted page text (PDF) or equal the actual
  worksheet cell (XLSX); otherwise it counts as an **invented value** (threshold: 0).
* Cells that ground truth marks unreadable or ambiguous must not carry a number.
* Every row's canonical code is compared with ground truth, including rows that must stay **unmapped**.
* Validation precision/recall compares reported failures with the deliberately injected ones.
* `test_rules.py` proves that missing/unreadable/dash inputs produce `insufficient_data`, never a pass or fail.
