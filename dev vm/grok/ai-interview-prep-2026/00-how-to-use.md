# 00 — How to Use This Interview System

This handbook is designed so you can generate answers in the room, not reciting scripts.

If you catch yourself memorizing a paragraph, stop. Convert it into:

1. Concept (what it is)
2. Logic (why it exists)
3. Structure (how you will say it)
4. Keywords (the 5–8 terms interviewers listen for)
5. Example (one real or honestly scoped project)
6. Trade-off (what you gave up)

That six-part card is the only thing you should memorize per topic.

---

## The interview is a signal game

Every question is a probe. The interviewer is rarely hunting for the Wikipedia definition. They are scoring:

| Signal | How you show it |
| --- | --- |
| You have shipped | Specific constraints, numbers, incidents |
| You can debug | Ordered investigation, not guesses |
| You can design | Requirements before components |
| You can judge | When *not* to use the trendy thing |
| You can communicate | Structured, time-boxed, interruptible |
| You can be trusted | Honest boundaries, no bluffing |

A correct but unstructured answer scores lower than a slightly incomplete structured one, because the panel cannot tell whether you will hold up in a production incident.

---

## Recommended paths

### Path A — You have 8–10 days and a scheduled loop

Pick **one** primary role from Chapter 02.

| Day | Work |
| --- | --- |
| 1 | Chapters 01–05. Fill the scorecard honestly. Pick the two weakest high-weight topics. |
| 2 | Role process + Python/API/SQL as needed. One coding drill. |
| 3 | LLM + RAG. Speak 10 answers out loud. |
| 4 | Agents + MCP + security. Speak 10 answers. |
| 5 | Cloud / Docker / LLMOps depending on JD. One full system design. |
| 6 | Project defense + behavioral STAR. Record yourself. |
| 7 | Mock interview for your role. Do not peek. Score it. |
| 8 | Remediate the two lowest scores. Pressure mode. Rapid-fire. |
| 9 | 24-hour checklist. Company + JD prediction. |
| Interview day | 60-minute sheet only. Do not cram new topics. |

### Path B — You have 4 weeks

| Week | Focus |
| --- | --- |
| 1 | Foundations: Python, APIs, SQL, Docker, answer frameworks. Daily 45-minute coding. |
| 2 | RAG + evals + vector DB. One end-to-end retrieval notebook with metrics. |
| 3 | Agents + MCP + security + cloud of the JD. One agent with hard step limits and traces. |
| 4 | System design, project defense, behavioral, mocks, pressure, rapid-fire. |

### Path C — Career transition from another IT domain

Do Path B, but add Chapter 26 on day 1 and rewrite your intro (Chapter 25) before any technical drill. If you cannot explain transferable production skills in 60 seconds, technical prep will not save the recruiter screen.

---

## How to study a question in this book

For every major question, the handbook gives more than an answer. Use it like this:

1. Cover the answer. Attempt it out loud in 30 seconds.
2. Check: did you hit what the interviewer is testing?
3. Attempt the 2-minute version.
4. Only then read the deep answer.
5. Write *your* 6-part card in your own words.
6. Invent one follow-up and answer it.

If you only read answers, you will freeze when the wording changes.

---

## How long should an answer be?

| Question type | Default length | Stop when |
| --- | --- | --- |
| Definition | 20–40 seconds | You have WHAT / WHY / one example |
| Practical “how would you…” | 60–120 seconds | You named components + one trade-off |
| Production / troubleshooting | 2–4 minutes | You have an investigation order |
| System design | 8–12 minutes structured | You invited follow-ups |
| Behavioral | 90–150 seconds STAR | Result is quantified |
| Coding narration | continuous | Tests exist and edge cases are named |

If the interviewer nods and looks down at notes, stop. Silence after a structured answer is usually them scoring you, not you failing.

---

## Daily drill (45–70 minutes)

1. **10 min** — Rapid-fire: 8 questions from Chapter 31.
2. **20 min** — One deep topic card (RAG chunking, agent loops, MCP security, etc.).
3. **15 min** — One project or behavioral story, timed.
4. **15 min** — Optional: coding or SQL, or one design sketch.

Three focused hours a week of spoken drill beats fifteen hours of silent reading.

---

## What “prepared” means in this system

You are interview-capable when you can, without notes:

- Explain RAG, agents vs workflows, and evals at senior depth.
- Whiteboard an enterprise assistant with ACL, citations, and failure modes.
- Defend one project for 20 minutes of “why not X?”
- Debug a latency, cost, or quality incident in a fixed order.
- Tell four STAR stories with your contribution and a number.
- Admit a boundary without collapsing.

Use Chapter 35 to score that, not a feeling of “I read a lot.”
