# ADDENDUM — GROK BUILD DEVELOPMENT + VERCEL DEPLOYMENT

Append this entire addendum to the master specification.

This addendum is mandatory. Do not treat it as optional documentation.

---

# 141. BUILD AND DEPLOY MANDATE

You are executing this specification as **Grok Build** (`grok` CLI / TUI coding agent by SpaceXAI / xAI).

Your job is not only to design the product.

Your job is to:

1. Scaffold the complete Next.js application locally
2. Implement the full working product from the master specification
3. Verify typecheck, lint, unit tests, and production build
4. Prepare the repo for Vercel
5. Deploy a working preview (and production if credentials/project exist)
6. Return the live URL plus local run commands

Do not stop at a plan.
Do not stop at a partial prototype.
Do not wait for extra approval.

---

# 142. GROK BUILD EXECUTION RULES

Use Grok Build capabilities fully:

* Read and edit the entire codebase
* Run shell commands
* Install dependencies
* Run tests and builds
* Use Plan Mode first for the architecture, then implement
* Use skills, plugins, hooks, and MCP servers when they improve quality
* Use the official **Vercel plugin** if available (`/marketplace` → Vercel, or install when Vercel is mentioned)
* Use Vercel MCP if connected (`npx -y add-mcp https://mcp.vercel.com -g`)
* Prefer small, verifiable increments over one giant untested dump

Recommended Grok Build setup:

```bash
# Install Grok Build if missing
curl -fsSL https://x.ai/cli/install.sh | bash
grok --version

# Optional: Vercel plugin / skills
npx plugins add vercel/vercel-plugin
npx skills add vercel-labs/agent-skills

# Optional: Vercel MCP
npx -y add-mcp https://mcp.vercel.com -g
```

If running through Vercel AI Gateway for models, keep provider keys out of the application source and out of exported career-OS state.

Inside Grok Build:

* Start in Plan Mode
* Approve a phase plan that matches the spec’s Phase 1–10
* Implement phase by phase
* After each phase: `npm run typecheck` and a focused smoke check
* After Phase 10: lint, typecheck, test, build, then deploy

---

# 143. APPLICATION IDENTITY FOR DEPLOYMENT

Use these defaults unless the workspace already has a name:

* App name: `AI Career OS`
* Package / project slug: `ai-career-os`
* Vercel project name: `ai-career-os`
* Repo name (if created): `ai-career-os`

Do not use student-project names like `career-tracker`, `job-board`, or `habit-os`.

---

# 144. VERCEL IS THE PRODUCTION TARGET

This application must be deployable on **Vercel** as a Next.js App Router project.

Required platform fit:

* Next.js 16.x App Router
* TypeScript
* Tailwind CSS
* Client-first persistence (localStorage + IndexedDB)
* No required backend in v1
* No secrets required to run the core product
* Works on Vercel Hobby / Pro without a database

Vercel configuration must include:

* Framework preset: Next.js
* Build command: `next build` (or Vercel auto-detect)
* Output: standard Next.js
* Node version compatible with Next.js 16
* Region: close to India if selectable (`bom1` / `sin1` preferred; do not fail the build if region cannot be set)

Create:

```text
vercel.json
```

Keep it minimal. Do not invent custom routing that breaks App Router.

Example starting point (adapt only if needed):

```json
{
  "framework": "nextjs",
  "$schema": "https://openapi.vercel.sh/vercel.json"
}
```

Also create:

* `.gitignore` that excludes `.env*`, `.vercel`, `node_modules`, `.next`, coverage, Playwright artifacts
* `README.md` with local + Vercel commands
* Optional `public/manifest.webmanifest` if PWA is added only after core reliability

---

# 145. DEPLOYMENT CONSTRAINTS (CRITICAL)

v1 must deploy as a **static-capable / serverless Next.js app with no required env vars**.

Allowed:

* Client-side storage
* Optional future API routes that are unused in v1
* Public static assets

Forbidden in v1 deploy:

* Required `OPENAI_API_KEY`, `XAI_API_KEY`, or any provider key
* Required database URL
* Required auth provider
* Hardcoded secrets
* Server features that crash the build when env is empty
* Scraping jobs
* Background workers that Vercel Hobby cannot run

If an API route exists, it must fail closed and not be required for the UI.

Remember the spec security rule:

> Browser → server endpoint → provider.
> Do not expose provider secrets client-side.
> No API keys in localStorage or export files.

---

# 146. LOCAL DEVELOPMENT COMMANDS

The finished repo must support:

```bash
npm install
npm run dev
npm run lint
npm run typecheck
npm run test
npm run build
npm run start
```

Add these scripts to `package.json` if missing:

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "typecheck": "tsc --noEmit",
    "test": "vitest run",
    "test:watch": "vitest",
    "e2e": "playwright test"
  }
}
```

Default local URL:

`http://localhost:3000`

---

# 147. VERCEL CLI + GIT DEPLOY FLOW

Implement this exact deployment path.

## A. Project files first

Finish a production build locally:

