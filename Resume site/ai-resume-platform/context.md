# AI Resume Builder & Job Trends Platform — Developer Handoff

> **Purpose of this file:** Paste this entire document into a new AI coding session (different model/window) to continue development without losing context. Last updated: July 10, 2026.

---

## 1. What This Project Is

A **full-stack MVP web app** for Indian job seekers with two modules under shared navigation:

| Module | Route | Purpose |
|--------|-------|---------|
| **Resume Builder** | `/resume-builder` | Turn raw text, guided chat, or uploaded resume into an ATS-safe resume with live preview and `.docx` export |
| **Job Trends** | `/job-trends` | Trending job domains (real Adzuna data) + keyword/filtered job search |

**Landing page** at `/` with Apple-inspired minimal design, product cards, and CTAs.

**MVP constraints (by design):**
- No user authentication
- No database — session persisted in `localStorage` only
- All third-party API keys server-side only
- Primary export format is `.docx` (not PDF)

**Original build specification:** `D:\resumes\ai-resume-job-trends-build-prompt.md`

---

## 2. Project Locations

There are **two copies** of the codebase on this machine:

| Location | Notes |
|----------|-------|
| `C:\Users\manoj\ai-resume-platform` | Primary build location from original session |
| `D:\ai apps\ai-resume-platform` | Copy for parallel development (may have `.env.local` here) |

**Resume template source PDFs (original designs):** `D:\resumes\`

**This context file:** `D:\ai apps\context.md`

**Before continuing:** Pick one canonical project folder and work from it consistently. If API keys are configured, check which copy has `.env.local`.

---

## 3. Tech Stack (Installed Versions)

| Layer | Package / Version |
|-------|-------------------|
| Framework | Next.js **16.2.10** (App Router), TypeScript |
| React | **19.2.4** |
| Styling | Tailwind CSS **4**, shadcn-style UI components |
| Font | Inter (Google Fonts via `next/font`) |
| Motion | framer-motion **12.42.2** |
| State | Zustand **5.0.14** |
| AI | `@google/generative-ai` **0.24.1** (Gemini, server-side only) |
| Job data | Adzuna API — India endpoint (`api.adzuna.com/v1/api/jobs/in`) |
| DOCX export | `docx` **9.7.1** |
| DOCX parse | `mammoth` **1.12.0** |
| PDF parse | `pdf-parse` **2.4.5** (v2 API with worker setup) |
| Icons | lucide-react |

---

## 4. Quick Start

```bash
cd C:\Users\manoj\ai-resume-platform   # or D:\ai apps\ai-resume-platform
cp .env.example .env.local
# Fill in API keys (see Section 6)
npm install
npm run dev        # http://localhost:3000
npm run build      # production build (verified passing)
```

---

## 5. Environment Variables

Create `.env.local` from `.env.example`:

```env
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
GEMINI_CLASSIFIER_MODEL=gemini-2.5-flash-lite
ADZUNA_APP_ID=
ADZUNA_APP_KEY=
```

| Variable | Required For | Get Keys |
|----------|--------------|----------|
| `GEMINI_API_KEY` | AI resume enhance, job title classification, trend blurbs | https://aistudio.google.com/ |
| `GEMINI_MODEL` | Resume structuring/rewriting | Default: `gemini-2.5-flash` |
| `GEMINI_CLASSIFIER_MODEL` | Job title → domain classification, trend blurbs | Default: `gemini-2.5-flash-lite` |
| `ADZUNA_APP_ID` + `ADZUNA_APP_KEY` | Live job search + trending data | https://developer.adzuna.com/ |

**Model note:** Original spec referenced `gemini-3.5-flash` / `gemini-3.1-flash-lite` which were unavailable in July 2026. Project uses `gemini-2.5-flash` variants instead. Confirm current IDs at https://ai.google.dev/gemini-api/docs/models before deploying.

**Restart `npm run dev` after changing `.env.local`.**

Health check: `GET /api/health` → `{ gemini: boolean, adzuna: boolean }`

`SetupBanner` component shows orange warning on resume-builder and job-trends pages when keys are missing.

---

## 6. Feature Status (Last Verified)

| Feature | Status | Notes |
|---------|--------|-------|
| Landing page `/` | ✅ Working | Apple-style hero, product cards |
| Resume Builder layout (40/60, mobile stack) | ✅ Working | Build/Preview switcher on mobile |
| Paste Content input + enhance flow | ⚠️ Needs `GEMINI_API_KEY` | Returns 503 without key |
| Guided Chat (10 steps) | ⚠️ Needs `GEMINI_API_KEY` | Live preview updates per step; final "Polish with AI" calls enhance |
| Upload .pdf / .docx | ✅ Working | Parse works; enhance needs Gemini |
| 5 resume templates + live preview | ✅ Working | React components match PDF designs |
| Template switching (no data loss) | ✅ Working | Same JSON, different renderer |
| Resume score ring + section bars | ✅ Working | Client-side heuristic in `lib/resumeScore.ts` |
| Keyword match % (vs job description) | ✅ Working | Client-side in `lib/keywordMatch.ts` |
| Before/after compare toggle | ✅ Working | Stores `previousResume` on enhance |
| .docx export/download | ✅ Working | No API key needed |
| localStorage auto-save | ✅ Working | Key: `resumeai-session` |
| Toast notifications | ✅ Working | Zustand toast store |
| Job Trends trending cards | ⚠️ Mock without Adzuna | Real data when keys configured |
| Job search + filters | ⚠️ Needs Adzuna keys | Returns 503 without keys |
| Recent searches | ✅ Working | Key: `resumeai-recent-searches` |
| `npm run build` | ✅ Passing | |

---

## 7. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│  Browser (React 19 + Zustand + localStorage)                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │ /resume-     │  │ /job-trends  │  │ / (Landing)      │  │
│  │ builder      │  │              │  │                  │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────────────┘  │
│         │                  │                                 │
│         ▼                  ▼                                 │
│  useResumeStore      JobFilters state (page-local)          │
│  SessionProvider      RecentSearches (localStorage)          │
└─────────┬──────────────────┬────────────────────────────────┘
          │ fetch            │ fetch
          ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│  Next.js API Routes (server-side only)                      │
│  POST /api/resume/enhance  → lib/gemini.ts                  │
│  POST /api/resume/export   → lib/docxExport.ts              │
│  POST /api/resume/parse    → mammoth + lib/pdfParse.ts      │
│  GET  /api/jobs/search     → lib/adzuna.ts                  │
│  GET  /api/jobs/trending   → lib/trending.ts                │
│  POST /api/jobs/refresh-trends                              │
│  GET  /api/health                                           │
└─────────┬──────────────────┬────────────────────────────────┘
          │                  │
          ▼                  ▼
    Gemini API          Adzuna API (India)
```

