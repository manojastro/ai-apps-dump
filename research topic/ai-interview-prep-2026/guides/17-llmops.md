# 17 — LLMOps

**What this chapter trains:** the production loop that turns a demo into a system you can ship, measure, regress, and roll back. Tracing, logs, metrics, versioned prompts, tokens, latency, cost, evaluation, canaries, RAG and agent monitors.

**Who gets this:** every applied AI loop. GenAI, Agentic, LLM Engineer, Cloud AI, FDE, Solutions. If the JD says “production,” they will probe how you know it works.

**Interview frequency:** near-certain at mid and senior. The silent vendor-model-change question is a common senior filter.

**The single line they want:** *We do not ship on “looks good.” We ship on a numeric bar, and we can tell you which metric moved when quality dropped.*

If you only remember one stance from this chapter: **evaluation is the product.** Orchestration without evals is a demo with extra YAML.

---

## How to use this chapter

For every major question: cover the answer, speak 30 seconds, then 2 minutes, then read the senior version. Write your own 6-part card (concept, logic, structure, keywords, example, trade-off). Invent one follow-up and answer it out loud.

Do not memorize paragraphs. Memorize the **order you talk** and the **numbers you would actually put on a dashboard**.

---

## What interviewers are scoring

| Signal | Pass | Fail |
| --- | --- | --- |
| You have operated, not just built | Named traces, eval slices, a rollback | “We used LangSmith” with no metrics |
| You can debug | Ordered investigation: retrieval vs gen vs tools vs model | Guessing “maybe the prompt” |
| You can judge | Numeric ship bar, known judge biases | “Human vibe check before release” |
| You can be trusted with cost | Tokens, cache, routing, cost/task | “It’s just API spend” |
| You expect drift | Pins, canaries, nightly golden-set, vendor change | “The model is GPT-4 so it should be stable” |

**Keywords they listen for:** trace, span, TTFT, TPOT, E2E, golden set, slice, LLM-as-judge calibration, position bias, verbosity bias, self-bias, prompt registry, model pin, canary, rollback, faithfulness, citation fail, empty retrieval, loop rate, cost per successful task, OpenTelemetry.

---

## The LLMOps loop (say this on a whiteboard)

```
  change (prompt / model / index / tool / policy)
           │
           ▼
   offline eval on frozen golden sets + slices
           │
           ▼
   canary / shadow  ──fail──► rollback (pin previous)
           │ pass
           ▼
   online monitors (quality, latency, cost, safety)
           │
           ▼
   traces + human review ──► new labeled examples ──► datasets
```

Four artifacts you version together: **prompt**, **model ID**, **retrieval index / corpus hash**, **tool schemas**. A change to any one is a release.

---

## Telemetry map — traces, logs, metrics

Do not say “we log everything.” Say **what each signal is for**.

| Signal | What it is | What you use it for | What it is bad at |
| --- | --- | --- | --- |
| **Traces** | One request = one trace; nested spans for retrieve, rerank, LLM, tools, judge | Replay a failure, attribute latency/cost, debug agent loops | Cheap high-cardinality dashboards; long retention of raw prompts |
| **Logs** | Discrete events: authz deny, empty retrieval, tool timeout, safety block | Incident search, audit, paging | Reconstructing a multi-step agent without span IDs |
| **Metrics** | Time-series: TTFT, TPOT, E2E, tokens, $, error rates, eval scores | SLOs, alerts, capacity, cost | Explaining *why* a single user got a bad answer |

**Interview-safe instrumentation:** OpenTelemetry spans with gen-AI semantic conventions (`gen_ai.system`, model, token counts, tool name) as the **export**. LangSmith / Langfuse / Phoenix / Datadog as the **backend**. Do not couple business logic to a vendor SDK if you can emit OTel.

**Minimum span attributes on every LLM call:** `model_id` (pinned), `prompt_version`, `input_tokens`, `output_tokens`, `ttft_ms`, `tpot_ms`, `cached_tokens`, `finish_reason`, `safety_route`, `user_or_tenant` (hashed), `session_id`, `trace_id`.

**Redaction:** traces are a secret store if you are sloppy. Strip API keys, raw PII, and full document bodies by default; store pointers and hashes. This is also an LLM02 / MCP01 issue — see Chapter 19.

---

## Tooling landscape (pick by constraint, not by tweet)

| Tool | Interview-safe fit | Probe they will make |
| --- | --- | --- |
| **OpenTelemetry** | Vendor-neutral export; required answer even if you use a SaaS | Semantic conventions, sampling, PII in spans |
| **LangSmith** | LangChain / LangGraph teams; traces + datasets + experiments | Lock-in, data residency, cost at high volume |
| **Langfuse** | OSS / self-host, framework-agnostic, prompt management | You actually ran it, not just starred it |
| **Arize Phoenix** | OTel-native, embedding viz, eval primitives | How you use it in CI vs prod |
| **MLflow** | Databricks / classical ML orgs that already have a registry | Prompt registry vs “notebook logging” |
| **Datadog LLM Observability** | Estate already on Datadog APM | Correlation with infra metrics, not a second island |
| **Cloud monitors** | CloudWatch, Azure App Insights, GCP Cloud Trace / Vertex evals | Identity, VPC, and where traces live |

**Interview-safe stance:** “Traces go out over OTel. The backend is whoever already owns observability, plus an LLM-native store for prompt versions, datasets, and evals. I can defend LangSmith *or* Langfuse *or* Phoenix; I will not pretend they are interchangeable with Prometheus.”

---

## The ship bar (numeric, or it is not a bar)

Write a bar like this on the board. Adjust numbers to the product; never leave them blank.

| Gate | Example bar (internal RAG copilot) | What happens if missed |
| --- | --- | --- |
| Faithfulness / groundedness | ≥ 0.88 on golden set, no slice < 0.80 | Block release |
| Citation coverage | ≥ 0.90 of claims have a retrieved span | Block if user-facing |
| Answer correctness (human or calibrated judge) | ≥ 0.85 overall; hard slice ≥ 0.75 | Block |
| Empty retrieval rate | ≤ 2% of eligible queries | Page if prod exceeds 2× baseline |
| Citation fail (claimed doc not in context) | ≤ 1% | Block |
| Safety / policy | 0 P0 jailbreak or PII leaks on red-team set | Block |
| E2E latency | p50 ≤ 3s, p95 ≤ 8s streaming | Warn; block if p95 > 12s |
| TTFT | p95 ≤ 1.2s | Warn |
| Cost per successful task | ≤ $0.04 (or budget SLO) | Warn; rollback routing |
| Tool error rate (agents) | ≤ 3% | Page |
| Loop / step-cap hits | ≤ 0.5% of sessions | Page |

“Looks good to the PM” is a **review**, not a gate. Human spot-checks calibrate the judge; they do not replace the bar.

---

## Q1 — What is LLMOps, and how is it different from MLOps?

**Why they ask.** They are checking whether you operate *generative* systems or you recycled a 2019 MLOps answer (feature store, model registry, batch drift). Wrong boundary here poisons every later answer.

