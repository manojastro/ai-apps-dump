# Citation Guard: design

## Flow

```
answer {claims: [claim, quote, section_id]}
   |
   v
Check A  quote_match.py   normalise quote + doc -> exact substring search
   |  NOT_FOUND ............................ FAIL_FABRICATED_QUOTE (no model call)
   |  QUOTE_TOO_SHORT (<20 chars) .......... HUMAN_REVIEW (no model call)
   |  FOUND_IN_CITED_SECTION / FOUND_ELSEWHERE
   v
passage window   ~1,500 chars each side, snapped to sentences, clipped to the section
   v
Check B  judges/*.py      one Choice question "relation": supports / contradicts / says_nothing
   v
gate.py                   thresholds from config -> PASS / FAIL_CONTRADICTED / HUMAN_REVIEW
   v
answer result             all PASS -> DELIVER; any FAIL -> BLOCK; else REVIEW (no claims -> REVIEW)
   v
runs/<run_id>/decisions.jsonl   one JSON line per claim
```

## Why code owns the decision

Jev returns probabilities. The verdict is a rule in `gate.py` with thresholds in
`config.yaml`, so:

- the policy is visible, versioned and testable (boundary tests at 0.79/0.80 and 0.49/0.50);
- thresholds can be re-tuned from logged probabilities without new model calls;
- a judge failure can only lead to `HUMAN_REVIEW`, never to a silent `PASS`;
- fabricated quotes are caught by plain string matching, which cannot hallucinate.

## Check A details

- Normalisation (applied identically to quote and document): Unicode NFKC, curly to straight
  quotes, every dash variant to `-`, whitespace runs to one space. Matching is
  **case-sensitive**, because `MUST` and `must` differ in an RFC.
- Search order: cited section first, then the whole document. A hit outside the cited
  section is `FOUND_ELSEWHERE`: it still goes to Check B and is flagged in the log
  (`found_section_id`). Table-of-contents hits rank below body text.
- `normalize()` returns an index map, so every match points back to an exact span of the
  cleaned document (`offsets.start/end`) and to a raw line of the download (`offsets.raw_line`).
- `rapidfuzz` only fills `closest_fuzzy_score` for `NOT_FOUND` quotes, for debugging.
  It never makes a quote count as found.
- A quote that is not found fails even when it is short. Only *found* short quotes go to
  review, because the risk with short quotes is accidental matches.

## Ingest details

- Removes page footers (`Jones, et al. ... [Page N]`), form feeds and repeated page headers
  (`RFC 7519 ... May 2015`). A paragraph split by a page break is rejoined.
- Hyphen rejoin: RFCs break lines only at real hyphens (`case-` / `sensitive`). The line break
  is removed and **the hyphen is kept** (`case-sensitive`). Removing it would corrupt
  compounds such as `case-sensitive` and `RSAES-PKCS1-v1_5` and break exact matching.
- Sections come from column-0 headings: numbered (`4.1.4.`), appendix (`Appendix A.`, `A.1.`)
  and unnumbered (`Abstract`, `Acknowledgements`). RFC 7519 gives 57 sections
  (50 numbered/appendix + front and back matter).
- New documents: add an entry to `data/sources/manifest.yaml`. Only the `rfc_text` format
  exists today; another format needs its own cleaner.

## Check B details

- State is a JSON object with three labelled keys: `CLAIM`, `QUOTE`, `SOURCE PASSAGE`. A JSON
  object keeps source text structurally apart from the claim, so text in the passage cannot
  pose as a new label.
- Instructions tell Jev to judge only from the passage, to read RFC 2119 keywords strictly,
  and to treat everything in the state as data.
- Criteria carry short descriptions (the SDK accepts `str | None` per label).
- Async client, concurrency capped by `run.concurrency` (default 5).

## Threshold policy

- Starting values: PASS if P(supports) >= 0.80; FAIL_CONTRADICTED if P(contradicts) >= 0.50;
  otherwise HUMAN_REVIEW. PASS is checked first (the two cannot both hold, since the
  probabilities sum to 1).
- `citation-guard report` grid-searches thresholds on the **dev split only**: keep dev
  wrong-pass rate <= `tuning.max_wrong_pass_rate` (default 0), then minimise false alarms,
  then review rate; ties go to the stricter pair. Test-split results are shown with both
  the config thresholds and the dev-tuned ones.
