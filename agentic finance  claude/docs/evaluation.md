# Evaluation (synthetic fixtures)

> **Synthetic only.** All documents are generated for fictional companies by `engine/fixtures/generate.py`.
> These numbers guard against regressions in this repository. They are **not** an estimate of real-world accuracy.

Run: `cd engine && uv run python -m eval.run_eval` (add `--ocr` for the scanned fixture). Thresholds:
`engine/eval/thresholds.yaml`. The pytest wrapper `tests/test_eval_regression.py` fails the build on regression.

## Fixtures (ground truth in `engine/fixtures/ground_truth/manifest.json`)
| # | Fixture | Covers |
|---|---|---|
| 01 | complete company, 3 statements × 2 years + notes | clean digital PDF, parenthesised negatives |
| 02 | image-only scan of BS + IS | scanned statement / local OCR |
| 03 | balance sheet continued on page 2 without a title | multi-page table |
| 04 | XLSX, three worksheets + notes sheet, lakhs, Indian number format | XLSX, Indian numbering, lakh units |
| 05 | BS + IS only | missing cash flow statement |
| 06 | standalone and consolidated in one PDF | scope separation |
| 07 | FY2026 report, FY2025 comparatives restated (revenue, other expenses) | restated comparative + overlapping uploads (with 01) |
| 08 | "INR crores" and "INR lakhs" both declared | conflicting units → analyst question |
| 09 | `6l2.1O` cell and an undefined dash | unreadable cell, ambiguous dash |
| 10 | inventories printed 421.80 instead of 412.80 | arithmetic mismatch (known failure R04, −9.00 crore) |
| 11 | start-up: zero prior revenue, negative equity, net loss; no scope stated | zero/negative denominators, scope question |
| 12 | note containing instructions to an AI agent | malicious document instructions |
| 13 | labels `=HYPERLINK(...)`, `+cmd|...`, `@SUM(...)` | spreadsheet formula injection |
| 14 | fictional co-operative bank | unsupported entity |
| — | duplicate upload of 01; other tenant's user | duplicate uploads, cross-workspace access (integration tests) |

## Latest results (demo mode, 13 non-OCR fixtures, 2026-11-08)
| Metric | Result | Threshold | Counts |
|---|---|---|---|
| Numeric extraction accuracy | 1.000 | ≥ 0.99 | 920 / 920 located cells |
| Row and period association | 1.000 | ≥ 0.97 | 920 / 920 |
| Unit and sign accuracy | 1.000 | ≥ 0.99 | 920 / 920 |
| Mapping accuracy (incl. rows that must stay unmapped) | 1.000 | ≥ 0.95 | 401 / 401 rows |
| Source citation coverage | 1.000 | 1.0 | 1,206 / 1,206 observations |
| Validation precision / recall | 1.000 / 1.000 | 1.0 / 1.0 | TP 1, FP 0, FN 0 |
| Unsupported-value invention rate | 0.000 | 0.0 | numeric values checked against page text / worksheet cells |
| Analyst intervention rate | 0.0025 | — | 3 metadata confirmations (fixtures 08 and 11) |
| Cost | $0.00 | — | no model calls in demo mode |
| Latency | 0.2–1.8 s per digital document | ≤ 20 s | |

Scanned fixture (`pytest -m ocr`): processed end to end with local OCR in ~76 s for two pages; total assets read
exactly as `2670.70`; every OCR cell carries its confidence and bounding box.

Validation precision/recall rests on a single injected failure (fixture 10) plus 12 fixtures that must produce no
failures; add more corrupted variants before relying on these two numbers.