**Critical data rule (from spec):** Gemini NEVER outputs statistics presented as real market data. Opening counts and CTC ranges come only from Adzuna. Gemini only classifies job titles into domains and writes one-line trend blurbs.

---

## 8. Folder Structure

```
ai-resume-platform/
├── app/
│   ├── page.tsx                    # Landing page
│   ├── layout.tsx                  # Root layout (Navbar, Footer, SessionProvider, Toast)
│   ├── globals.css                 # Design tokens, utility classes
│   ├── resume-builder/page.tsx     # Module A
│   ├── job-trends/page.tsx         # Module B
│   └── api/
│       ├── health/route.ts
│       ├── resume/
│       │   ├── enhance/route.ts    # POST — Gemini structuring
│       │   ├── export/route.ts     # POST — .docx download
│       │   └── parse/route.ts      # POST — PDF/DOCX text extraction
│       └── jobs/
│           ├── search/route.ts     # GET — Adzuna search proxy
│           ├── trending/route.ts   # GET — cached trending domains
│           └── refresh-trends/route.ts  # POST — bust cache + recompute
├── components/
│   ├── landing/LandingPage.tsx
│   ├── resume-builder/
│   │   ├── BuildPane.tsx           # Tabs: Paste / Chat / Upload + TemplatePicker
│   │   ├── PreviewPane.tsx         # Live preview, download, compare
│   │   ├── PasteContentTab.tsx
│   │   ├── GuidedChatTab.tsx       # 10-step chat flow
│   │   ├── UploadTab.tsx
│   │   ├── TemplatePicker.tsx
│   │   ├── ResumeInsights.tsx      # Score ring + keyword match
│   │   └── ChatStepper.tsx
│   ├── resume-templates/
│   │   ├── TemplateRenderer.tsx    # Switch on template ID
│   │   ├── BlueCleanTemplate.tsx
│   │   ├── TechProTemplate.tsx
│   │   ├── AtsFriendlyTemplate.tsx
│   │   ├── ModernBwTemplate.tsx
│   │   ├── CorporateMinimalTemplate.tsx
│   │   └── shared.tsx
│   ├── job-trends/
│   │   ├── TrendingCards.tsx
│   │   ├── SearchFilters.tsx
│   │   ├── JobResults.tsx
│   │   ├── RecentSearches.tsx
│   │   └── CountUp.tsx
│   ├── shared/
│   │   ├── Navbar.tsx
│   │   ├── Footer.tsx
│   │   ├── SetupBanner.tsx
│   │   ├── SessionProvider.tsx     # localStorage hydrate + debounced save
│   │   ├── Toast.tsx
│   │   ├── PageHero.tsx
│   │   ├── ModuleBridge.tsx        # Cross-module CTA links
│   │   ├── ResumeScoreRing.tsx
│   │   ├── AmbientBackground.tsx
│   │   └── ShimmerOverlay.tsx
│   └── ui/                         # shadcn-style primitives
│       ├── button.tsx, input.tsx, textarea.tsx, tabs.tsx
│       ├── card.tsx, badge.tsx, label.tsx, slider.tsx, skeleton.tsx
├── lib/
│   ├── resumeSchema.ts             # ResumeData types, emptyResume, merge helpers
│   ├── templates.ts                # TEMPLATES style tokens (5 templates)
│   ├── gemini.ts                   # enhanceResume, classifyJobTitles, generateTrendBlurb
│   ├── adzuna.ts                   # searchJobs, fetchSampleJobs, getSalaryHistogram
│   ├── trending.ts                 # computeTrendingDomains, getMockTrendingData
│   ├── domains.ts                  # JOB_DOMAINS (8 domains with keywords)
│   ├── docxExport.ts               # generateDocx from ResumeData + style tokens
│   ├── pdfParse.ts                 # extractPdfText (pdf-parse v2 worker fix)
│   ├── resumeScore.ts              # Client-side resume quality scoring
│   ├── keywordMatch.ts             # Client-side JD keyword matching
│   ├── persistence.ts              # localStorage session save/load
│   ├── cache.ts                    # In-memory server cache (1hr TTL)
│   └── utils.ts                    # cn, formatCtc, formatDate, stripJsonFences
├── store/
│   ├── resumeStore.ts              # Zustand — all resume builder state
│   └── toastStore.ts               # Zustand — toast queue
├── templates/                      # Source PDF files (from D:\resumes)
├── public/templates/               # Same PDFs served at /templates/*.pdf
├── NOTES.md                        # Build assumptions and Phase 2 items
├── .env.example
└── package.json
```

