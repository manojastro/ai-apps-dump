# Worked example — keyword-overlap faithfulness

`Faithfulness = grounded claims ÷ total claims in the answer.`
(A claim is one sentence. Grounded = shares ≥1 keyword with the context.
Stopwords like "the", "in", "and" don't count.)

## Setup

- Question (AQ-003): "How do I clear a stuck print queue on a Windows till?"
- Context (DOC-PRINT-001): "Open Services, restart the Print Spooler, then
  delete jobs in the printer queue folder."
- Answer: "Open Services and restart the Print Spooler. Then delete jobs in
  the printer queue folder. Penguins migrate in winter."

## Claim by claim

| # | Claim | Keywords overlapping context | Grounded? |
|---|---|---|---|
| 1 | "Open Services and restart the Print Spooler" | open, services, restart, print, spooler | yes |
| 2 | "Then delete jobs in the printer queue folder" | delete, jobs, printer, queue, folder | yes |
| 3 | "Penguins migrate in winter" | (none — penguins/migrate/winter absent) | no |

Faithfulness = 2 ÷ 3 = **0.667**.

## Why it matters

The stub target returns the reference answer verbatim for most rows
(score ≈ 1.0) but emits generic filler ("follow ITIL best practices…") for
every 9th record, which scores ≈ 0.0 against the reference context. That is
why the mock full-run faithfulness lands near 0.85–0.9 instead of 1.0 —
the metric visibly reacts to ungrounded output, like a monitor that actually
pages when the service degrades.
