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

## Phase 2 items (not built)
- User accounts + persistent resume history
- PDF export
- Resume ↔ job match scoring
- Historical trend growth from stored snapshots
- Redis-backed cache for serverless

## Running locally
```bash
cp .env.example .env.local
# Fill in GEMINI_API_KEY, ADZUNA_APP_ID, ADZUNA_APP_KEY
npm run dev
```

Get free Adzuna credentials at https://developer.adzuna.com/