**Structure.** (1) Job of LLMOps. (2) What is non-stationary. (3) Contrast with MLOps. (4) One sentence on AIOps so you do not mix the three.

**30-second answer.** LLMOps is how we develop, evaluate, ship, observe, and roll back systems whose behavior is dominated by prompts, retrieved context, tools, and a non-stationary model. The unit of release is not only a model binary — it is prompt + model pin + index + tool schema. MLOps optimized training pipelines and statistical drift on tabular/CV models. LLMOps optimizes traces, evals, tokens, and blast radius when the vendor changes the model under us.

**2-minute answer.** I split the loop into four loops that run continuously. *Dev:* prompts and graphs are versioned artifacts with owners, diffs, and reviews — same as code. *Eval:* frozen golden sets plus slice metrics, not a vibe check. *Release:* pin the model ID, canary, automatic rollback. *Operate:* traces for replay, metrics for SLOs (TTFT, TPOT, E2E, cost/task), online judges and user feedback for drift. What makes it unlike classical MLOps is that a “model upgrade” can happen without our training job, retrieval quality dominates generation quality, and a single prompt edit can change production more than a fine-tune. We still steal the good parts of MLOps: registries, lineage, canaries, rollback. We add prompt registries, token economics, and judge calibration.

**Senior answer.** I would not run LLMOps as a separate platform religion. I would attach it to the existing delivery path. CI runs the golden set on every prompt, model, or index change; CD cannot promote if any gated slice drops more than the allowed delta (I use 2 points absolute on the primary metric unless we have a documented exception). Production emits OTel traces sampled by route: 100% of errors and safety events, 5–20% of successes, 100% of canary. Datasets are living: production traces that fail the judge or get thumbs-down are reviewed, labeled, and promoted into the golden set on a weekly cadence so we do not freeze the eval to last quarter’s traffic. The operational contract with the business is a ship bar they signed — faithfulness, citation, latency, cost, safety — not a model name. If the org already has MLflow, I put prompts and eval runs there and keep traces in the APM. If the org is LangGraph-native, LangSmith is the fastest path, with OTel export so we are not trapped. The failure mode I watch is **eval theater**: a 50-example notebook that always passes. I would rather have 200 labeled items with slices and a known judge kappa than 5,000 unlabeled “scores.”

**Weak answer.** “LLMOps is MLOps for LLMs. We use LangChain and LangSmith to monitor the model.” No distinction, no artifacts, no numbers, no rollback.

**Follow-ups.**

- *Where does AgentOps fit?* AgentOps is LLMOps plus tool/step/loop/HITL monitors. Same platform, extra spans and extra gates. I do not buy a second religion for it.
- *Where does AIOps fit?* AIOps is applying ML/LLMs to *IT operations* (alerts, correlation, RCA). Different user, different write-access policy. Chapter 18.
- *Do we still need a model registry?* Yes, for fine-tunes, adapters, and pins. For hosted models the registry row is `vendor + snapshot ID + eval digest`, not a pickle file.

---

## Q2 — How would you instrument an LLM application?

**Why they ask.** They want an investigation order, not a product tour. Seniors instrument for *attribution*: which span burned the tokens, which tool looped, which retrieval returned nothing.

**Structure.** (1) One trace per user task. (2) Spans you always have. (3) Metrics and logs beside traces. (4) Sampling, redaction, correlation IDs. (5) What you alert on vs what you only query.

**30-second answer.** One trace per user task, nested spans for routing, retrieval, rerank, each model call, each tool, and any online judge. Metrics for SLOs: TTFT, TPOT, E2E, tokens, cost, error and empty-retrieval rates. Logs for audit events. OTel out, LLM-native backend for replay. Redact PII. Sample successes, keep all failures.

**2-minute answer.** I start from the question I need to answer at 2 a.m.: “this user got a wrong, slow, or expensive answer — which stage failed?” That forces a span per stage with inputs/outputs *pointers*, token counts, and latency. I propagate `trace_id` through the gateway, the orchestrator, the vector DB, and tools. RED metrics (rate, errors, duration) sit on each span name. For LLMs I add USE-like saturation: queue time, cache hit rate, GPU or RPM headroom. I never alert off raw prompt text. I alert off SLOs and sentinel rates: p95 E2E, cost/task spike, empty retrieval, tool error, loop-cap hits, judge-score drop. Traces are for debug and for mining eval datasets. If I can only add one thing to a messy app this week, it is a single `trace_id` and model/prompt version on every log line — then I add real spans.

**Senior answer.** Instrumentation is a product decision because traces contain the business. I treat the trace pipeline as a data store with ACL, retention, and redaction, not as “debug stdout.” Default: hash user ids, drop raw retrieved chunks after N days, keep chunk IDs and scores, keep model IO for failed traces longer than for successes. Sampling is **tail-based** if the collector supports it: keep slow, expensive, and low-judge traces at 100%, random-sample the rest. I budget observability cost as a percent of LLM spend (I start at 5–10% and cut if it exceeds). For multi-agent graphs I force a parent span per agent and a `step_index` so loops are queryable (`count(tool_calls) by trace` > N). I correlate with infra: if TPOT doubles, I join to GPU throttling or vendor HTTP 429s in Datadog/CloudWatch — LLM dashboards that cannot see the load balancer are toys. OpenTelemetry is the contract between app teams and the platform team; vendor SDKs are allowed as convenience, not as the source of truth.

**Weak answer.** “I’d add print statements and LangSmith.” No sampling, no redaction, no SLO, no 2 a.m. question.

**Follow-ups.**

- *What is in a span vs a log?* Span = timed unit of work with attributes. Log = event inside it. If you only log, you will not get a waterfall.
- *How do you handle streaming?* TTFT is the time to first streamed token. The LLM span stays open until `finish_reason`. Record `bytes_to_first_token` and cancel/disconnects.
- *PII in traces?* Redact at the exporter. Never “we’ll remember not to prompt PII.” Assume someone will.

---

## Q3 — Prompts as versioned artifacts — what does that actually mean?

**Why they ask.** Prompt-in-a-string-in-code is how quality incidents become un-reproducible. They want change control.

**Structure.** (1) What is versioned. (2) How it is reviewed. (3) How it is loaded at runtime. (4) How it ties to evals. (5) What you do not put in a prompt.

**30-second answer.** A prompt is a release artifact: ID, version, template, model pin, input schema, owner, eval digest. You review it like code, you pin it in production, you can roll it back without a full app deploy, and you never ship a prompt that has not run the golden set. Secrets and trust-critical policy do not live in the prompt text.

**2-minute answer.** In practice I keep prompts in a registry (Langfuse / LangSmith / a git-backed repo with a loader). The running service asks for `prompt_id@version` or a label like `prod`. A change creates a new immutable version; `prod` is a pointer. CI runs the golden set comparing `prod` vs candidate and posts a diff: win/lose/tie per slice. Runtime logs `prompt_version` on every trace so a regression is attributable. For structured outputs I version the schema with the prompt. For RAG, the system prompt versions with the citation policy. Rollback is flipping the label, not reverting a 4,000-line PR that also changed billing. I still keep the templates in git for review and disaster recovery — the registry is not a second source of truth without an export.

