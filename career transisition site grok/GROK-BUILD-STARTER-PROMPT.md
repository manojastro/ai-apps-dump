# Paste this into Grok Build first

Use this as the opening message in a new `grok` session, inside an empty project folder. Then paste or attach the full master specification and the addendum.

---

You are Grok Build (`grok` CLI / TUI). Build and deploy the product specified in:

1. AI Career & Transition Operating System — 2026 master specification
2. Grok Build + Vercel addendum

Do not plan-only. Implement the complete working Next.js application.

## Product

Private career mission-control OS for an experienced technology professional transitioning from enterprise IT operations / service desk into senior AI engineering roles in 2026.

Baseline: 8.5 years, ₹11 LPA
Target: ₹20–25+ LPA, stretch ₹30–35+ LPA
Primary roles: Agentic AI Engineer, GenAI Engineer, AIOps Engineer, AI Solutions Engineer, AI Solutions Architect, Cloud AI Engineer, Forward Deployed AI Engineer, Intelligent Automation Engineer, AI Security Engineer, LLM Engineer
Locations: Bengaluru, Hyderabad, Chennai, Coimbatore, Remote India, Hybrid India

Do not position work around helpdesk bots, ticket routers, or password-reset agents.
Do not add Java or SQL learning tracks.

## Stack

Next.js 16 App Router, TypeScript, React, Tailwind, Zod, Lucide, Radix/shadcn-style, Recharts, date-fns, Vitest, Playwright.
Client-first. No required backend. No API keys. Persist with storage abstraction to `ai_career_os_state_v1`.

## Deploy target

Vercel project name: `ai-career-os`

After lint, typecheck, tests, and `next build` succeed:

```bash
npm i -g vercel
vercel login
vercel link --yes --project ai-career-os
vercel --yes
vercel --prod --yes
```

If Vercel auth is already available via plugin/MCP, use that and still return the live URL.

## Stop only when

- All primary routes work
- Persistence survives refresh
- Backup/restore works
- Scoring uses real state
- Production build passes
- Vercel preview exists or the exact deploy blocker is documented
- README includes Grok Build + Vercel commands

Build it now.
