# 18 — AIOps

**Roles that score this chapter as core:** AIOps Engineer, Intelligent Automation (ops / ITSM side).

**Roles that still get asked:** Cloud AI, FDE / AI Deployment, Solutions Architect. Anyone who says “we’ll let the agent restart the pod” will be asked the rest of this chapter whether they like it or not.

This chapter trains **operations judgment**. LLMOps (Chapter 17) is how you operate *LLM products*. AIOps is how you apply ML and, in 2026, LLMs to *IT operations*: signals, noise, topology, RCA, tickets, and gated remediation. Mixing the two is a mid-level tell.

---

## Interviewer intent

They are not hiring you to bolt a chatbot onto Datadog. They are hiring you to decide **which signals matter, which events are the same incident, what is allowed to change production without a human, and how an LLM copilot is bounded**.

They are scoring six signals:

| Signal | Pass | Fail |
| --- | --- | --- |
| Telemetry literacy | Metrics / logs / traces / profiles, each with a job | “We log everything into the LLM” |
| Cardinality | You protect the time-series store on purpose | `user_id` on every Prometheus label |
| Topology | Blast radius is a graph, not a vibe | Correlate by clock only |
| Causation | Correlation is a hypothesis, change is evidence | “The spike lined up so that’s root cause” |
| Automation safety | Restart vs rollback vs never, with kill switches | “The copilot can remediate” |
| ITSM | Ticket is the system of record; HITL on writes | Silent closes, silent restarts |

**The highest-signal 2026 question in this chapter:** *When do you not auto-remediate?*

If you cannot answer that cleanly, the RCA vocabulary will not save you.

---

## Probability ranking (AIOps / Intelligent Automation loops, 2026)

| Rank | Topic | Likelihood | Depth they want |
| --- | --- | --- | --- |
| 1 | Metrics / logs / traces / profiles | Almost certain | Which signal answers which question |
| 2 | Cardinality | Almost certain | Explosion, cost, query death, what you never label |
| 3 | RCA method after a deploy | Very high | Ordered investigation, not a tool tour |
| 4 | Alert noise / correlation | Very high | Dedup, suppress, topology, change events |
| 5 | Auto-remediation safety | Very high | Restart vs rollback vs never |
| 6 | SLO / error budget | High | SLI, burn rate, when to halt deploys |
| 7 | ITSM / ServiceNow lifecycle | High (IA + AIOps) | Incident vs problem vs change |
| 8 | LLM as RCA copilot + HITL | High | Read-only default, citations, approval |
| 9 | Event pipelines | High | Ingest → enrich → correlate → route |
| 10 | Topology / CMDB freshness | High | Stale graph is a wrong-RCA machine |
| 11 | Correlation vs causation | High | What would *disprove* the story |
| 12 | AIOps vs LLMOps | Medium–high | Wrong chapter = wrong job |
| 13 | Runbook quality / evals for copilots | Medium | Faithfulness to telemetry, not fluency |
| 14 | Platform design (Datadog / Dynatrace / Splunk / Prometheus + tickets) | Medium | Fit to estate, not a vendor pitch |

**MARKET OBSERVATION:** AIOps JDs still list vendor logos first. Interview time goes to cardinality, topology, and whether you would let a model bounce prod. Prepare the judgment, name the tools second.

---

## How to study this chapter

Cover the answer. Speak 30 seconds. Then 2 minutes. Then read the deep cut. Write *your* six-part card: concept → logic → structure → keywords → example → trade-off. Invent one follow-up.

Do not memorize vendor click-paths. Interviewers change the wording: “observability,” “event intelligence,” “AI SRE,” “self-healing,” “ITSM copilot.” The test is always: **can you see, can you decide, can you act without making it worse.**

---

## The one diagram you should be able to draw

```
 sources          pipeline                    decision
 ─────            ────────                    ────────
 metrics ─┐
 logs    ─┤     normalize → enrich ─┐
 traces  ─┼──►  dedup      CMDB     ├─► correlate ─► incident
 profiles─┤     suppress   topology ┤     │
 changes ─┘     window     identity ┘     ▼
                                   ticket (ITSM) ← HITL
                                          │
                          ┌───────────────┼───────────────┐
                          ▼               ▼               ▼
                       restart         rollback         never
                      (stateless,     (bad deploy,    (stateful,
                       known sig,      prior healthy,   unknown,
                       cooldown)       flag ready)      security)
```

The LLM, if present, **drafts** on the right-hand side. It does not own the arrows.

---

## AIOps vs LLMOps vs MLOps (say this unprompted)

| | **AIOps** | **LLMOps** (Ch. 17) | **MLOps** |
| --- | --- | --- | --- |
| User | SRE, NOC, ITSM | Product / platform for GenAI apps | Data science + ML eng |
| Job | Reduce noise, find cause, gate repair | Ship, eval, observe, roll back LLM apps | Train, register, drift, retrain |
| Unit of work | Incident / SLO burn | Prompt + model pin + index + tools | Model binary + features |
| Write policy | Production infra is sacred | Model/prompt pins are sacred | Training pipeline is sacred |
| LLM role | Copilot over telemetry | *The* product | Optional assistant |

**FACT:** Chapter 17 already flags this split. Repeating it in the first two minutes of an AIOps screen is a senior tell. “I would not run the copilot’s traces as if they were the production SLO.”

---

## Q1. What is AIOps, and how is it different from LLMOps?

**Why they ask.** Wrong boundary poisons every later answer. They have candidates who recite “AI for IT operations” and then design LangSmith.

**What they expect.** An operational definition, a contrast table, and where an LLM is allowed to sit.

**Answer structure keywords.** signals → incidents → actions · noise · topology · ITSM · copilot not controller · LLMOps is the product loop.

**30-second.** AIOps is the practice of turning telemetry into fewer, better incidents and safer actions. Collect metrics, logs, traces, profiles, and change events; enrich with topology; correlate; route to humans and to *gated* automation. LLMOps is how we operate generative products — prompts, evals, pins, cost per task. I use LLMs *inside* AIOps as a read-mostly RCA copilot. I do not confuse “operating an LLM app” with “operating the estate.”