**Senior answer.** The hard part is **composition**. Production prompts are not one string: system, developer, tool-preambles, memory summaries, retrieved docs, user. I version the *controlled* parts (system, tools, routing policy) and treat retrieved text as untrusted data, never as a versioned instruction. I refuse to put API keys, tenant ACLs, or “never do X” as the only enforcement in prompt text — that is LLM08 waiting to happen. Policy enforcement stays in code: allowlists, schema validation, HITL. The prompt can *explain* the policy; it cannot *be* the policy. For multi-tenant products I parameterize tone and product names, but I do not let each tenant paste a system prompt without a review queue. Eval-wise, a prompt change that wins overall but loses the “refusal” or “citation” slice does not ship. I also track **prompt length** as cost and as attention dilution: if the system prompt grew 3× in six months, that is a design smell, not a badge.

**Weak answer.** “We keep prompts in a Google Doc and paste them into LangChain.” No version, no eval, no rollback.

**Follow-ups.**

- *Hot-reload vs deploy?* Labels can hot-reload if the app is built for it; I still require CI eval before the label moves.
- *Who approves?* Same as code: author cannot approve their own prompt for a gated surface.
- *A/B prompts?* Fine, with traffic splits, independent eval, and a kill switch. Not five undocumented variants in if-statements.

---

## Q4 — TTFT vs TPOT vs E2E — which latency matters?

**Why they ask.** Latency answers that say “we stream so it’s fine” fail. They want you to pick the metric that matches the UX and to debug the right span.

**Structure.** (1) Define the three. (2) What the user actually feels. (3) Typical budgets. (4) How you debug a breach. (5) Trade-offs (model size, retrieval, tools).

**30-second answer.** TTFT is time to first token — perceived snappiness. TPOT is time per output token — how fast the rest streams. E2E is the whole task, including retrieval and tools. Users feel TTFT first and E2E if they must wait for a complete, cited answer. I set SLOs on all three and debug with a span waterfall, not a single timer.

**2-minute answer.** For a streaming chat UX I budget TTFT p95 under about 1.2s and TPOT in the 20–80 ms range depending on the model. E2E p95 for a simple RAG turn under 8s; agents get a step budget, not a blank check. TTFT includes queueing, auth, retrieval if you retrieve *before* first token, and the vendor’s prefill. If TTFT is bad but TPOT is fine, I look at retrieval, cold starts, prefix-cache misses, and gateway queue — not at decoding. If TPOT is bad, I look at the model tier, concurrency, GPU saturation, or vendor throttling. If E2E is bad but both token metrics are fine, I have too many sequential tools or a slow reranker. I always stream when the user is waiting on language; I do not stream when the next step is a tool that needs the full JSON.

**Senior answer.** Prefill vs decode is the mental model. TTFT is dominated by **prefill** (input tokens, including a fat RAG context) plus any synchronous work before the call. That is why dumping 20 chunks into context makes the product feel slow even on a “fast” model. I cap context, run retrieval in parallel with a short “thinking” preamble only if product allows, and use prompt caching / prefix caching for the static system prompt so TTFT does not pay full prefill every time. I report **TTFT excluding retrieval** and **TTFT including retrieval** as two series; otherwise a retrieval regression looks like a model regression. For agents, I report **time-to-first-useful-token** after the last tool, and **time-to-HITL**. SLOs are per route: autocomplete ≠ research agent. I would rather hit a smaller model with p95 TTFT 400 ms than a frontier model that stares at the user for 4s. Cost and latency couple: output tokens dominate both TPOT-wait and bill, so I constrain max tokens by route. Failure mode: averaging latency across cheap FAQ and expensive agent traces until the SLO is green and the agent is unusable.

**Weak answer.** “We measure response time. Streaming makes latency not matter.”

**Follow-ups.**

- *p50 vs p95 vs p99?* p50 is product feel for typical; p95 is the SLO; p99 catches vendor blips and pathological retrieval. Never alert only on mean.
- *How does RAG hurt TTFT?* Large contexts increase prefill. Fix: rerank down to 3–6 chunks, compress, cache.
- *Time-to-first-byte vs TTFT?* For LLMs they should match on the token stream. If TTFB is fast but first *token* is slow, you are flushing headers and stalling on retrieval.

---

## Q5 — How do you manage tokens and cost in production?

**Why they ask.** Unbounded consumption is LLM06. Interviewers want cost as a first-class SLO, not an invoice surprise.

**Structure.** (1) Unit of cost (per task, not per token only). (2) Where tokens go. (3) Controls. (4) Alerts. (5) Routing.

**30-second answer.** I budget **cost per successful task**, not just $/1k tokens. I attribute tokens to prompt, retrieval, tools, retries, and judge calls. Controls: max tokens, context caps, prompt caching, smaller models on easy routes, hard step caps on agents. I alert on spend rate and on cost/task drift, and I can shed load to a cheaper model without a code freeze.

**2-minute answer.** Output tokens usually cost several times input, so verbosity is a budget bug. RAG context is the other silent killer: 4k retrieved tokens on every query with a 10% cache hit rate will dominate. I log `input`, `output`, `cached`, and `reasoning` tokens (if the vendor exposes them) on every span, multiply by the pinned price table, and roll up by tenant, route, and prompt version. Product gates: max output tokens per route, retrieve-top-k, tool-call budgets, and a per-tenant daily cap. Engineering gates: retry budgets with jitter, no unbounded agent loops, batch embeddings. I publish a weekly cost review: cost/task, cache hit rate, retry waste, judge spend (offline judges should not sit on the user path). If cost/task jumps 30% without a traffic mix change, I treat it as an incident — usually a prompt regression, a model swap, or a retrieval-k change.

**Senior answer.** I separate **unit economics** from **denial-of-wallet**. Unit economics is product: is this task worth $0.04? Denial-of-wallet is security: a prompt injection or a recursive tool loop should not be able to print money. The latter gets rate limits, per-session caps, and circuit breakers that do not wait for finance. I keep a **price table as config** keyed by model pin so a vendor price change does not require a code hunt. Routing: cheap classifier or small model first; escalate on uncertainty or on a hard slice. I measure **escalation rate** — if everything escalates, routing is theater. For agents I optimize **cost per completed successful task**, which punishes loops that burn tokens and then fail. Shadow evals and LLM-as-judge have a cost budget too; I run cheap judges online on a sample and expensive judges offline. I will not “save money” by dropping traces — one un-debuggable week costs more than the trace store. Trade-off I will say out loud: prefix caching helps TTFT and cost but can leak context across users if the cache key is wrong. Cache keys include tenant and prompt version.

**Weak answer.** “We’d watch the OpenAI bill and switch to a cheaper model if it gets high.”

**Follow-ups.**

- *How do you cost a RAG call?* Embed query (often negligible) + retrieval infra + rerank model + generation tokens (prompt includes chunks) + citation check.
- *Should the judge run on every request?* No. Sample. Calibrate. Keep the judge off the critical path unless it is a cheap safety filter.
- *Reserved capacity vs on-demand?* If p95 latency is a product SLO, buy provisioned throughput for the pinned model. If load is spiky and quality-tolerant, on-demand plus a fallback model.