---

## 9. API Routes Reference

### `POST /api/resume/enhance`
**Body:**
```json
{
  "rawText": "string (required)",
  "targetJobDescription": "string (optional)",
  "existingResumeJson": { /* ResumeData */ }
}
```
**Response:** `ResumeData` JSON  
**Errors:** 400 (no rawText), 503 (no GEMINI_API_KEY), 500 (parse/Gemini failure)  
**Implementation:** `lib/gemini.ts` → `enhanceResume()` with `responseMimeType: "application/json"`

### `POST /api/resume/export`
**Body:**
```json
{
  "resume": { /* ResumeData */ },
  "templateId": "blue-clean"
}
```
**Response:** Binary `.docx` file stream  
**Filename:** `{FullName}_Resume.docx`

### `POST /api/resume/parse`
**Body:** `multipart/form-data` with `file` field (.pdf or .docx)  
**Response:** `{ "text": "extracted plain text" }`

### `GET /api/jobs/search`
**Query params:** `q`, `location`, `minCtc`, `maxCtc`, `page`  
**Response:** `{ jobs: NormalizedJob[], total: number }`  
**Requires:** Adzuna credentials (503 if missing)

### `GET /api/jobs/trending`
**Response:** `TrendingDomainData[]` — real Adzuna data when configured, mock placeholder otherwise

### `POST /api/jobs/refresh-trends`
**Response:** `{ refreshed: true, count: number }` — clears `trending-domains` cache and recomputes

### `GET /api/health`
**Response:** `{ gemini: boolean, adzuna: boolean }`

---

## 10. Resume Data Schema

Defined in `lib/resumeSchema.ts`:

