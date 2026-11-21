# Taxonomy, normalization and rules

## Taxonomy `spreadlens-tax-1.0`
Defined in `engine/spreadlens/taxonomy/taxonomy_v1.yaml` (63 items). Each item: `code`, `label`, `statement`,
`unit` (`monetary`/`eps`), `period` (`instant`/`duration`), `sign` (`positive` magnitude or `signed`), `section`
(where it may appear: `current_assets`, `non_current_liabilities`, `expenses`, `investing`, …), `total`, display
order and synonyms. Not every company must disclose every item. Add a new version by adding a YAML file and
bumping `TAXONOMY_VERSION`; proposals record the version they used.

## Mapping (deterministic scorer, `agents/financial_mapping.py`)
score = label similarity (exact 1.0; spacing-insensitive 0.95; token overlap / containment) + 0.15 when the row's
section matches the item's section − 0.6 when it contradicts (e.g. "Borrowings" under current liabilities can
never become non-current borrowings) − 0.25 when total/subtotal flags differ + 0.03 when the linked note mentions
the item; EPS rows only map to EPS items. Confidence: high (≥0.9, gap ≥0.15), medium (≥0.75, gap ≥0.08), low,
none (<0.55 → unmapped). Two rows claiming one code in a statement: the weaker is left unmapped for review.

## Normalization rules
* Raw text is kept; the parser (`numeric/parse.py`) handles Indian (`12,34,567.89`) and international grouping,
  parentheses and trailing minus as negatives, currency symbols, `%`. Irregular grouping or OCR letters →
  `unreadable`. A dash is `dash_ambiguous` unless the document states that a dash means nil.
* Scales use exact Decimal factors: thousands 10³, lakhs 10⁵, millions 10⁶, crores 10⁷, billions 10⁹.
* Table-level unit statements override document-level ones; conflicting statements become an analyst question.
* Sign: canonical sign is recorded per item; a statement that presents expenses as negative figures is detected
  (≥60 % negative in the expenses section) and flipped with a `sign_flip` transformation.
* EPS, percentages and share counts are never scaled.
* Annual, quarterly, YTD and point-in-time observations are kept separate; only annual/point-in-time enter annual
  comparisons (others raise an info exception).
* Standalone/consolidated and different currencies go to different spreads; no currency conversion.
* When several documents report the same item and period: analyst adjustment > restated > latest document > higher
  mapping confidence. All versions are kept; differences are surfaced by R10.

## Rules (`rules/engine.py`, ruleset `rules-1.2.0`)
| ID | Check | Severity |
|---|---|---|
| R01 | total assets = total equity and liabilities (or equity + total liabilities, or equity + current + non-current liabilities) | critical |
| R02 | total current assets + total non-current assets = total assets | critical |
| R03 | total current + non-current liabilities = total liabilities | critical |
| R04 | printed component rows = their "Total …" subtotal (from the extracted hierarchy; inner totals replace their children, so nothing is double counted) | warning |
| R05 | revenue − cost of sales = gross profit (only when gross profit is presented) | warning |
| R06 | profit before tax − tax (charge positive, credit negative) = net profit | critical |
| R07 | operating + investing + financing = net change in cash | critical |
| R08 | opening cash + net change + separately reported FX effect = closing cash | critical |
| R09 | cash-flow closing cash = balance-sheet cash ± disclosed reconciling items; otherwise *requires review* | warning |
| R10 | the same item and period agrees across uploaded documents; restatements surfaced, both versions kept | warning/info |

Every result stores: rule ID and version, statement, period, input observation IDs, expression, expected,
observed, exact difference, tolerance and its basis, severity, status, explanation, source references.

**Statuses:** `pass`, `fail`, `not_applicable` (the source structure does not present the inputs at all),
`insufficient_data` (an input exists but is missing for the period, unreadable, ambiguous or the statement is
missing — never turned into a pass or fail), `requires_review`.

**Rounding tolerance** = Σ half a unit of the last printed digit of every rounded input and the total, scaled to
base units (`rules/tolerance.py`). It is derived from source precision only; analyst materiality is a separate
workspace setting and never widens a check. Residuals are stored exactly.

## Metrics (`metrics/ratios.py`, `metrics-1.1.0`)
revenue growth (prior base ≤ 0 → special interpretation; only adjacent annual periods), net profit margin, gross
margin (only if gross profit reported), current ratio, working capital, debt-to-equity (current + non-current
borrowings ÷ total equity; excludes leases; equity ≤ 0 → special), net debt (borrowings − cash and cash
equivalents), OCF ÷ net profit (net profit ≤ 0 → special), free cash flow (OCF − |purchase of PPE|). Each carries
formula, input IDs, period, unit and limitations. EBITDA and debt service coverage are deliberately not computed.
Narrative distinguishes percentage changes from percentage-point changes.