---

## Q6 — How do you evaluate an LLM system before users see it?

**Why they ask.** This is the differentiator chapter. Candidates who cannot talk evals get filtered even if they can wire RAG.

**Structure.** (1) What “good” means for this product. (2) Golden sets and slices. (3) Metrics (task, not BLEU). (4) Human vs code vs judge. (5) The numeric ship bar.

**30-second answer.** I define the user task and a numeric bar: correctness, faithfulness, citations, refusal quality, latency, cost. I freeze a golden set with slices (easy, multi-hop, adversarial, empty-retrieval, safety). I score with a mix of exact checks, retrieval metrics, and a **calibrated** LLM-as-judge, then I require a human-labeled subset for agreement. Nothing ships if a gated slice drops.

**2-minute answer.** Offline first. Build a dataset of real queries — production traces if we have them, otherwise carefully authored ones — with expected answers or acceptable-claim lists and the docs that should be retrieved. Split by slice so an overall 90% cannot hide a 40% on “numbers and dates.” Retrieval gets recall@k and MRR on labeled relevant IDs. Generation gets faithfulness (no claim without support), citation coverage, and task correctness. Safety gets a separate red-team set that must stay at zero P0. I run this in CI on every prompt/model/index change. Online next: sample production, score asynchronously, watch the same metrics plus user feedback. Human review is the calibration source, not the bottleneck for every row. The ship bar is written down; “PM liked it” is not in the table.

**Senior answer.** Eval is a measurement system, so I treat error like I would in any metric: sampling bias, label noise, judge bias, leakage. Leakage: if the golden answers sat in the prompt or the index, we are testing memorization of the eval. I keep eval queries out of fine-tunes and out of few-shot prompts. Label noise: dual-annotate a subset, measure agreement, adjudicate. Slices I insist on: **freshness** (docs that changed this week), **ACL** (must refuse or hide cross-tenant), **unanswerable** (must abstain), **injection** (retrieved docs that contain instructions). For agents I eval **task success**, **unauthorized tool calls**, **step count**, and **cost**, not just the final paragraph. I report confidence intervals when the set is small — a 2-point drop on n=40 is not a release blocker; a 2-point drop on n=400 with a bad hard-slice *is*. I version datasets like prompts: `gold_v14` plus a changelog. When product strategy changes, the bar changes in the same PR as the prompt, so we do not silently grade the old task.

**Weak answer.** “We’d have some people try it and use LLM-as-judge.” No slices, no calibration, no bar.

**Follow-ups.**

- *BLEU / ROUGE?* Almost never for assistants. They punish valid paraphrases and miss hallucinations.
- *How big is the golden set?* Enough per slice to see a 5-point swing. I would rather 50 per slice than 1,000 undifferentiated rows. Grow from production failures.
- *Eval in CI time?* Fast subset on every PR (minutes), full set on merge / nightly. Do not skip the fast subset.

---

## Q7 — LLM-as-judge: how do you calibrate, and what biases do you watch?

**Why they ask.** Uncalibrated judges are how teams ship regressions with green dashboards. This question separates people who have been burned from people who read a blog.

**Structure.** (1) Why a judge exists. (2) Calibration protocol. (3) Position, verbosity, self-bias. (4) When you do not use a judge. (5) How it fails in prod.

**30-second answer.** A judge is a noisy metric. I calibrate it against human labels on a held-out set and publish agreement (Spearman / Cohen’s κ / pairwise accuracy). I randomize order to cut **position bias**, instruct and length-normalize to cut **verbosity bias**, and I do not let a model grade its own family without a cross-family check — **self-bias**. If agreement is weak, I do not gate releases on that judge.

**2-minute answer.** Protocol: collect 100–300 items with human scores or preferences. Run the judge. Look at scatter and confusion, not a single correlation number. Tune the rubric until disagreement is understood — usually the rubric was vague (“be helpful”). Then freeze the judge prompt and model pin the same way I pin the app. Position bias: in pairwise eval, swap A/B and drop items where the judge flips with order, or average both orders. Verbosity bias: ask for claim-level scoring, or penalize extra claims, or compare on a fixed outline. Self-bias: use a different provider as judge, or an ensemble, or humans on the residual. I use code graders wherever I can — schema valid, citation ID exists, regex on required fields — and save the LLM judge for fuzzy quality. Online, I run the judge on a sample, never as the only user-visible filter unless it is a cheap safety classifier I have FPR/FNR for.

**Senior answer.** I treat judge drift as first-class: if I upgrade the judge model, I re-score a frozen panel and renormalize historical series so it does not look like the *app* improved. I slice agreement too: judges are often fine on fluency and bad on faithfulness, or fine on English and bad on citations. For faithfulness I prefer span-level entailment against retrieved text, not a holistic 1–5 “quality.” For agents I judge **process** (illegal tool, missing HITL) with deterministic checks, and **outcome** with humans or a judge. I will say the uncomfortable part: **a 0.8 correlation with humans is usable for trend and canary, not for firing people or for auto-blocking every release**. Gating thresholds come from a ROC-style view: what regression size do we catch at what false-block rate. Failure modes I have seen: judge prompt accidentally includes the candidate’s chain-of-thought in a way that rewards verbosity; pairwise judge always picks the first; safety judge over-refuses and we “fix” the app into being useless. I keep a **disagreement queue** for humans — that queue is the best dataset miner we have.

**Weak answer.** “We use GPT-4 as a judge. It’s aligned so the scores are reliable.” This is a hard fail. Alignment is not measurement.

**Follow-ups.**

- *Pointwise vs pairwise?* Pairwise is better for prompt A/B. Pointwise is better for dashboards. Calibrate both.
- *Can the app model judge itself?* Only as a weak signal. Never as the gate.
- *What if humans disagree?* Then the task definition is unclear. Fix the rubric before you automate.

---

## Q8 — Datasets: how do you build, slice, and maintain them?

**Why they ask.** No dataset, no eval. They want a living process, not “we downloaded MMLU.”

**Structure.** (1) Sources. (2) Labels. (3) Slices and leakage. (4) Refresh. (5) Privacy.

**30-second answer.** Datasets come from production traces, expert-authored edge cases, and red-team scripts — not from public leaderboards. Each row has input, context IDs, expected behavior, slice tags, and a label provenance. We refresh from failures weekly, we guard against leakage into prompts and indexes, and we treat dataset rows as PII-bearing until proven otherwise.

**2-minute answer.** I start with 30–50 expert examples so the pipeline exists, then I replace them with sampled production as soon as we have traffic. Labeling: task-specific. For RAG, relevant chunk IDs plus an answer key or claim list. For agents, a success predicate and a forbidden-tool list. Slices are tags, not separate folders that drift: `multi_hop`, `unanswerable`, `acl`, `injection`, `locale_de`, `long_context`. Maintenance: every incident becomes at least one row. Every thumbs-down sampled. I track **coverage vs current traffic** — if 40% of prod queries are “reset password” and the golden set is 90% trivia, the bar is lying. Privacy: annotate on redacted traces; store raw behind ACL; do not dump customer text into a SaaS eval tool without a DPA and a filter.