```typescript
interface ResumeData {
  personalInfo: {
    fullName: string;
    email: string;
    phone: string;
    location: string;
    linkedin: string;
    portfolio: string;
  };
  targetRole: string;
  summary: string;
  experience: Array<{
    company: string;
    role: string;
    location: string;
    startDate: string;
    endDate: string;
    current: boolean;
    bullets: string[];
  }>;
  education: Array<{
    institution: string;
    degree: string;
    field: string;
    startDate: string;
    endDate: string;
  }>;
  skills: { technical: string[]; soft: string[] };
  certifications: Array<{ name: string; issuer: string; date: string }>;
  projects: Array<{ name: string; description: string; tech: string[]; link: string }>;
}
```

**Download eligibility:** `isResumeDownloadable()` requires fullName + (email OR phone) + at least one experience OR education entry.

**Template IDs:** `blue-clean` | `tech-pro` | `ats-friendly` | `modern-bw` | `corporate-minimal`

**Legacy ID mapping** (for old localStorage sessions):
- `modern` → `blue-clean`
- `classic` → `ats-friendly`
- `minimal` → `corporate-minimal`

---

## 11. Resume Templates

Imported from `D:\resumes` PDF designs. Each has a React preview component + shared style tokens in `lib/templates.ts` + matching DOCX styling in `lib/docxExport.ts`.

| Template ID | Source PDF | React Component | Layout |
|-------------|-----------|-----------------|--------|
| `blue-clean` | Blue and White Clean and Professional Resume (1).pdf | `BlueCleanTemplate.tsx` | left, blue accent |
| `tech-pro` | White and Black Tech Professional Resume (1).pdf | `TechProTemplate.tsx` | left, dark |
| `ats-friendly` | Black and White Professional ATS Friendly Resume.pdf | `AtsFriendlyTemplate.tsx` | ats, Arial |
| `modern-bw` | Black and White Modern Professional Resume (1).pdf | `ModernBwTemplate.tsx` | centered |
| `corporate-minimal` | White and Blue Minimalist Professional Corporate ATS Resume.pdf | `CorporateMinimalTemplate.tsx` | left, blue |

PDFs copied to:
- `templates/` (source)
- `public/templates/` (served at `/templates/<filename>.pdf`)

To replace a design: drop new PDF, update tokens in `lib/templates.ts`, adjust matching component in `components/resume-templates/`.

---

## 12. State Management

### Zustand `useResumeStore` (`store/resumeStore.ts`)

| Field | Purpose |
|-------|---------|
| `resume` | Current structured resume data |
| `previousResume` | Snapshot before AI enhance (for compare) |
| `templateId` | Active template |
| `inputMode` | `"paste"` \| `"chat"` \| `"upload"` |
| `mobilePane` | `"build"` \| `"preview"` (mobile only) |
| `isEnhancing` | AI call in progress |
| `enhanceError` | Last enhance error message |
| `rawText` | Paste mode content |
| `targetJobDescription` | Optional JD for tailoring |
| `chatStep` / `chatAnswers` | Guided chat progress |
| `showCompare` | Toggle before/after preview |
| `hydrated` | localStorage loaded flag |

### Persistence (`lib/persistence.ts`)
- **Key:** `resumeai-session`
- **Saved fields:** resume, templateId, rawText, targetJobDescription, inputMode
- **Debounce:** 500ms via `SessionProvider`
- **NOT saved:** chatStep, chatAnswers, isEnhancing, previousResume

### Job Trends State
- Page-local React state for filters (`JobFilters`)
- `searchTrigger` counter + `activeQuery` string to avoid stale search bug
- Recent searches in localStorage key `resumeai-recent-searches` (max 5)

---

## 13. Guided Chat Flow (10 Steps)

Defined in `components/resume-builder/GuidedChatTab.tsx`:

1. fullName
2. email
3. phone
4. location
5. targetRole
6. summary (textarea)
7. experience (textarea → bullets split by newline)
8. education (textarea → institution/degree split by comma)
9. skills (textarea → comma-separated technical skills)
10. certifications/projects (textarea)

Each answer calls `applyChatAnswer()` for immediate live preview update. On last step, "Polish with AI" sends all Q&A as `rawText` to `/api/resume/enhance` with `existingResumeJson`.

---

## 14. Job Domains & Trending Logic

### 8 Domains (`lib/domains.ts`)
`ai-ml`, `fullstack`, `cloud-devops`, `data-engineering`, `mobile`, `cybersecurity`, `product-management`, `fintech`

Each has `keywords[]` for fallback classification when Gemini unavailable.

