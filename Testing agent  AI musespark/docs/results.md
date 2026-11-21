# Results — headline eval numbers

> Phase 1: planner-only. Full 7-metric table + red-team table land in Phase 5 with real runs. Nothing is fabricated here.

| Metric | What it answers | Result |
|---|---|---|
| Precision | Of reported bugs, how many were real? | TBD (Phase 5) |
| Recall | Of real bugs, how many found? | TBD |
| False-alarm rate | Flaky called bug? | TBD |
| Blocked-misclassification | Env problem called bug? | TBD |
| Mean cost per test case | Affordable at scale? | TBD |
| Mean steps per flow | Efficient or wandering? | TBD |
| Bug report quality (1–5 LLM judge) | Reproducible? | TBD + rubric |

## Red team

| Category | Pass rate |
|---|---|
| DOM prompt injection | TBD |
| Fake success (banner vs 500) | TBD |
| Infinite loop bait | TBD |
| Data exfiltration bait | TBD |

## What does not work yet

Phase 1: no browser, no Jira/PR, no golden runs. See phase acceptance in the build prompt.
