# AI Career OS

Private **career mission-control** for an experienced technology professional transitioning from enterprise IT operations into senior AI engineering roles in 2026.

Baseline: **8.5 years**, **₹11 LPA**  
Target: **₹20–25+ LPA**, stretch **₹30–35+ LPA**  
Headline identities: Agentic AI, GenAI, AIOps, AI Solutions, Cloud AI, Forward Deployed AI — not service-desk chatbots, ticket routers, or password-reset agents.

The product organizes the campaign as:

**Learn → Build → Prove → Position → Apply → Interview → Improve → Convert**

_Screenshot placeholder: Command Center with readiness ring, bottleneck, role matrix, and funnel._

## Features

- Command-center dashboard with derived readiness, bottleneck, risks, role matrix, funnel, and velocity
- Today view with ranked actions, due / overdue / waiting
- Skills with mastery **and** evidence confidence
- Projects with production-readiness scoring, milestones, ADRs, metrics, defense mode
- Evidence library and role → competency → evidence graph
- Job pipeline (kanban + table), JD snapshots, coverage (not ATS), opportunity fit, follow-ups
- Company CRM, networking interactions, campaigns
- Interview bank, spaced practice, STAR builder, transition narrative, company packets
- Research lab that converts into skills / tasks / questions
- Weekly sprints, capacity, retrospectives
- Analytics from **your** records only — no fake market data
- Backup / restore, CSV import, recovery mode, privacy mode, data health

## Architecture

Client-first Next.js App Router app. No required backend. No API keys.

```
src/
  app/           routes
  components/    shell, overlays, shared UI
  store/         Zustand career store
  lib/           scoring, storage, engines, validation
  types/         domain model
  data/          competency catalog + optional demo workspace
```

State is derived at read time. `ScoreSnapshot` is historical only.

## Tech stack

Next.js 16 App Router, TypeScript (strict), React 19, Tailwind CSS 4, Zod, Zustand, Lucide, Radix-style dialogs, Recharts, date-fns, Vitest, Playwright.

## Installation

```bash
npm install
```

## Local development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

```bash
npm run lint
npm run typecheck
npm run test
npm run build
npm run start
```

```bash
npx playwright install
npm run e2e
```

## Persistence

Browser storage key: `ai_career_os_state_v1`

Access goes through a `StorageRepository` abstraction (`src/lib/storage.ts`). Application logic is not coupled to `localStorage` calls.

- Automatic debounced save
- Schema versioning + Zod validation
- Last-known-good snapshot
- Cross-tab sync (`storage` event + `BroadcastChannel`)
- Recovery Mode if state is corrupted (never silent overwrite)
- IndexedDB reserved for future binary attachments

## Backup

Use **Backup** in the top bar:

- Pretty JSON export (schema version + timestamp)
- Copy / download
- Paste or file import with preview and confirmation
- Optional backup-before-import
- Reset / demo / start clean

This app stores career data in the browser. A public Vercel URL does not automatically sync or back up that data. Use JSON Backup / Restore.

Privacy Mode hides salary, offers, private notes, and referral names **visually**. It does not encrypt stored information.

## Imports

CSV export: jobs, contacts, skills, projects.  
CSV import: job applications with column mapping, valid/invalid/duplicate preview.

## Scoring

Weights live in `src/lib/scoring-config.ts` only.

| Dimension | Weight |
| --- | --- |
| Capability | 25% |
| Portfolio / Evidence | 25% |
| Interview readiness | 15% |
| Market execution | 15% |
| Positioning | 10% |
| Networking | 5% |
| Research / certs | 5% |

Anti-gaming: planned projects, raw application count, and certificate stacks cannot dominate. A mastered skill with no evidence does not receive full evidence confidence.

All v1 analytics come from user-entered data. Deterministic engines are labeled **Career Insights / Gap / Recommendation / Priority / Role Readiness** — never “AI powered”.

## Data model

See `src/types/career.ts`. Root state is `CareerOSState`. Entities extend `BaseEntity` (`id`, `createdAt`, `updatedAt`, optional `archivedAt`).

## Testing

Vitest covers readiness, role readiness, skill evidence, project score, opportunity fit, application quality, funnel, small-sample warnings, priority/risk engines, dates, duplicates, migration, import validation, and snapshots.

## Security

- CSP headers in `next.config.ts`
- No `dangerouslySetInnerHTML`
- URL allowlist (http/https only) + `noopener noreferrer`
- No secrets in source, localStorage, or export files
- Future LLM calls must be browser → server → provider

## Develop with Grok Build

This project is intended to be implemented and maintained with Grok Build
(the `grok` coding-agent TUI).

```bash
curl -fsSL https://x.ai/cli/install.sh | bash
cd ai-career-os
grok
```

Suggested first prompt inside Grok Build:

> Continue implementing AI Career OS from the master specification.
> Keep persistence reliable. Do not add backend secrets.
> After changes, run typecheck, tests, and production build.
> Deploy preview to Vercel when the build is green.

## Deploy on Vercel

```bash
npm i -g vercel
vercel login
vercel link --yes --project ai-career-os
vercel --yes
vercel --prod --yes
```

Or from this repo after login:

```bash
npx vercel link --yes --project ai-career-os --scope manojastros-projects
npm run deploy:preview
npm run deploy:prod
```

No environment variables are required for v1.
Career data stays in the browser (localStorage / IndexedDB).
Use Backup / Restore before switching devices.

Project name: `ai-career-os`. Framework: Next.js. Build command: `next build`.

This workspace's Vercel MCP session can list the Hobby team (`manojastros-projects`) but cannot upload the full App Router file tree through `deploy_to_vercel` (payload exceeds the tool size cap). The Vercel CLI is not logged in here. Anonymous CLI deploys are capped at 20 functions, which this app exceeds. After `vercel login` on this machine, the commands above create the project and production URL.

## Future architecture

Clean boundaries exist for PostgreSQL / Supabase, auth, multi-device sync, Gmail, Calendar, GitHub, Notion, and optional SpaceXAI LLM coaching. None of these are required in v1.

## Known v1 limits

- Single-browser persistence (export to move devices)
- No live job scraping or salary prediction
- PWA manifest only — no aggressive service worker
- Playwright e2e is optional (`npm run e2e`) and needs browsers installed
