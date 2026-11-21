# Build Notes & Assumptions

## Ambiguous choices made during build

### Gemini model IDs
The spec references `gemini-3.5-flash` and `gemini-3.1-flash-lite`, which are not available as of July 2026. Defaults in `.env.example` use `gemini-2.5-flash` (resume enhancement) and `gemini-2.5-flash-lite` (job classification/blurbs). Confirm current model IDs at https://ai.google.dev/gemini-api/docs/models before deploying.

### Trend growth percentage
Adzuna's free tier does not expose historical opening counts, so the trend arrow/percent on trending cards uses a placeholder (`stable` or a random 5–20% "up") until a time-series store is added in Phase 2. Opening counts and CTC ranges are always real Adzuna data when credentials are configured.

### Domain filter in job search
When a single domain chip is selected, its primary keyword is appended to the search query sent to Adzuna (e.g. selecting "AI/ML" adds `machine learning`). Multi-select domain filtering is UI-only for MVP; Adzuna has no native domain filter.

### Guided chat experience parsing
Chat answers update the live preview immediately with basic field mapping. The final "Polish with AI" step sends the full conversation to Gemini for proper structuring into the resume schema — same as the paste flow.

### In-memory cache
Trending and search results are cached in server memory (1-hour TTL). This resets on cold starts in serverless (Vercel). For production, swap to Redis or Vercel KV.

### PDF parsing
`pdf-parse` is loaded dynamically in the parse API route to avoid bundling issues with its test-file side effects in some environments.

## LLM stack (Azure Foundry Grok — not Gemini)
- All AI (resume enhance, job title classify, trend blurbs, live-search answers) uses Azure Foundry via `lib/azureFoundryModel.ts`.
- Env: `AZURE_FOUNDRY_API_KEY`, `AZURE_FOUNDRY_BASE_URL`, `AZURE_FOUNDRY_MODEL=grok-4-20-reasoning`.
- `GEMINI_API_KEY` is **not required** and is ignored. `lib/gemini.ts` only re-exports Azure helpers for compatibility.
- Health: `{ llm, azureFoundry, exa, adzuna }` — `gemini` is a legacy alias of `azureFoundry`.

## Live web search (Exa + Azure Foundry Grok)
- Route: `POST /api/live-search` — browser never calls Exa or Azure directly.
- Flow: validate query → Exa search (highlights) → Azure Grok grounded answer with [n] citations.
- Citation URLs always come from Exa-normalized sources, not model-generated text.
- Secrets: `EXA_API_KEY`, `AZURE_FOUNDRY_API_KEY` only via `process.env` / `.env.local` (gitignored).
- UI: `LiveSearchPanel` on `/job-trends`.

## Adzuna-free Job Trends (Exa path)
- Without Adzuna keys, `/api/jobs/trending` uses Exa + Grok (`lib/exaMarketInsights.ts`).
- Cards show qualitative **demand signals** (strong/moderate/limited) + blurbs + skills — **never invented vacancy counts or CTC**.
- Without Adzuna, `/api/jobs/search` uses Exa web discovery of public job pages (real URLs from Exa).
- If Adzuna keys are present, Adzuna remains preferred for real counts/listings.
- Cache: Exa trending results cached 1 hour (`trending-domains-exa`).

## UI simplification pass (July 25, 2026)

Goal: keep only elements that carry information or enable an action. Removed:

- **Command palette + keyboard shortcuts dialog** — a 3-route app doesn't need
  one, and it bound Ctrl/⌘ + P, S and U globally, overriding browser print,
  save and view-source.
- **Landing "workspace preview" mockup + 5-step carousel** (`ProductShowcase`) —
  placeholder bars, not the real product. Also dropped the duplicate dark CTA
  block; the hero and module cards already carry the CTA.
- **`AmbientScene` / `AmbientBackground`** — pointer-tracking spotlight, two
  looping orbs and a dot grid, replaced by a static CSS wash on `body`. Removes
  a `pointermove` listener that set React state on every frame.