**2-minute.** Three loops. *Detect:* SLIs and events, not raw pages. *Understand:* topology + change + traces so we can form a causal hypothesis. *Act:* a policy table that says restart, rollback, or never, with the ticket as the audit trail. ML in AIOps is old: anomaly scores, clustering, event correlation. The 2026 layer is an LLM that can *read* a trace waterfall and a runbook and *draft* a timeline. That layer inherits Chapter 11 and 19: step caps, tool allowlists, HITL on writes, no secrets in prompts. LLMOps still exists beside it for the copilot’s own quality, cost, and prompt versions. If the copilot hallucinates a root cause, that is an LLMOps eval miss *and* an AIOps process miss — the human was supposed to verify against the graph.

**Senior / deep.** I refuse the vendor sentence “our platform is AIOps because it has a chatbot.” Chat on logs without topology, change feed, and an action policy is search. The scarce skill is **encoding operational policy**: which signatures are auto-safe, which services are stateful, which environments are dual-control, how stale the CMDB is allowed to be. I also split *platform AIOps* (one pipeline for the company) from *service AIOps* (a team’s burn-rate alerts and runbooks). Central platform owns ingest, identity, and the never-list. Service owners own SLOs and the yes-list for their stateless tiers.

**Weak answer.** “AIOps is using AI to monitor systems. We’d connect GPT to Splunk and ServiceNow.”

**Mistakes.**

- Treating AIOps as a synonym for LLMOps or MLOps.
- Leading with a vendor.
- Giving the model write credentials “so it can be autonomous SRE.”
- No mention of tickets, topology, or change events.

**Follow-ups + strong replies.**

- *“Where does AgentOps fit?”* — AgentOps is LLMOps plus tool/loop monitors for *product* agents. If that agent is an SRE copilot, AIOps policy wraps it.
- *“Do we still need anomaly detection if we have an LLM?”* — Yes. Anomaly scores are cheap, deterministic-enough gates. The LLM explains; it does not scan every time series every 10 seconds.
- *“Is observability AIOps?”* — Observability is the signal plane. AIOps is signal + decision + (gated) action.

**Example.** Payments API p99 burns the SLO. Pipeline correlates deploy `api@sha` + error log signature + downstream timeout. Copilot drafts: “rollback candidate; DB CPU flat; not a lock.” Human approves rollback. Copilot never held kube credentials.

---

## Q2. Metrics, logs, traces, profiles — which do you use when?

**Why they ask.** This is the observability screen. They want job-to-signal mapping, not “four pillars” recitation.

**What they expect.** What each is *for*, what it is bad at, and an investigation order.

**Answer structure keywords.** RED/USE · exemplar · span · cardinality · continuous profiling · change events as a fifth feed.

**30-second.** Metrics tell me *that* something moved and whether to page. Logs tell me *what a instance said*. Traces tell me *which hop* ate the latency. Profiles tell me *which function or alloc* inside a hop. I start from the symptom’s SLO, use metrics to bound blast radius, traces to locate the span, logs for the error string, profiles if the span is CPU/mem inside our code. I do not paste all four into an LLM first.

**2-minute.**

| Signal | Job | Bad at |
| --- | --- | --- |
| **Metrics** | SLIs, capacity, cheap alerts, comparisons before/after | Explaining one user; high-cardinality “just in case” |
| **Logs** | Error text, audit, security events, unique exceptions | Reconstructing a distributed request without IDs |
| **Traces** | Waterfall across services; exemplar of a slow request | Cheap long-retention dashboards; PII if you store raw payloads |
| **Profiles** | On-CPU, off-CPU, alloc, lock contention inside a binary | Cluster-level “who talks to whom” |

Investigation order for “p99 5×”: (1) metric: which SLO, which region, which version, (2) trace exemplars at p99, (3) the slow span’s logs, (4) profile that process if the span is us, not a dependency. **Change events** sit beside the four: deploys, flags, kube events, IAM changes. A pipeline that cannot join `version` and `trace` will blame the database by default.

**Senior / deep.** Exemplars are the bridge: a metric bucket that carries a `trace_id`. Without them you sample blindly. Tail-based sampling: keep 100% of errors, SLO-burning traces, and canary; sample the rest. Profiles are the underused 2026 answer for “the span is 800 ms in our JVM/Go process and logs are fine” — you want pprof / JFR / continuous profiling, not another dashboard. For AI services I still use Chapter 17’s TTFT/TPOT/E2E split; that is LLMOps telemetry *consumed* by AIOps when the inference gateway is a dependency.

Redaction: logs and traces are secret stores. Same rule as Chapter 17: pointers and hashes, not tokens and payloads.

**Weak answer.** “We’d collect all four and use Datadog.”

**Mistakes.**

- Alerting off logs at high volume instead of metrics.
- Tracing every health check at 100%.
- Profiling only in staging.
- No `trace_id` on logs.

**Follow-ups + strong replies.**

- *“RED vs USE?”* — RED (rate, errors, duration) on request-serving services. USE (utilization, saturation, errors) on resources (CPU, disk, queue). I use both.
- *“Do we trace the LLM?”* — Yes, as spans. Sampling and redaction are LLMOps. Paging on those spans is AIOps if the gateway is a production dependency.
- *“OpenTelemetry?”* — Default export. Vendor is the backend, not the contract.

**Example.** Checkout p99. Metric: only `/pay` in `us-east-1`, version `2026.09.12`. Trace: 2.1 s in `fraud-score`. Log: `timeout talking to vendor`. Profile: our process idle. RCA is vendor, not our GC. Auto-restart would have been malpractice.

---

## Q3. What is cardinality, and why do interviewers care?

**Why they ask.** Cardinality is how observability platforms die, bills explode, and alerts become unqueryable. It is the AIOps equivalent of unbounded context.

**What they expect.** A definition, dangerous labels, how you detect explosion, and what you do instead of “add a label.”

**Answer structure keywords.** time series = name × label set · bound · drop · aggregate · exemplars · never user_id as a metric label.

