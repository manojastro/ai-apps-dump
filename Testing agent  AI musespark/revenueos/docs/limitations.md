# Limitations, and what I would do with real client data

## Limits of what exists today

**The numbers prove the pipeline, not accuracy.** I wrote the rules in the data, then the models found them. Real deals have messier causes, missing fields and changing behaviour.

**The copilot has never talked to a real model.** Its loop, scoping, audit and guardrails are tested with a scripted stand-in. Whether Claude picks the right tools, cites correctly, refuses properly and resists injection is unknown until the live eval runs.

**Small samples.** The churn test set has 35 positive rows, and the forecast back-test has four quarters. Confidence intervals are wide. The forecast range cannot be called calibrated from four points.

**Known simplifications:**

- Every account starts as a customer, so a `new` deal means new business with an existing account.
- Deal amounts are not linked to subscription MRR, except that renewals use contract value.
- A deal's close date can only change once in the data.
- The champion-left signal only exists on an account's latest contract term.
- Renewal outcomes follow the churn simulation, so deal-level signals say little about them.
- Six closed deals have impossible dates. They are excluded from training, but still count in closed-won totals.
- Reason thresholds, such as "no activity in 10 days", are judgement calls and not learned.

**Search matches words, not meaning.** The local embedder finds "SSO login" but would miss "sign-on trouble".

**Injection filtering is a pattern list.** It catches obvious attacks and will miss clever ones. The real boundary is that tools are read-only and scoped, so a successful injection can still mislead the answer text, but cannot leak other teams' data or change anything.

**The number check has gaps.** It confirms a number exists somewhere in tool results, not that it is attached to the right fact. Correctly derived sums get flagged as ungrounded.

**Single-process assumptions.** The rate limiter is in memory, and the scheduler runs inside the API.

**Not built:** password reset, multi-factor login, SSO, audit-log export, per-field permissions, real connectors, and automated model retraining or drift monitoring. The cookie-based login relies on SameSite=Lax rather than CSRF tokens.

## What I would do with real client data

1. **Start with a data audit.** Run the quality report on real exports first. Stage history and close-date history often are not kept, and without them honest back-tests are impossible.
2. **Agree definitions in writing.** What counts as churn, ARR, a qualified deal, or commit differs by company. Models inherit those choices.
3. **Build real connectors behind the existing interface,** with incremental sync and handling for deleted records. The current upsert never removes rows.
4. **Rebuild features from history.** Many CRMs overwrite fields, so point-in-time correctness may need snapshots collected from day one.
5. **Re-establish every baseline.** Compare with the client's actual forecast process, not a stage rule I made up. If the model cannot beat it, say so.
6. **Run in shadow mode for at least two quarters.** Score without showing users, then compare with reality before anyone relies on it.
7. **Check fairness and feedback loops.** If reps act on a low score by dropping a deal, the model confirms itself.
8. **Monitor drift, calibration and copilot quality,** with retraining on a schedule and a human reviewing the audit log.
9. **Handle privacy properly.** Real tickets and emails hold personal data. That needs a data processing agreement, retention rules, redaction before text reaches an LLM, and a review of what the LLM provider stores.
10. **Use a semantic embedding model,** after approving where that text is sent.