- **`AiActivityIndicator` and `ResearchTimeline`** — fake step timers that
  admitted in their own footnotes that they weren't real progress. The preview
  shimmer and an inline spinner cover the same states honestly.
- **`ResumeChecklist`** — merged into `ResumeInsights`, which was already a
  second completeness meter. One card now shows the score ring, the next items
  to add, and the job-description match.
- **Focus mode** — existed to hide the clutter above; nothing left to hide.
  `focusMode` removed from `resumeStore`.
- **"View original" template PDF link** and the preview's duplicate mode pills.

Behaviour changes worth knowing:

- Domain filter in job search is now **single-select** in the UI (it always was
  single-select in the API), so the "select only one domain" error is
  unreachable from normal use. The guard in `JobResults` stays as a backstop.
- `TrendingCards` renders the grid only when web research actually returned a
  blurb or skills. Previously, a failed Grok call fell through to
  `signal: "moderate"` for all 8 domains and the UI displayed that default as a
  finding — see the swallowed `catch` in `lib/exaMarketInsights.ts`. Now it says
  no signals came back.
- User-facing copy no longer names Exa / Azure Grok / Adzuna as the mechanism.
  The "not official vacancy counts" honesty note is kept.

## Trending failure root-caused & hardened (August 22, 2026)

The "8 identical Moderate cards" bug was reproduced and root-caused:

- **Root cause is a dead Azure Foundry API key**, not code. Direct probes of
  `https://divya-mreu8v6r-eastus2.services.ai.azure.com` return
  **401 "invalid subscription key"** on both the `/openai/v1/` and classic
  endpoints, with both `api-key` and `Authorization: Bearer` headers. The Exa
  key in the same `.env.local` was probed and works, so it is not an env-
  parsing issue. `/api/health` previously reported `azureFoundry:true` because
  it only checked env-var presence — it could never catch this.
- The bare `catch { insights = [] }` in `computeExaTrendingDomains` then
  swallowed the auth error and returned default cards.

Hardening shipped this pass:

1. `computeExaTrendingDomains` returns `{ domains, synthesisError }`; failures
   (`auth_error`, `rate_limit`, `timeout`, `empty_or_unparseable`,
   `no_sources`) are logged server-side and passed through the API as
   `detail`. Failed syntheses are **no longer cached** (the old code cached the
   empty result for an hour).
2. `/api/jobs/trending` adds `detail` + an honest note when research is down;
   `TrendingCards` renders a vendor-free reason sentence in the no-signals
   state ("The research service rejected its credentials." etc.).
3. `/api/health?deep=1` performs one real LLM ping (cached 60s) and reports
   `llmReachable` + `llmCode`, so config-present-but-broken is detectable.

**Remaining manual step (owner-only):** generate a fresh Azure Foundry key
(Azure Portal → the `divya-mreu8v6r-eastus2` resource → Keys, or
`az cognitiveservices account keys list` after `az login`), put it in
`.env.local` as `AZURE_FOUNDRY_API_KEY`, restart the server, then confirm:
`GET /api/health?deep=1` → `"llmReachable":true`, and `/api/jobs/trending`
returns non-empty blurbs/keySkills. Until then trending intentionally shows
the honest no-signals state instead of defaults-as-findings.

## Phase 2 items (not built)
- User accounts + persistent resume history
- PDF export
- Resume ↔ job match scoring
- Historical trend growth from stored snapshots
- Redis-backed cache for serverless

## Running locally
```bash
cp .env.example .env.local
# Fill in AZURE_FOUNDRY_API_KEY (+ EXA_API_KEY for job trends; ADZUNA_APP_ID/KEY optional)
npm run dev
```

Verify the LLM credential actually works (not just configured):
`GET http://localhost:3000/api/health?deep=1` → `"llmReachable":true`.

Get free Adzuna credentials at https://developer.adzuna.com/