**Senior answer.** The dataset is part of the contract with the business. I get domain owners to sign off on slice weights: a bank care bot might weight “do not invent balances” at 10× trivia. I keep a **holdout** the team does not iterate on daily, so we cannot overfit the golden set with prompt-tuning-by-hand. I also keep a **canary set** of 10–20 items that must never break — the “if this fails, page me” items, including a known injection and a known unanswerable. Versioning: `dataset@sha` recorded on every eval run. When the index changes, retrieval labels may rot; I have a job that re-checks labeled chunk IDs still exist and still match the query, and it flags stale rows instead of silently scoring zeros. For multi-tenant, I never mix tenant A’s traces into a dataset that tenant B’s engineers can see. That sounds obvious and is the thing teams get wrong when they export LangSmith CSVs to Slack.

**Weak answer.** “We’d use public benchmarks like MMLU and GSM8K.” Those test the *model*, not your application.

**Follow-ups.**

- *Synthetic data?* Useful to bootstrap slices (especially injections and unanswerables). Always mix with real traffic before you trust the bar.
- *How do you label retrieval?* Binary relevant/not on the returned IDs, plus a note of *missed* relevant IDs if the annotator can search. Recall needs the misses.
- *Who labels?* Domain experts for the hard slice; trained annotators for volume; engineers for schema/safety. Not “whoever is free.”

---

## Q9 — A prompt, model, or index changed. How do you regression-test?

**Why they ask.** This is the weekly reality of LLMOps. They want a pipeline, not “we’d re-run some examples.”

**Structure.** (1) Treat each as a release. (2) What you freeze vs what you vary. (3) Metrics and deltas. (4) Canary. (5) Rollback.

**30-second answer.** Any of the three is a production change. I run the same frozen golden set, compare to the last good `eval digest`, and fail the pipeline if a gated slice drops more than the allowed delta. Index changes get extra retrieval metrics. Then I canary in prod with the same online scores and a one-click rollback to the previous pin.

**2-minute answer.** Isolation: change one axis at a time unless I am deliberately shipping a bundle. Prompt-only: generation and faithfulness. Model-only: the same plus latency/cost and a safety set (new models fail differently). Index-only: recall@k, empty retrieval, citation IDs still valid, then generation — because a better index can still break prompts that expected old chunk shapes. I store a baseline run: `gold_v14 + prompt@12 + model:xyz-2026-04-01 + index:sha`. The candidate must beat or tie within bounds. I look at **diffs**, not just means: which queries flipped from pass to fail. Those flips get human eyes before prod. Then shadow or canary 5–10% of traffic, watch online judge, empty retrieval, TTFT, cost/task, and error rate for a soak window (hours to days depending on traffic). Rollback is reverting the pointer, not rebuilding the world.

**Senior answer.** Index changes are the ones teams under-test. A re-embed, a chunker change, a metadata filter, a hybrid-weight tweak — all of these change the prompt the model actually sees. I keep **retrieval snapshots** for the golden queries: the candidate must explain recall moves. I also run a **pairwise** judge on flipped items so we do not argue from averages. For model changes I insist on a **pin**, a **price table update**, and a **tokenizer check** (silent tokenizer changes wreck length budgets). For prompt changes I require a diff review of the rendered prompt with a fixture context, not just the template — Jinja that accidentally drops the citation instruction is a classic miss. Bundle releases (prompt+model+index) are allowed if labeled as such, but the rollback plan has to say which axis we wind back first. I never A/B three things at once on the same population. Statistical note I will mention: with n=200, I am looking for consistent slice movement, not a 1-point overall wiggle. If traffic is low, I extend the canary, I do not lower the bar.

**Weak answer.** “If the new prompt seems better we’d deploy it and watch Slack.”

**Follow-ups.**

- *What is the allowed delta?* I default to “no gated slice down >2 points and no P0 safety fail.” Product can raise the bar; they cannot remove safety.
- *Re-embedding the corpus?* Treat as an index change plus a cost/latency event. Dual-write, switch reads, keep the old index until canary passes.
- *Feature flags?* Yes: `model_pin`, `prompt_label`, `index_alias` independently flaggable.

---

## Q10 — Model version pins, canaries, and rollback — how do you ship a model change?

**Why they ask.** Hosted models move under you. This is the operational core of 2026 LLMOps.

**Structure.** (1) Pin. (2) Contract tests. (3) Canary / shadow. (4) Rollback. (5) Communication with vendor and with the product.

**30-second answer.** Production calls a **pinned snapshot ID**, never `model: latest`. A new pin goes through golden-set CI, shadow traffic, then a percent canary with auto-rollback on quality, latency, or cost SLO burn. Rollback is switching the pin back, which I have tested.

**2-minute answer.** Pin in config, not in scattered code. The client SDK gets `model_id` from a runtime flag. CI runs evals on the candidate pin. Shadow: send a sample of prod traffic to the candidate, score offline, never show the user. Canary: 1% → 5% → 25% → 100% with soak. Auto-rollback if faithfulness, error rate, TTFT, or cost/task breach. I keep the previous pin warm (provisioned capacity if needed) so rollback is not a cold-start incident. I record the pin on every trace. I watch vendor status and changelogs, but I do not trust them as the detection system — see Q11. For open models the pin is an image digest / adapter hash, not a Hub tag that moves.

**Senior answer.** There are three different “model changes”: (a) we choose a new snapshot, (b) the vendor mutates a pinned alias despite the contract, (c) our serving stack changes (quantization, tensor parallelism, max context). All three get the same eval gate. For (b) I prefer dated snapshots (`…-2026-04-14`) and I run a **daily contract suite** even when we did not ship — that is how we catch silent quality. Canary is not only percent of users; it is percent **per slice**. A model can look fine on FAQ and die on multi-hop; I canary across routes, not just globally. Rollback drills: I practice them. A pin flip that also needs a prompt revert should be a single script. Capacity: rolling to a larger model without provisioned throughput is how you pass evals and fail prod. I include p95 TTFT and 429 rate in the canary gate, not only quality. Organizationally, no one — including a founder demo — bypasses the pin. Demo environments can use `latest`; production cannot.

**Weak answer.** “We call gpt-4o and trust the provider to keep it good.”

**Follow-ups.**

- *Shadow vs canary?* Shadow has no user impact and no true latency SLO under load. Canary has both. Do both when the change is a new model family.
- *Multi-model routing during canary?* Yes, but log the chosen pin and do not let the router hide a bad model by sending it only easy tasks unless that is the actual routing policy.
- *Fine-tunes?* Same path, plus a regression set for **capabilities you did not intend to change** (safety, refusal, citations).

---

## Q11 — A vendor model silently changed quality. How would you know before users?

**Why they ask.** This is the senior probe for this chapter. They are testing whether your evals run when *you* did not change anything.

**Structure.** (1) Assume it will happen. (2) Pin + contract tests on a schedule. (3) Online monitors and drift. (4) Canary residual / shadow. (5) Response playbook.