**30-second.** Cardinality is the number of unique time series you store: each distinct combination of metric name and label values. Unbounded labels — `user_id`, `trace_id`, raw `pod_name` with no limit, URL with IDs — create millions of series, slow queries, and a bill that looks like a data incident. I keep SLI labels bounded (`service`, `route_template`, `status_class`, `region`, `version`). High-cardinality identifiers go on traces and logs, not on metrics.

**2-minute.** A metric `http_requests_total{service,route,code,pod,user}` is a series factory. Ten services × 50 routes × 20 codes is fine. Add 5,000 pods that churn and 1M users and you have bought a second data warehouse. Symptoms: scrape or ingest lag, dashboard timeouts, “this query was rejected,” sudden observability cost, alert rules that cannot evaluate in time (which then pages you for the wrong reason). Controls: allowlist of labels at the instrumentation library; relabel/drop at the collector; aggregation (record rules, rollups) before long-term store; separate a **bounded metrics** path from an **analytics** path (logs/traces). For logs, cardinality shows up as too many unique fields indexed — same discipline.

**Senior / deep.** Two cardinalities: *storage* (series count) and *query* (how many series a rule touches). A well-bounded metric can still kill Prometheus if the alert does `sum by (user)`. I review recording rules and alert expressions like I review indexes. **Churn** matters: `pod` is high-churn even if bounded at any instant. Prefer `workload` / `deployment` on metrics; put `pod` on the exemplar. In Datadog-style tagged metrics, custom tags are the same trap. Interview-safe rule: if the value set is not enumerable on a whiteboard, it is not a metric label.

Trade-off: you will *want* per-user latency. Product analytics can have it. The paging SLI cannot. Use traces sampled by user hash, or a privacy-safe top-k sketch, not a label.

**Weak answer.** “Cardinality is how many logs we have.”

**Mistakes.**

- Putting `trace_id` on Prometheus labels “for join.”
- Using raw URLs instead of route templates.
- No budget or alert on series count itself.
- Fixing cost by dropping *all* labels, including `version` — then you cannot RCA deploys.

**Follow-ups + strong replies.**

- *“We need per-tenant SLOs.”* — Tenant is allowed if the set is hundreds, not millions, and you have a series budget. Otherwise SLO at platform + per-tenant traces.
- *“Histogram cardinality?”* — Buckets multiply. Use a small explicit bucket set or exponential histograms; do not copy 50 linear buckets per route.
- *“Can the LLM look at all series?”* — No. That is unbounded consumption (LLM06) applied to ops. Summaries and exemplars in, not the whole TSDB.

**Example.** Someone added `customer_id` to `request_latency`. Series 200× overnight, alert manager timeouts, false pages. Fix: drop the label at the collector, keep `customer_id` on the trace, restore the SLO rule. Then a linter in CI that bans unbounded label names.

---

## Q4. How do you use topology (and what if CMDB is wrong)?

**Why they ask.** Correlation without a graph is coincidental paging. Stale CMDB is how auto-remediation hits the wrong cluster.

**What they expect.** Topology as a first-class input, how you build it, how you detect staleness, and what you refuse to automate when it is stale.

**Answer structure keywords.** service graph · runtime vs declared · CMDB · blast radius · owner · freshness SLO.

**30-second.** Topology is who calls whom, where it runs, and who owns it. I use it to bound blast radius (“this error is only the checkout→fraud edge”), to suppress child alerts when the parent is down, and to pick the *smallest* remediation target. I prefer **runtime** graphs from traces and eBPF/service-mesh over a wiki CMDB, and I treat CMDB as declared intent plus owners. If freshness is unknown, I do not auto-act.

**2-minute.** Three layers:

1. **Runtime graph** — trace edges, mesh metrics, DNS, Kafka consumer groups. True now, noisy, may miss batch jobs.
2. **Declared graph** — Helm/terraform, service catalog, CMDB CIs, “depends on.” Good for owners, environments, change windows; drifts.
3. **People graph** — service owner, secondary, vendor. Required to route the ticket.

Correlation uses (1) to group events that share an upstream. Tickets use (3). Auto-remediation uses (1) ∩ (2): I will bounce the deployment the traces actually hit, not the CI name someone typed in 2023. Staleness detectors: catalog service with no telemetry, telemetry with no catalog, owner group empty, edge that appeared this week and is not in the mesh. Those are **problem** tickets, not just hygiene.

**Senior / deep.** The failure mode is **CMDB-driven automation**. A runbook that says “restart `payments-app`” when traffic moved to `payments-app-v2` in another namespace is a self-inflicted outage. I key actions on runtime identity (`k8s.deployment.uid`, AMI id, `service.version`) and only *display* CMDB names. For multi-tenant shared stores (one RDS, many services) topology must mark **shared** vs **owned** or the copilot will “restart the database” for a single noisy neighbor.

Freshness SLO: catalog completeness and owner coverage are platform SLIs. I would rather have a small accurate graph than a beautiful stale one. Discovery jobs that write to CMDB need the same change control as app deploys.

**Weak answer.** “We’d keep a microservice diagram in Confluence and feed it to the model.”

**Mistakes.**

- Correlating only by time window.
- Auto-remediating off CI name.
- Ignoring shared dependencies.
- No owner → ticket to `#sre` as a dumping ground.

**Follow-ups + strong replies.**

- *“We have no mesh.”* — Start from traces and load-balancer logs. A partial graph beats none.
- *“Serverless?”* — Topology is still there: function → bus → table. Use vendor traces; declared graph is the IaC.
- *“Can the LLM infer topology?”* — It can *propose* edges from traces. A human or a reconcilers’ test must accept them before they gate actions.

**Example.** 200 alerts at 02:10. Graph shows one Redis cluster shared by 12 apps. Parent incident on Redis; children suppressed. Copilot suggests failover. Topology marks Redis as stateful + shared → policy = never auto. Human + DBA.

---

## Q5. Correlation vs causation — how do you not lie to the on-call?

**Why they ask.** This is the senior discriminator. AIOps products over-claim “root cause.” Interviewers have been burned by a copilot that blamed the last deploy because it was last.

**What they expect.** Correlation as hypothesis generation. A method to confirm or kill the story. Honesty about confounders.

**Answer structure keywords.** join keys · change evidence · counterfactual · control metric · disconfirm · do not close on a score.