- With ~19 dev claims, one bad claim can push the tuned pass threshold to the top of the grid
  ("review everything"). That is the policy working as written on too little data. Do not
  copy tuned thresholds into config until the dev set is larger and reviewed.
- The LLM baseline is tuned separately. Its numbers are prompted guesses, not calibrated.

## Splits and labels

- `claims.jsonl` records carry `label_source` (`claude_draft` / `manoj_reviewed`) and
  `split` (`dev` / `test`), assigned 50/50 at random with seed `run.seed`, stratified by label.
- A claim keeps its split forever, so adding claims later never moves an item between
  dev and test.
- `build-claims` keeps `manoj_reviewed` labels when the claim and quote text are unchanged.
- Generated claims with no draft label get `fabricated` automatically when Check A cannot
  find their quote. Others stay unlabelled (excluded from metrics) until labelled.

## Run modes

| Mode | Meaning |
|---|---|
| `LIVE` | Judge calls a real external model API (Jev or the LLM baseline) |
| `MOCK` | Offline heuristic `MockJudge`; numbers say nothing about Jev |
| `NO-MODEL` | String-match baseline: Check A only, every found quote passes |

The brief asked for LIVE or MOCK on every run. The string-match baseline is neither (it is
real but calls no model), so it gets its own label instead of a misleading one.

Failure handling: authentication, permission and not-found errors abort the whole run, as
does a run where every judge call fails. Writing those out as per-claim `HUMAN_REVIEW`
would look like a result. Other per-claim errors give `HUMAN_REVIEW` with `error` set.

## SDK: what was verified and what differs from the brief

Read on 2026-11-21: quickstart, sdk/python, usage/basic, types/questions, types/responses,
retries, exceptions, constants and models. Installed `typesafe-sdk==0.7.5` with `uv add typesafe-sdk`.

| Brief said | Docs / SDK say | What the code does |
|---|---|---|
| `client.models.list()` | Returns `ListModelsResponse`; iterate `.models` (`name`, `description`, `release_date`) | `list_models()` iterates `.models` |
| Pick a concrete version from `models.list()` | `GET /v1/models` "currently lists the aliases"; versioned IDs are accepted whether listed or not. Current: `jev-1.14.0` (2026-10-14) and `jev-1.13.0` | Pinned `jev-1.14.0` from the models page. `models.list()` not run: no key |
| `criteria` values may be `None` | `Mapping[str, Content | None]`: description strings allowed | Short descriptions per label |
| Retries via `RetryPolicy` | `RetryPolicy(max_retries=2, backoff..., http_statuses, timeout=30.0)`, passed as `retry=` to the client or per call | `retry=RetryPolicy(max_retries=3, timeout=30)` |
| `result.choices["relation"]` | Same; also `result.answers`, `result.model` (versioned id that answered) | Logs `result.model` as `model` |
| Missing key raises `TypeSafeError` at creation | Confirmed: `TypeSafeError: No API key was provided...` | `eval --judge jev` stops before writing anything |
| Default model `jev-latest` | `DEFAULT_MODEL = 'jev-latest'`, override with `TYPESAFE_DEFAULT_MODEL` | Client always gets `model=` explicitly; aliases rejected |
| — | `DEFAULT_TIMEOUT = 10.0` s per HTTP operation | `timeout=30` passed explicitly |

Price used for estimates: $0.042 per million input tokens, output free (models page,
checked 2026-11-21), stored in `config.yaml` with its date.

## Auth for later Foundry integration (not built)

The local API has no auth and binds to 127.0.0.1. Before Foundry uses it:

- Caller identity: service-to-service tokens (OIDC / workload identity), checked on every
  request; no shared static keys.
- Authorisation: per-tenant access to `doc_id`s. A caller must not verify against
  documents it cannot read, or the API leaks source text through passages.
- Secrets: `TYPESAFE_API_KEY` and provider keys from a secret manager, never env files in images.
- Limits: per-caller rate limits and a per-request cap on claims (the run cap already
  exists as `max_api_calls_per_run`) to bound Jev spend.
- Audit: keep `decisions.jsonl`-style logs with caller id and request id, without
  logging full answer text where it may hold user data.