### Trending Pipeline (`lib/trending.ts`)
1. Fetch sample jobs from Adzuna for 8 broad search queries (25 each)
2. Classify job titles via Gemini `classifyJobTitles()` (batched, 50 at a time) OR keyword fallback
3. Aggregate counts + CTC min/max per domain
4. Generate blurbs for top 5 domains via `generateTrendBlurb()`
5. Cache result under key `trending-domains` (1 hour TTL)

### Known Limitation: Trend Percent
Adzuna free tier has no historical data. `trendPercent` is a **placeholder** (random 5–20% "up") or "stable" in mock mode. Opening counts and CTC ranges are real when Adzuna is configured.

### Domain Filter in Search
- **Single domain selected:** appends domain's primary keyword to search query
- **Multiple domains:** UI shows error "Select only one domain filter at a time"
- Multi-select is UI-only for MVP; no native Adzuna domain filter

---

## 15. UI / Design System

Apple-inspired minimal aesthetic applied across the app:

| Token | Value |
|-------|-------|
| Background | `#fbfbfd` with ambient gradients (`AmbientBackground`) |
| Primary text | `#1d1d1f` |
| Muted text | `#6e6e73` |
| Accent / links | `#0071e3` |
| Warning banner | `#ff9500` |
| Font | Inter via CSS variable `--font-inter` |
| Nav | Glass effect (`glass-nav` class in globals.css) |
| Cards | `rounded-2xl`, soft shadows `shadow-[0_2px_20px_rgba(0,0,0,0.04)]` |
| Buttons | Pill-shaped, primary blue |
| Document preview | `document-preview` class — white paper look |
| Section labels | `section-label` utility class |

Motion: framer-motion for page enter, score bars, count-up on trends, shimmer overlay during AI enhance.

---

## 16. Bugs Fixed During Original Build

### 1. PDF parse worker error (Next.js + pdf-parse v2)
**File:** `lib/pdfParse.ts`  
**Fix:** Call `PDFParse.setWorker(pathToFileURL(workerPath).href)` before parsing, pointing to `node_modules/pdf-parse/dist/pdf-parse/esm/pdf.worker.mjs`

### 2. Generic job search errors
**File:** `components/job-trends/JobResults.tsx`  
**Fix:** `parseApiError()` extracts actual API error message from response body

### 3. Stale recent search query
**File:** `app/job-trends/page.tsx`  
**Fix:** Separate `activeQuery` state passed to `JobResults` instead of reading `filters.q` directly at fetch time

### 4. Gemini model IDs
Original spec models unavailable; updated to `gemini-2.5-flash` / `gemini-2.5-flash-lite` in `.env.example` and `lib/gemini.ts`

---

## 17. Server-Side Caching

**File:** `lib/cache.ts` — in-memory `Map` with TTL (default 1 hour)

| Cache Key Pattern | Used By |
|-------------------|---------|
| `search:{params}` | Job search results |
| `sample:{query}:{count}` | Trending sample jobs |
| `histogram:{query}` | Salary histogram |
| `categories` | Adzuna categories |
| `trending-domains` | Full trending dashboard data |

**Limitation:** Resets on serverless cold starts (Vercel). Phase 2: Redis or Vercel KV.

---

## 18. Gemini Prompts (Key Rules)

### Resume Enhancement (`lib/gemini.ts`)
- Return strict JSON matching ResumeData schema
- Strong action verbs, active voice
- Quantify ONLY with numbers user provided — never invent metrics/employers/dates
- Mirror JD terminology when targetJobDescription supplied
- Temperature: 0.3, `responseMimeType: "application/json"`

### Job Title Classification
- Maps titles to one of 8 domain IDs
- Uses lighter classifier model (`GEMINI_CLASSIFIER_MODEL`)
- Temperature: 0.1

### Trend Blurbs
- Single sentence, max 15 words
- Must not invent numbers beyond opening count provided

---

## 19. Definition of Done (Spec Checklist)

| Requirement | Status |
|-------------|--------|
| Paste raw text → AI rewrite → .docx download | ✅ (needs Gemini key for AI step) |
| Guided chat on par with paste flow | ✅ (needs Gemini key) |
| Upload old resume → schema → new template | ✅ |
| Template switch never loses data | ✅ |
| Trending shows real Adzuna counts/CTC | ✅ with keys / mock without |
| Search + filters return real listings | ✅ with Adzuna keys |
| No API key in client code or network | ✅ |

---

## 20. Phase 2 — Not Built Yet

From `NOTES.md` and original spec:

- [ ] User accounts + database (resume history across devices)
- [ ] PDF export (`html2canvas` + `jsPDF` or Puppeteer)
- [ ] Resume ↔ job match scoring via Gemini (partially scaffolded: `keywordMatch.ts` is client-side heuristic only)
- [ ] Historical trend growth from stored snapshots (replace placeholder trend %)
- [ ] Redis/KV cache for serverless deployments
- [ ] Experience level filter in job search (UI not built)
- [ ] Scheduled cron for trending refresh (currently on-demand via page load + manual POST refresh)
- [ ] Multi-domain search filter (currently single-domain only)

---

## 21. How to Continue Development

### Recommended next steps (priority order)

1. **Configure API keys** — Create `.env.local`, verify `/api/health` returns both `true`, test enhance + job search end-to-end
2. **Pick canonical project path** — Sync changes between `C:\Users\manoj\` and `D:\ai apps\` copies if both exist
3. **Resume ↔ job match (Phase 2 bridge)** — Wire Gemini match scoring between modules; `keywordMatch.ts` already shows basic client-side version
4. **PDF export** — Add `POST /api/resume/export-pdf` or client-side html2canvas approach
5. **Trend growth time-series** — Store daily Adzuna snapshots, compute real trend %
6. **Deploy to Vercel** — Set env vars in Vercel dashboard, consider KV for cache

### Code patterns to follow

- **All external API calls** go through `app/api/*` routes, never from browser directly
- **Resume preview + DOCX export** share `ResumeData` schema and `TemplateStyleTokens` from `lib/templates.ts` — keep them in sync
- **Error handling:** Always show visible error + retry, never silent blank (see `PreviewPane`, `JobResults`, `UploadTab`)
- **Loading states:** `isEnhancing` + `ShimmerOverlay` on preview; `Skeleton` on job results
- **Ambiguous decisions:** Log in `NOTES.md`, don't block on questions

### Files to read first when picking up

1. `lib/resumeSchema.ts` — data contract
2. `store/resumeStore.ts` — builder state
3. `lib/gemini.ts` — AI integration
4. `lib/adzuna.ts` + `lib/trending.ts` — job data
5. `components/resume-builder/BuildPane.tsx` + `PreviewPane.tsx` — main UX
6. `NOTES.md` — assumptions already made

### Testing manually

```bash
# Health
curl http://localhost:3000/api/health

# Enhance (needs GEMINI_API_KEY)
curl -X POST http://localhost:3000/api/resume/enhance \
  -H "Content-Type: application/json" \
  -d '{"rawText":"John Doe, Software Engineer at Infosys. Built React apps."}'

# Job search (needs Adzuna keys)
curl "http://localhost:3000/api/jobs/search?q=react%20developer&location=Bangalore"

# Trending
curl http://localhost:3000/api/jobs/trending
```

---

## 22. Key Dependencies & Gotchas

| Topic | Detail |
|-------|--------|
| `pdf-parse` v2 | Must set worker path before use — see `lib/pdfParse.ts` |
| `docx` export | Server-side only in API route; uses style tokens not React components |
| Adzuna India | Base URL: `https://api.adzuna.com/v1/api/jobs/in` |
| CTC format | Salaries in INR; `formatCtc()` shows LPA/Cr notation |
| Next.js 16 | Default App Router; no pages/ directory |
| Tailwind 4 | Uses `@tailwindcss/postcss` in devDependencies |
| localStorage keys | `resumeai-session`, `resumeai-recent-searches` |

---

## 23. Transcript / Session History

Full build conversation transcript (if more detail needed):
```
C:\Users\manoj\.grok\sessions\C%3A%5CUsers%5Cmanoj%5C019f3364-4568-7630-a2ed-5b9b5096d9a1\updates.jsonl
```

Original one-shot build prompt:
```
D:\resumes\ai-resume-job-trends-build-prompt.md
```

---

## 24. Instructions for New AI Session

When you (the new model) receive this file:

1. Read this document fully before making changes
2. Ask user which project path to use: `C:\Users\manoj\ai-resume-platform` or `D:\ai apps\ai-resume-platform`
3. Check if `.env.local` exists and `/api/health` status
4. Run `npm run build` to verify current state
5. Continue from Phase 2 items or user's specific request
6. Log any new ambiguous decisions in `NOTES.md`
7. Do not add auth/database unless explicitly requested
8. Keep Gemini for labeling/commentary only — never fabricate job market statistics

**Product name in UI:** ResumeAI  
**Target users:** Indian job seekers (entry to senior level)  
**Export format:** `.docx` (ATS-friendly Word, not PDF)