**30-second.** Correlation is “these events share time, identity, or a graph edge.” Causation is “intervening on X would have prevented Y,” which I can only *support* with evidence: a deploy diff that matches the span, a flag that when flipped back restores the SLI, a dependency error that is necessary and sufficient. I present ranked hypotheses with what would disprove each. I never let a similarity score close a P1.

**2-minute.** I correlate on **join keys**, not vibes: `trace_id`, `version`, `node`, `tenant`, `change_id`, upstream cluster. Time-window-only grouping is how a batch job and a real outage become one ticket. To move toward cause: (1) **what changed** in the blast radius (deploy, flag, cert, quota, vendor), (2) **control metrics** that should *not* move if the hypothesis is true (if “it’s the DB,” why is DB CPU flat and the client pool exhausted?), (3) **counterfactual** — canary hosts without the change healthy? other regions healthy?, (4) **reproduce or replay** a failing trace against last-good. If I cannot disconfirm, I say “leading hypothesis” and mitigate (rollback, shed load) rather than invent certainty.

**Senior / deep.** Confounders: traffic shape (market open), vendor incident, GC coinciding with deploy, DST, a *previous* partial rollback. Simultaneous deploys are common; I split by version label on the *exemplar*, not by calendar. Bayesian language is fine if you are honest: prior that deploys cause prod incidents is high, likelihood needs the version on the failing traces. An LLM will write a causal story because language models complete narratives — that is why the copilot is a **drafter** and why I require citations to specific metric names, trace IDs, and change IDs (faithfulness, Chapter 17). Wrong-correlation rate is an AIOps eval slice.

**Weak answer.** “If the AI says 92% confidence it’s the deploy, we roll back.”

**Mistakes.**

- Last-change bias.
- No control metric.
- Closing the incident with a fluent paragraph and no artifact IDs.
- Treating Granger-style “A moved then B” in a 60-second window as proof.

**Follow-ups + strong replies.**

- *“Business wants a root-cause field in ServiceNow.”* — Enum: `confirmed_change`, `confirmed_dependency`, `confirmed_capacity`, `unknown_mitigated`. Forbid free-text “the AI said.”
- *“What if rollback is expensive?”* — Then I need stronger evidence *or* a cheaper mitigate (flag off, traffic shift). Cost of rollback vs cost of remaining burn is an error-budget question (Q11).
- *“Causal inference?”* — Natural experiments (canary, regional split) beat clever stats on observational telemetry.

**Example.** p99 5× after deploy *and* after a vendor SSL renewal. Traces on the new version are fine; old version failing TLS. Cause is cert on the *legacy* pool, not the deploy. Rolling back the good version would have extended the outage.

---

## Q6. 10k alerts — how do you reduce noise without dropping pages you need?

**Why they ask.** Alert storms are the daily AIOps problem. They want a pipeline, not “tune thresholds.”

**What they expect.** Dedup, suppress, group, route, and a philosophy of **symptoms not causes** as pages.

**Answer structure keywords.** symptom SLOs · dedup · suppression · parent/child · inhibition · maintenance windows · actionability.

**30-second.** A page must be **actionable, owned, and tied to a user symptom or a safety invariant**. I page on SLO burn and on a short list of invariants (disk will fill, cert will expire, queue is not consumed). Everything else is a ticket or a dashboard. Storms get collapsed by signature + topology: one parent incident, children attached, maintenance windows honored. I do not “fix noise” by widening thresholds until the next outage is silent.

**2-minute.** Layers:

1. **Don’t emit.** Instrumentation and alert design. RED on the SLO, not 40 internal gauges. No page on CPU unless CPU is the SLO (it almost never is).
2. **Dedup.** Same fingerprint (`alertname + service + resource`) in a window is one event.
3. **Inhibit / suppress.** If the node is down, do not page every pod on it. If the region is isolating, suppress children. If a change window is open for that service, route as ticket not page — *unless* the SLO is already burning.
4. **Correlate.** Topology parent. Change-id join. Storm of 10k → 1–N incidents.
5. **Route.** Owner from catalog. Pager for burn; ITSM for the rest.
6. **Review.** Every page that did not need a human is a defect. Error budget for *pages* too: page-precision as a platform metric.

**Senior / deep.** Symptom-based alerting (Google SRE style) still wins: page on **user-visible SLI burn**, not on “pod restart.” Restarts are a *signal* for RCA, not a page, unless you are below replica floor. Flapping: hysteresis and `for:` windows. Alert-of-alert: if the manager cannot evaluate (cardinality, Q3), that is a P1 on the observability path — I keep a **dead-man’s switch** from a tiny external probe. For Intelligent Automation: auto-creating a ServiceNow incident per raw event is how you DDoS your ITSM. Create on **correlated incident**, not on event.

**Weak answer.** “I’d use AI to score alerts and only show the important ones.” Without defining important, that is a silent-drop machine.

**Mistakes.**

- Paging on every 5xx.
- AI suppression with no audit of dropped events.
- No dead-man’s switch.
- Same Slack channel for P1 and “disk 70%.”

**Follow-ups + strong replies.**

- *“ML anomaly pages?”* — Only if they map to an SLI or a validated signature. Anomaly-on-everything is 2017 AIOps theater.
- *“On-call wants more context, not fewer alerts.”* — Put context **on the one page** (runbook, graph, last change, trace exemplar). Do not add pages.
- *“Business KPI as page?”* — As an SLO if they signed it. Not as a shadow metric owned by nobody.

**Example.** Kube node failure → 4,000 CrashLoop alerts. Inhibition: node NotReady parent. One page to the node owner, 4,000 events attached. Copilot drafts the timeline; does not page again.

---

## Q7. Walk an RCA: p99 is 5× after a deploy.

**Why they ask.** This is the scenario round. They want OBSERVE → ISOLATE → HYPOTHESIZE → VERIFY → FIX → PREVENT (Chapter 05), applied to ops — not the LLM-latency incident in Chapter 22.

**What they expect.** Blast radius first, version on the traces, a rollback *decision*, and a prevent that is a gate.

**Answer structure keywords.** blast radius · version exemplar · control metrics · rollback vs ride · error budget · post-incident test.

