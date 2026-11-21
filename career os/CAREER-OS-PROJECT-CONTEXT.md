# Career OS — complete project history and continuation context

**Prepared:** 10 October 2026, Asia/Kolkata.

This document reconstructs work from the first request using this chat's earlier responses, Git history, deployment/setup reports, Hermes migration reports, and the latest functional audit. Historical verification is identified separately from the latest observed state. Secret values, private Telegram IDs, and private career-record contents are omitted.

## 1. Current situation at a glance

| Area | Latest established position |
| --- | --- |
| Product | Career OS: personal career execution, learning, evidence, networking, interviews and application tracking |
| Live application | [career-os-manoj.lovable.app](https://career-os-manoj.lovable.app) |
| Lovable project | Career Compass, `79875339-208c-46e9-9a92-43b90bb04184` |
| Local workspace | `D:\ai apps dump\career os` |
| Repository | [manojastro/career-os-](https://github.com/manojastro/career-os-) |
| Original implementation | Next.js/React/TypeScript; hosted Supabase mode plus browser-local demo |
| Published implementation | Separate TanStack Start/Vite/React Lovable application with Supabase cloud database |
| Hermes | Separate Windows installation at `C:\Users\manoj\AppData\Local\hermes`; not a process hosted inside Lovable |
| Hermes provider/default | OpenRouter / `meta/muse-spark-1.3-contributor`, explicitly approved by user |
| Application Copilot provider | Production source uses Lovable AI gateway / `openai/gpt-6-astra`; it was not switched by the Hermes model change |
| Learning curriculum | 30 available chapters imported; supplied document ends at V-6 despite contents listing I–XVI |
| Baseline | Last checked: unconfirmed; learner must review starting levels in Skills |
| Automated learning job | Existing job `46a628bb9ae9`, paused; full learning completion loop unverified |
| Gateway health | Restart/connectivity passed during provider setup; latest audit found no running Hermes gateway and stale saved PID |
| Readiness | Latest audit: **Not ready for daily use**; several normal demo workflows pass, but significant defects and private-production verification gaps remain |
| Latest work | Audit report/test/evidence files created; no business fixes, production data changes or deployments performed during the audit |

## 2. Original request and first implementation — 18 September 2026

You requested a private, production-quality Career Operating System to manage daily work, learning, skills, projects, goals/milestones, networking, interview preparation, job applications, evidence, plans, resources and notes.

Design requirements emphasized information, speed, keyboard access, low-friction updates and evidence-based progress. The requested design was calm and compact, avoiding decorative AI SaaS styling, excessive gradients, giant cards and unnecessary charts.

### First release built

- Application shell, navigation, responsive layouts, dark mode, keyboard shortcuts, global search and quick capture.
- Dashboard with planned/actual work, goal progress, priorities, followups, interview preparation, application stages and recent activity.
- Tasks with six stages: Backlog, This Month, This Week, Today, Doing, Completed; editable ordinary fields and selected links.
- Today execution view, manual ordering, overdue items, quick notes and schedule.
- Internal Planner time blocks and Focus timer with pause/resume/save/completion.
- Goals, milestones, manual Skills/topics with independent readiness indicators, Projects with linked-task progress and saved GitHub/deployment URLs.
- Contacts, interaction history and followup dates; interview questions, answers, practice history/confidence and STAR stories; application list and Kanban presentation.
- Notes with rich-text autosave, resources, evidence, Daily Log/journal, Weekly Review, analytics and JSON export.
- Confirmation-based AI Copilot, small local parser, server-side OpenAI/Anthropic/Gemini adapters, and a job-description analysis endpoint.
- Supabase email authentication, PostgreSQL tables/RLS/owned-link checks, private evidence Storage bucket, plus isolated local demo persistence.
- Specification, capability map, implementation tasks, README, unit and browser tests.

This was a **first release**, not completion of every original advanced requirement. Recurrence, subtasks/dependencies, complete resume management, mock interviews, restore/import, full offline sync and other gaps remained. The October audit gives the more precise current feature inventory and known defects.

### First-release Git history

| Commit | Work |
| --- | --- |
| `0532a01` | Initial Next.js scaffold |
| `9c63ea6` | Foundation and daily execution |
| `3ca467b` | Networking, interviews and application tracking |
| `c2ff8db` | Career insights, evidence and AI Copilot |

Initial verification was reported as passing lint, TypeScript, build, **12 unit tests and seven Playwright flows**. Hosted Supabase authentication/RLS/Storage and real provider calls could not be tested in the local environment at that stage.

## 3. Lovable port and initial deployment — 19 September 2026

You asked to deploy in Lovable. The existing local app was Next.js; the Lovable environment used a different framework. This was explained as a **separate Lovable port**, and you replied “yes.”

The Lovable version was built and published at:

- [Live Career OS](https://career-os-manoj.lovable.app)
- [Lovable editor](https://lovable.dev/projects/79875339-208c-46e9-9a92-43b90bb04184)

The earlier deployment response reported successful checks of the published sign-in/sample workspace, hosted signup, private data access and an authenticated Copilot request. These were historical checks; they were not repeated with an isolated private account during the latest audit.

**Important architecture distinction:** the live app is not a deployment of the current local Next.js tree. Both implementations must be evaluated separately. A local Next.js build does not certify Lovable's published source or database.

## 4. Capability and information review — 9 October 2026

You asked whether Lovable could handle everything and what was pending.

The response distinguished core application hosting from additional implementation and integrations. Lovable can host the core UI/backend, but agent scheduling, external notifications, calendar services and advanced career workflows need separate configuration or implementation. Automatically sending messages or applications also requires authorization.

The earlier review found an agent account/preference setup, but only a skipped connection check and no verified successful scheduled workflow. Notification delivery was reported unconfigured at that point.

Additional information identified for personalized career assistance:

- Preferred locations and remote/hybrid/office preference.
- Optional minimum salary with currency and annual/monthly basis.
- Priority skills to improve.
- Latest resume and relevant portfolio/GitHub links.
- Review of target roles already saved.
- Notification destination and preferred schedule.

Earlier general assistant preferences showed a 07:30 IST briefing and 50-minute study duration. Those are historical general preferences, not proof of the later learning scheduler's current configuration. The later learning schedule is described below.

## 5. Initial GitHub push — 9 October 2026

The local repository initially had no remote. You supplied `https://github.com/manojastro/career-os-.git` and asked for it to be pushed.

The local Next.js source was pushed to **main** while preserving the repository's initialization history. Verified main commit:

`93006b229483008ac6df86f42e28c29091cbd680`

This push did not upload the live Lovable framework tree to main or establish automatic Lovable/GitHub synchronization.

## 6. Daily AI Learning Manager extension — 9 October 2026

You then requested an extension of the existing application, using Hermes, your Google Docs curriculum, Career OS progress and Telegram. You explicitly instructed that existing frontend, Copilot and core learning/task structures be preserved and reused.

### Deployment target and runtime clarified

You confirmed the deployed Lovable application as the target. Although you initially described Hermes as running in Lovable, inspection found an installed **Hermes v0.21.3 Windows runtime**. Lovable hosts Career OS and agent API routes; Hermes is a separate gateway/worker on this computer.

### Curriculum source

[AI Career Transition Learning Guide](https://docs.google.com/document/d/1mvhBvoHWR70ZlynZTQp2KVvzyAwU0O6w-o7tTlC85dU/edit?usp=sharing)

Actual document access showed that the text ends at **V-6** while its table of contents lists **Volumes I–XVI**. You supplied the same link again. Only the available **30 chapters** were imported, with an incomplete-source notice. Missing chapters were not generated or invented. The real owner's guide was imported; no demo/fixture progress was copied into the account.

### Extension implemented and preserved

- Curriculum sources/versions/content hashes and stable chapter IDs.
- Import validation, repeat-import handling and preservation of a previously good version after a failed/incomplete update.
- Source references, priorities and prerequisites with explicit inference labels.
- Manual/evidence-based learner baseline, reviewed by the user rather than automatically marking knowledge.
- Eligible daily recommendations, duration budgets, practical outcomes and completion criteria.
- Canonical existing Learn tasks rather than a duplicate agent task database.
- Existing Skills, Tasks, Today, Dashboard, Settings, Focus and Daily Log integration.
- Transactional focus/learning feedback and ledger accounting, including avoidance of counting mirrored timer minutes twice.
- Authenticated owner-scoped learning APIs, input validation, persisted idempotency and request/rate safeguards.
- Telegram assignment/message/reply mapping and validation of real sender/chat identity.
- Delivery reservations before sending, actual receipts, and unknown-outcome handling that avoids blind resend.
- Scheduler leases, run tracking, bounded catch-up and persisted timezone/preferences.
- Installable Hermes `career-os-learning` skill, narrow API client, Python precheck and private Telegram sender helper.
- Explicit paused/incomplete states and integration/test controls.

Production uses its own additive **Drizzle migrations 0000–0004**. The matching Next.js implementation has separate Supabase migrations `202610090001`–`202610090005`. **Do not apply the Next.js migrations to the already-migrated Lovable database or merge the two framework trees together.**

### Source locations

Next.js learning code: `src/lib/learning/{models,parse,engine,http,auth.server,service.server}`, `src/app/api/learning`, `src/app/api/agent/learning`, `src/features/learning-manager`, modified existing store/domain/feature integrations, migrations and tests.

Hermes adapter in repository: `scripts/hermes-learning/{SKILL.md,client.mjs,telegram-send.mjs,precheck.py}`. The installed skill targets the production API contract, including delivery-begin/finish, run claims and command acknowledgement. Do not guess endpoint contracts from the other framework implementation.

### Verification at this phase

- Next.js lint/typecheck/build and **64 unit/database/adapter tests** were reported passing after security dependency patches.
- Seven existing browser regression flows were verified; one transient Chromium network-suspended failure was rerun successfully.
- Lovable build agent reported **55 learning tests**, build/typecheck and **ten real-database safeguards** passing with disposable data cleaned up. These are recorded build-agent results, not a complete Telegram learning loop.
- Live publication/navigation and privacy gates were checked.
- Imported source/chapters and owner binding verified.
- Initial authenticated worker check returned 401 until the server token fingerprint was updated.

## 7. Secure app/Telegram setup — 9 October 2026

### Where configuration was placed

- Lovable: **Cloud → Secrets**, including `AGENT_TOKEN_SHA256` and `TELEGRAM_OWNER_ID_SHA256`. The raw agent bearer belongs only on the Hermes host; Lovable compares a fingerprint.
- Hermes: protected local profile configuration/environment, containing the matching agent bearer, bot credential and provider credentials. No raw credentials belong in frontend variables or Git.

The Lovable connector could not replace an existing secret, so you were guided to replace `AGENT_TOKEN_SHA256` in the Secrets UI and publish for the live app. You replied that this was done. Subsequent authenticated Career OS calls returned **HTTP 200**, superseding earlier documentation that still lists token-fingerprint activation as pending.

Telegram bot authentication was initially invalid, then successfully configured. A real private `/start` established the owner/destination; the server sender fingerprint and local recipient binding were saved. A controlled Career OS connection message was delivered, its receipt saved, and Hermes received your “OK” reply.

This proved transport and inbound receipt, **not completed learning progress**. The inference provider then rejected the reply.

### Secret handling history

Bot/provider secrets were pasted into the chat despite requests to use secure configuration. Those values are intentionally excluded here. You were advised to revoke/rotate exposed credentials. A replacement OpenRouter credential was subsequently entered through the masked local terminal and verified. Rotation of the previously exposed Telegram bot token has not been conclusively verified in the latest audit; getMe success alone does not prove rotation.

## 8. API failure diagnosis and OpenRouter migration — 9 October 2026

The Telegram screenshot showed **HTTP 403: OpenCode's free tier can only be used from within OpenCode**. Live Career OS learning API returned 200 and Telegram had delivered/received the test, so the immediate failure was Hermes inference, not a blanket failure of the app API or Telegram transport.

The old configured OpenRouter credential also returned **401**. Switching providers without fixing authentication would not resolve it.

You requested an inference-only migration: preserve Career OS, Telegram and existing automation; replace the OpenCode provider with a valid OpenRouter credential through a secure local terminal.

### Migration completed

- Provider changed to `openrouter`, endpoint `https://openrouter.ai/api/v1`.
- Replacement key validated with authentication **HTTP 200** and saved using supported Hermes secure configuration.
- Old invalid OpenRouter credential removed from the active credential pool; unrelated configuration preserved.
- A stale inherited process credential was identified as another source of 401 and excluded from the restarted gateway environment.
- Credential file ACLs were checked; private migration backups kept outside the repository.
- First selected free model: `nvidia/nemotron-3-super-120b-a12b:free`.
- Real inference, natural language, automatic tool calling, tool-result roundtrip and strict structured output passed.
- A real Hermes terminal tool read the Career OS API with **HTTP 200**.
- Controlled Telegram delivery/receipt and a real reply reading the saved learning schedule were verified under this free model.
- Gateway restarted successfully and Telegram connected.
- Existing learning job was updated to the provider/model and remained paused.
- Supported Windows Startup-folder login entry installed; actual reboot/logon and crash recovery were not tested.

No genuine topic completion or learned minutes were fabricated. The baseline remained unconfirmed, preventing assignment of a real learning topic for the full completion test.

Evidence: [OpenRouter migration report](C:/Users/manoj/AppData/Local/hermes/runtime/openrouter-migration/REPORT.md).

## 9. Approved Muse Contributor default — 9 October 2026

You asked to make Meta Muse 1.3 Contributor the default. Because the earlier request required approval before a paid model, the exact model and quoted pricing were presented. You explicitly replied **“Approve Muse Contributor.”**

### Applied

- Hermes default and existing learning job override: **`meta/muse-spark-1.3-contributor`**.
- Provider remained OpenRouter.
- Existing job identity, prompt, schedules, skill, precheck, working directory, recipient and paused state preserved.
- Existing reasoning preference preserved; validation enabled reasoning as required by the model.

### Historical verification

- Stored credential authentication 200 and authenticated model catalog lookup.
- Natural-language inference, automatic tool selection/validated arguments, tool-result roundtrip and strict JSON-schema response all HTTP 200.
- Catalog context reported 1,048,576 tokens.
- Four synthetic validation requests reported total cost **$0.0002953**.
- Real Hermes CLI session used Muse, called terminal tools and read Career OS API 200. Hermes estimated **$0.001200426** for that session; an actual-cost receipt was unavailable.
- Gateway restarted as PID **56772**, with Telegram/local API and scheduler heartbeat verified then.

Prices at approval were **$0.10/million input tokens and $0.20/million output tokens**. These are recorded approval-time figures, not a fresh price quotation. The Telegram read-only roundtrip from the free-model phase was not repeated under Muse during the model switch.

**Scope distinction:** this changed Hermes inference. It did not change the published app Copilot's Lovable gateway model. If the intended requirement is Muse for every application AI feature too, that remains a separate configuration decision/work item.

Evidence: [Muse verification report](C:/Users/manoj/AppData/Local/hermes/runtime/openrouter-migration/MUSE_REPORT.md).

## 10. Scheduler design and activation state

One existing Hermes pulse runs on a five-minute schedule with a precheck that reads the app's persisted settings. It was designed to avoid duplicate independent cron jobs and to skip model invocation when no eligible work is due.

Last verified learning schedule, **Asia/Kolkata**:

| Action | Local time |
| --- | --- |
| Guide synchronization | 10:30 AM |
| Daily learning recommendation | 11:00 AM |
| Evening completion check-in | 8:30 PM |

Job ID: `46a628bb9ae9`. **Paused.** A installed schedule is not proof that jobs executed successfully.

Remaining activation gates:

1. User reviews topic levels in Skills and clicks **Baseline done**.
2. Create a genuine eligible learning assignment.
3. Deliver it with a persisted Telegram reservation/receipt.
4. Process the learner's actual completion/partial feedback.
5. Re-read persisted topic/task/learning progress and Daily Log; retry same reply to verify no duplicate minutes.
6. Verify gateway recovery/reboot and the scheduled job before activation.

The complete assignment → delivery → learning reply → persisted progress → next recommendation loop remains **unverified**. Telegram connectivity and successful inference are only parts of that loop.

## 11. GitHub, branches and pull request — verified again 10 October 2026

| Branch/artifact | Revision/status | Meaning |
| --- | --- | --- |
| `main` | `93006b229483008ac6df86f42e28c29091cbd680` | Initial local Next.js app push; newer extension is not merged here |
| `codex/daily-learning-manager` | `fd32277bf3601efaa1875ca4d958b4c27c806111` | Current local HEAD; matching remote SHA verified with git ls-remote |
| `codex/lovable-learning-manager` | `63c172fc221de0abb6d8be89af80718c71d0c48b` | Exported Lovable production source/migrations plus delivery-helper artifacts; separate history |
| [PR #1](https://github.com/manojastro/career-os-/pull/1) | **OPEN, DRAFT, not merged**, confirmed through GitHub connector | “Add Daily AI Learning Manager and transactional Hermes integration”; Next.js branch → main |
| Latest inspected Lovable editor source | `4473f3723dc547bd6c15708948257f0e13c033a7` | Published project/source inspection; exact served runtime SHA not independently exposed |

Significant extension commits include:

- `b0e2d54`: preserve production Lovable learning source.
- `221366d`: owner-scoped curriculum schema/atomic transactions.
- `7a61497`: validated importer/authenticated agent APIs.
- `25bea98`: existing workspace integration/installable Hermes skill.
- `a74c6c4`/`6b2e226`: real guide import/private binding/deployment verification records.
- `98b3fdd`/`e873493`: private Telegram destination/server sender setup records.
- `6d5a0a7`/`63c172f`: reservation-aware private Telegram sender helper.
- `fd32277`: include standalone learning time in the weekly category breakdown without counting timer mirrors again.

New audit artifacts and this context document are **uncommitted and not pushed**. No automatic GitHub-to-Lovable synchronization has been established by these branch pushes. Do not assume merging the Next.js PR deploys the Lovable app.

## 12. Comprehensive functional audit — 9–10 October 2026

You requested an audit of all existing Career OS functionality **excluding the unfinished Daily AI Learning Manager**, with no rebuilding, redesign, provider changes or automation changes. You then explicitly said **“No test account—continue safe checks.”**

### Work actually performed

- Inspected repository architecture, core feature/UI/API source, migrations, types/store/calculations, deployment metadata, relevant live Lovable source, and existing tests.
- Ran supported install/lint/typecheck/test/build/browser commands.
- Added isolated local demo browser tests and real embedded PostgreSQL owner/RLS/constraint/Storage-policy tests.
- Tested normal task/goal/skill/project/contact/interview/application/Copilot/notes/resource/journal/export flows using AUDIT fixtures in fresh browser localStorage.
- Ran real anonymous and sample-mode checks against the published app across 14 routes at 1440/768/390px.
- Checked live anonymous API validation/auth rejection, read-only database schema/policy/aggregate metadata, private bucket status, agent API health, Hermes process health and Telegram getMe.
- Reviewed dependencies, current tracked-file secret patterns, errors/network responses and measured navigation performance.
- Did not sign into a private production account, write personal career records, upload files, trigger learning jobs, send messages, change providers, fix business code or deploy.

### Results

| Check | Result |
| --- | --- |
| npm ci/lint/typecheck/build | Passed; final lint/typecheck also passed after audit tests added |
| All Vitest tests | 71/71 passed with audit DB tests; includes 51 excluded learning tests |
| Core-only unit/database subset | 20/20 passed |
| Original demo Playwright suite | 7/7 passed before audit additions |
| Expanded local audit | 19 distinct cases across runs: **10 passed, 9 failed** expected-behavior assertions |
| Live anonymous/sample diagnostics | Two separate tests passed; one deliberately asserts the observed Copilot error rather than successful AI functionality |
| Live core UI page errors | Zero sampled page errors; supplemental login/Vault/Agent console collection zero errors |
| Live DB metadata | 60 public tables report RLS enabled; private career-evidence bucket confirmed |
| Production dependency audit | Zero known advisories with development dependencies omitted |
| Development dependency audit | Five high findings in the lint dependency chain; not repaired during audit |
| Navigation measurement | 42 sample route visits, heading ready 171–1,001 ms, median 266.5 ms; not Core Web Vitals/private DB measurement |

### Reproduced local defects

1. Arbitrary start-time Planner block (08:30) is saved but hidden in day rendering.
2. Task editor can mark Completed while leaving completed_at null; reopen timestamp logic is inconsistent.
3. Refresh loses the active unsaved Focus session/time while task remains Doing.
4. Today actual total drops from 1m to 0m after completing the focused task.
5. Tablet shell overflows every tested core route at 768px.
6. Keyboard focus escapes an open modal with reverse Tab.
7. Demo accepts duplicate exact skill names contrary to hosted uniqueness.
8. Editing task date leaves its linked Planner block on the old date.
9. Confirmed Copilot High-priority creation saves Medium.

The published sample app independently reproduced tablet overflow and **Copilot HTTP 401** instead of intended local fallback. Dashboard stage omissions, store 1,000-row truncation, split writes/activity-log consistency, search destinations, missing restore and AI rate/cost control were documented as source-confirmed defects/limitations or risks, not fabricated live incidents.

### Latest operational findings

- Career agent authenticated health API: **HTTP 200**.
- Telegram getMe: **HTTP 200 / ok=true**. No audit message sent.
- Hermes gateway status: **no process detected**; PID 56772 from the earlier successful restart was absent. Saved running state was stale. Root cause of exit was not established, and no restart was performed during the audit.
- Last baseline check remained false; job remains paused.
- Vercel connector listed Career OS projects but deployment details returned 403; deployment revisions/URLs remain unverified.
- No isolated account: private login/logout/session expiry, current account persistence, live cross-user authorization, file uploads and authenticated app AI success were **not retested**.

### Updated readiness judgment

**Not ready for daily use.** This supersedes earlier broad “core app usable now” statements. The later audit exercised edge cases the first regression suite did not cover. Passing the earlier suite or successful historical deployment login does not disprove the newly reproduced defects or certify the current private deployment.

Full evidence, feature matrix, exact reproduction steps/files and prioritized fixes: [CAREER-OS-FUNCTIONAL-AUDIT.md](CAREER-OS-FUNCTIONAL-AUDIT.md).

## 13. What remains to do

### Application reliability first

1. Centralize task completion/reopen metadata and reconcile Dashboard/Log counts.
2. Persist/recover Focus sessions and prove retry idempotency/background accuracy.
3. Render arbitrary Planner times, normalize database time format, and update linked task/block schedules together.
4. Correct Today daily totals and Dashboard job-stage coverage.
5. Repair tablet layout, modal focus, duplicates and record-specific search navigation.
6. Correct explicit demo Copilot fallback and requested priority while preserving current provider until separately authorized.
7. Harden atomic writes/affected-row checks; pagination/complete exports; actual backup restore.
8. Run isolated hosted two-user/account/file/API workflows before declaring readiness.

### Learning/agent operation separately

- User baseline confirmation and genuine completion feedback.
- Full persisted learning roundtrip, reply retry and scheduled execution verification.
- Investigate stopped gateway; verify supported startup/recovery after reboot.
- Confirm rotation of any exposed bot credential through secure settings.
- Keep job paused until activation gates pass.
- Obtain complete curriculum if all I–XVI volumes are required.

### Delivery/documentation

- Audit/context artifacts have not been committed/pushed.
- PR #1 is draft/unmerged; merging is not authorized by this request for context.
- Preserve source histories and separate migration/deployment paths.
- Earlier setup docs/PR descriptions contain stale “token update pending” and “supervisor missing” details. Later successful auth and installed login entry supersede those items; current gateway health is still failed.

## 14. User decisions and continuing constraints

Recorded decisions:

- Approved the separate Lovable port/deployment.
- Authorized the initial GitHub push.
- Selected existing Lovable deployment as learning-extension target.
- Supplied the Google Docs guide; supplied same link when incomplete source was flagged.
- Completed the Lovable secret/publish step and Telegram test reply.
- Entered replacement OpenRouter key securely after the exposed-key warning.
- Explicitly approved paid Muse Contributor for Hermes/default learning job and limited verification.
- Selected safe audit checks without a private test account.

Continuing boundaries:

- No secrets in chat/source/Git or printed logs.
- No production personal-data mutation without appropriate approval/isolated scope.
- No real networking messages/applications or notifications without authorization.
- Do not invent learning completion, minutes, mastery or missing curriculum chapters.
- Do not infer working autonomous learning from successful Telegram transport or inference alone.
- Do not rebuild/redesign the application or switch providers as part of the audit/context task.
- Read applicable AGENTS.md and installed Next.js guides before code changes.
- Draft PR/branch push is not merge or deployment authorization.

## 15. Key files for the next person/agent

| Document | Purpose and freshness |
| --- | --- |
| [This context](CAREER-OS-PROJECT-CONTEXT.md) | Chronology, decisions, source separation and latest state |
| [Functional audit](CAREER-OS-FUNCTIONAL-AUDIT.md) | Latest comprehensive test evidence, limitations and fix priority |
| [README](README.md), [SPEC](SPEC.md), [capability map](CAPABILITY-MAP.md) | Original Next.js product/architecture; some “what works” language must be read alongside audit |
| [Learning deployment](docs/LEARNING_DEPLOYMENT.md) | Import/deployment/source and test record; activation paragraphs partly superseded |
| [Hermes setup](docs/HERMES_LEARNING_SETUP.md) | Contracts/runtime design; older operational blockers need latest context |
| [Learning review](docs/LEARNING_REVIEW.md) | Security/architecture/accounting review and migration separation |
| [Learning tasks](tasks/learning-todo.md), [plan](tasks/learning-plan.md) | Extension scope and unfinished roundtrip |
| [Hermes skill](scripts/hermes-learning/SKILL.md) | Agent API behavior, safety, delivery and completion rules |
| [OpenRouter migration report](C:/Users/manoj/AppData/Local/hermes/runtime/openrouter-migration/REPORT.md) | Historical free-model migration and real read-only Telegram roundtrip |
| [Muse report](C:/Users/manoj/AppData/Local/hermes/runtime/openrouter-migration/MUSE_REPORT.md) | Approved default/model tests and limits; current health requires audit context |

## 16. Copyable continuation brief

> Career OS has two distinct source trees: local Next.js at `D:\ai apps dump\career os` on `codex/daily-learning-manager` (fd32277), and the published TanStack/Lovable app at https://career-os-manoj.lovable.app, project 79875339-208c-46e9-9a92-43b90bb04184. Production source is exported on `codex/lovable-learning-manager` (63c172f); inspected editor revision 4473f37, exact served SHA unverified. GitHub main remains 93006b2; PR #1 is open draft, not merged. Hermes v0.21.3 runs separately on Windows, configured for OpenRouter `meta/muse-spark-1.3-contributor` with explicit paid-model approval. App Copilot still uses Lovable gateway; it was not changed by Hermes configuration. Thirty real guide chapters imported, source incomplete after V-6. Baseline last unconfirmed; learning job 46a628bb9ae9 paused. Historical Telegram transport/read-only reply and OpenRouter inference/tools/API 200 passed, but genuine learning completion/database progress/scheduled loop remain unverified. Latest audit found gateway stopped/stale PID despite bot getMe 200 and Career agent API 200. Comprehensive core audit excluded unfinished learning automation and used safe local-demo/anonymous/read-only checks because no isolated account was supplied. Build/lint/types and 20 core unit/DB tests pass; 19 distinct expanded local browser cases yield 10 pass/9 fail. Main defects: editor completion timestamps, Focus refresh loss, invisible/stale Planner blocks, Today totals, tablet overflow, modal focus escape, demo duplicates, Copilot priority; published sample Copilot returns 401. Read CAREER-OS-FUNCTIONAL-AUDIT.md before fixes. No business fixes/deployments were made during audit. Audit/context files are local/uncommitted. Do not change providers, secrets, automation, production personal data, send messages or activate jobs without applicable authorization. Keep migrations/framework histories separate, and distinguish historical successes from current health and untested private workflows.
