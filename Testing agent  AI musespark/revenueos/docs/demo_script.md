# Five-minute demo script

Before you start, run the app and sign in as `cro@revenueos.example`. Exact figures change if the data is regenerated, so read them from the screen. Say early that all data is synthetic.

**0:00 The problem (30 seconds).** "Revenue data sits in four systems: CRM, billing, product and support. Leaders ask three questions: what will we close, what are we about to lose, and why. RevenueOS joins that data, models calculate the answers, and an AI explains them with a source for every claim."

**0:30 Dashboard (60 seconds).** Point to expected revenue and its range. "A forecast is a range, not a number. This comes from 5,000 simulated quarters." Compare it with rep commit. Show "What changed this week" and note that it reconciles exactly to the total change. Scroll to the back-test: "Each past quarter was forecast using only what was known at the time. On this synthetic data it beat stage-weighting on average, though one quarter was a tie. It proves the pipeline, not real-world accuracy."

**1:30 Deals (60 seconds).** Open Deals, sorted by risk. Read a few reason chips aloud. "These are SHAP explanations written as plain facts about each deal." Open one deal. Mention that heavy discounts do not help, which was a planted rule the model recovered.

**2:30 Account 360 (45 seconds).** Open an account from Retention. Show usage against seats, open risks, the timeline across systems, and click a citation chip to open the source record. "Every claim traces back to a row."

**3:15 Retention (30 seconds).** Show at-risk ARR and reasons. "This total traces to named accounts." Point out expansion triggers. "Same data, opposite direction."

**3:45 Copilot (45 seconds).** If a key is configured, ask "Which deals are most at risk this quarter, and why?" Click a citation. Then ask "What is the capital of Australia?" to show the refusal. If no key is configured, show the page, say so plainly, and explain the design: seven read-only tools, no SQL, citations and numbers checked in code after each answer.

**4:30 Governance (30 seconds).** Sign out, then sign in as `manager1.emea@revenueos.example`. "This manager sees only EMEA. It is enforced in the backend, so it applies to the API and the copilot too." Sign in as admin and show model versions, data health and the audit log.

**5:00 Close.** "Next step with a real client is a data audit, then shadow mode for two quarters before anyone relies on it."
