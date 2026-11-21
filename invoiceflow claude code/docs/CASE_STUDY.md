# Case study: what broke while building InvoiceFlow, and what changed

Every item below happened during this build (2026-10-25). Each one gives the symptom, how
it was found, and the fix.

## 1. The spec was already out of date

**Found:** reading current Databricks docs in Phase 0. (The web-search tool was failing,
so the docs were read directly in a browser.)

- `ResponsesAgent` + MLflow AgentServer is now the *legacy* serving path.
- Vector Search was renamed AI Search, with a new SDK.
- Free Edition allows 3 Apps, not 1.
- Agent Bricks was not listed as unsupported.

**Changed:** ADR 0001 records the corrections. ADR 0007 runs the graph as a job, keeps a
`ResponsesAgent` wrapper, and defers serving. **Lesson:** verify the platform before
designing to it.

## 2. "Open-weight only"

**Found:** `databricks serving-endpoints list` returned 12 endpoints, none of them GPT,
Gemini or Claude. **Changed:** the agent's quality bar was set for open-weight models, and
the deterministic-first design limits the damage a weaker model can do.

## 3. An approved rule that could never fire

**Found:** while coding duplicates. The approved near-duplicate rule required equal
normalized numbers, which the exact-duplicate rule already covered. **Changed:** the code
follows the spec's own wording ("different number format"), and the deviation is flagged
in CONTROL_MATRIX.md for Manoj to confirm. **Lesson:** approved text can still be wrong;
surface it rather than implement it silently.

## 4. Two generator bugs that would have corrupted the answer key

- **A partial receipt of a 1-unit line rounded down to zero received.** That is
  MISSING_GRN, not the labelled QTY_OVERBILLED. Found by reading the code before running
  it; fixed by making every line at least 2 units.
- **Exact gross targets were unreachable.** With tax rounding, a single line cannot always
  hit ₹10,00,000.01 at 18% inter-state: the gross jumps from .00 to .02. The first
  fallback (a whole-rupee second line) also failed, because 18% of a whole-rupee amount is
  exact, so the rounding pattern never changed. Found when the generator crashed; fixed by
  stepping the second line's price 13 paise at a time.

**Lesson:** labels come from intent, so generator bugs are label bugs. The generator now
refuses to finish if a scenario's price intent does not come out as designed.

## 5. The retriever answered questions it should not

**Found:** the first retrieval eval. "Which warehouse forklift brand is approved?" scored
above the BM25 threshold on one common word, "approved". **Changed:** abstention now also
needs the best section to contain at least half of the question's content words. **Cost:**
recall@5 fell from 1.000 to 0.964, because one valid question's answer is split across two
sections. Both runs are recorded in ADR 0005. Abstaining is the safer failure in AP, and
the decision was made on the same small eval set, which is disclosed there.

## 6. A hold that would have run without approval

**Found:** an end-to-end agent test (`qty_over_ordered` expected AWAITING_APPROVAL, got
EXECUTED). The case context gave the model the matrix's default action *without the
matcher's findings*, so over-ordered quantities defaulted to HOLD_FOR_GRN (which needs no
approval) instead of REQUEST_CREDIT_NOTE. **Changed:** defaults are now computed from the
actual findings. **Lesson:** "safe" defaults depend on context; this is why the harness
has end-to-end tests for every exception type.

## 7. A fast path that never ran

**Found:** reviewing the graph. "Clean invoice with no vendor text → deterministic path"
never triggered, because every line has a description. **Changed:** vendor text now means
notes, remarks, or a description that differs from the PO line's own.

## 8. Citations in the wrong order

**Found:** the first smoke run cited `AP-POL:§8.1` (holds) for a clean invoice. Citations
were offered to the model in alphabetical order, not in retrieval rank. Fixed. The stub
model still cites weakly (60.2% relevant), and the eval reports that rather than hiding it.

## 9. Things the environment would not do

- **Docker Desktop would not start from the build session.** The Postgres integration tests
  were written but not run locally, so CI runs them against a `pgvector` service
  container instead.
- **The command-safety check failed for a while.** The "tests first, see them fail" step
  could not be shown for the core. Mutation checks were added instead: 8 deliberate bugs,
  all caught.
- **Windows kept SQLite files open,** so temporary eval directories could not be deleted.
  Cleanup errors are now ignored for those directories.

## 10. The first run on the real workspace

- **Parity timed out after almost 2 hours.** The per-record reader issued about 1,500 SQL
  statements, and each took about 5 s on the Free Edition 2X-Small warehouse; one finally
  hit the SDK's 5-minute retry limit. **Changed:** batch work reads each table once
  (`Snapshot`, 8 statements). Parity now compares every record and label in about 2
  minutes, with a per-record sample kept to cover the online path.
- **The AI Search client refused the CLI login.** From a laptop it only accepts a personal
  access token or a service principal. Rather than mint a token, the adapter moved to the
  Databricks SDK's vector_search services, which use the existing OAuth login.
- **The CLI's PATH was missing in fresh shells,** and the SDK failed with "cannot configure
  default credentials". It shells out to `databricks auth token`, so the fix was the PATH.
- **AI Search never abstains.** It returns the nearest sections even for "Which forklift
  brand is approved?". Recorded as open work, not tuned on the eval set (ADR 0005).

## 11. Report bugs caught before publishing

A placeholder expression in the baseline column of the eval report, and recall@k showing
`None` (integer dict keys become strings in JSON). Both were caught by reading the
generated report before committing it. **Lesson:** read generated evidence as critically as
code.