**30-second answer.** I would not wait for tickets. Production is pinned, and a **scheduled eval** runs the frozen golden set against that pin every day. I watch online faithfulness, citation fail, empty retrieval (as a control), TTFT/TPOT, cost/task, and embedding-distance of outputs on a canary query set. A breach pages us, we confirm with traces, and we roll to a previous snapshot or a fallback vendor before users become the detector.

**2-minute answer.** Detection is layered because silent changes are partial — they hit one slice or one locale. Layer 1: pin dated snapshots; aliases named `latest` or even `gpt-x` are untrusted. Layer 2: nightly (or hourly for top-tier surfaces) **contract eval** on a frozen golden set and a frozen judge. Same code that gates releases. Layer 3: **canary queries** — 20–50 synthetic-plus-real prompts with stored reference outputs; I compare embeddings and judge scores continuously. Layer 4: **online sample** of live traffic, scored asynchronously; I compare against a 7-day baseline per slice. Layer 5: infra signals — TPOT, tokenizer length, finish_reason shifts, 4xx/5xx — which often move when a backend changes even if the name did not. Empty retrieval is my **control metric**: if retrieval is stable and generation quality drops, the model (or the prompt renderer) moved. If retrieval also moved, it is not the vendor. When any gated signal drops, we page, freeze deploys, open traces, and switch pins. We tell the vendor after we are safe.

**Senior answer.** The point of this design is **independence from the vendor’s honesty**. Contracts and status pages are inputs, not monitors. I assume (a) aliases drift, (b) snapshots can still change serving, (c) safety layers in front of the model change, (d) our own gateway or cache could be the real culprit. So the playbook is differential: run the same inputs at the previous pin in shadow. If old pin is healthy and new/current is not, we fail over. If both are sick, we look at *our* renderer, index, or judge. I keep **last-known-good outputs** for the canary set in object storage, hashed, so we can compute delta without re-trusting a judge that might also have changed — judges get pinned too. Statistical process control on judge scores (EWMA / CUSUM) catches slow bleed that a nightly t-test misses. I also watch **user-level** leading indicators: regeneration rate, thumbs-down, “copy citation” clicks, HITL reject rate. Those confirm, they do not detect first if I did my job. Cost of this system: a few dollars a day in eval tokens, which is cheaper than a week of silent wrong answers on a bank copilot. What I would not do: rely on a single chatty Slack channel of employees saying “it feels dumber.” That is a late, biased detector.

**Weak answer.** “Users would complain, or the vendor would email us.” Hard fail. That is not LLMOps.

**Follow-ups.**

- *What if there is no snapshot ID?* Put a proxy in front, hash a probe set daily, and have a second vendor ready. Consider not using that model for a gated surface.
- *False positives from judge drift?* Pin the judge, re-score a panel when you change it, and require two independent signals (judge + embedding delta, or judge + human spot).
- *Legal / procurement angle?* Put change-notification and snapshot availability in the contract. Still build the detector. Contracts do not page you at 2 a.m.

---

## Q12 — How do you monitor RAG in production?

**Why they ask.** Most “LLM bugs” are retrieval bugs. They want RAG-specific monitors, not generic latency.

**Structure.** (1) Split retrieval vs generation. (2) Core metrics. (3) Citation checks. (4) Index health. (5) What you page on.

**30-second answer.** I monitor retrieval and generation separately. Retrieval: recall@k on a labeled probe, empty-retrieval rate, score distributions, freshness lag. Generation: faithfulness, citation coverage, citation fail (cited span not in context). If empty retrieval spikes, I do not blame the LLM. If retrieval is healthy and faithfulness drops, I look at the model or prompt.

**2-minute answer.** Online, every request logs: `n_retrieved`, `top_score`, `empty_bool`, `rerank_used`, `chunk_ids`, `index_alias`, `acl_filtered_count`. Metrics: empty retrieval %, p50/p95 retrieval latency, % of answers with zero citations, % of citations that fail a membership check, judge faithfulness on a sample. Offline, a frozen retrieval set scores recall@k whenever the index or embedder changes. I watch **embedding distribution drift** on new corpus adds and **query embedding drift** vs last week — a new client app sending different query phrasing is a retrieval incident. Freshness: documents updated vs searchable time. I page on empty-retrieval SLO, citation-fail SLO, and a drop in sampled faithfulness. I do not page on a single wrong answer.

**Senior answer.** Citation fail is the best cheap metric I know: parse the answer’s citations, assert each ID was in the retrieved set, assert the cited span actually occurs in the chunk (string or fuzzy). It catches models inventing sources without a judge. Faithfulness still needs a judge or an NLI model on claims. I also track **refusal on empty retrieval** — if we retrieved nothing and still produced a confident paragraph, that is a ship-bar fail, not a curiosity. ACL: `acl_filtered_count` going to zero suddenly can mean the filter broke (too open) or the index is empty for that tenant. I alert on both directions vs baseline. Multi-index / hybrid: log BM25 vs dense contribution so a bad hybrid weight is visible. Failure mode: monitoring only generation quality. You will “fix” the prompt for a month while the chunker silently dropped tables. Another failure: logging full chunks into the APM and creating an LLM02 incident. Store IDs, scores, and hashes.

**Weak answer.** “We’d look at user feedback and maybe retrieval count.”

**Follow-ups.**

- *How do you measure recall online?* You cannot, fully, without labels. Use a probe set plus proxy metrics (empty rate, top score). Promote failures to labels.
- *Reranker died — what do you see?* Top-score distribution shifts, faithfulness drops, retrieval latency may drop. Canary the reranker like a model.
- *Cross-tenant retrieval?* That is security, not only quality. See Chapter 19. Monitor would be: retrieval IDs whose tenant ≠ request tenant must be zero, and that alert is P0.

---

## Q13 — How do you monitor agents (loops, tools, cost/task)?

**Why they ask.** Agents fail by doing too much, not by saying the wrong sentence. Senior loops want operational limits.

**Structure.** (1) Unit of work = task, not call. (2) Loop and tool metrics. (3) Cost/task. (4) Safety / HITL. (5) Kill switches.

**30-second answer.** I monitor **per task**: steps, unique tools, tool error rate, repeated-tool loops, HITL rate, success, and cost. Hard caps on steps and tokens. I page on loop-cap hits, tool-error spikes, unauthorized tool attempts, and cost/task. Traces show the graph; metrics tell me when to wake up.

**2-minute answer.** Spans: one parent per agent task, children for model thoughts (if stored), each tool, each HITL wait. Metrics: `steps_per_task`, `tool_error_rate`, `loop_cap_hit_rate`, `repeat_tool_3plus`, `cost_per_success`, `cost_per_failure` (failures that burn money are a special hell), `time_to_HITL`, `HITL_reject_rate`. A loop is not only “while true”; it is the same tool with the same args three times, or ping-pong between two tools. I detect both. Caps are enforced in the orchestrator, not in the prompt: max steps, max wall time, max tokens, allowlisted tools per route. Tool errors get classified: 4xx (our schema), 5xx (dependency), model-arg garbage. Only the last is an LLM problem. Success is a predicate (ticket updated, test passed), not a cheerful final message.