**30-second.** I treat it as an incident, not a modeling puzzle. Bound who is hit and whether the new version is on the slow traces. If the canary or the new `version` label owns the p99 and error budget is burning, I roll back first and analyze second. If old and new are both sick, I do not roll back; I look at a shared dependency. I do not restart randomly while I think.

**2-minute.** **Observe:** start time vs deploy/flag time, region, route, p50 vs p95 vs p99, error rate, saturation. **Isolate:** client, edge, our service, dependency, data store. Trace exemplars *with version*. **Hypotheses (ranked):** (1) the release itself (CPU, N+1 query, bad flag default, lock), (2) dependency capacity exposed by extra load from the release, (3) unrelated vendor/region event, (4) observability change that only *looks* like 5× (histogram buckets, clock, sampling). **Verify:** compare last-good vs now on the same route; check DB/CPU/locks as *controls*; confirm canary. **Fix:** mitigate = rollback or flag off or traffic shift; durable = the actual bug. **Prevent:** canary on the *SLI*, not only on 5xx; error-budget halt; regression test for the slow query.

**Senior / deep.** Rollback is allowed when: previous version is still healthy, data migrations are backward compatible, you have capacity on the old replica set. If the deploy included a **forward-only schema change**, rollback is a **never** until you have a reverse migration — that is Q9. I say that out loud so they know I will not “just helm rollback” a payments DB. During the incident I assign a **scribe** (human or copilot) to keep a timeline of actions; duplicate restarts are how you lose the evidence. After: the failing trace becomes a synthetic SLI probe.

Do not steal Chapter 22’s LLM-specific latency drill unless they said the service *is* an LLM gateway. The method is the same; the spans differ.

**Weak answer.** “I’d look at logs in Splunk and maybe roll back.”

**Mistakes.**

- Restarting the healthy dependency.
- Ignoring p50 (if p50 is also 5×, it is not a tail GC story).
- No version label so you cannot know.
- Fixing only in prod with no prevent.

**Follow-ups + strong replies.**

- *“Rollback made it worse.”* — Forward-only migration or cache keys. Stop. Treat as a data incident. Forward-fix with a freeze on new deploys.
- *“Only one tenant?”* — Not a global rollback. Tenant-specific data, ACL, or noisy neighbor. Different blast radius.
- *“p99 5× but errors flat and users fine?”* — Check if the histogram or the probe changed. Still worth a ticket; maybe not a P1.

**Example.** New version adds a sync call to a search cluster on every checkout. Traces show the new span; search CPU saturated; old version in the other region fine. Mitigate: flag off the call. Prevent: the call goes async + budget, and canary includes checkout p99 not just `/health`.

---

## Q8. ServiceNow / ITSM — what is the ticket lifecycle, and where does AI sit?

**Why they ask.** Intelligent Automation and AIOps both live here. They will punish “the bot just closes it.”

**What they expect.** Incident vs problem vs change vs request. States. Who is accountable. Where LLM/RPA is allowed.

**Answer structure keywords.** incident · problem · change · request · P1–P4 · assignment · pending · resolve ≠ close · CAB · audit.

**30-second.** The ticket is the system of record for who knew what when. An **incident** restores service; a **problem** finds the enduring cause; a **change** is a controlled modification; a **request** is a catalog item. AI can classify, draft, enrich, and *propose*. Humans (or a policy engine) assign, approve changes, and close Sev-1/2. I never auto-close an incident that had a production write.

**2-minute.** Lifecycle I can draw:

```
detect → create incident (CI, severity, caller, correlation_id)
      → classify / enrich (service, owner, last change, runbook)
      → assign → work (work notes, timeline)
      → pending (vendor / customer / change)
      → resolve (what restored service, linked change/problem)
      → close (confirmation, knowledge)  ─ reopen if bounce
```

Severity from SLO impact and safety, not from the model’s adjective. Major incidents get a bridge, a commander, a scribe — the copilot is the scribe, not the commander. Changes: standard (pre-approved, low risk, maybe auto), normal (CAB), emergency (post-reviewed). Auto-remediation that mutates prod **is a change** and must leave a change record, even if the change is a standard restart. Problems: you do not file a problem for every incident; you file when the cause survives restoration (bad memory leak, recurring vendor).

**Senior / deep.** Intelligent Automation interviews want **exception paths**. The happy path is a catalog request with a workflow (Chapter 11: not an agent). The exception is an incident. Bots that open duplicate incidents because the correlation id was missing are a platform bug. Identity: the integration user is not allowed to approve its own change (SoD). Work notes are evidence; the model’s paragraph is a draft until a human or a deterministic enricher stamps facts (CI, version, trace links). KPI traps: “mean time to close” incentivizes premature close. I report **time to mitigate**, **reopen rate**, **% auto-resolved that reopened**, **change fail rate**.

**Weak answer.** “We’d auto-create and auto-close tickets with an LLM.”

**Mistakes.**

- Collapsing incident and change.
- Auto-closing P1s.
- No CI / service on the ticket.
- Using the chatbot as the approval (same session as the requester).

**Follow-ups + strong replies.**

- *“RPA vs agent vs workflow?”* — Catalog request = workflow. Messy intake email = LLM extract into a form, then workflow. Open-ended “fix prod” = never an open agent.
- *“User wants status.”* — Status from ticket fields, not from model prose. The model can *render* the fields.
- *“Major incident review?”* — Timeline from the ticket + traces, not from chat memory.

**Example.** Alert → correlated incident INC123, CI=`checkout-api`, last change CHG88 attached, owner group paged. Copilot drafts work note with trace links. Restart is a standard change CHG89 auto-opened. Resolve requires the on-call. Close next business day if no reopen.

---

## Q9. Safe auto-remediation — restart vs rollback vs never?

**Why they ask.** This is the automation-safety round. “Self-healing” without a never-list is how you take the rest of the estate with you.

**What they expect.** A policy table, preconditions, blast-radius caps, and examples in all three buckets.

**Answer structure keywords.** signature · cooldown · parallelism · idempotent · stateful · shared · security · freeze · kill switch.

