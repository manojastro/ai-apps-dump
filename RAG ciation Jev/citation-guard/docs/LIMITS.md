# Citation Guard: limits

## What Jev is asked, and what it cannot judge well here

Check B asks one question about one passage. It is not built for:

- **Multi-step reasoning.** Claims that need several passages combined ("because X in 4.1.4
  and Y in 7.2, therefore Z") get one passage only, and will tend to land in `says_nothing`
  or review.
- **Arithmetic.** "A NumericDate of 86400 is 2 January 1970" needs computation the passage
  does not state.
- **Dates and time logic.** Expiry and not-before comparisons, leeway windows and time zones
  depend on values outside the passage.
- **Claims that cite the wrong passage but are true elsewhere.** The judge sees only the
  window around the cited quote.
- **Absence claims.** "The RFC never requires X" cannot be shown by one passage.

## Dependence on clean source text

Exact matching only works when the cleaned text is faithful. The cleaner handles RFC page
furniture, form feeds and line-break hyphens. It does not handle PDFs, HTML, tables, or
ASCII-art figures. A new source format needs its own cleaner and its own tests. If cleaning
breaks a sentence, true quotes become `NOT_FOUND` (false alarms), not false passes.

Normalisation is case-sensitive and does not fold punctuation beyond quotes and dashes, so a
generator that "tidies" a quote (changes `MUST` to `must`, drops a comma) fails Check A. That
is deliberate: the quote is supposed to be exact.

## Small sample

- 37 planted claims (19 good, 18 bad), split into dev 19 and test 18. With 9 bad claims on test,
  one claim moves the wrong-pass rate by 11 points.
- Calibration bins hold far fewer than 10 items each, so ECE is not reliable.
- Dev-tuned thresholds on ~19 claims are noisy. Treat them as a check that the tuning works,
  not as production thresholds.
- Generated claims are missing (the generator run was blocked), so the set has no
  claims from real model behaviour yet, only claims written to test specific cases.

## Draft labels

Every label is currently `claude_draft`, written by the same assistant that wrote the
claims and the mock heuristic. Any metric based on these labels is provisional until they are
reviewed with `citation-guard label` (which sets `manoj_reviewed`). Borderline cases to look at:
`u02` (adds a reason), `u06` (adds a benefit), and `b02` ("may still be accepted" against MUST
be rejected).

## The mock judge

`MockJudge` is a word-overlap + RFC 2119 keyword heuristic written for this repo. Its scores
come from code tuned while looking at the planted claims. MOCK results show that the
pipeline runs end to end. They are not evidence about Jev or any model.

## Prompt injection

Source documents are treated as data. The judge state is a JSON object with fixed keys, and the
instructions say to ignore instructions inside the state. This lowers the risk but does not
remove it: a hostile source could still contain text written to sway the judge. Mitigations
in place: Check A is pure code, and the gate is code. A judge can at most move a claim between
PASS / FAIL / REVIEW for claims whose quote really exists. Not yet tested: no injected source
document is in the eval set.

## Cost and latency numbers

Cost per 1,000 claims uses input tokens *reported by the API* and the price stored in
`config.yaml` with its check date. If the API stops reporting tokens, the report says
"unknown" instead of guessing. Latency includes network time from this laptop.
