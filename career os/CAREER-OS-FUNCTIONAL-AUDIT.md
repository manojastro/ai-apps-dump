# Career OS functional audit

**Audit date:** 10 October 2026, Asia/Kolkata (test timestamps are recorded in UTC).

**Overall assessment: Not ready for daily use.** Core demo workflows work, but task completion through the editor produces incorrect completion metadata, valid Planner blocks can disappear, and refreshing an active focus session loses its unsaved time. Private production persistence and login lifecycle could not be verified safely. This is a readiness assessment, not a claim that every module is broken.

The unfinished Daily AI Learning Manager is excluded from this assessment and from core test counts. Existing Hermes and Telegram were checked only for service health. No provider, credential, automation, application business logic, production schema, or deployment was changed. No learning job, notification, networking message, or application was sent.

## A — Application overview

### Repositories, revision and deployment

| Item | Observed result |
| --- | --- |
| Repository | [manojastro/career-os-](https://github.com/manojastro/career-os-) |
| Local checkout | `D:\ai apps dump\career os` |
| Checked-out branch | `codex/daily-learning-manager` |
| Local HEAD | `fd32277bf3601efaa1875ca4d958b4c27c806111` |
| GitHub push verification | `git ls-remote origin refs/heads/codex/daily-learning-manager` returned the same SHA. The existing implementation is pushed to this branch. This does not establish a merge into the default branch. |
| Lovable export branch | Remote `codex/lovable-learning-manager` returned `63c172fc221de0abb6d8be89af80718c71d0c48b`; it has a separate source history. |
| Published app examined | [career-os-manoj.lovable.app](https://career-os-manoj.lovable.app) |
| Lovable project | Career Compass, project `79875339-208c-46e9-9a92-43b90bb04184`; published and ready according to project metadata. |
| Lovable editor revision | Latest commit `4473f3723dc547bd6c15708948257f0e13c033a7`, edited 9 October 2026. This is the editor revision; the published runtime did not expose a verified build SHA. |
| Deployment parity | **Not established.** Local code is Next.js; Lovable project source uses TanStack Start/Vite. Local test success cannot certify the published application. |
| Vercel | Connector listed six Career OS related projects, including `career-os`, `career-os-app`, and `career-os-github`. Reading deployment details returned HTTP 403 for the account scope. Vercel CLI is not installed. Deployment URLs/revisions remain **BLOCKED BY CONFIGURATION**, not evidence that no Vercel deployment exists. |
| Audit artifacts | New report, isolated test files, and JSON evidence are uncommitted. They were not pushed or deployed during the audit. |

### Architecture and operating modes

- **Local repository:** Next.js 16.3.8 App Router, React 19, TypeScript, React Hook Form/Zod, dnd-kit, TipTap, Recharts, Supabase Auth/PostgreSQL/private Storage, Vitest/PGlite/Playwright. Routes live under `src/app`; business screens under `src/features`; shared calculations in `src/lib/domain`; persistence in `src/lib/store.tsx`; provider adapters in `src/ai`.
- **Local run:** production build at `http://127.0.0.1:3102`, with no configured hosted Supabase/provider variables. Browser workflows use the actual demo repository and `career-os-demo-v4` localStorage. This is browser persistence, not Supabase persistence.
- **Lovable:** published application, connected Supabase cloud database, authenticated private workspace and explicit sample workspace. Production source includes additional agent/Vault panels. Its app AI gateway is separate from Hermes' OpenRouter provider.
- **Local APIs:** `/api/ai/command`, `/api/ai/analyze-jd`, and learning/agent-learning routes. Learning business functionality is excluded. Lovable additionally exposes agent context/health and agent action routes.
- **Auth:** Supabase email/password, signup/confirmation, client workspace protection and independently authenticated server APIs. Local proxy refreshes/verifies the session. The private workspace depends on a valid authenticated user.
- **State:** typed client repository, immediate local state changes, localStorage in demo mode, Supabase reads/writes in hosted mode, activity records and selected realtime refreshes. This is not a full offline sync engine.

### Test environment and evidence

Inspected `README.md`, `SPEC.md`, `CAPABILITY-MAP.md`, `AGENTS.md`, routes, components, feature code, domain types/calculations, AI adapters, all local migrations, existing tests, and relevant production source. Installed Next.js guides were read before adding audit tests.

The user explicitly said **“No test account—continue safe checks.”** No private production login, signup, upload, or career-record write was performed. Anonymous live API calls and a fresh browser's existing sample mode were used. Live database checks were metadata and aggregate SELECTs. Existing agent health authentication was checked without queueing work. Health GETs may update operational last-seen/rate-limit metadata; no personal career records were changed.

Evidence identifiers used throughout the tables:

| ID | Evidence and scope |
| --- | --- |
| E1 | [Core workflow and defect browser tests](e2e/functional-audit.spec.ts); [initial final combined output](audit-browser-results-final.json); [targeted follow-up](audit-targeted-results.json); [corrected schedule reproduction](audit-schedule-results.json). Across separate runs, 19 distinct local demo cases: ten passed, nine failed reproducible expected-behavior assertions. B/I persistence checks were strengthened and rerun. |
| E2 | [Production browser test](e2e/production-readonly-audit.spec.ts); [successful live run](audit-production-browser-results.json); [42 route measurements and responses](audit-production-observations.json). Actual published app; anonymous/sample mode only. |
| E3 | [Supplemental production run](audit-production-console-results.json): live `/vault` and `/agent` sample gates, console/page-error collection; one test passed, zero errors in these sampled visits. |
| E4 | [Isolated database tests](tests/functional-audit-database.test.ts): seven real embedded PostgreSQL tests against the two original migrations. Auth claims and Storage infrastructure are test fixtures; this is not a hosted Supabase network test. |
| E5 | Original `e2e/career-flows.spec.ts`, `tests/domain.test.ts`, `tests/copilot.test.ts`, `tests/job-gap.test.ts`; executed baseline and core-only runs described below. |
| E6 | Live Lovable connector reads: project/package/source, database table/RLS/policy/trigger metadata, private bucket, aggregate counts. Recorded findings in D/E below; no row contents or secrets included. |
| E7 | [Dependency audit JSON](audit-dependency-results.json), `npm audit --omit=dev --json`, tracked-file secret-pattern scan. Scope limitations in the security section. |
| E8 | [Read-only integration health script](tests/audit-integration-health.py), Hermes gateway status/process check, existing authenticated Career API pulse. No inference or messages sent. |
| S | Source inspection only. It establishes implementation or a code defect/risk; it does not establish a completed live transaction. Paths in F identify the relevant functions. |

### Commands actually executed

| Command/run | Outcome | Scope/qualification |
| --- | --- | --- |
| `npm ci` | PASS | Installed 507 packages; audited 508. Registry responses were slow. Reported five high dependency findings. |
| `npm run lint` | PASS | Also rerun after adding all audit test files; exit 0. |
| `npm run typecheck` | PASS | Also rerun after adding all audit test files; exit 0. |
| `npm run test` | PASS | Baseline 64/64; with database audit tests 71/71 across nine files. These totals include 51 excluded learning tests and are not the core functional pass rate. |
| Core-only Vitest selection | PASS | `npx vitest run tests/copilot.test.ts tests/domain.test.ts tests/job-gap.test.ts tests/functional-audit-database.test.ts`: 20/20 across four files. |
| `npm run build` | PASS | Next.js production build completed, including compilation, type checking and route generation. Compilation about 9.9 s; build type checking about 11.6 s. |
| `npm run test:e2e` before audit additions | PASS | Original seven Chromium tests passed. They run the local production build in demo mode. |
| Expanded local audit | FAIL, as expected from defects | Initial 9/16 passed, 7/16 failed. Targeted follow-up verified Focus Complete and reproduced schedule/priority defects. Final distinct-case aggregate across runs: 10/19 passed, 9/19 failed. F describes each failing assertion. No application code was altered to make these green. |
| Published anonymous/sample audit | PASS as a diagnostic test | Corrected live test 1/1 passed; it explicitly expects the observed Copilot 401. That diagnostic pass does **not** mean demo Copilot works. |
| Published console/agent gate audit | PASS | Separate test 1/1 passed, no sampled console/page errors; both private agent surfaces were gated. |
| Dependency audit | Production: zero known advisories; all dependencies: five high | Development lint dependency chain only in the examined output. No upgrades performed. |

The combined E1 JSON includes an initial live failure caused by clicking sample mode before hydration. Adding a network-idle wait fixed the test, and E2 subsequently passed. It is not counted as an application defect. An earlier weaker modal assertion also passed; the final reverse-Tab assertion reproduces the actual focus escape. The targeted schedule test initially timed out because its selector used “Scheduled date” instead of the actual “Scheduled day” label; the corrected run reached the real date-mismatch assertion. That timeout is not counted as another defect. Final local distinct-case result across these runs is 10/19. No tests in these selected runs were skipped.

No overall feature pass percentage is supplied: the expanded tests intentionally target defects, and account-dependent workflows are blocked. Adding together demo, schema, and diagnostic test passes would misrepresent production readiness.

## B — Feature status matrix

**Scope rule:** VERIFIED WORKING below means verified in the stated environment only. Every demo write/persistence result remains unverified against the hosted private database. An implementation present in source with no executed workflow is NOT TESTED or PARTIALLY WORKING, never a verified production success.

### Module summary

| Module | Overall status | Main qualification |
| --- | --- | --- |
| Dashboard | PARTIALLY WORKING | Normal demo counters pass; editor metadata and omitted job stages affect summaries |
| Today | PARTIALLY WORKING | Normal execution passes; actual total decreases after completion |
| Planner | BROKEN | Valid arbitrary-time blocks hidden; existing block lifecycle incomplete |
| Tasks | PARTIALLY WORKING | Normal create/checkbox lifecycle passes; editor completion and linked rescheduling fail |
| Focus | PARTIALLY WORKING | Normal save works; refresh recovery broken; hosted save unverified |
| Goals | PARTIALLY WORKING | Demo progress verified; editing and completed-goal lifecycle incomplete |
| Manual Skills | PARTIALLY WORKING | Topic/readiness/proof tested; demo duplicate handling fails |
| Projects | PARTIALLY WORKING | Core demo progress/URLs verified; production extra panels untested |
| Networking | PARTIALLY WORKING | Contact/followup/history tested; core reminder delivery absent |
| Interviews | PARTIALLY WORKING | Answer/practice/counts tested; difficulty/skill/mock workflows incomplete |
| Jobs/JD | PARTIALLY WORKING | Dropdown pipeline tested; drag/drop absent; AI inference unverified |
| Daily Log | PARTIALLY WORKING | Normal demo ledger/journal pass; task-editor metadata can distort completion |
| Copilot | PARTIALLY WORKING | Local confirmed create works; published sample fallback and priority handling fail |
| More | PARTIALLY WORKING | Selected demo records/export tested; restore absent, private files unverified |
| Authentication/private Settings | BLOCKED BY CONFIGURATION | No isolated account for successful login/write/expiry tests |
| Production agent/Vault | NOT TESTED authenticated operations | Sample access gates verified; no queue/file/config writes |


### Dashboard and Today

| Feature | Expected behavior | Implementation/status | Test performed | Actual result | Evidence | Severity | Recommended fix/next check |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Dashboard task counts and recent activity | Completion changes counts/activity | VERIFIED WORKING in demo checkbox path | A, navigation/reload | One completed task, one recorded focus minute; activity created | E1 A, E5 | — | Repeat with isolated hosted account |
| Dashboard actual work hours | Sum recorded work without duplicate ledger | VERIFIED WORKING for tested demo session | A + domain tests | 1m session counted once; weekly task/ledger calculations passed selected tests | E1/E5 | — | Hosted RPC and retry test pending |
| Planned weekly hours | Reflect scheduled work | PARTIALLY WORKING | A + formula inspection | Uses scheduled task estimates; standalone Planner blocks contribute no planned time | E1/S `weeklyTime` | P2 | Define task vs block policy and include standalone blocks once |
| Career/goal progress | Linked work affects correct goal | VERIFIED WORKING in demo | B + domain tests | Two milestones 50→100%; linked unfinished task reduces to 67%; unrelated work has no effect | E1/E5 | — | Verify hosted data consistency |
| Skills/projects/interview summaries | Reflect stored status/progress/practice | PARTIALLY WORKING | C/D/F; source inventory | Tested project/practice values agree with demo records; full production summaries unverified | E1/S | — | Isolated hosted fixtures for every card |
| Overdue tasks/followups | Due items appear and change when resolved | PARTIALLY WORKING | E followup; overdue source logic | Due followup count cleared after future followup; overdue task filtering implemented, not separately exercised | E1 E/S | — | Add overdue-task boundary fixture |
| Application statistics | Display every supported stage | PARTIALLY WORKING | G total + stage-array inspection | Applied count verified; Dashboard omits Planning to Apply, Hiring Manager, Rejected, Withdrawn stage rows | E1 G/S | P2 | Use shared complete stage definition (F10) |
| Persistence after refresh/navigation | Same records/counts | VERIFIED WORKING in demo | A–I reloads | Tested browser-storage records survived reload | E1 | — | Login/browser restart hosted persistence is blocked |
| Today pending list/completion | Show today's unfinished work | VERIFIED WORKING in demo checkbox path | A | Completion removes task from pending list; Dashboard/Log update | E1 A | — | Repair editor completion metadata separately |
| Today priority ordering/reordering | Respect manual order and priority policy | NOT TESTED end to end | Source review | dnd-kit pointer/keyboard ordering and writes exist; sort_order is primary, high priority a tie-breaker | S TodayPage/insights | — | Verify reorder and reload with two tasks |
| Today editing/reschedule/overdue/next-up | Updates stay consistent across views | PARTIALLY WORKING | A schedule; source review | Controls exist; reschedule can leave old Planner block (F9) | E1/S | P1 | Update linked scheduling records together |
| Today actual total | Retain recorded work after completing task | BROKEN in demo | Dedicated defect assertion | 1m becomes 0m when the completed task leaves pending list | E1 | P2 | Sum today's ledger, not pending tasks (F4) |
| Today schedule/quick notes | Display blocks and save note | PARTIALLY WORKING | A schedule; source review | Linked schedule visible; note saving code present, separate quick-note workflow not exercised | E1/S | — | Verify quick-note reload and failure feedback |

### Planner, Tasks and Focus

| Feature | Expected behavior | Implementation/status | Test performed | Actual result | Evidence | Severity | Recommended fix/next check |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Create block/schedule existing task | Save and show selected time | PARTIALLY WORKING | A at 18:00; arbitrary 08:30 defect | 18:00 works; saved 08:30 block is hidden in day view | E1 | P1 | Render arbitrary times; normalize database time (F1) |
| Edit/delete/move existing block | Maintain one current schedule | NOT IMPLEMENTED in inspected core UI | Source review | No existing-block edit/delete/move controls; drag/drop creates from unscheduled tasks only | S PlannerPage | P2 gap | Provide block lifecycle after schedule consistency fix |
| Week/month views | Correct selectable date range | PARTIALLY WORKING | Source + route visits | Week exists; “Month” renders 28 days from a Monday, not the calendar month | S/E2 | P2 | Render true month boundaries or accurately label four-week view |
| Date/timezone behavior | Dates agree across views | PARTIALLY WORKING | A same-day + domain tests; source | Local-day helper uses browser timezone; profile timezone is not the core planner's authority. DST/travel/midnight/overnight not tested | E1/E5/S | — | Test boundary dates; use one documented zone policy |
| Task create/edit ordinary fields | Preserve title/type/priority/dates/estimate/links | VERIFIED WORKING for tested demo fields | A/C/D/G; existing tests | Task creation, linked skill/project/goal and scheduling persist | E1/E5 | — | Additional field permutations and private DB test pending |
| Six task stages | Consistent lifecycle metadata | PARTIALLY WORKING | A + Completed editor assertion; source | Stage choices exist; editor Completed leaves completed_at null | E1/S | P1 | Centralize completion/reopen transitions (F2) |
| Task actual duration | Record focus minutes correctly | PARTIALLY WORKING | A/F4 | Ledger and task actual_minutes agree for one saved session; Today summary fails | E1 | P2 | Ledger-derived daily totals; retry/failure tests |
| Manual milestone/application/contact links | Select intended associations | PARTIALLY WORKING | Source review | Types/ownership exist; task form only skill/project/goal. Job-gap flow creates milestone/application links | S TaskForm/JobsPage | P2 gap | Add selective editing after validating parent associations |
| Task archive/delete | Supported safe lifecycle | NOT IMPLEMENTED in common task UI | Source review | Store soft-remove helper exists; no exposed task archive/delete control | S | — | Do not describe schema/helper as completed UI |
| Recurrence/subtasks/dependencies | Expand/run genuine workflows | NOT IMPLEMENTED | Schema/source inventory | Fields/tables exist without a complete execution/UI lifecycle | S | — | Keep capability documentation explicit |
| Start/pause/resume/stop Focus | Correct status/time and one save | VERIFIED WORKING in tested demo normal path | A: advance 61s, pause 10s, resume, save | Paused clock unchanged; one 1m record; stopped task becomes Today, not Completed | E1 A | — | Clock simulation does not prove background-tab accuracy |
| Focus complete task | Save session + completion | VERIFIED WORKING in tested demo normal path | Targeted 61s Complete/reload/Log check | Completed timestamp, actual_minutes=1, one ledger, Log one completion/1m; production transaction untested | E1 | — | Hosted normal and repeated-save tests |
| Focus refresh/interruption recovery | Preserve unsaved session | BROKEN in demo | Start then reload | Dialog/timer disappear; task remains Doing, no saved focus record | E1 | P1 | Persist/recover active session identity/time (F3) |
| Focus rounding/timer accuracy | Accurate elapsed time | PARTIALLY WORKING | Simulated clock + source | Per-second interval; duration rounded with minimum 1m even at zero elapsed. Real background throttling not tested | E1/S | P2 risk | Derive elapsed time from clock anchors and document rounding |
| Focus retry/idempotency | Avoid duplicate time after failures | PARTIALLY WORKING | Source inspection; normal-path A | Hosted RPC/API uses stable save identity; demo/fallback uses separate insert then update. Partial-failure retry not exercised | S FocusProvider/E1 | P2 risk | Fault-test both paths; retain idempotency without editing automation |

### Goals, manual Skills and Projects

| Feature | Expected behavior | Implementation/status | Test performed | Actual result | Evidence | Severity | Recommended fix/next check |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Goal create/milestones | Save and calculate linked progress | VERIFIED WORKING in demo | B + strengthened reload assertion | Milestones and task-driven equal-weight progress survive reload; target-date editing boundaries not tested | E1 B/E5 | — | Live persistence remains unverified |
| Goal completion state | Clearly distinguish progress and status | PARTIALLY WORKING | B | 100% progress still has active status; completion is manual. Not treated as automatic completion | E1 B | P3 clarity | Explain manual status; allow access to completed goals |
| Goal/milestone editing | Update existing descriptions/dates/title | NOT IMPLEMENTED beyond supported status changes | Source review | No general goal/milestone edit form; completed goals excluded from normal list | S GoalsPage | P2 gap | Add lifecycle controls only in a future implementation task |
| Parent/child goals | Correct hierarchy, no cycles | PARTIALLY WORKING | Domain tests/source | Child-score recursion has cycle guard; non-career goal auto-links first career goal, no parent picker | E5/S | — | Verify explicit hierarchy selection if implemented later |
| Skill create/category/status | Persist manual skill | PARTIALLY WORKING | C + duplicate assertion | Ordinary create works; duplicate exact names accepted in demo but rejected by SQL | E1/E4 | P2 | Consistent normalized duplicate handling (F7) |
| Skill edit | Edit identity/category | PARTIALLY WORKING | Source review | Status and five readiness fields editable; no general name/category edit control | S SkillsPage | P2 gap | Document currently editable fields |
| Topic create/status | Store topic progress distinctly | VERIFIED WORKING in demo | C | Applied topic persists; no artificial hands-on/interview increase | E1 C | — | “Applied” is a topic state, not evidence of interview capability |
| Readiness indicators | Independent knowledge/practice/proof/production/interview | VERIFIED WORKING for tested demo changes | C | Knowledge 3 did not change hands-on/interview 0 | E1/E5 | — | History/audit of readiness changes is not a complete feature |
| Skill linked tasks/evidence | Correct associations after reload | VERIFIED WORKING for demo URL evidence | C | Linked completed task and skill proof association persist | E1 C | — | Private file storage operation remains blocked |
| Skill learning/readiness history | Genuine historical records | PARTIALLY WORKING | Source | Tasks/topics/activity visible; no complete manual readiness-history interface | S | — | Do not equate current indicators with a historical ledger |
| Project create/status/progress | Linked completion changes progress | VERIFIED WORKING in demo | D | Building status, linked task and 100% project progress persist | E1 D/E5 | — | Hosted project_tasks progress relation requires testing |
| Project editing/GitHub/demo/architecture | Preserve editable content | PARTIALLY WORKING | D + source | URLs/architecture/status editable; name/description/problem/value have no general edit form | E1/S | P2 gap | Extend editor only in a subsequent fix task |
| Project milestones/tasks/evidence | Manage related records | PARTIALLY WORKING, production writes NOT TESTED | Production source review | Lovable ProjectTasksPanel adds milestone/task/evidence kinds, Start and feedback controls. These extra records are outside core task-based projectProgress calculation | E6/S | P2 risk | Verify both progress sources agree; no writes attempted |
| Project notes/decisions | Attach contextual notes | NOT IMPLEMENTED as complete inspected core workflow | Source/schema review | General notes do not provide project-link selection; project_decisions exists without core UI | S | — | Schema presence is not a completed notes workflow |
| GitHub synchronization | Read live repo changes | NOT IMPLEMENTED | Source inventory | Project GitHub field stores a URL; no repository-sync API workflow | S | — | Label as a link, not synchronization |

### Networking, Interviews and Jobs

| Feature | Expected behavior | Implementation/status | Test performed | Actual result | Evidence | Severity | Recommended fix/next check |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Contact create/LinkedIn URL | Persist identity and link | VERIFIED WORKING for tested demo contact | E + source | Contact created and persisted; URL field exists, live LinkedIn service not called | E1/S | — | Verify other identity fields separately |
| Contact edit/stage/followup | Preserve updates | PARTIALLY WORKING | E + source | Stage/notes/followup supported; full identity/company/URL editing absent | E1/S | P2 gap | Add identity editor in follow-on work |
| Interaction/history/dashboard reminder | Keep history and due count | VERIFIED WORKING in demo | E | Interaction persists; future followup removes due Dashboard item | E1 E | — | Hosted history writes still blocked |
| Contact search | Find contact | PARTIALLY WORKING | Source + global search shortcut | Global grouped search implemented; no module search filter workflow verified | S/E1 | P2 | Correct search destination (F12) |
| Followup reminder delivery | Actually notify user | NOT IMPLEMENTED for core manual followups | Source inventory | Dashboard due indicator exists; stored dates are not proof of delivery | S | — | Separate agent notification preferences from core reminder support |
| Production outreach/events | Review drafts; mark manual actions | NOT TESTED authenticated workflows | Production source review | Draft editing/copy/approval/manual sent/response history and sourced events exist; no automatic sending | E6/S | — | Use isolated account; preserve manual-send boundaries |
| Interview question/working answer | Save and edit answer | VERIFIED WORKING in demo | F | Created question and edited answer survived reload | E1 F | — | Hosted persistence not verified |
| Practice/confidence/history | Preserve attempts and update counts | VERIFIED WORKING for tested demo counts/history | F | Two attempts entered with confidence 2 and 4; history 2; Dashboard 1 practiced question, Log 2 attempts. Reloaded confidence value not separately asserted | E1 F | — | Keep question count distinct from attempt count; assert stored confidence separately |
| Difficulty/question identity/skill links | Edit and select skill | NOT IMPLEMENTED in core editor | Source review | Difficulty fixed at Medium on create; skill_id null; no manual controls | S InterviewsPage | P2 gap | Document missing fields |
| Interview stories/mock interview | Manage complete workflows | PARTIALLY WORKING | Source inventory | STAR story creation exists but not separately exercised; mock_interviews schema has no core workflow | S | — | Test stories; mark mock interviews as missing |
| Weak-topic indication | Reflect confidence | PARTIALLY WORKING | Source review | Chooses low-confidence question, not an aggregate topic competency assessment | S | — | Label question-level signal accurately |
| Save application/pipeline/stage counts | One row across stage changes | VERIFIED WORKING in demo dropdown path | G | All ten requested stages, notes/JD and Applied count; one record, no duplicates after reload | E1 G | — | Additional Planning to Apply is present in source |
| Kanban drag/drop | Move cards by dragging | NOT IMPLEMENTED | Source review | Stage dropdown controls exist; Kanban cards lack drag/drop handlers | S JobsPage | P2 gap | Clearly describe dropdown movement |
| Edit application/followup/priority | Persist available fields | PARTIALLY WORKING | G + source | JD/notes/stage tested; other controls exist. General company/role/location editing absent | E1/S | — | Test editable followup/priority separately |
| Recruiter/resume versions/interview details | Preserve recruitment context/files | NOT IMPLEMENTED as complete core UI workflows | Types/schema/source | Supporting fields/tables exist without full forms/file lifecycle | S | — | Do not advertise roadmap as operational |
| Local JD skill recognition | Identify known requirements and gaps | PARTIALLY WORKING | Job-gap unit tests + source | Deterministic skill categories; substring matching, no reliable required/preferred distinction | E5/S | P2 risk | Use boundary-aware matching and distinguish heuristic output |
| JD AI analyzer | Authenticated structured extraction | BLOCKED BY CONFIGURATION for authenticated inference | Live invalid/anonymous calls; source | 400 invalid input; 401 valid anonymous input. Real extraction/matching/write workflow not executed | E2/E6/S | — | Isolated account + authorized minimal inference required |
| JD gap plan | Confirm before goal/milestone/task creation | NOT TESTED full workflow | Source + pure gap tests | Creates linked goal, milestones, two tasks per gap; sequential writes; possible partial plan on failure | E5/S | P2 risk | Transaction/idempotency for multi-record creation |

### Daily Log, Copilot and More

| Feature | Expected behavior | Implementation/status | Test performed | Actual result | Evidence | Severity | Recommended fix/next check |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Log task/focus/interview activity | Match source records by date | VERIFIED WORKING in tested demo normal paths | A/F | One completed task/1m focus and two practice events match demo records | E1 | — | Editor timestamp defect affects alternative completion path |
| Log networking/learning/build/recent changes | No invented activity | PARTIALLY WORKING | Source + selected workflows | Derived from records; stale completed_at after editor reopen can count an unfinished task. Change summaries cover selected entities | S/E1 | P1 | Fix task transition invariant (F2); inspect each activity category |
| Journal save/update/date/empty day | Save and filter by selected date | PARTIALLY WORKING | I new journal/reload; source update handler | New journal reload persists; separate empty date displays no journal/activity; second save to existing journal not exercised | E1 I/S | — | Test existing-journal update; hosted write blocked |
| Copilot opens/input/error display | Accept command and show errors | VERIFIED WORKING in sampled environments | H + live demo error | UI opens; local proposal appears; live 401 clearly shown | E1/E2 | — | Error visibility does not establish inference success |
| Local create_task confirmation | No write before approval; persist once | VERIFIED WORKING in local demo | H using actual 503, no route interception | Zero tasks before confirmation; one after; saved actions disabled, reload one | E1 H | — | This does not prove a Supabase database write |
| Published demo local fallback | Work without private account where promised | BROKEN in production sample mode | Live Copilot command | Returns 401 “Sign in to use AI commands”; client fallback only handles 503 | E2/S | P2 | Use explicit local demo path (F8) |
| Complete/reschedule/create_skill/add_note proposals | Correct confirmed mutation | NOT TESTED full browser/provider workflows | Schema/unit/source review | Five action schemas and apply branches exist. Only create_task executed in browser; local parser does not fully support all five | E5/S | — | Isolated fixtures for each action and ambiguous task requests |
| High-priority create command | Preserve requested priority | BROKEN in demo | Targeted actual command/confirm/reload | Requested High; saved Medium. create_task schema has no priority and apply hardcodes Medium | E1/S | P2 | Add validated priority and propagate it (F11) |
| Structured output/invalid actions | Reject unsupported/destructive proposals | PARTIALLY WORKING | Unit tests/source | Zod discriminated union, max eight proposals, client existing-ID checks; no bulk deletion action | E5/S | — | Runtime invalid-provider JSON not injected during audit |
| Actual Copilot provider | Authenticate and infer successfully | BLOCKED BY CONFIGURATION for local provider; production inference NOT TESTED | Source/live auth rejection | Local provider absent. Lovable gateway source configured; no authorized authenticated model request made | E2/E6/S | — | Do not conflate with Hermes/OpenRouter |
| Universal Inbox | Capture/classify/archive/convert | VERIFIED WORKING for tested demo conversion | I | Clearly marked capture becomes task; persisted in export | E1 I | — | Other classifier branches have unit/source coverage only |
| Notes rich text/title/autosave | Save and reload content | VERIFIED WORKING in tested demo | I | Title and content survive navigation/reload/export | E1 I | — | Browser-close/hosted autosave race remains untested |
| Notes linked to skills/projects/goals | Select and navigate association | NOT IMPLEMENTED in inspected editor | Source | General note writes entity_type/entity_id null; no association picker | S | — | Do not claim linked-note workflow |
| Resources URLs/skill/status | Save and preserve reference | PARTIALLY WORKING | I create/reload/export; source | Resource URL persists; skill/status controls exist; no project-link picker/general edit/filter lifecycle | E1/S | — | Test status changes and explicit link selections |
| Evidence URL/skill/project | Preserve proof association | VERIFIED WORKING for demo skill URL; project workflow NOT TESTED | C + source | URL proof linked to skill; project association control exists | E1 C/S | — | Test authenticated private files separately |
| Evidence files/goal links | Private upload and correct links | BLOCKED BY CONFIGURATION for files; goal selector NOT IMPLEMENTED | Live metadata/PGlite/source | Bucket private; local ownership tests pass; no live upload; goal_id normally null from UI | E4/E6/S | — | Test signed file access with two isolated users |
| Weekly Review/rollover | Accurate review and next-week schedule | NOT TESTED full workflow | Domain/source review | Derived metrics; confirmed rollover updates tasks but can leave old Planner blocks | E5/S | P1 consistency | Fix shared scheduling path before exercising rollover |
| Analytics | Explain recorded time by category | PARTIALLY WORKING | Domain tests/routes/source | Recharts/pure weekly totals implemented; no large-data or all-chart interaction test | E5/E2/S | — | Verify all chart values against hosted fixture |
| Export JSON | Valid complete loaded data | VERIFIED WORKING for small demo fixture | I download and parse | Includes notes/resources/tasks, source demo. Only currently loaded data, not file binaries | E1 I | P2 limit | Paginate complete export and define file inclusion |
| Import/restore backup | Restore exported workspace | NOT IMPLEMENTED | Source inventory | No JSON import/restore workflow; export is not a restorable backup system | S | — | Do not rely on export alone for recovery |
| Production document Vault | Upload/link/reprocess/archive/claim review | NOT TESTED authenticated workflows | E3 gate + production source | `/vault` correctly gates sample users; source supports operations, none executed | E3/E6/S | — | No document reprocessing or queue work was triggered |

### Auth, UI, data and agent operations

| Feature | Expected behavior | Implementation/status | Test performed | Actual result | Evidence | Severity | Recommended fix/next check |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Login/signup/logout/session lifecycle | Preserve private records across auth/restart | BLOCKED BY CONFIGURATION | Login rendering/source; no test account | Form loads. Actual login/signup/logout/expiry/restart private-data workflow not tested | E2/S | — | User-authorized isolated account required |
| Protected routes/API rejection | Deny anonymous private operations | VERIFIED WORKING for sampled live checks | `/tasks`, agent context, both AI APIs | Sign-in gate; 401 APIs; invalid body 400 | E2/E6 | — | Server auth success/expiry paths remain unverified |
| Password recovery | Recover account | NOT IMPLEMENTED in inspected UI | Source review | No password-reset/change flow | S login | P2 gap | Add supported recovery workflow in future task |
| Cross-user database isolation | Cannot read/write another user's rows | VERIFIED WORKING in isolated PostgreSQL; live NOT TESTED | E4 two-user role/claim tests + live policy metadata | Read/update/delete/forge and foreign links rejected in fixture; policies present live | E4/E6 | — | Fixture is not live Supabase end-to-end authorization proof |
| Core hosted persistence/activity logs | Correct database/state/log | NOT TESTED transactions | Source + read-only metadata | Connectivity established; no private writes permitted; split-write risks in D/F | E6/S | P2 risks | Atomic writes and affected-row checks |
| Desktop/mobile navigation | Accessible routes and fitting documents | VERIFIED WORKING for sampled route rendering | 14 routes at 1440/390, local and published | No document overflow at these widths; not every form interaction on each device | E1/E2 | — | Mobile touch, long forms, cross-browser testing remain |
| Tablet layout | Fit 768px viewport | BROKEN local and published | All 14 core routes | Published document widths 867–910px at 768px; Dashboard 901px | E1/E2 | P2 | Responsive shell/topbar sizing (F5) |
| Dialog keyboard access | Focus remains in modal and returns on close | BROKEN local | Close button focus + Shift+Tab | Keyboard focus leaves dialog; no trapping/restoration implementation | E1/S | P2 | Accessible dialog focus lifecycle (F6) |
| Dark mode/shortcuts/capture/search opening | Persist theme; keyboard controls work | VERIFIED WORKING for tested demo actions | C/T/Slash/Escape; reload | Dialog shortcuts and dark-mode persistence passed before layout assertion failed | E1 | — | Contrast/screen-reader audit not completed |
| Search result destination | Open matching record | PARTIALLY WORKING | Source + search-opening test | Group search exists; click ignores item.id and only opens module; note goes More overview | S/E1 | P2 | Navigate to selected record/subview (F12) |
| Preferences/profile/onboarding | Save private setup/settings | NOT TESTED authenticated workflow | Source/routes | Configuration forms exist; private saves not executed | S/E2 | — | Isolated account required |
| Agent Activity/settings/notifications | Health and user-controlled agent actions | NOT TESTED authenticated UI actions | `/agent` gate + source | Run queue/cancel/read notifications/preferences/owner linking implemented in Lovable source; untouched | E3/E6/S | — | Health checks only; no run-now/pause/config changes |
| Hermes process health | Gateway running and receiving | BROKEN at audit time | CLI status + PID check | No gateway process detected; saved running state refers to absent PID 56772 | E8 | P1 integration | Investigate/start service in a separately authorized task (F16) |
| Telegram bot authentication | Credential accepted | VERIFIED WORKING for getMe only | Real Telegram getMe | HTTP 200, ok=true; no message sent or inbound handling tested | E8 | — | Bot auth does not prove delivery while gateway is stopped |

## C — End-to-end workflow results

All A–I browser mutations below happened in fresh isolated **local demo** storage using clearly marked AUDIT records. No mocked success responses were injected. They do not verify a hosted private database.

| Workflow | Steps and actual assertions | Result and limitation |
| --- | --- | --- |
| A | Create high-priority task → linked 18:00 Planner block → Today → start Focus → advance clock 61s → pause 10s (no change) → resume → stop → verify task Today and actual_minutes=1, exactly one focus ledger → checkbox complete → Dashboard completed=1/actual=1m → Log one completion/1m → reload | **VERIFIED WORKING** for this demo normal path. Arbitrary times, editor completion, Today total and focus refresh fail separate tests. No real inactive-tab test. |
| B | Goal → two milestones → complete first (50%) → second (100%) → linked task (67%) → unrelated completed task (unchanged) → complete linked task (100%) → reload | **VERIFIED WORKING** demo goal association/progress. Linked task is attached to goal; manual milestone selection is not provided by task form. Goal status remains active until manual completion. |
| C | Manual skill → topic Applied → knowledge 3 → verify hands-on/interview remain 0 → linked completed task → URL proof attached to skill → reload | **VERIFIED WORKING** demo association/persistence. URL evidence only; private file upload not tested. Automated curriculum import excluded. |
| D | Project → GitHub/demo URL/architecture/Building status → linked task → complete → 100% core project progress → reload URLs/status | **VERIFIED WORKING** demo core workflow. GitHub is only a saved link; extra Lovable project_tasks records not written. |
| E | Contact with past followup → Dashboard due count → interaction notes + future followup → reload history → Dashboard due count zero | **VERIFIED WORKING** demo reminder indicator/history. No reminder delivery or outreach message tested. |
| F | Interview question → edit answer → practice confidence 2 then 4 → practice_count 2/history 2 → reload → Dashboard 1 practiced question → Log 2 attempts | **VERIFIED WORKING** demo; no mock interview or manual skill link. |
| G | Application → move same record through Saved, Applied, Recruiter Contact, Screening, Technical Interview, Hiring Manager, Final Round, Offer, Rejected, Withdrawn → notes/JD → reload → Applied count fixture | **VERIFIED WORKING** demo dropdown transitions, one row. Kanban drag/drop absent; Dashboard omitted-stage bug is separate. |
| H | Create command → real local API 503 → local proposal → verify no task written → explicit confirmation → one task → repeated confirmation disabled → reload | **PARTIALLY WORKING**: local create_task verified, not hosted database or all five actions. Published sample command returns 401; provider inference blocked/unexecuted. |
| I | Note title/rich text → autosave → resource URL → Inbox conversion → parsed JSON export → journal save → navigation/reload → assert stored note/resource again → different empty date | **VERIFIED WORKING** for tested demo records. No import/restore, existing-journal update, hosted autosave, or browser-close durability proof. |
| J | Logout → login → verify existing private data → expiry/restart | **BLOCKED BY CONFIGURATION**: no isolated account. Anonymous protected-route/API rejection verified separately; this does not complete J. |

## D — Database findings

### Schema and store inventory

The two original local migrations create **31 public tables**, all with RLS enabled in E4:

`profiles`, `goals`, `skills`, `projects`, `contacts`, `job_applications`, `milestones`, `skill_topics`, `tasks`, `planner_blocks`, `focus_sessions`, `network_interactions`, `interview_questions`, `interview_practice`, `notes`, `resources`, `evidence`, `inbox_items`, `activity_log`, `daily_logs`, `task_subtasks`, `task_dependencies`, `learning_sessions`, `project_milestones`, `project_decisions`, `followups`, `mock_interviews`, `interview_stories`, `job_interviews`, `job_skill_requirements`, `notifications`.

The current local store enumerates 33 entities: 23 original business entities plus ten newer learning entities. The original tables absent from that entity list are `profiles` (handled separately), `task_subtasks`, `task_dependencies`, `project_milestones`, `project_decisions`, `followups`, `mock_interviews`, `job_interviews`. Schema presence is not evidence of a user-facing workflow. `notifications` is loaded but has no complete core notification-delivery interface. Automated learning additions are excluded from readiness.

Lovable's live database has **60 public tables**, all reported RLS-enabled. Its additional agent/document/project_tasks schema and production-only `useRows` access are distinct from the local entity map. Do not apply the local Next.js migrations to the Lovable database on the assumption that schemas are interchangeable. No migrations were executed against production.

### Security and integrity checks

| Check | Actual verification |
| --- | --- |
| Owner policies | Live sampled core tables have authenticated user_id=auth.uid() USING/WITH CHECK; profiles use id=auth.uid(). All 60 public tables report RLS enabled. Full policy semantics for every extra agent table were not exercised. |
| Two-user isolation | E4 owner can read; other user cannot read/update/delete owner's task or insert forged ownership. Anonymous role cannot read task. Real embedded PostgreSQL execution, fixture auth.uid(). |
| Owned foreign links | E4 rejects another user's skill links in tasks/evidence. Live metadata contains task skill/project/goal/milestone/application/contact, added skill-topic, goal parent, milestone goal, and evidence owned-link triggers. Metadata entries repeated for INSERT/UPDATE are not duplicate-trigger defects. |
| Parent consistency | Same-owner goal and milestone may still be unrelated parents. Ownership enforcement alone does not require task.milestone.goal_id=task.goal_id. Source/schema risk, not a demonstrated production incident. |
| Polymorphic note links | entity_type/entity_id have no normal FK/owned-link trigger. Current UI does not expose link selection; no demonstrated cross-user disclosure. Validate on any future linking implementation. |
| Invalid values | E4 rejects invented task stage, negative actual_minutes, reversed block times and exact duplicate skill name. |
| Soft deletion | E4 confirms deleted parent excluded with deleted_at filter and new links rejected. Existing-child cascade/undo/recovery UI is incomplete; RLS ownership alone does not hide deleted rows unless query filters are used. |
| Storage | Live `career-evidence` bucket public=false, aggregate object count 0. E4 folder-owner insert/read allowed; other user read/insert rejected in fixture. Live upload/download/signed URL expiry were not tested. |
| Type/schema alignment | Inspected core table columns correspond to original domain fields; live tasks also has skill_topic_id. This is not exhaustive generated-type parity for all 60 production tables. |
| Indexes | Original migrations declare ownership, scheduling/link indexes and uniqueness/FK constraints. No live query plan or index effectiveness benchmark was run. |

### Live read-only connectivity evidence

Aggregate SELECTs succeeded. At the time checked, the inspected tables contained: **skills 11**; tasks, goals, projects, contacts, job_applications, planner_blocks, focus_sessions, activity_log, notes **0 each**. These are database-wide aggregate observations, not personal record contents. They prove database access through the connector, not a browser's authenticated write/read lifecycle. There were no existing core task/focus rows available to reconcile a Dashboard completion workflow against the live database.

### Consistency and persistence risks

1. **Completion metadata:** TaskForm can set status Completed without completed_at; reopening through that form can leave the old completed_at. Dashboard weekly completion uses both status/timestamp; Daily Log's timestamp filtering can diverge. Confirmed local failure plus source evidence (F2).
2. **Schedule divergence:** Planner creates a block and updates a task separately. Editing scheduled_date to 2099-01-01 left block_date at 2026-10-10 in the isolated browser test after reload. Copilot rescheduling and Weekly Review rollover have the same task-only source path, but were not separately executed (F9).
3. **Nontransactional activity logging:** `StoreProvider.add/update` writes main record, changes client state, then independently inserts activity_log. A log failure can show an error after the primary write succeeded; retry can create duplicate records. Fault injection was not performed (F14).
4. **Zero affected rows:** Hosted update/remove check error but do not select/count an affected row. An ownership/deletion race can return zero matching rows without a SQL error while client state still changes. Source risk, not evidence of RLS bypass (F14).
5. **1,000-row limit:** Core refresh uses select('*').is(deleted_at,null).limit(1000), without pagination or a stable order. More than 1,000 active rows silently omit records from progress, search, logs and export. Inspected live core tables are presently below the cap; large-workspace failure is not runtime reproduced (F13).
6. **Refresh breadth:** Local hosted refresh issues up to 33 parallel table queries, despite the current screen needing only a subset. Missing core table/error can prevent a coherent refresh. getUser is outside the main try/finally; a thrown auth/network error may leave loading true. This failure mode was not injected.
7. **Multi-tab/live freshness:** Demo has no storage event synchronization. Hosted realtime refresh covers selected tables, not every core/agent table. Reload/foreground refresh is not equivalent to guaranteed realtime consistency.
8. **Partial multi-record saves:** JD gap plans, production outreach response recording and feedback controls update several rows independently. Error-after-partial-write handling needs an explicit contract. No deliberate live failure was induced.

## E — APIs and integrations

### Actual live endpoint results

Fresh anonymous HTTP calls without cookies:

| Request | Result | Interpretation |
| --- | --- | --- |
| GET `/` | HTTP 200; approximately 2,989 ms on first measured request | HTML reachable; not private workspace verification |
| GET `/login` | HTTP 200; approximately 302 ms | Sign-in page reachable |
| GET `/tasks` | HTTP 200 HTML; approximately 65 ms; browser displays sign-in gate | Client protection is observed; 200 HTML is not anonymous data access |
| GET `/api/agent/context` | HTTP 401 | Anonymous agent data rejected |
| POST `/api/ai/command`, invalid null | HTTP 400 | Input validation working |
| POST `/api/ai/command`, valid minimal command | HTTP 401 | Authentication required; no inference occurred |
| POST `/api/ai/analyze-jd`, invalid null | HTTP 400 | Input validation working |
| POST `/api/ai/analyze-jd`, valid synthetic description >=80 characters | HTTP 401 | Authentication required; no inference occurred |
| Sample Copilot command through actual browser | HTTP 401, visible “Sign in to use AI commands” | Demo local-fallback mismatch, F8 |
| Existing authenticated agent pulse/health | HTTP 200; no pending commands | Existing API authentication/connectivity works; no command queued |

No authenticated core AI success request or forced provider-failure test was made. No paid inference was incurred by this audit. Server-side logs for the published runtime were not available; no conclusion of zero server errors is made.

### Integration matrix

| Integration | Source/configuration | Authentication/live read | Writes and monitoring | Status |
| --- | --- | --- | --- | --- |
| Supabase | Local adapter/migrations; Lovable cloud database enabled | Live metadata/aggregate reads succeeded; policies/private bucket inspected | Private account write/Auth/Storage lifecycle not tested; source handles some errors but has split-save risks | PARTIALLY WORKING |
| Local Career OS Copilot | OpenAI/Anthropic/Gemini adapters; server-only keys; optional configuration | Local provider absent; actual demo 503 invokes parser | Confirmed create_task localStorage write verified; other apply actions unexecuted in browser | PARTIALLY WORKING / provider BLOCKED BY CONFIGURATION |
| Lovable Career OS Copilot/JD | Production gateway source uses `LOVABLE_API_KEY` and `openai/gpt-6-astra` | Anonymous validation/auth tests pass; gateway inference not tested | Proposal confirmation present; no authenticated production writes executed; no core app-level rate limiter found | NOT TESTED authenticated inference; demo fallback BROKEN |
| Hermes/OpenRouter | Existing separate Hermes configuration uses approved `meta/muse-spark-1.3-contributor` | No OpenRouter inference/auth request made in this health-only audit | Gateway CLI says no process; saved state is stale. Provider/model/credentials untouched | BROKEN gateway health; provider NOT TESTED |
| Telegram | Existing bot token configured securely | Real getMe HTTP 200 / ok=true | No outbound test or inbound reply processing; gateway stopped, so delivery cannot be certified | PARTIALLY WORKING |
| Career agent API | Existing client/server authentication | Read-only authenticated health pulse HTTP 200 | Pending commands 0; no run-now, queue, cancellation or automation changes | VERIFIED WORKING for health/auth only |
| GitHub | Git remote and stored project URL fields | git ls-remote verifies pushed feature branch | No source push during audit; no application repository-sync implementation | Git remote VERIFIED WORKING; app sync NOT IMPLEMENTED |
| Google Docs | Existing source/import integration is part of excluded learning work | No new document fetch/import performed for this audit | No curriculum import/reprocessing or schedule job triggered | NOT TESTED; excluded from readiness |
| Production Vault/outreach/agent panels | Additional Lovable source and tables exist | Sample users correctly gated; inspected source only | Authenticated operations and notification delivery not tested; partial multi-write risks noted | NOT TESTED |
| Vercel | Existing matching account projects returned | Project/deployment detail requests HTTP 403 | No deployment action; no CLI fallback available | BLOCKED BY CONFIGURATION |

The app Copilot and Hermes do not share a verified inference path. Changing Hermes' model previously does not establish that the application Copilot uses Muse Contributor.

### UI and performance evidence

- Actual published sample pages: **42 route visits** across 14 core routes at widths 1440, 768, 390. `goto` to visible main heading ranged **171–1,001 ms**, median **266.5 ms**; login ready measurement **2,782 ms**. These are one-machine headless browser navigation measurements, not Core Web Vitals or private database performance.
- Dashboard ready measurements: **427 ms at 1440**, **225 ms at 768**, **241 ms at 390**. Cache/network conditions differ; no device-speed comparison is inferred.
- At 768px, every published core route overflowed: Dashboard 901, Today 873, Planner 882, Tasks 871, Goals 900, Skills 870, Projects 886, Networking 904, Interviews 890, Jobs 910, Daily Log 867, Copilot 880, More 867, Settings 886 pixels. At 1440 and 390 none had document overflow. Internally scrollable wide tables are separate from document overflow.
- E2 page-error events: **0**; recorded >=400 responses: the deliberately tested Copilot **401**. E3 console errors and page errors: **0** on login/sample entry/Vault/Agent gate visits. Console events were not collected on the entire E2 route sweep; these results do not prove an error-free app.
- Local dark-mode reload and C/T/Slash/Escape actions passed. A modal keyboard focus test failed. The 768px Dashboard screenshot was visually inspected and corroborated cramped/right-overflowing shell controls; screenshots were temporary Playwright output, JSON measurements are the durable evidence.
- No large-data load test, stress test, SQL EXPLAIN, screen-reader/contrast certification, real background-tab timer measurement, mobile touch workflow, browser restart, or cross-browser run was performed.

### Security findings and limits

- No tracked `.env*`, `.pem` or `.key` files were returned by the tracked-file check. The inspected current tracked files had no matches for the tested real OpenRouter/OpenAI/Telegram/private-key secret patterns. This is **not an exhaustive Git history scan or proof that no secret has ever been exposed**. Secret values are not included in this report/evidence.
- AI provider keys remain server-side in inspected routes/adapters. Supabase public URL/anon key is intentionally client configuration; RLS is the data authorization boundary. No service-role value was printed.
- Live unauthorized core APIs reject access; schema-level owner/foreign-link tests pass. Live two-user Supabase API authorization remains untested.
- Core Copilot/JD input and structured output validation exist; proposal execution requires explicit confirmation. Broad destructive actions are not in the schema. Prompt injection cannot be ruled out by schema checks alone, and provider outputs were not adversarially exercised.
- No app-level user rate limit/cost bound found in inspected core Copilot/JD routes. Authenticated usage can therefore consume provider resources repeatedly unless platform controls intervene. **P2 source risk**, not a demonstrated denial of service or abuse incident (F15).
- Dependency report: five **high** findings in the development lint chain (`braces`/`micromatch`/`fast-glob` through Next ESLint tooling), including stack-exhaustion advisory GHSA-vfj7-8cjw-p6xm for braces <=3.0.3. `npm audit --omit=dev` returned **zero known production dependency advisories**. No remediation was applied. No P0 security exposure was verified.

## F — Bug report

**P0:** None verified. Hosted auth success and live cross-user transactions were unavailable, so this is not a comprehensive security clearance.

“Reproduced” means a real browser assertion failed in the stated environment. “Source-confirmed” means the implementation path is present and defective/incomplete but the failure has not been triggered in a hosted transaction. Suggested fixes are recommendations; none were applied.

### F1 — P1: Saved arbitrary-time Planner blocks disappear

- **Status/evidence:** Reproduced local demo, E1 `DEFECT: arbitrary start time...`; same restrictive rendering inspected in Lovable source. Private production persistence not exercised.
- **Reproduce:** Planner → new block on current day, start 08:30/end 09:30, title AUDIT hidden 08:30 block → save → day view. Storage contains one block; title is not visible. Reload does not correct the slot predicate.
- **Location/root cause:** `src/features/planner/PlannerPage.tsx:11`, `PlannerPage` rendering at line 67: only six exact slots and `block.start_time === time`.
- **Additional source risk:** PostgreSQL time may arrive as `18:00:00` while slots are `18:00`. Live table was empty, so hosted serialization mismatch is not runtime verified.
- **Fix:** Normalize times at the repository boundary; render all valid start/end intervals rather than filtering to six exact times. Test 08:30 and HH:mm:ss round trips.

### F2 — P1: Task editor completion/reopen corrupts lifecycle metadata

- **Status/evidence:** Completed timestamp failure reproduced local, E1. Reopen branch omission source-confirmed.
- **Reproduce:** Create unfinished task → Edit task → Stage Completed → Save → inspect fixture task. status is completed, completed_at is null. Separately checkbox-complete then reopen through editor: form does not clear old timestamp.
- **Location/root cause:** `src/features/tasks/TaskForm.tsx:39`, `save`; updates status without completion transition fields, and new records always set completed_at null.
- **Impact:** Weekly completion counts can omit completed tasks; Daily Log timestamp filtering can retain reopened task completion. Checkbox path passing does not fix editor path.
- **Fix:** One validated completion/reopen transition shared by editor/checkbox/focus/Copilot; set timestamp on transition to Completed and clear it on reopening. Verify Dashboard and Log against both paths.

### F3 — P1: Active focus time is lost on refresh

- **Status/evidence:** Reproduced local, E1; same in-memory session pattern in inspected production provider.
- **Reproduce:** Create Today task → Start Focus → let clock advance → reload → no focus dialog, no saved session, task still Doing.
- **Location/root cause:** `src/features/focus/FocusProvider.tsx:13`, React state taskId/startedAt/seconds; no persisted active-session recovery.
- **Fix:** Persist active session ID, clock anchors, pause state and pending save; recover after refresh and make final recording idempotent. Test reload during running/paused/save-pending states. Background timing requires a separate real-tab test.

### F4 — P2: Today actual work resets when task completes

- **Status/evidence:** Reproduced local, E1.
- **Reproduce:** Record 1m on a Today task → Today Actual shows 1m → checkbox complete → Actual shows 0m despite unchanged session ledger.
- **Location/root cause:** `src/features/today/TodayPage.tsx:25`, `actual` sums `todayTasks`, which excludes completed tasks.
- **Fix:** Derive daily actual minutes from dated focus/work ledgers independently of pending list; verify completion and navigation do not reduce total.

### F5 — P2: Tablet shell overflows all core routes

- **Status/evidence:** Reproduced local and **published app**, E1/E2.
- **Reproduce:** Open published sample workspace at 768×900 → Dashboard document width 901px, Jobs 910px; repeat all 14 routes. Right edge extends beyond viewport.
- **Location/root cause:** `src/app/globals.css` shell/sidebar/topbar responsive rules; mobile collapse threshold 760px leaves desktop sidebar/topbar active at 768px. Production shell CSS has the same observed width problem.
- **Fix:** Make shell/topbar shrink/collapse at supported tablet widths; keep wide planner/table overflow within their own containers. Regression at 760/768/820/1024 plus existing mobile/desktop.

### F6 — P2: Modal keyboard focus escapes

- **Status/evidence:** Reproduced local, E1.
- **Reproduce:** Open Quick capture (C shortcut) → focus Close button → Shift+Tab → active element is outside dialog while modal remains open.
- **Location/root cause:** `src/components/ui.tsx:30`, `Dialog`: aria-modal markup and Escape/backdrop closing without focus trap/background inertness/focus restoration.
- **Fix:** Add a complete accessible dialog focus lifecycle. Verify forward/reverse Tab, initial focus, Escape and focus return.

### F7 — P2: Demo skill duplicates disagree with hosted constraint

- **Status/evidence:** Reproduced local E1; database exact-name rejection verified E4.
- **Reproduce:** Create skill AUDIT duplicate twice → two demo rows. Same `(user_id,name)` exact-name insert is rejected by original database constraint.
- **Location/root cause:** `src/features/skills/SkillsPage.tsx` create path and `src/lib/store.tsx` demo add lack duplicate check; original SQL unique constraint is case-sensitive.
- **Fix:** Define one normalized name rule; validate in UI/repository and database, preserving existing IDs/references. Test exact/case/whitespace variants and readable conflicts.

### F8 — P2: Published sample Copilot cannot use intended local fallback

- **Status/evidence:** Reproduced **published app**, E2.
- **Reproduce:** Login → Explore sample workspace → Copilot → “Create AUDIT sample-only proposal” → Run command → “Sign in to use AI commands,” HTTP 401; no proposal.
- **Location/root cause:** Production `src/features/copilot/CopilotPage.tsx` ask falls back only on 503; `src/routes/api/ai/command.ts` correctly requires auth and returns 401 to demo users.
- **Fix:** Explicitly select local parser in demo mode; retain authentication for server AI requests. Test both demo fallback and anonymous API denial. This does not require changing providers.

### F9 — P1: Task rescheduling leaves stale Planner blocks

- **Status/evidence:** Reproduced local after reload, E1 corrected schedule run. Other rescheduling paths are source-confirmed; no private hosted write.
- **Reproduce:** Create AUDIT schedule consistency task → linked Planner block today → Edit task → Scheduled day 2099-01-01 → Save task → reload → task.scheduled_date is 2099-01-01 while planner_blocks.block_date remains 2026-10-10. The task editor and Planner now disagree.
- **Location/root cause:** `TaskForm.save`, `CopilotPage.applyOne` reschedule branch, `src/features/more/ReviewPanels.tsx` rollover, versus `PlannerPage.saveBlock/onDrop`; schedule stored in two independently updated entities.
- **Fix:** Define one scheduling operation updating task and related block transactionally, including reschedule/unschedule/rollover. Do not silently drop standalone blocks.

### F10 — P2: Dashboard pipeline omits supported stages

- **Status/evidence:** Source-confirmed; G verifies transitions, not this Dashboard display edge case.
- **Reproduce to verify:** Put an application in Hiring Manager → Dashboard pipeline lacks its stage. Repeat Planning to Apply, Rejected, Withdrawn.
- **Location/root cause:** `src/features/dashboard/DashboardPage.tsx:23` stage array differs from `src/features/jobs/JobsPage.tsx:11` complete array.
- **Fix:** Share canonical stages; intentionally label any hidden terminal-stage summary rather than silently omitting it.

### F11 — P2: Copilot cannot preserve requested high priority

- **Status/evidence:** Reproduced local with actual fallback command/confirmation/reload, E1 targeted run. Not an authenticated provider test.
- **Reproduce:** “Create a high-priority task to review FastAPI” → approve create_task → reload → saved priority is Medium, expected High. Parser also retains command wording as title instead of fully interpreting it.
- **Location/root cause:** `src/ai/types.ts` create_task lacks priority; `src/features/copilot/CopilotPage.tsx:39` apply hardcodes medium.
- **Fix:** Validate priority in proposal schema; carry it through parser/provider/application. Ambiguous “Complete this task” needs explicit selected task context, not guessed IDs.

### F12 — P2: Search opens module instead of matching record

- **Status/evidence:** Source-confirmed; opening search itself tested.
- **Reproduce to verify:** Search distinctive note title → select result → `/more` overview opens, not note. Task results similarly ignore selected ID.
- **Location/root cause:** `src/components/SearchDialog.tsx`, result click uses PATHS[group.entity] and ignores item.id/subview.
- **Fix:** Support selected record and appropriate More tab in route/state, then verify returned focus and record visibility.

### F13 — P2: Loaded data/export silently truncated at 1,000 rows

- **Status/evidence:** Source-confirmed capacity limitation; inspected production core counts below cap.
- **Reproduce to verify in isolation:** Seed 1,001 active tasks for a test user → refresh/export → at most 1,000 loaded, calculations/search omit at least one.
- **Location/root cause:** `src/lib/store.tsx` refresh select('*').limit(...1000); no pagination/stable order. Production core refresh has equivalent cap; extra agent useRows defaults to 200.
- **Fix:** Paginate/order queries or compute summaries server-side; export all pages with versioned format. Implement/test restore before describing export as recoverable backup.

### F14 — P2: Split writes and zero-row success can misreport saves

- **Status/evidence:** Source risk; no production failure injection.
- **Reproduce to verify in isolation:** Permit main task insert but reject activity_log insert → save reports failure after task committed; retry may duplicate. Separately remove/revoke a loaded row before update → query can affect zero rows while local state appears updated.
- **Location/root cause:** `src/lib/store.tsx` add/update/writeActivity/remove; independent writes, update checks error only. Production agent feedback/outreach performs multiple independent writes too.
- **Fix:** Atomic business/log operations or explicitly distinguish saved-record/log-warning outcomes; stable idempotency on retry; require affected-row confirmation. Surface async handler errors instead of unhandled void rejections.

### F15 — P2: No core AI per-user rate/cost guard found

- **Status/evidence:** Source risk; no abuse/load test or demonstrated exposure.
- **Reproduce to verify safely in isolated environment:** Repeated authenticated AI requests within a bounded mocked quota → inspect whether endpoint rejects over-limit requests. No app-level limiter found in inspected core routes.
- **Location/root cause:** Local `src/app/api/ai/command/route.ts`, `src/app/api/ai/analyze-jd/route.ts` and production `src/routes/api/ai/*` authenticate/validate but lack an inspected core per-user request budget.
- **Fix:** Add bounded user quotas/rate limits/provider cost observability, preserving current providers. First verify existing platform limits to avoid duplicate controls.

### F16 — P1 integration: Hermes gateway not running despite stale state

- **Status/evidence:** Current service-health failure, E8. Separate from excluded learning feature correctness.
- **Reproduce:** `hermes gateway status` → No gateway process detected; saved state claims running PID 56772; OS process check finds no such PID. Saved update timestamp is from previous day.
- **Location/root cause:** Existing Hermes runtime/service lifecycle and stale `gateway_state.json`; cause of process exit not established. Telegram getMe succeeds, so credential rejection is not the observed gateway failure.
- **Fix:** In a separately authorized repair task, inspect exit logs/service startup, restore gateway and verify health. Then obtain permission before any real message/notification test. No restart was performed in this audit.

### P3 usability/documentation findings

- **Goal state visibility:** goal at 100% stays active until manual completion; completed goals disappear from ordinary active listing with no obvious reopen workflow. Explain manual completion and expose history when implementing lifecycle improvements.
- **Deployment documentation:** README describes a Next.js/Vercel app; examined published app is a separate TanStack/Lovable build. Document branch/deployment mapping and expose a non-secret build revision.
- **Agent UI copy:** production settings refer to a Linux worker although the inspected Hermes runtime is Windows. Correct platform wording after verifying the actual worker configuration; no functionality inferred from text alone.
- **Accessibility inventory:** progressbar has no inspected accessible label; nested card button/select patterns need review. Full contrast/screen-reader results are NOT TESTED, not certified failures from this audit.

## G — Missing, simulated or unverified functionality

### Missing complete core workflows

Recurring-task execution, subtasks/dependencies, existing Planner block edit/delete/move, true calendar-month display, manual task milestone/application/contact selection, general goal/milestone identity editing, skill identity/category/topic renaming/history, general project/contact identity editing, linked project notes/decisions, interview difficulty/manual skill links/mock interviews, Kanban drag/drop, recruiter/resume file/interview-detail forms, core followup notification delivery, password recovery, JSON restore/import and full offline sync are not completed workflows in the inspected core UI.

Production has additional project_tasks/outreach/Vault/Agent panels; these are present in source and gated correctly, but private operations were not tested. They must not be described as absent merely because the Next.js core lacks them, nor as verified simply because their code exists.

### Simulated or limited behavior

- Demo records are browser-local, visibly separate from private accounts, and not automatically synced to production.
- Focus tests used an accelerated Playwright clock; they verify event logic, not real background timing.
- Copilot local parser is a small deterministic command set, not full five-action AI capability. Only confirmed create_task was executed in the browser.
- Local JD recognition is heuristic substring matching, not verified AI extraction or a numeric job match score.
- Readiness indicators are independent manual ratings; Applied topic status is not automatic practical/interview competence.
- Project GitHub/deployment fields store links. No live GitHub synchronization is implemented.
- Export includes loaded JSON records and links, not a complete restore system or file backup.
- Stored reminder dates/notification preferences and bot credential validity do not prove actual message delivery.

### Required information for currently blocked checks

No secret needs to be pasted into chat. To complete private production verification later, provide an **isolated staging deployment or approved disposable test account**, with credentials stored securely, plus explicit scope for test career records/files and cleanup. A second isolated account is needed for live cross-user authorization tests. Authenticated minimal AI inference also needs authorization; this audit did not request or incur it. Vercel deployment parity requires readable deployment metadata/account scope or a verified build revision from the project owner. Current user direction is to finish safe checks, so these gaps remain documented rather than holding up the audit.

## H — Recommended fix order

1. **Protect daily data integrity:** F2 completion/reopen invariant; F3 focus session recovery; F1 arbitrary Planner times; F9 shared task/block scheduling. Validate task counts/Log/Planner after reload and failed saves.
2. **Prove hosted core operation safely:** run A–J with two isolated users against the actual deployed code; file upload/access isolation, logout/login/expiry/restart, and hosted focus retry. Confirm which Git branch deploys to Lovable and expose build SHA.
3. **Correct daily calculations and visibility:** F4 Today totals; F10 all application stages; planned standalone blocks; clearly defined goal/project progress including production project_tasks.
4. **Fix demonstrated UI defects:** F5 tablet shell; F6 modal keyboard lifecycle; F7 duplicate handling; F12 record search destinations.
5. **Correct AI experience within current providers:** F8 explicit demo fallback; F11 priority and selected-task context; F15 rate/cost bounds. Exercise all five confirmed actions with invalid/stale IDs and repeated requests.
6. **Harden persistence/capacity:** F14 atomic/idempotent saves and affected-row checks; F13 pagination/complete export; autosave close/retry, multi-tab freshness and restore validation.
7. **Repair integration health separately:** investigate F16 Hermes process exit and startup; verify Telegram delivery only with authorization. Keep unfinished learning jobs excluded and unchanged until their own task authorizes testing.
8. **Align documentation and maintenance:** capability/deployment mapping, explicit unsupported workflows, development lint dependency advisories, accessible labels and tested recovery guidance.

## I — Production readiness

### **Not ready for daily use**

The application is useful for evaluation and several core manual workflows. Verified local functionality includes task planning at supported slots, checkbox completion, ordinary focus save/pause/resume, linked goal/project progress, manual skill/topic/URL evidence, contact interaction/followup indicators, interview practice, dropdown application stages, notes/resources/journals, and small JSON export. The published app is reachable, rejects sampled unauthorized operations, and renders its sample core pages.

Reliable daily use is not established because unsaved focus time is lost on refresh, valid Planner blocks can be invisible, task-editor completion metadata is inconsistent, Today totals decrease after completion, and all sampled tablet pages overflow. The published sample Copilot cannot invoke its intended local fallback. Separately, the existing Hermes gateway is stopped despite valid Telegram bot authentication.

Most importantly, **private production login, career-record writes, persisted summaries, uploads, live two-user authorization and authenticated AI behavior were not tested**. The connected database, passing demo tests and passing schema fixtures do not fill those gaps. No verified P0 incident was found, but this audit cannot certify production security or recovery under the unavailable account workflows.

**Recommended use now:** explore with noncritical sample data. Do not depend on unsaved focus time, editor-based completion counts, complete backup restoration, or unverified notifications. After the high-priority defects and isolated hosted verification are complete, reassess readiness using the same workflows.

### Audit delivery

- Application business source, production data/schema, providers, credentials, Hermes automation and deployments were unchanged.
- Added isolated test/evidence files and this report only. Nine failing local audit assertions intentionally remain visible.
- Earlier implementation SHA `fd32277...` was verified pushed to `codex/daily-learning-manager`. New audit artifacts remain local/uncommitted; this report does not imply a new push, default-branch merge, or deployment.