**30-second.** Auto-action is a privilege earned by a **known signature**, a **reversible effect**, and a **bounded target**. Restart: stateless replicas matching a known crash signature, with cooldown and max parallelism. Rollback: bad deploy with a healthy previous version and a backward-compatible data plane. Never: stateful unique processes, shared data stores, unknown signatures, security events, freeze windows, first-of-class failures. The LLM does not choose the bucket; a table does.

**2-minute.** Preconditions for *any* auto action: identity of the target from **runtime** topology, signature match, error budget or invariant firing, no overlapping human incident commander lock, under the hourly action budget, kill switch green. Then:

| Action | When | Guards |
| --- | --- | --- |
| **Restart** | Stateless, crashloop or leak with known fingerprint, N identical events | Max % of replica set per window, PDB respected, cooldown, not the last healthy replica |
| **Rollback** | Version on failing exemplars, canary red, previous pin healthy | Backward-compatible schema, feature-flag off preferred if it exists, one service at a time |
| **Scale out** | Saturation SLI, headroom in quota | Max replicas, cost budget, not a thundering herd on a storm |
| **Never** | See the never-list below | Ticket + human |

Every action writes a change record and a trace. If the signature fires again immediately, **stop** — you are in a loop (Chapter 11 energy, applied to infra).

**Senior / deep.** Restart vs kill vs bounce-traffic: restarting a JVM with a leak buys time; restarting Kafka brokers as a pack is a partition incident. I encode **statefulness** on the service catalog: `stateless | durable-queue | single-writer | datastore | stateful-set`. Only `stateless` is in the default yes-list. Feature flags beat rollbacks when the badness is a code path. Rollbacks beat restarts when the process is healthy but the *build* is wrong — restarting a bad binary is theater.

**Weak answer.** “If error rate is high we’d auto-restart the pod, and if that fails roll back.”

**Mistakes.**

- Restarting during a DB failover.
- Rolling back a schema-forward deploy.
- Acting on the first occurrence of a new fingerprint.
- No global kill switch.
- Letting the model add tools to the yes-list.

**Follow-ups + strong replies.**

- *“Kubernetes restartPolicy already restarts.”* — That is process liveness, not AIOps. AIOps restart is a *deliberate* bounded action with a change record when kube’s own loop is not the right medicine (node drain, config revert).
- *“Can we auto-rollback ML models?”* — That is LLMOps pin flip (Chapter 17), still a change, still a gate. Same never-list if the model serves a regulated decision without a shadow path.
- *“How do you test this?”* — Game day: inject the signature in staging, assert one restart not ten, assert kill switch, assert ticket.

**Example.** `checkout` pods OOM on a known cache-stampede fingerprint, 3 of 12. Auto-restart those 3, not the whole deployment, not Redis. If OOM continues, stop and page — the signature no longer matches “stampede that a bounce fixes.”

---

## Q10. How do you use an LLM as an RCA copilot without letting it SRE unsupervised?

**Why they ask.** 2026 flavor of the design round. They want HITL, citations, and a tool allowlist — Chapter 11 applied to ops.

**What they expect.** Read-only default. Draft artifacts. Deterministic policy around the model. Evals that are not fluency.

**Answer structure keywords.** read-only tools · citations · runbook retrieve · HITL · step cap · never-list · faithfulness · wrong-correlation eval.

**30-second.** The copilot reads: metrics APIs, trace links, logs (redacted), catalog, runbooks, the open ticket. It writes: a timeline draft, ranked hypotheses with disconfirmers, a suggested action *name* from the policy table, a customer-status paragraph. A human or the policy engine commits. Tools that mutate have the same HITL as any agent. Caps on steps, tokens, and dollars. If it cannot cite a `trace_id` or a change id, it must say unknown.

**2-minute.** Architecture: workflow, not an open agent. Nodes: gather context (deterministic queries) → retrieve runbooks (RAG with ACL) → LLM draft → schema validate → human. The gather node is code: “last deploy, SLI chart, exemplar traces, sibling errors.” The model does not get `query_prometheus` as a free-form DSL if I can avoid it; it gets *pre-built* summaries plus links. If I must give a query tool, it is SELECT-only, time-bounded, row-capped — LLM06 and LLM03. Output schema: `hypotheses[]`, `evidence[]`, `recommended_policy_action`, `confidence`, `unknowns`. Confidence is not a probability of truth; it is “how complete is the evidence pack.” Eval: faithfulness to cited telemetry, action-allowed vs action-proposed, time-to-first-useful-draft, reopen rate when we followed the draft.

**Senior / deep.** Lethal combination in ops: **private telemetry + untrusted runbook wiki + a write tool** (OWASP LLM01 + LLM03). A poisoned wiki page that says “always restart postgres” is the wiki-jailbreak they will ask Security about (Chapter 19). Mitigations: pin runbooks, treat retrieved text as data, policy table in code, HITL. I also isolate tenants in the copilot: on-call for service A does not retrieve service B’s customer payloads. Traces of the copilot are LLMOps; they must not contain secrets from prod logs (LLM02). Wrong drafts are a **quality** incident for the copilot and must enter its golden set — that is how AIOps and LLMOps meet without merging.

**Weak answer.** “We’d give the model kubectl and let it fix things, with a system prompt to be careful.”

**Mistakes.**

- Free-form shell.
- Runbook RAG without ACL or pinning.
- Measuring success as “tickets closed.”
- No step cap on investigation loops.

**Follow-ups + strong replies.**

- *“When is an agent justified?”* — Unknown investigation path across many tools, still with a 8–12 step cap and no writes. Most RCAs are a graph: gather → draft → approve.
- *“Vendor copilot in Datadog/Dynatrace/ServiceNow?”* — Fine as the UI. I still need *our* never-list, *our* identity, and *our* eval of wrong RCAs.
- *“What does the user see?”* — The ticket. The model is a sidecar.

**Example.** Copilot attaches three trace URLs, names `version=2026.09.12` as the failing pin, recommends `rollback` because the service is marked `stateless` and schema-compat `ok`. On-call clicks approve; CD runs the pin flip. Postgres instances are not even in the tool catalog.

---

## Q11. SLOs and error budgets — how do they change what you page and what you ship?