```bash
npm run lint
npm run typecheck
npm run test
npm run build
```

Fix failures before deploying.

## B. Vercel project files

Ensure the repo is Vercel-ready:

* `package.json`
* `next.config.ts` or `next.config.js`
* `vercel.json` if needed
* no private files committed

## C. Login and link

```bash
npm i -g vercel
vercel login
vercel link --yes --project ai-career-os
```

If already logged in via Grok Build / Vercel plugin / MCP, use that session.

## D. Preview deploy

```bash
vercel
```

or

```bash
vercel --yes
```

## E. Production deploy

```bash
vercel --prod --yes
```

## F. Preferred durable setup

If a GitHub/GitLab remote exists:

1. Commit a clean working tree
2. Push to the production branch
3. Link the Git repo to the Vercel project so every push deploys

Do not create a second unused Vercel project if one already exists for this repo.

## G. After deploy

Return:

* Preview URL
* Production URL (if created)
* Project name
* Framework detected
* Build command used
* Any warnings

If deploy fails, do not declare the product complete. Diagnose logs, fix the build, redeploy.

---

# 148. GROK BUILD + VERCEL PLUGIN BEHAVIOR

When this prompt mentions Vercel, Grok Build should:

1. Install / use the Vercel plugin
2. Follow current Vercel + Next.js App Router recommendations
3. Use official project-link / deploy commands rather than inventing a custom host
4. Keep deployment protection sensible for a personal career OS:
   * Preview can stay protected
   * Production may stay private / password-protected because this app stores personal career data in the browser, not because the source must be secret
5. Never paste career salary notes, offers, or contact data into public commit messages

Important product note to surface in README and Settings:

> This app stores career data in the browser. A public Vercel URL does not automatically sync or back up that data. Use JSON Backup / Restore.

---

# 149. WHAT “DONE” MEANS FOR THIS ADDENDUM

The agent may only stop when all of the following are true:

1. The Next.js app runs locally
2. All specified primary routes render real working modules, not placeholders
3. Persistence survives refresh
4. Backup / restore works
5. Scoring engines run on real state
6. `npm run typecheck` passes
7. `npm run lint` passes or only has justified, documented exceptions
8. `npm run test` covers the required scoring / storage / import cases
9. `npm run build` succeeds
10. A Vercel preview or production deployment succeeds
11. README documents:
    * Grok Build development workflow
    * local commands
    * Vercel deploy commands
    * backup / privacy behavior
    * known v1 limits

If Vercel credentials are missing in the current environment, still:

* keep the repo 100% deploy-ready
* document the exact commands
* attempt `vercel` and record the blocker
* do not leave a broken `vercel.json` or env requirement

---

# 150. README SECTION TO ADD

Add this section to README.md:

```md
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

No environment variables are required for v1.
Career data stays in the browser (localStorage / IndexedDB).
Use Backup / Restore before switching devices.
```

---

# 151. PHASE ADJUSTMENT FOR GROK BUILD

Keep the original Phase 1–10 order, then add:

## Phase 11 — Vercel Productionization

* Confirm Next.js config is Vercel-compatible
* Add `vercel.json` only if needed
* Confirm zero required secrets
* Confirm CSP headers can be set via `next.config` without breaking the app
* Add deployment section to README
* Run production build
* Deploy preview
* Smoke-check `/`, `/dashboard`, `/today`, `/skills`, `/projects`, `/jobs`, `/settings`
* Deploy production if preview is healthy

## Phase 12 — Handoff

Return:

1. What was built
2. Architecture summary
3. Routes
4. Major features
5. Scoring explanation
6. Storage behavior
7. Backup / recovery
8. Test results
9. Build result
10. Vercel URLs
11. Local commands
12. Known limitations
13. Recommended Phase 2 enhancements

---

# 152. COPY-PASTE STARTER PROMPT FOR GROK BUILD

If a new Grok Build session is started in an empty folder, use this as the first message:

```text
Read and obey the full AI Career & Transition Operating System — 2026 master specification plus the Grok Build + Vercel addendum.

You are Grok Build. Build the complete Next.js 16 App Router TypeScript application now. Do not stop at planning.

Constraints:
- Client-first. No required backend. No API keys.
- Persist to ai_career_os_state_v1 through a storage abstraction.
- Dark-first premium OS, not a student dashboard.
- Target roles are Agentic AI / GenAI / AIOps / AI Solutions / Cloud AI / Forward Deployed AI.
- Do not position the product around service-desk chatbots.
- No Java or SQL learning tracks.
- Deploy to Vercel after lint, typecheck, tests, and production build pass.

Execution:
1. Plan the repo structure.
2. Scaffold Next.js 16 + Tailwind + TypeScript.
3. Implement types, storage, scoring, then modules in spec order.
4. Seed optional DEMO MODE only when the user chooses it.
5. Verify locally.
6. Prepare vercel.json / README.
7. Deploy preview to Vercel project `ai-career-os`.
8. Return local commands + live URL.
```

---

END OF ADDENDUM
