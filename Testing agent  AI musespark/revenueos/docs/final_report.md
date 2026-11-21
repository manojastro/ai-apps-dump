# RevenueOS AI: final report

Date: 2026-11-07. All data is synthetic. Metrics prove the pipeline works on planted rules, not real-world accuracy.

## 1. Built and tested

| Phase | Status | Real result |
|---|---|---|
| 0 Setup | Tested, except Docker and CI | FastAPI health, Alembic, Next.js shell. Compose files validate, but images were never built |
| 1 Data and quality | Tested | 206 accounts, 600 deals, 1,500 tickets. Second load gave identical counts. All injected issues found |
| 2 Account 360 | Tested | Page median 325 ms, max 479 ms, 10 loads |
| 3 Deal intelligence | Tested | LightGBM AUC 0.830 against 0.750 for the stage baseline |
| 4 Forecast | Tested | Back-test error 5.5%, against 13.8% stage-weighted and 45.3% rep commit |
| 5 Retention | Tested | AUC 0.943, top-decile capture 80%, against 37% for renewal date alone. At-risk ARR $948,418 across 18 accounts |
| 6 Copilot | Built, plumbing tested, **live quality not tested** | Tools, scoping, audit, guardrails tested with a scripted stand-in |
| 7 Governance | Tested, except Docker and CI | Role scoping, audit, admin, rate limiting and redaction tested |

**Checks run:** 98 pytest tests passing, ruff clean, TypeScript clean, production build, `npm audit` with 0 production vulnerabilities, 5 Playwright flows passing, every page reviewed in light and dark mode.

**Bugs the checks caught and fixed:**

- Region code "NA" was read as a missing value.
- Renewal deals could be created in the future, and new business could appear after a customer had left.
- HNSW vector search was unreliable on near-duplicate text, and would have applied team filters after searching.
- A dashboard chart squashed its bars during a resize, seen only by looking at screenshots.
- Re-running the build left old rows mixed into the database, seen only because a count looked wrong.
- First-pinned Next.js and React versions had known vulnerabilities.

## 2. Not built, and known limits

- **Copilot eval not run.** There was no API key, so the pass rate is unknown and no real LLM call has been made. The 20/20 dry run only proves the wiring.
- **`docker compose up` not verified.** Docker Desktop would not start on this machine.
- **CI never ran,** because the repo has not been pushed.
- **Clean-clone run: partly verified.** A clean copy of the repo, with a new virtualenv and a new Postgres, followed the no-Docker README steps. The full rebuild worked, all 98 tests passed, and the frontend built. It was a file copy, not a `git clone`, and the Docker path remains unverified.
- **No cloud deployment,** and no cost estimate yet. See [deployment_plan.md](deployment_plan.md).
- Logistic regression matched LightGBM on the test sets, so the extra complexity is not justified by these results.
- Test sets are small: 35 positive churn rows and four forecast quarters.
- Search is lexical, injection filtering is pattern-based, and the rate limiter and scheduler assume one process.

Full list: [limitations.md](limitations.md).

## 3. How I would explain this project in an interview

### One-minute pitch

Revenue leaders ask what will close, what might churn, and why, but the answers sit across CRM, billing, product and support systems. I built RevenueOS to join that data into one account record, then predict win probability, churn and forecast. The key design rule is that models calculate, the LLM explains, and every claim cites its source. The LLM can only reach data through read-only tools scoped to the user's team, and code checks its citations and numbers after each answer. Because the data is synthetic, I planted known rules and tested that the system recovers them, while being clear that this proves the pipeline, not real-world accuracy.

### Three-minute architecture walk-through

Data enters through a connector interface, so Salesforce or Stripe can be added without changing anything else. Quality checks run on raw rows, and the loader upserts on source ids, so it is idempotent. Bad rows are quarantined, not dropped.

Everything lands in Postgres with pgvector, which keeps relational data and search together, so team scoping is one join.

The ML layer's most important idea is point-in-time features. Each training row is a deal as it looked on a past date, and a test deletes all later data and proves the features do not change. Splits are by time. For churn I also purge 90 days between train and test, because the label looks 90 days ahead. Models are chosen on validation, never on the test set. SHAP values become plain-language reasons that use the record's real values.

The forecast simulates each open deal 5,000 times, using win probability and a learned chance of landing in the quarter. That gives a range. A walk-forward back-test retrains for each past quarter using only earlier data. Weekly changes are categorised per deal and reconcile exactly to the total.

FastAPI serves everything through one Scope object, so a manager's restrictions apply equally to the API, citation lookups and the copilot. Role comes from the database, not the token.

The copilot is a Claude tool-use loop with seven read-only tools and no SQL tool. Tool results are marked as untrusted, and suspicious text is withheld. After each answer, code checks that citations match real tool results and numbers match tool data. It repairs once, then removes or flags what fails, and everything goes to an audit table.

### Five likely follow-up questions

**1. How do you know the model is not leaking?**
Three controls. Features are built as of a date, and a test deletes everything after that date and asserts the features are unchanged. Splits are by time, not random. For churn, training stops 90 days before testing, because labels look 90 days ahead. Point-in-time correctness also needed extra columns for close-date history, because the final close date would have leaked.

**2. Your churn AUC is 0.94. Is that good?**
It is good evidence the pipeline works, and weak evidence of anything else. I planted the rules, so the signal is unusually clean, and the test set has only 35 positive rows, so the interval runs from 0.84 to 0.99. On real data I would expect much lower, and I would judge it by capture rate against the client's current process.

**3. Why LightGBM if logistic regression did as well?**
I selected on validation, where LightGBM won, and I did not switch after seeing the test set, because that would make the test result meaningless. Honestly, logistic regression was slightly ahead on test, within noise. The planted rules are nearly linear, so that makes sense. In production I would lean towards the simpler model unless real data showed a clear gain.

**4. How do you stop the LLM from inventing numbers?**
In layers. It has no data access except tools, and the prompt says to use only tool results. Then code checks every citation against records actually returned, and every number against tool values, with rounding tolerance. Failures get one repair attempt, then invalid citations are removed and unmatched numbers are flagged. The limit is that the check proves a number exists, not that it is attached to the right fact. I also have to be honest that I have not yet run this against a live model.

**5. What happens if someone hides a prompt injection in a support ticket?**
I planted four to test this. Free text is neutralised and suspicious text is withheld before the model sees it, and tool output is marked as untrusted data. Pattern matching will miss clever attacks, so the real defence is structural: tools are read-only, scoped and cannot send anything. A clever injection could still distort the wording of an answer, but it cannot change data or reach another team's records.