**Senior answer.** The first agent incident I design for is **runaway money and runaway side effects**, not wrong text. Kill switch: flag to disable write tools globally, per tenant, and per tool. Circuit breaker: if tool error rate > threshold, stop calling it and degrade. For loops, I hash tool+args and increment; at N, I force stop and escalate. I also record **policy denials** (tool the model wanted but was not allowed) — a spike means injection or a prompt/tool-schema mismatch. Cost/task is the north-star efficiency metric; I will take a slightly lower success rate if cost/success explodes due to retries. Evaluation of agents is trajectory-based: illegal action = automatic fail even if the final answer looks right. That is the bridge to Chapter 19 (excessive agency). Observability-wise, I refuse to dump chain-of-thought into long-term logs for privacy and LLM08; I keep tool names, args schemas, and outcomes. If the framework hides tool args, I wrap tools myself. Multi-agent: a supervisor span, per-specialist budgets, and a cap on handoffs. The failure I call out: teams alert on “LLM error rate” which stays green while the agent quietly loops 40 steps and files 12 duplicate tickets.

**Weak answer.** “We’d log the conversation and see if the agent got stuck.”

**Follow-ups.**

- *What is a reasonable step cap?* Start at 8–12 for an internal copilot; raise with evidence. Not 100.
- *Tool error vs model error?* If args fail schema, it is the model or the schema. If the HTTP API 500s, it is the tool. Separate series.
- *Do you trace every thought?* Enough to debug, not enough to create a second copy of private data. Prefer tool IO and states.

---

## Q14 — Walk me through a production quality drop at 4 p.m. on a Friday.

**Why they ask.** They want an investigation order under pressure. This is the live-debug companion to Q11.

**Structure.** (1) Stabilize. (2) Split the stack. (3) Differential eval. (4) Fix or rollback. (5) Aftercare.

**30-second answer.** I freeze deploys, check the ship-bar dashboards, and decide rollback vs ride-through. I split: infra vs retrieval vs model vs prompt vs tools vs judge. I compare traces from now vs last-known-good, run the golden probe, and I roll the last pin/label that was green. I do not prompt-tweak in production during an incident.

**2-minute answer.** Stabilize: if error rate, TTFT, or safety is on fire, roll back the last change (prompt label, model pin, index alias, gateway). If we did not change anything, fail over to the previous model pin or the backup vendor. Split: empty retrieval up? Index/ACL/embedder. Retrieval stable, faithfulness down? Model, prompt renderer, or context stuffing. TPOT doubled? Vendor or our concurrency. Tool errors up? Dependency. Judge down but humans on a 10-item spot check say quality is fine? Judge drift. I pull 20 traces, not 1. I run the 20-item canary set immediately. I communicate a simple status: user impact, what we rolled, when the next update is. After: add the failing traces to the golden set, write the missing monitor, and only then consider a prompt fix.

**Senior answer.** I assume multiple things can be true and I use **controls**. Empty retrieval is the retrieval control. A static canary query that does not use RAG is the model control. A replay of stored requests against last-good prompt+pin in a sandbox is the differential. I will not “improve the prompt” while the index is serving the wrong namespace. I watch **blast radius**: one tenant, one route, one locale, one model pin. If it is one tenant, it is probably ACL, data, or a per-tenant prompt overlay — not OpenAI. If it is all routes and all tenants, it is gateway, vendor, or a global prompt. People under-index **our** bugs: a feature flag default flipped, a tokenizer mismatch after a library bump, a cache key that started mixing tenants (that is a P0 security incident, not a quality one). I keep the incident **quality vs safety vs cost vs latency** as four different severities. A 10% latency miss does not get the same response as citation fail on a regulated assistant. Aftercare includes evaluating whether the ship bar would have caught this in canary — if not, the bar is wrong.

**Weak answer.** “I’d try a better prompt and see if users stop complaining.”

**Follow-ups.**

- *When do you not rollback?* When the rollback is worse (known bad pin) or when the issue is data poisoning in the corpus — rolling the model will not help; you must freeze the index.
- *How fast is ‘before users’?* For a top-tier copilot, contract eval hourly and online sample continuous. For an internal tool, nightly may be enough. Name the SLO.
- *Who owns the page?* The service owner. LLMOps platform provides the signals; it is not a dumping ground for every bad answer.

---

## Q15 — Online vs offline evaluation — how do they work together?

**Why they ask.** Teams either never eval in prod or they *only* look at prod and cannot reproduce.

**Structure.** (1) Offline = reproducible gate. (2) Online = drift and mix shift. (3) Feedback loops. (4) What never goes online.

**30-second answer.** Offline golden sets gate releases and catch us when we change something. Online sampling catches traffic mix, vendor drift, and unknown unknowns. Online failures become offline rows. Safety red-teams stay offline-first so we do not probe production with live exploits against real tenants.

**2-minute answer.** Offline: frozen inputs, pinned models, CI, apples-to-apples diffs. Online: real mix, real tools, real index, real latency. Online methods: implicit feedback (regenerate, copy, thumbs), explicit ratings, sampled judges, probe canaries. I do not A/B on safety-critical write tools. I do A/B on tone and retrieval k with a kill switch. The join key is `trace_id` so a thumbs-down becomes a labeled row without a Slack archaeology session. I keep **distribution shift** metrics: query embedding vs golden set; if they diverge, the golden set is stale even if scores are stable.

**Senior answer.** The failure mode is optimizing the offline set until it is a different product. I report **offline-online correlation** quarterly: did the last five releases move prod metrics in the same direction as gold? If not, gold is wrong. Another failure: online judge on 100% of traffic, adding latency and leaking data to a second model. Sample. A third: using user thumbs as ground truth on a tool that users cannot verify (citations they did not open). For those, I need expert review, not NPS. Shadow mode is the bridge: new retriever or new model scores on live inputs without affecting the user, then we compare. That is how I promote changes that offline says are a tie.

**Weak answer.** “We eval before launch and then look at CSAT.”

**Follow-ups.**

- *Bandit / adaptive routing?* Only after the gated bar, with exploration caps, and never on write tools.
- *Human-in-the-loop eval?* HITL is operations and safety. Do not confuse “a human approved the refund” with “the corpus is correct.”

---

## Q16 — Which LLMOps tools would you pick, and why not the others?

**Why they ask.** They do not want a fanboy. They want constraints: data residency, existing APM, framework, team size.

**Structure.** (1) Restate constraints. (2) Default. (3) Alternatives. (4) What you standardize. (5) Lock-in.

**30-second answer.** I emit OpenTelemetry regardless. If the team is LangGraph-heavy and SaaS is allowed, LangSmith is the fastest complete loop. If data cannot leave the VPC, Langfuse or Phoenix self-hosted. If Datadog is already the APM, I use Datadog LLM Observability for ops and keep a native eval store for datasets. MLflow if the org already lives there. I will not run four overlapping sources of truth.