**Why they ask.** Without SLOs, AIOps is a pile of gauges. They want SLI → SLO → budget → policy.

**What they expect.** A user-centric SLI, a target, burn-rate alerting, and budget as a *release brake*.

**Answer structure keywords.** SLI · SLO · SLA · error budget · burn rate · multi-window · halt deploys · never page on CPU.

**30-second.** An SLI is the measurement of a user-valued symptom (availability, latency, quality). An SLO is the target we promise ourselves. An SLA is the legal cousin, looser. Error budget is `1 − SLO`. When we burn it fast, we page and we halt risky deploys. AIOps exists to detect budget burn early and to spend budget on *intentional* change, not on noise.

**2-minute.** Pick SLIs from the user path: successful checkouts / attempts, p99 latency under a threshold, freshness of a feed. Availability SLI: good events / valid events (exclude 404s you caused by bad clients if that is the contract). Alert on **burn rate**, not on a 30-day average that pages too late: a 1-hour window at 14× burn plus a 6-hour window at 6× (multi-window, multi-burn) catches both sharp and slow. Budget policy: if remaining monthly budget < X% and the change is not a fix, it waits. That is how you stop shipping features through an incident. AI quality SLOs (faithfulness, citation fail) are Chapter 17; they still *are* SLOs — the AIOps pipeline can page on them if that product is production.

**Senior / deep.** Count vs time-window SLIs: for low-QPS admin APIs, a 30-day availability percent is noisy; use a time-based “bad minutes” SLI or a probe. **Never** make CPU an SLI unless the product *is* CPU (batch). Error budget for automation: if auto-restarts cause more budget burn than they save (thundering herd), the automation is a defect. I report **budget spent on incidents vs budget spent on releases** — a healthy org spends most of the budget on shipping. For Intelligent Automation, ticket SLOs (time to first response) are real, but they must not incentivize auto-close.

**Weak answer.** “We have 99.9% uptime.” No SLI definition, no budget, no halt policy.

**Mistakes.**

- SLO on internal gauges.
- Page on any burn, including 1% of budget over a month.
- SLA tighter than SLO (legal will lose).
- Hiding brownouts because the average is green.

**Follow-ups + strong replies.**

- *“Multiple SLOs?”* — Latency, availability, quality. A latency-only SLO will ship an available-but-wrong copilot.
- *“Canary vs SLO?”* — Canary is how you avoid spending the whole budget on one release. SLO is how you know.
- *“What if the vendor burns our budget?”* — Dependency SLI + error budget on *them*, and a customer-comms path. Do not “fix” it by restarting yourselves.

**Example.** Checkout success SLO 99.9%. 1-hour burn 14× after a flag flip. Page, halt deploys, flag off. Budget recovered; RCA later. Without burn-rate, you would have noticed at the weekly review.

---

## Q12. Event pipelines — what actually happens between a metric and a ticket?

**Why they ask.** Platform-design question. They want stages you can draw, backpressure, and exactly-once-enough delivery into ITSM.

**What they expect.** Ingest, normalize, enrich, reduce, correlate, route, act. Failure modes: lag, dupes, poison events.

**Answer structure keywords.** bus · schema · enrichment · fingerprint · window · backpressure · DLQ · idempotent ticket create.

**30-second.** Raw signals hit a bus, not ServiceNow. A pipeline normalizes them to a common event schema, enriches with topology/identity/change, fingerprints and suppresses, correlates into incidents, then routes: page, ticket, or auto-policy. Each stage has a SLA. Ticket create is idempotent on `correlation_id`. If the pipeline lags, I shed *debug* events, not SLO burns.

**2-minute.**

```
producers → ingest API / collector
         → normalize (type, resource, severity, labels)
         → enrich (CMDB, owner, version, change_id, trace exemplar)
         → reduce (dedup, thresh, maintenance)
         → correlate (graph + time + change)
         → decide (page / ticket / auto / drop-audited)
         → sinks (Pager, ServiceNow, chat, actuator)
```

Schema: a small envelope (`id`, `source`, `fingerprint`, `resource`, `start`, `end`, `payload_ref`). Fat payloads stay in object storage. Enrichment must timeout; a slow CMDB cannot stall P1s — degrade to unenriched and mark `enrichment=partial`. Correlation windows: short for pages (1–5 min), longer for problems. Exactly-once into ITSM is really **at-least-once + idempotency key**. Poison events (bad schema) go to a DLQ with an alert on DLQ depth — silent drops are how you miss the next outage.

**Senior / deep.** Multi-tenant pipelines: a noisy product team cannot drown the bus (quotas per source). Ordering: do not assume global order; incidents are state machines keyed by fingerprint. **Replay** is a requirement: I must rebuild an incident view from the event log. That is also how I eval the copilot. Cost: high-cardinality events are the log equivalent of Q3 — drop or sample at ingest with an allowlist of fields. Security: the actuator sink is a separate identity from the ingest identity (Chapter 19 energy): the pipeline that *hears* alerts should not be the principal that *kubectl deletes*.

**Weak answer.** “Webhooks from Datadog into ServiceNow.”

**Mistakes.**

- One webhook per alert to ITSM.
- Enrichment as a single point of failure.
- No DLQ.
- Auto-actuator on the same queue as “debug.”

**Follow-ups + strong replies.**

- *“Kafka vs vendor bus?”* — If the estate already has a bus, use it. The stages matter more than the logo.
- *“How do you version schemas?”* — Additive first; consumers ignore unknown fields; fingerprint algorithm versioned so a change does not split one incident into two.
- *“Backfill?”* — Replay from the log; do not re-page. `replay=true` suppresses notifications.

**Example.** Metric alert and log signature and deploy event share `service=checkout` + 2-min window + edge in the graph → one incident, one page, one ServiceNow row with three artifacts. A later restart action is a child event, not a new P1.

---

## RCA checklist (say this unprompted)

Use this as the spoken spine in scenario rounds. It complements Chapter 22 (do not recycle those incidents; reuse the *method*).