**2-minute answer.** Decision order: (1) Where may traces live? (2) What is the orchestrator? (3) What APM already pages people? (4) Who will run the eval CI? LangSmith: best graph replay for LangChain, strong experiments, weakest story if legal says no SaaS. Langfuse: prompt registry + traces + scores, self-host, framework-agnostic. Phoenix: excellent for embedding/eval notebooks and OTel; I often pair it with an APM. Datadog: correlate LLM spans with k8s and Redis, weaker dataset workflow. MLflow: registry and eval runs for hybrid ML+LLM shops; not a trace debugger. Cloud native (Bedrock traces, Azure App Insights, Vertex evals): right default when the rest of the app is already there, but I still want a golden-set runner in CI that is cloud-agnostic. Standardize: span names, `prompt_version`, `model_id`, dataset hashes. That is what lets you change backends.

**Senior answer.** The tool is not the system. I have seen LangSmith used as a graveyard of unreviewed traces and Phoenix used as a serious eval gate. I staff the **process**: who labels, who owns the bar, who gets paged. Budget: SaaS LLM observability can rival model spend at high volume; sampling is a feature. Lock-in: I export datasets and prompt files to git weekly. If a vendor cannot export, they are a dashboard, not a platform. For enterprise, SSO, RBAC on traces (tenant isolation in the obs tool), and retention controls are as important as pretty waterfalls. I would say in an interview: I can implement the loop with pytest + a CSV + CloudWatch if I must. The tools accelerate; they do not create the discipline.

**Weak answer.** “LangSmith is the industry standard so I’d use that.” No constraints, no OTel, no exit.

**Follow-ups.**

- *OpenTelemetry GenAI conventions?* Use them so span attributes are consistent: model, tokens, operation name. Custom attributes for prompt version and index alias.
- *Prometheus for LLMs?* Yes for RED and token counters. No as the only place you store prompt payloads.
- *Grafana?* Dashboards on top of Prometheus/OTel. Still need a trace store.

---

## Investigation order (memorize this)

When quality, cost, or latency moves:

1. **Did we change something?** Prompt label, model pin, index alias, tool schema, gateway, flags.
2. **Is it one slice, tenant, route, or everyone?**
3. **Retrieval control:** empty retrieval, recall probe, ACL filter counts.
4. **Model control:** pinned canary queries without RAG; TTFT/TPOT vs baseline.
5. **Tools/agents:** error rate, loop-cap, cost/task.
6. **Judge control:** did the judge pin move? Spot-check 10 traces with a human.
7. **Infra:** 429s, GPU, timeouts, cache hit rate.
8. **Rollback the last pointer.** Then write the missing eval row.

Never start at “maybe we need a better prompt.”

---

## Rapid-fire (30–45 seconds each)

**What is a golden set?** A frozen, versioned, sliced set of labeled tasks used as a regression gate. Not a vibes spreadsheet.

**TTFT vs TPOT?** First token vs per subsequent token. UX vs stream smoothness.

**What do you pin?** Model snapshot, prompt version, index alias, judge, price table.

**Name three judge biases.** Position, verbosity, self-preference.

**Empty retrieval spiked. First look?** Index, embedder, ACL filters, query pipeline — not the LLM.

**Citation fail?** Answer cites an ID or span not in the retrieved context. Cheap hallucination detector.

**Cost metric you want?** Cost per successful task, plus spend-rate circuit breakers.

**Canary vs shadow?** Canary serves users at small %; shadow does not.

**Why OTel?** So traces are not trapped in a vendor, and so infra and LLM share context.

**Agent loop monitor?** Repeated tool+args, step cap, token cap, no progress in state.

**Ship bar example?** Faithfulness ≥ 0.88, citation ≥ 0.90, p95 E2E ≤ 8s, empty retrieval ≤ 2%, 0 P0 safety.

**Vendor changed quality. Detector?** Scheduled golden-set eval on the pin, plus online slice monitors — not the ticket queue.

**Logs vs traces?** Events vs timed causal graph of a request.

**When is LLM-as-judge a hard fail?** Ungated, uncalibrated, same-family, holistic “quality 1–5” as the only release metric.

**What is prompt caching’s risk?** Cost/latency win; tenant-mixing if the cache key omits tenant or version.

---

## 6-part cards (study these, then rewrite in your words)

### Card: LLMOps

1. **Concept** — Operate generative systems as versioned products.
2. **Logic** — Behavior comes from prompt+model+index+tools, and the model may move without you.
3. **Structure** — Dev artifacts → offline eval → canary → online monitors → traces back to datasets.
4. **Keywords** — pin, golden set, slice, OTel, TTFT, cost/task, rollback.
5. **Example** — Nightly contract eval caught a vendor TPOT and faithfulness drop; we flipped the pin.
6. **Trade-off** — Eval tokens and labeling cost vs silent user harm.

### Card: LLM-as-judge

1. **Concept** — A model scoring outputs is a noisy metric, not ground truth.
2. **Logic** — Humans cannot score every row; judges scale but drift and bias.
3. **Structure** — Rubric → calibrate on humans → pin judge → report agreement → gate only if calibrated.
4. **Keywords** — position bias, verbosity, self-bias, κ, pairwise.
5. **Example** — Pairwise judge flipped with order; we average both orders and drop unstable items.
6. **Trade-off** — Cheap holistic scores vs expensive claim-level faithfulness.

### Card: Silent model change

1. **Concept** — Hosted models can change behavior without a deploy on your side.
2. **Logic** — You cannot trust changelogs as a detector.
3. **Structure** — Pin → scheduled golden eval → canary probes → online slices → rollback playbook.
4. **Keywords** — snapshot, contract test, control metric, last-known-good.
5. **Example** — Faithfulness down, empty retrieval flat → model/serving, not RAG.
6. **Trade-off** — Extra eval spend and conservative pins vs always-latest quality.

---

## What to practice out loud (45 minutes)

1. Draw the LLMOps loop and put numbers on a ship bar for a product you know.
2. Explain TTFT/TPOT/E2E with a waterfall: gateway → retrieve → rerank → prefill → decode.
3. Calibrate a judge: name the three biases and how you measure them.
4. Friday incident: quality drop, no deploy. Speak the investigation order without notes.
5. Tool choice: interviewer says “data cannot leave the VPC.” Pick Langfuse/Phoenix and defend OTel.

---

## Boundaries (say these so you do not overclaim)

- If you have not run production evals, say: “I have implemented this loop in a project / staging; I have not owned a 24/7 page for it. Here is how I would.”
- Do not pretend MMLU is an application eval.
- Do not claim a vendor is “stable.”
- Do not dump PII into traces in your examples.

---

## Links

- RAG metrics and retrieval failure modes: [10-rag.md](10-rag.md)
- Agent loops and when not to use agents: [11-agentic-ai.md](11-agentic-ai.md)
- MCP telemetry and tool contracts: [12-mcp.md](12-mcp.md)
- Cloud pins, provisioned throughput: [15-cloud-ai.md](15-cloud-ai.md)
- AIOps vs this chapter: [18-aiops.md](18-aiops.md)
- Security of traces, injection, unbounded spend: [19-ai-security.md](19-ai-security.md)
- Incident drills: [22-troubleshooting.md](../banks/22-troubleshooting.md)