1. **Time and blast radius** — when, who, which region/tenant/version, user-visible or only a gauge.
2. **What changed** — deploy, flag, cert, quota, vendor, schema, traffic shape, observability itself.
3. **SLI first** — which SLO is burning; p50 vs p99; errors vs latency vs saturation vs quality.
4. **Exemplar** — at least one `trace_id` on the failing slice, with `version`.
5. **Control metrics** — what should be *quiet* if your leading hypothesis is true.
6. **Topology** — parent vs child; shared vs owned; last healthy replica.
7. **Mitigate vs analyze** — error budget decides whether you roll back now.
8. **One action at a time** — write a change; wait; do not restart *and* rollback *and* scale.
9. **Disconfirm** — what evidence would kill this story; look for it.
10. **Prevent** — a probe, a gate, a label, a never-list entry; not “we’ll watch it.”
11. **Ticket truth** — timeline, correlation id, links to traces; no fluent fiction.
12. **Copilot hygiene** — citations required; unknown is allowed; writes HITL.

Missing blast radius or a `version` on the exemplar is a mid-level ceiling on an AIOps loop.

---

## When you do NOT auto-remediate (memorize this list)

Say “never-list” in the interview. Then name ten, not two.

| Never | Why |
| --- | --- |
| **Unknown signature / first occurrence** | You do not know the blast radius |
| **Stateful unique writers** (primary DB, Kafka controller, single-writer leader) | Restart is a failover you did not intend |
| **Shared dependency** for many services | Local optimize, global outage |
| **Forward-only schema / data migration** | Rollback is not rollback |
| **Security / suspected intrusion** | You want containment and forensics, not a bounce that wipes evidence |
| **Change freeze / dual control required** | Policy is the product |
| **Last healthy replica / below PDB** | Availability cliff |
| **Human incident commander already locked the incident** | Automation vs human fight |
| **Pipeline enrichment stale / topology freshness unknown** | Wrong target |
| **Action already fired N times this window** | Loop |
| **Capacity / quota unknown** | Scale-out that OOMs the node |
| **Customer-visible data repair, delete, or replay** | Irreversible or legally scoped |
| **DNS / identity / cert changes without a rehearsed playbook** | Blast radius is “the company” |
| **The model recommended it and it is not in the table** | LLM03 excessive agency, applied to SRE |

Restart is not “safe” just because Kubernetes will recreate the pod. Rollback is not “safe” just because git has a previous tag. **Safe** means reversible, targeted, rehearsed, and cheaper than waiting.

---

## Rapid-fire (30–45 seconds each)

**Is a high CPU alert an SLO?** Almost never. CPU is a resource. Page on the user symptom unless you are a batch farm whose product *is* CPU.

**Metrics vs logs for paging?** Metrics. Logs for diagnosis and audit.

**Where does `user_id` go?** Trace/log attribute, not a metric label.

**Correlation id?** The join key across events, traces, tickets, and changes. If you cannot name it, you cannot dedup.

**CMDB vs traces?** Traces are runtime truth. CMDB is owners and declared intent. Automate off runtime identity.

**Can the copilot close INC?** Not Sev-1/2, not after a prod write. Maybe a pre-approved known-error with a signature — still audited.

**Error budget halt?** Fast burn → stop feature deploys, allow *fixes*.

**Profiles?** When the slow span is *inside* your binary and logs are boring.

**AIOps vs LLMOps?** Estate vs generative product. Copilot is both: AIOps policy, LLMOps evals.

**What if auto-restart loops?** Kill switch, then it becomes a never for that signature until a human edits the table.

---

## Weak vs strong posture (memorize the posture, not the paragraph)

| Weak | Strong |
| --- | --- |
| “We’ll add an AI SRE” | “Signals, topology, policy table, then maybe a drafter” |
| “Log everything into the model” | “Bounded metrics, sampled traces, redacted logs, pre-built summaries” |
| “AI will find root cause” | “Ranked hypotheses + disconfirmers + citations” |
| “Self-healing pods” | “Restart / rollback / never with cooldowns and a kill switch” |
| “Auto-close tickets” | “Ticket is SoR; AI drafts; humans close Sev-1” |
| “Thresholds are too noisy so we widen” | “Page on SLO burn; suppress children; review page precision” |
| “Last deploy caused it” | “Version on the exemplar, or it is a hypothesis” |

---

## A complete example you can reuse in interviews

**Setting.** Mid-size commerce estate. Prometheus + OTel + ServiceNow. They want “AIOps with an LLM.”

**Wrong design.** Model with `kubectl`, `aws`, and `snow_close_incident`. Wiki runbooks in a vector index. Pages on CPU. No series budget.

**Right design.**

1. SLIs on checkout success and p99. Burn-rate pages only.
2. Event pipeline: normalize, enrich from catalog, correlate on graph + `version` + change_id.
3. Cardinality linter in CI; `user_id` banned on metrics.
4. Policy table in code: `checkout` stateless → restart up to 25% / 15 min; rollback allowed if schema-compat; `orders-db` → never.
5. Copilot workflow: gather → draft timeline with trace links → HITL. No shell. Runbooks pinned.
6. ITSM: one incident per correlation_id; auto-open standard change on restart; no auto-close.
7. Eval: page precision, time-to-mitigate, wrong-correlation rate, copilot faithfulness, reopen rate of auto-actions.
8. Kill switch on a feature flag. Game day quarterly.

**One sentence close:** “The model writes the timeline; the policy table writes production; the ticket remembers.”

That sentence is what a 2026 AIOps interviewer is listening for.

---

## Map to the rest of the handbook

- LLM product telemetry, evals, pins: [17-llmops.md](17-llmops.md)
- Agents, HITL, tool validation, when not to agent: [11-agentic-ai.md](11-agentic-ai.md)
- MCP if the copilot uses tool servers: [12-mcp.md](12-mcp.md)
- Prompt injection via runbooks, excessive agency: Chapter 19
- Production incident drills (LLM/RAG/agent/K8s): [../banks/22-troubleshooting.md](../banks/22-troubleshooting.md) — reuse the method, not the stories
- Behavioral “a wrong correlation”: Chapter 24

Next drill: speak Q2, Q3, Q5, Q9, Q10 out loud. If those five are clean, you will survive most AIOps and Intelligent Automation ops screens. Then add Q7 and Q8 for the scenario and ITSM rounds.
