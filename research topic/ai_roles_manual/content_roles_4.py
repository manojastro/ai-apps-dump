# -*- coding: utf-8 -*-
"""Role modules 5-6: Forward Deployed Engineer, GenAI/Agentic AI Engineer."""
from docx_builder import H, P, BULLETS, NUMBERS, CODE, CALLOUT, TABLE, PAGEBREAK


# =====================================================================
# ROLE 5: FORWARD DEPLOYED / AI DEPLOYMENT ENGINEER
# =====================================================================
def build_fde(doc):
    H(doc, "Role Module 5 - Forward Deployed / AI Deployment Engineer (FDE)", 1, page_break_before=True)
    P(doc,
      "The Forward Deployed Engineer is a production engineer embedded with customers: you ship AI "
      "systems inside their VPCs, on their data, against their compliance constraints, while owning "
      "the eval harness that proves the system works on their reality. Palantir created the discipline; "
      "OpenAI, Anthropic, Meta, Sierra, Harvey, Glean, and Decagon industrialized it. It is currently "
      "the highest-paid generalist role in AI.")

    H(doc, "Module A - Labor Telemetry & Hiring Dynamics", 2)
    H(doc, "Quantitative Openings by Geography", 3)
    TABLE(
        doc,
        ["Geography", "Est. Active Openings", "Demand Character"],
        [
            ["United States", "1,200 - 1,800", "Frontier labs (OpenAI, Anthropic, Meta) and AI-native unicorns (Sierra, Harvey, Decagon, Glean); government/defense deployments (Palantir, Anduril) form a parallel cleared track."],
            ["Europe / EMEA", "400 - 600", "Enterprise deployments for EU banks/industrials; London and Paris hubs for lab expansion teams."],
            ["India / APAC (GCC)", "500 - 900", "GCC deployment pods for global customers; APAC expansion roles for lab-adjacent companies."],
            ["Global Remote", "200 - 350", "Rare for true FDE (travel expectations); remote variants skew to deployment engineering without customer embedding."],
        ],
        widths=[1.6, 1.5, 3.9],
        caption="Active openings estimate, September 2026",
    )

    H(doc, "Compensation Bands (Annual, Total Target Compensation)", 3)
    TABLE(
        doc,
        ["Percentile", "US (USD TTC)", "India (INR LPA)", "Europe (EUR)"],
        [
            ["25th", "$150,000", "20 - 28", "75,000 - 90,000"],
            ["50th (median)", "$195,000 - $210,000", "35 - 50", "105,000 - 125,000"],
            ["75th", "$280,000", "60 - 80", "145,000 - 165,000"],
            ["90th", "$400,000+", "90 - 120", "200,000+"],
        ],
        widths=[1.5, 1.8, 1.8, 1.9],
        caption="FDE TTC composites. Anchors: Bloomberry n=1,000+ postings median base $173,816; Palantir TTC $171K-$295K (top $415K); OpenAI FDSE estimated $350K-$550K TTC",
    )
    CALLOUT(
        doc,
        "Palantir's posted band runs $135K-$200K base with total comp $171K-$295K; one 2026 comp report "
        "calls the FDE 'the highest-paid generalist role in AI', and OpenAI's FDSE listings land near "
        "$350K-$550K total. The 75th-90th percentile spread is equity-driven: deployment success at "
        "strategic accounts reprices your refreshers.",
        title="Pay positioning.",
    )

    H(doc, "Top 15 Active Hiring Organizations", 3)
    TABLE(
        doc,
        ["Category", "Organizations"],
        [
            ["Frontier labs", "OpenAI (FDSE, SF, up to 50% travel), Anthropic (Applied AI), Meta (GenAI org), Cohere (deployment)"],
            ["Deployment-native companies", "Palantir (FDSE), Sierra, Harvey, Decagon, Glean, Writer, Cognition, Anysphere"],
            ["Defense / gov-adjacent", "Palantir Gotham, Anduril, Shield AI (cleared variants)"],
            ["Enterprise consultancies (AI pods)", "BCG X, McKinsey QuantumBlack, Accenture A-forward, Slalom GenAI practice"],
        ],
        widths=[2.2, 4.8],
        caption="Where FDEs are being hired right now",
    )

    H(doc, "Experience Baseline & Transition Backgrounds", 3)
    BULLETS(doc, [
        ("Baseline: ",
         "3-6 years shipping production software, with explicit customer exposure (consulting, "
         "professional services, startup 0-to-1). Travel tolerance (25-50%) is a hard filter."),
        ("Fullstack Engineer -> FDE: ",
         "dominant path; add LLM integration, evals, and customer communication evidence."),
        ("Consultant / Analytics Engineer -> FDE: ",
         "Palantir's classic intake; add production Python rigor (many consultants cannot ship)."),
        ("Data Engineer -> FDE: ",
         "strong for data-heavy deployments (Snowflake/Databricks estates); add product instinct."),
        ("Backend / DevOps -> FDE: ",
         "works when paired with demonstrated customer-facing work; the interview tests taste in scope, "
         "not infrastructure depth."),
    ])

    H(doc, "Module B - Role Taxonomy & Daily Operational Reality", 2)
    H(doc, "Boundary Mapping", 3)
    TABLE(
        doc,
        ["Adjacent Role", "They Own", "FDE Owns", "Flashpoint"],
        [
            ["Solutions Architect", "Reference architectures, pre-sales design", "Actually shipping and running it in the customer's environment", "The architect's diagram meets the customer's IAM reality"],
            ["Product Engineering (HQ)", "Core platform features", "Customer-specific configuration, integrations, and bespoke glue", "Bespoke code that should have been a platform feature (and vice versa)"],
            ["Customer Data Team", "Warehouse tables, pipelines", "The AI system's data contracts and eval datasets", "Who owns data quality failures that break model outputs"],
            ["Account Manager / PM", "Commercial relationship, scope", "Technical truth: what is possible, at what cost, by when", "Being used as the 'yes engineer' vs technical honesty"],
        ],
        widths=[1.5, 2.1, 2.2, 1.2],
        caption="Ownership boundaries",
    )

    H(doc, "Five Concrete Daily Operational Artifacts", 3)
    BULLETS(doc, [
        ("Customer deployment runbook: ",
         "environment-by-environment steps (customer VPC, their IdP, their logging), smoke tests, "
         "rollback, and the security-review checklist the customer's SOC will run."),
        ("Eval harness on customer data: ",
         "a golden set built from their real documents/tickets (PII-scrubbed), an error taxonomy, and "
         "a dashboard tracking accuracy per class across model and prompt versions."),
        ("Scope one-pager: ",
         "a one-page contract of what ships this increment, what explicitly does not, success metrics, "
         "and dependencies - reviewed with the customer sponsor weekly."),
        ("Production incident writeup at customer site: ",
         "what broke in their environment, the customer-safe narrative, and the config/template change "
         "that makes the fix permanent."),
        ("Feedback loop report to HQ: ",
         "the distilled customer-usage telemetry (which features are used, which failure classes recur) "
         "that turns bespoke deployments into platform roadmap items."),
    ])

    H(doc, "Core Daily Toolchain", 3)
    TABLE(
        doc,
        ["Layer", "Tools Used Daily"],
        [
            ["Languages", "Python (primary), TypeScript/React for customer-facing UIs, SQL everywhere"],
            ["Customer estates", "Snowflake, Databricks, customer VPCs (AWS/Azure/GCP), customer IdPs (Okta/Entra)"],
            ["AI integration", "Lab SDKs (OpenAI/Anthropic), LangChain/LlamaIndex, eval frameworks (Ragas, custom), prompt versioning"],
            ["Deployment", "Docker, Terraform (their modules), GitHub/GitLab in customer orgs, Airflow/dbt adjacent"],
            ["Collaboration", "Slack/Teams (customer channels), Jira/Linear, Notion/Confluence, Miro for discovery"],
            ["Observability", "Langfuse/LangSmith traces, customer Datadog, per-deployment dashboards"],
        ],
        widths=[1.5, 5.5],
        caption="Daily driver toolchain",
    )

    H(doc, "Module C - Exhaustive Technical Skills, Tools & Services Matrix", 2)
    TABLE(
        doc,
        ["Category", "Skill / Tool / Service", "Frequency"],
        [
            ["Core engineering", "Production Python (typing, testing, packaging) - non-negotiable", "Critical"],
            ["Core engineering", "SQL and data modeling over messy customer warehouses", "Critical"],
            ["Core engineering", "TypeScript/React for demo-to-production UI", "High"],
            ["LLM integration", "Prompt engineering with versioning; structured outputs; function calling", "Critical"],
            ["LLM integration", "RAG architecture on customer corpora (chunking, hybrid retrieval, rerank)", "Critical"],
            ["Evaluation", "Golden-set construction, error taxonomy, Ragas/custom metrics, A/B across model versions", "Critical"],
            ["Deployment", "Customer-VPC deployment, zero-data-retention configurations, air-gapped variants", "Critical"],
            ["Deployment", "Docker/K8s, Terraform in customer orgs, CI/CD inside customer constraints", "High"],
            ["Data platforms", "Snowflake / Databricks / BigQuery integration patterns", "High"],
            ["Security & compliance", "Customer security reviews (SOC 2 evidence), PII scrubbing, data residency, DPA constraints", "Critical"],
            ["Product judgment", "Scope contracting, demo-to-production gap management, discovery interviewing", "Critical"],
            ["Observability", "Trace-based debugging of LLM apps in the customer environment", "High"],
            ["Communication", "Written one-pagers, executive demos, technical negotiation", "Critical"],
            ["Adjacent breadth", "Fine-tuning awareness (when to reject it), cost modeling per customer", "High"],
            ["Emerging", "Agent deployment with HITL, MCP-based integrations at customer sites", "Emerging"],
        ],
        widths=[1.7, 4.3, 1.0],
        caption="Skills matrix with market frequency",
    )

    H(doc, "Module D - Deep Technical Reference Manual (The Living Textbook)", 2)
    H(doc, "Deep Theory: Eval-First Deployment Methodology", 3)
    P(doc,
      "FDE work fails predictably: a great demo meets production data and dies. The counter-doctrine "
      "is eval-first: no feature ships to a customer environment before an executable definition of "
      "'works' exists on THEIR data. The methodology:")
    CODE(doc, r"""
DISCOVERY                 BUILD                    HARDEN                  SCALE
-------                   ------                   -------                 -----
  |                          |                        |                      |
  +--> mine 200-500 real     +--> smallest shippable  +--> error taxonomy    +--> rollout
     examples from the       slices, each with an     (every failure        governance
     customer's systems      eval; CI gates on        class owned +         per feature
  +--> PII-scrub + label     eval pass                countermeasure)       +--> bespoke ->
  +--> golden set v0         |                        |                        platform
  +--> error taxonomy        +--> prompt/model        +--> red-team pass       feedback
     co-owned with the       versioning behind        +--> latency/cost        to HQ
     customer SME            flags, eval-gated        budgets per tenant
  +--> success metric =      |                        |
     business event, not     +--> demo = golden-       +--> production
     'looks good'              set slice + UI          telemetry loop
""", caption="Figure 5.1 - The eval-first deployment lifecycle")
    BULLETS(doc, [
        ("Golden-set discipline: ",
         "200-500 customer-real examples, stratified by the error taxonomy you expect (retrieval "
         "misses, formatting, domain jargon, multilingual, adversarial inputs), versioned, and "
         "co-owned with a customer SME. A golden set the customer does not believe in is worthless "
         "when accuracy is questioned in month 3."),
        ("Error taxonomy: ",
         "every failure gets a class; every class gets an owner and a countermeasure (better "
         "retrieval, prompt change, model upgrade, or 'accepted risk'). The taxonomy converts vague "
         "dissatisfaction into a burndown."),
        ("Scope contracts: ",
         "the one-pager lists non-goals explicitly. Scope creep is the top killer of FDE velocity; "
         "the countermeasure is written, reviewed non-goals, not good intentions."),
        ("Zero-data-retention (ZDR) deployments: ",
         "enterprise customers demand no training on their data, prompt/response not retained beyond "
         "TTL, logs PII-scrubbed, and provider ZDR agreements cited. Know the exact knobs (OpenAI ZDR "
         "flag, Azure no-training default, Bedrock default no-retention) and the audit evidence."),
    ])

    H(doc, "Master Syllabus: What to Actually Study", 3)
    BULLETS(doc, [
        ("Deployment doctrine: ",
         "Palantir's public engineering blog on FDSE and forward-deployed software; fde.academy and "
         "OpenAI FDSE job descriptions (the real skill lists); 'Working Backwards' for customer-"
         "obsession framing."),
        ("Evaluation: ",
         "Ragas documentation (faithfulness, answer relevance, context precision); Hamel Husain's "
         "error-analysis writing on eval-driven development; OpenAI evals library."),
        ("Retrieval on real data: ",
         "the Hybrid RAG pattern (Module 6D) and the failure modes (context rot, lost-in-the-middle) "
         "documented there - the single most deployed architecture in FDE work."),
        ("Security/compliance: ",
         "SOC 2 evidence requests, DPA reading, ZDR configurations per provider, PII scrubbing with "
         "Presidio (Module 4D pattern)."),
        ("Data platforms: ",
         "Snowflake + Databricks quickstarts, dbt fundamentals - customer data estates are where FDE "
         "work lives."),
    ])

    H(doc, "Canonical Code Pattern 5.1 - Automated LLM Evaluation Pipeline (Ragas + LLM-as-Judge)", 3)
    P(doc,
      "The eval pipeline is the FDE's core artifact. This production version: loads a versioned "
      "golden set, runs retrieval + generation, scores faithfulness / context precision / answer "
      "relevance with Ragas, adds an LLM-as-judge rubric with a deterministic fallback, and fails CI "
      "when quality regresses beyond tolerance. (The GenAI module 6D uses the same harness for agent "
      "evals.)")
    CODE(doc, r'''
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    answer_relevancy,
    context_precision,
    faithfulness,
)

logger = logging.getLogger("fde.evals")


@dataclass(frozen=True)
class EvalTolerances:
    """Release gates. Fail the build when any metric drops beyond tolerance."""
    faithfulness_min: float = 0.85
    context_precision_min: float = 0.75
    answer_relevancy_min: float = 0.80
    max_regression: float = 0.03     # vs stored baseline


@dataclass
class GoldenCase:
    case_id: str
    question: str
    ground_truth: str
    tags: list[str] = field(default_factory=list)


class GoldenSet:
    """Versioned golden set loaded from JSON, co-owned with the customer SME."""

    def __init__(self, path: Path) -> None:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        self.version: str = raw["version"]
        self.cases: list[GoldenCase] = [GoldenCase(**c) for c in raw["cases"]]
        if len(self.cases) < 50:
            logger.warning("golden set v%s has only %d cases; target 200-500",
                           self.version, len(self.cases))


class EvalPipeline:
    """Runs the system under test over the golden set and gates the release."""

    def __init__(self, golden: GoldenSet,
                 answer_fn: Callable[[str], tuple[str, list[str]]],
                 judge_fn: Optional[Callable[[str, str], float]] = None,
                 tolerances: EvalTolerances = EvalTolerances()) -> None:
        self.golden = golden
        self.answer_fn = answer_fn      # returns (answer, retrieved_contexts)
        self.judge_fn = judge_fn        # optional 1-5 rubric score -> normalized
        self.tol = tolerances

    def run(self) -> dict:
        rows = {"question": [], "answer": [], "contexts": [], "ground_truth": []}
        for case in self.golden.cases:
            try:
                answer, contexts = self.answer_fn(case.question)
            except Exception:
                logger.exception("SUT failed on case %s", case.case_id)
                answer, contexts = "", []
            rows["question"].append(case.question)
            rows["answer"].append(answer)
            rows["contexts"].append(contexts or ["(none)"])
            rows["ground_truth"].append(case.ground_truth)

        ds = Dataset.from_dict(rows)
        scores = evaluate(ds, metrics=[faithfulness, context_precision, answer_relevancy])
        result = {m: float(scores[m]) for m in
                  ("faithfulness", "context_precision", "answer_relevancy")}

        if self.judge_fn is not None:
            rubric_scores = []
            for case, ans in zip(self.golden.cases, rows["answer"]):
                try:
                    rubric_scores.append(max(0.0, min(1.0, self.judge_fn(case.question, ans))))
                except Exception:
                    logger.exception("judge failed on %s", case.case_id)
                    rubric_scores.append(0.0)
            result["rubric_judge"] = sum(rubric_scores) / len(rubric_scores)
        return result

    def gate(self, result: dict, baseline: Optional[dict] = None) -> bool:
        failures = []
        for metric, floor in (("faithfulness", self.tol.faithfulness_min),
                              ("context_precision", self.tol.context_precision_min),
                              ("answer_relevancy", self.tol.answer_relevancy_min)):
            if result.get(metric, 0.0) < floor:
                failures.append(f"{metric}={result.get(metric):.3f} < floor {floor}")
            if baseline and result.get(metric, 0.0) < baseline.get(metric, 0.0) - self.tol.max_regression:
                failures.append(f"{metric} regressed beyond {self.tol.max_regression}")
        if failures:
            logger.error("EVAL GATE FAILED: %s", "; ".join(failures))
            return False
        logger.info("eval gate passed: %s", {k: round(v, 3) for k, v in result.items()})
        return True


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    demo = GoldenSet(Path("golden_set.json"))  # {"version": "v3", "cases": [...]}
    def system_under_test(q: str) -> tuple[str, list[str]]:
        return "answer from your RAG app", ["retrieved chunk text"]
    pipeline = EvalPipeline(demo, system_under_test)
    metrics = pipeline.run()
    print(json.dumps(metrics, indent=2))
    ok = pipeline.gate(metrics, baseline=None)
    raise SystemExit(0 if ok else 1)  # non-zero fails CI
''', caption="Code 5.1 - eval_pipeline.py: Ragas metrics + judge + release gate")

    H(doc, "Failure Modes & Edge Cases (FDE)", 3)
    BULLETS(doc, [
        ("Data-quality surprise: ",
         "the customer's 'single source of truth' has 30% duplicate or expired records; retrieval "
         "returns confidently wrong content. First-week action: data profiling report with the "
         "customer's name on it."),
        ("PII in the wild: ",
         "customer documents contain real PII; your eval fixtures must be scrubbed (Presidio) and "
         "your logs must not become their compliance incident."),
        ("Eval-set leakage: ",
         "golden questions were shown to the prompt/designer; numbers flatter the demo. Keep a "
         "held-out slice, rotate quarterly."),
        ("Drift after customer schema change: ",
         "a field rename silently empties retrieval results. Data-contract tests in CI against "
         "customer-schema snapshots."),
        ("Demo overfit: ",
         "the demo corpus is hand-curated; production corpora are messier (scans, multilingual, "
         "legacy formats). Ship the demo on a production-shaped corpus or fail early."),
        ("Scope creep via 'small favors': ",
         "every unpriced favor erodes the eval discipline; the one-pager's non-goals are the "
         "defense."),
        ("Pilot purgatory: ",
         "no success metric agreed up front means the pilot cannot end. Define the exit metric in "
         "writing at kickoff."),
        ("Air-gapped constraints: ",
         "no internet egress means no managed moderation APIs; plan self-hosted guardrails and "
         "models ahead."),
    ])

    H(doc, "Module E - Interview Mechanics & Hidden Hiring Patterns", 2)
    H(doc, "ATS Screening Triggers", 3)
    BULLETS(doc, [
        ("Must-appear keywords: ",
         "customer-facing or client-facing, deployment, evals/evaluation, RAG, prompt engineering, "
         "Python, SQL, VPC/on-prem, ZDR or data privacy, travel percentage acknowledged."),
        ("Phrasing that ranks: ",
         "'shipped an LLM doc-QA system into a customer VPC serving 2,000 employees; built the "
         "golden set with their SMEs; held faithfulness >= 0.88 across 6 releases'; travel: 40% OK."),
        ("Immediate-rejection anti-patterns: ",
         "pure interview-passing profiles (LeetCode-heavy, no customer artifact); 'built chatbots' "
         "with no eval story; no evidence of writing for stakeholders; unwilling to travel when the "
         "JD says 40%."),
    ])

    H(doc, "Interview Loop Breakdown", 3)
    TABLE(
        doc,
        ["Round", "Format", "What Is Actually Being Tested"],
        [
            ["Recruiter + HM screen", "Story + logistics", "Travel tolerance, customer instincts, salary fit"],
            ["Technical screen (60m)", "Coding + system questions", "Python fluency, SQL over messy data, RAG mechanics"],
            ["Deployment deep-dive (60m)", "Past-system walkthrough", "Did YOU run it in production? Error taxonomy discipline, honest post-mortems"],
            ["Take-home / live build (2-4h)", "Build a small doc-QA on messy data WITH evals", "Judgment under ambiguity; evals-first instinct; code quality"],
            ["Customer role-play (45m)", "Mock discovery or 'your model hallucinated' call", "Technical honesty under pressure; scoping; no over-promising"],
        ],
        widths=[1.5, 1.9, 3.6],
        caption="Typical loop: 4-5 rounds (labs add a research-literature round)",
    )

    H(doc, "Five Real Interview Questions with Model Answers", 3)
    NUMBERS(doc, [
        ("You deploy a document-QA system; week 2, the customer says 'it hallucinated on a policy question.' Walk me through your response. ",
         "Model answer: reproduce from the trace (Langfuse/LangSmith) - capture the exact prompt, "
         "retrieved chunks, answer; classify the failure (retrieval miss vs grounding failure vs "
         "correct-but-outdated source); fix at the correct layer; add the case to the golden set and "
         "the error taxonomy; then communicate: customer-safe narrative, what changed, and the "
         "measured delta on the eval suite. Never debate 'is it really a hallucination' semantics "
         "with the customer."),
        ("Design the eval harness for an AI system answering questions over 500k HR documents. ",
         "Model answer: mine 300-500 real questions from the customer (search logs, ticket themes), "
         "PII-scrub; stratify by document type, jurisdiction, and language; label ground truth with "
         "an SME; metrics: retrieval hit-rate@k, context precision, faithfulness, answer relevance; "
         "add behavioral suites (refusal on absent info, cross-document synthesis); CI gate with "
         "tolerances; quarterly rotation of held-out cases; dashboard per release."),
        ("Customer demands on-prem, air-gapped deployment with an open-weights model. What changes? ",
         "Model answer: model selection constrained to quantized open weights that fit their GPU "
         "footprint (vLLM serving); self-hosted embeddings and reranker; guardrails must be "
         "self-hosted (no moderation APIs); evals run in their environment with their data (export "
         "the harness, not just the app); update path via signed model bundles; ZDR is moot - their "
         "network is the boundary; document hardware sizing and expected TTFT."),
        ("The customer's data has 30% duplicate/stale records. The AI is 'wrong'. Who owns it? ",
         "Model answer: present the data-profile evidence first (dedup stats, freshness histogram); "
         "co-own the fix: ingestion-time dedup and freshness filters on our side (quick win), and a "
         "prioritized remediation list for their data team; make retrieval cite source-freshness so "
         "stale answers are visibly stale; renegotiate the accuracy target against measured corpus "
         "quality - put both in the one-pager."),
        ("How do you decide what stays bespoke vs what becomes platform? ",
         "Model answer: bespoke code earns platform status by recurrence (>= 3 customers), "
         "stability (the bespoke implementation survived a quarter unchanged), and testability "
         "(generalizes without customer-specific branches); HQ feedback loop ships the telemetry "
         "that proves recurrence; the FDE's job is to graduate glue code into platform with "
         "evidence, and to resist platformizing one customer's preferences."),
    ])

    H(doc, "Module F - Production Capstone Specifications", 2)
    H(doc, "Capstone 5.1 - Customer-VPC Document QA Deployment (Simulated Tenant)", 3)
    BULLETS(doc, [
        ("Architecture: ",
         "a 'customer VPC' simulated by a separate cloud account/network namespace: app (FastAPI + "
         "simple React) -> Hybrid RAG over a messy 50k-doc corpus (synthetic but realistic: scanned "
         "PDFs, multilingual, stale versions) -> ZDR-style config (no prompt/response persistence, "
         "PII-scrubbed logs) -> Code 5.1 eval harness with a 300-case golden set -> deployment via "
         "Terraform + Docker with a rollback runbook."),
        ("Verification tests: ",
         "eval gate passes on release candidate and fails on an intentionally regressed prompt "
         "(negative test); PII scan of all logs finds zero hits; rollback runbook executes < 10 min; "
         "freshness citation present on every answer; TTFT < 1.5s p95."),
    ])
    H(doc, "Capstone 5.2 - Deployment Eval Harness Productized", 3)
    BULLETS(doc, [
        ("Architecture: ",
         "a standalone harness: golden-set builder (mine samples from any corpus + SME labeling UI), "
         "error-taxonomy tracker, metric runner (Code 5.1), release-gate GitHub Action, and a "
         "report generator (per-release PDF: metrics, deltas, taxonomy burndown). Make it "
         "customer-configurable (YAML), because that is exactly how it gets reused across "
         "deployments."),
        ("Verification tests: ",
         "harness runs against two different mock apps (RAG app and agent app) unchanged; gate "
         "correctly blocks a regression and passes a tie; report includes per-error-class trends; "
         "golden-set rotation preserves distribution (stratification check)."),
    ])
    CALLOUT(
        doc,
        "FDE interviews are story interviews with code. Prepare three deployment narratives "
        "(build, incident, negotiation) in writing, each with numbers and a lesson. The take-home "
        "is won by evals, not features: candidates who ship a harness with tolerances beat "
        "candidates who ship more features with no eval every single time.",
        title="Portfolio packaging.",
    )


# =====================================================================
# ROLE 6: GENAI / AGENTIC AI ENGINEER
# =====================================================================
def build_genai(doc):
    H(doc, "Role Module 6 - GenAI / Agentic AI Engineer", 1, page_break_before=True)
    P(doc,
      "The GenAI/Agentic AI Engineer builds systems where an LLM plans, calls tools, and acts: "
      "single agents, supervisor-and-worker teams, and durable workflows. It is the fastest-growing "
      "role in this manual, the one where LangGraph appears as a hard requirement in a majority of "
      "senior postings, and the module where the canonical production code patterns of this textbook "
      "concentrate.")

    H(doc, "Module A - Labor Telemetry & Hiring Dynamics", 2)
    H(doc, "Quantitative Openings by Geography", 3)
    TABLE(
        doc,
        ["Geography", "Est. Active Openings", "Demand Character"],
        [
            ["United States", "4,000 - 6,000", "AI-native product companies (Sierra, Decagon, Clay, Replit) plus every enterprise building agents on platform teams; postings demand LangGraph/CrewAI/AutoGen by name."],
            ["Europe / EMEA", "1,500 - 2,200", "London/Berlin/Amsterdam startup belt; enterprise agent pilots in banking and telco."],
            ["India / APAC (GCC)", "5,000 - 8,000", "Explosive growth since late 2025; GCC agent-platform builds; postings 3-10 yrs experience, LangGraph often mandatory."],
            ["Global Remote", "800 - 1,200", "Agent-infra startups and devtools (LangChain, CrewAI ecosystem companies) hiring globally."],
        ],
        widths=[1.6, 1.5, 3.9],
        caption="Active openings estimate, September 2026",
    )

    H(doc, "Compensation Bands (Annual, Base Salary)", 3)
    TABLE(
        doc,
        ["Percentile", "US (USD)", "India (INR LPA)", "Europe (EUR)"],
        [
            ["25th", "$125,000", "12 - 16", "55,000 - 70,000"],
            ["50th (median)", "$160,000", "20 - 30", "85,000 - 100,000"],
            ["75th", "$195,000", "35 - 50", "115,000 - 135,000"],
            ["90th", "$240,000+", "60 - 80", "155,000+"],
        ],
        widths=[1.5, 1.8, 1.8, 1.9],
        caption="GenAI/Agentic base composites; US LangGraph/agentic listings span $80K-$300K with specialists to $500K TTC; India senior 35-60+ LPA",
    )
    CALLOUT(
        doc,
        "India bands (entry 5-14 LPA, mid 12-30, senior 35-60+, leaders 80+) come from Scaler, SCDL, "
        "and IIT KGP market studies; US ranges from the LangGraph job boards and Levels.fyi. Agent-"
        "infra devtools pay premium equity; enterprise platform teams pay premium cash.",
        title="Pay positioning.",
    )

    H(doc, "Top 15 Active Hiring Organizations", 3)
    TABLE(
        doc,
        ["Category", "Organizations"],
        [
            ["Agent-native startups", "Sierra, Decagon, Clay, Lindy, Cognition, Replit, Vellum, LangChain, CrewAI ecosystem companies"],
            ["Frontier labs (applied)", "OpenAI (Agents SDK ecosystem), Anthropic (MCP/Applied), Google (ADK/Gemini), Microsoft (AutoGen/Semantic Kernel)"],
            ["Enterprise GCCs", "JPMorganChase, Walmart Global Tech, Target India, Optum, Standard Chartered, LTIMindtree AI units"],
            ["Platform/consulting", "Accenture, Slalom, EPAM, Infosys Topaz, TCS, Wipro ai360"],
        ],
        widths=[2.2, 4.8],
        caption="Where GenAI/Agentic Engineers are being hired right now",
    )

    H(doc, "Experience Baseline & Transition Backgrounds", 3)
    BULLETS(doc, [
        ("Baseline: ",
         "2-5 years software engineering with shipped GenAI features; senior roles demand 2+ years "
         "of GenAI/agentic work specifically and LangGraph hands-on."),
        ("Backend / Fullstack -> GenAI: ",
         "dominant path; async Python, API design, and database skills transfer directly."),
        ("Data Scientist / ML Engineer -> GenAI: ",
         "adds modeling literacy; must acquire production engineering discipline (the harder "
         "direction)."),
        ("Automation Engineer -> GenAI: ",
         "workflow-thinking transfers; the Module 3 patterns (idempotency, HITL) are agent-adjacent."),
        ("QA / Test Engineer -> GenAI (evals track): ",
         "the eval-skill shortage makes this a real lateral entry: build eval harnesses, then move "
         "into building the agents they test."),
    ])

    H(doc, "Module B - Role Taxonomy & Daily Operational Reality", 2)
    H(doc, "Boundary Mapping", 3)
    TABLE(
        doc,
        ["Adjacent Role", "They Own", "GenAI/Agentic Owns", "Flashpoint"],
        [
            ["ML Engineer", "Training/fine-tuning models", "Orchestrating foundation models into systems with tools and memory", "Fine-tune vs better context engineering"],
            ["Data Engineer", "Pipelines and warehouse", "Retrieval corpora and agent-facing data contracts", "Agent needs a table that does not exist yet"],
            ["Product Engineer", "Application features", "The agentic feature surface: tools, guards, HITL, evals", "Agent autonomy level vs product risk appetite"],
            ["SRE / Platform", "Runtime and infra", "Agent-specific runtime semantics: state, replay, tracing, token budgets", "Who pages when the agent loops all night (token bill)"],
        ],
        widths=[1.5, 2.1, 2.2, 1.2],
        caption="Ownership boundaries",
    )

    H(doc, "Five Concrete Daily Operational Artifacts", 3)
    BULLETS(doc, [
        ("Agent-graph pull request: ",
         "a LangGraph state-machine change (new tool node, revised supervisor routing) with the eval "
         "suite diff and a token-cost delta estimate in the PR description."),
        ("Tool-schema definition: ",
         "a Pydantic-validated tool contract with descriptions tuned for the model, error-return "
         "semantics, and idempotency notes - reviewed like an API."),
        ("Agent trace review session: ",
         "a recurring pass over LangSmith/Langfuse traces of production runs, labeling failure "
         "modes (loop, bad routing, tool error mishandled) and filing fixes."),
        ("Eval report: ",
         "per-release metrics (task success rate, tool-call accuracy, cost per task, latency p95) on "
         "a scenario suite, with regressions annotated."),
        ("Human-in-the-loop breakpoint spec: ",
         "the written contract of which actions pause for approval, who approves, SLA for approval "
         "timeout, and what auto-happens on timeout."),
    ])

    H(doc, "Core Daily Toolchain", 3)
    TABLE(
        doc,
        ["Layer", "Tools Used Daily"],
        [
            ["IDE / editors", "VS Code / Cursor, LangGraph Studio for graph visualization and state inspection"],
            ["Frameworks", "LangGraph (primary), LangChain, CrewAI, AutoGen/AG2, OpenAI Agents SDK, Semantic Kernel"],
            ["Protocols", "MCP (Model Context Protocol) for tool servers, A2A for agent-to-agent, function calling"],
            ["Models", "OpenAI/Anthropic/Google APIs, open weights (Llama, Qwen) via vLLM/Ollama for self-hosted"],
            ["Retrieval", "Qdrant/pgvector/Milvus, hybrid search, rerankers (Module 6D pattern)"],
            ["Evals & tracing", "LangSmith, Langfuse, Arize Phoenix, Ragas, custom scenario suites"],
            ["Durable execution", "LangGraph Platform, Temporal for long-running agent workflows"],
            ["Runtime", "Docker/K8s, Redis (state/locks), Postgres (checkpoints), FastAPI"],
        ],
        widths=[1.5, 5.5],
        caption="Daily driver toolchain",
    )

    H(doc, "Module C - Exhaustive Technical Skills, Tools & Services Matrix", 2)
    TABLE(
        doc,
        ["Category", "Skill / Tool / Service", "Frequency"],
        [
            ["Core languages", "Python 3.11+ (asyncio, typing, pydantic v2)", "Critical"],
            ["Core languages", "TypeScript (Vercel AI SDK for agent UX)", "High"],
            ["Agentic frameworks", "LangGraph (StateGraph, checkpointer, interrupt(), subgraphs)", "Critical"],
            ["Agentic frameworks", "CrewAI (role-based teams), AutoGen/AG2 (conversation agents), OpenAI Agents SDK, Google ADK, Semantic Kernel", "High"],
            ["Protocols", "MCP server/client design, tool composition, A2A basics", "Emerging (fast-rising)"],
            ["Prompting & context", "Context engineering: write/select/compress/isolate; system prompt design; few-shot curation", "Critical"],
            ["Structured outputs", "Pydantic schemas, JSON-schema function calling, provider structured-output modes, repair loops", "Critical"],
            ["Retrieval", "Hybrid RAG (dense + BM25 + RRF + rerank), chunking strategy, metadata filters", "Critical"],
            ["Vector stores", "Qdrant, pgvector, Milvus, Pinecone, Weaviate; OpenSearch for enterprise hybrid", "High"],
            ["Memory", "Short-term (state), episodic (summarized history), long-term (vector/structured store), memory writes under policy", "High"],
            ["Multi-agent patterns", "Supervisor/worker, plan-and-execute, swarm/handoffs, hierarchical teams, subgraph composition", "Critical"],
            ["HITL", "interrupt() breakpoints, approval queues, timeout policy, state amendment and resume", "Critical"],
            ["Durable execution", "Checkpointers (Postgres/Redis), replay semantics, Temporal for cross-service workflows", "High"],
            ["Evals", "Scenario/task-success suites, trajectory evals, Ragas integration, cost/latency budgets", "Critical"],
            ["Observability", "LangSmith/Langfuse/Phoenix tracing, token accounting, trace-driven debugging", "Critical"],
            ["Serving", "vLLM for open-weight agents, streaming SSE/WS, backpressure", "High"],
            ["Security", "Tool least-privilege, injection defenses (Module 4D), memory poisoning defenses", "High"],
            ["Cost engineering", "Token budgets per task, caching, model-tiering per node, budget guards", "High"],
        ],
        widths=[1.7, 4.3, 1.0],
        caption="Skills matrix with market frequency",
    )

    H(doc, "Module D - Deep Technical Reference Manual (The Living Textbook)", 2)
    H(doc, "Deep Theory: Agents as State Machines", 3)
    P(doc,
      "An agent is not a chat loop - it is a state machine over a typed state, with edges that are "
      "either LLM routing decisions or hard-coded control. This framing is the entire interview "
      "vocabulary of 2026 agentic hiring.")
    CODE(doc, r"""
                        +--------------------+
   user msg ----------->|   SUPERVISOR node  |---------+
   (state.messages)     | (LLM routed)       |         | route: next worker
                        +---------+----------+         v
                                  |           +--------------------+
             route: respond       |           |  WORKER node(s)    |
                  v               |           |  - retriever       |
            +-------------+       +---------->|  - analyst (tools) |
            | WRITE node  |                   |  - operator (write)|
            | (final fmt) |                   +---------+----------+
            +-------------+                             | tool calls
                                                        v
                     interrupt() <---- HITL policy ---- [ APPROVAL GATE ]
                     (human review)                       (risky actions)
                                                        |
                                                        v
                     checkpointer saves state after EVERY node
                     (Postgres) => crash recovery + time travel
""", caption="Figure 6.1 - Supervisor/workflow agent as a typed state machine")
    BULLETS(doc, [
        ("Pattern selection: ",
         "single ReAct agent for < 5 tools and one decision-maker; supervisor/worker when tool count "
         "or context would exceed one model's comfort; plan-and-execute when tasks are long and "
         "replanning is rare; swarm/handoffs when expertise domains are cleanly separable; Temporal/"
         "durable graph when runs exceed minutes or must survive restarts."),
        ("State discipline: ",
         "state is typed (Pydantic/TypedDict), append-heavy (messages, artifacts), with explicit "
         "reducers; NEVER store derived conclusions without their evidence chain - you will need "
         "them for debugging and evals."),
        ("Context engineering (write/select/compress/isolate): ",
         "write down durable notes outside the window; select only task-relevant memory per step; "
         "compress history by summarization once it crosses ~60% of budget; isolate subtasks in "
         "subgraphs with their own windows. This is the modern successor to 'prompt engineering'."),
    ])

    H(doc, "Deep Theory: Context Rot, Lost-in-the-Middle, and Token Budgets", 3)
    BULLETS(doc, [
        ("Lost in the middle: ",
         "Liu et al. (2023) showed models retrieve best from the beginning and end of context, "
         "degrading in the middle. Countermeasures: put the current question at the end, most "
         "critical documents first/last, and cap context to the top reranked handful rather than "
         "'more is better'."),
        ("Context rot: ",
         "as conversations accumulate, effective reasoning quality decays (distraction, stale "
         "assumptions). Countermeasure: summarization compaction at a threshold, plus periodic "
         "'state reset with durable notes'."),
        ("Token budget runaway: ",
         "agents multiply tokens by every step; a 10-step loop with 8k context each costs 80k "
         "tokens for one task. Enforce per-node and per-run budgets; fail fast with a useful "
         "partial answer rather than an infinite loop."),
        ("Silent truncation: ",
         "max_tokens cut mid-tool-call produces JSON the parser 'helpfully' repairs into the wrong "
         "action. Detect stop_reason, never auto-repair across semantic boundaries."),
        ("Agent recursion loops: ",
         "the model retries a failing tool forever (RecursionLimit at 25 by default in LangGraph). "
         "Fix root cause: tool errors returned as structured data the model can act on, plus "
         "explicit retry budgets and loop-detection on state signatures."),
    ])

    H(doc, "Master Syllabus: What to Actually Study", 3)
    BULLETS(doc, [
        ("Frameworks (in order): ",
         "LangGraph docs end-to-end (StateGraph, reducers, checkpointer, interrupt, subgraphs, "
         "LangGraph Platform); OpenAI Agents SDK (handoffs, guardrails); CrewAI roleplay patterns; "
         "AutoGen conversation patterns; Semantic Kernel planners."),
        ("Protocols: ",
         "Model Context Protocol specification (tools, resources, prompts, sampling) - know how to "
         "expose and consume an MCP server; skim A2A for inter-agent interop."),
        ("Core papers: ",
         "Yao et al., 'ReAct: Synergizing Reasoning and Acting in Language Models' (2022); Shinn "
         "et al., 'Reflexion' (2023); Park et al., 'Generative Agents' (2023) for memory "
         "architectures; Wu et al., 'AutoGen' (2023); Schick et al., 'Toolformer' (2023); Lewis "
         "et al., RAG (2020); Liu et al., 'Lost in the Middle' (2023)."),
        ("Context engineering: ",
         "Anthropic's effective-context-engineering essays; LangChain's context-engineering "
         "write-ups (write/select/compress/isolate); LangChain State of Agent Engineering survey "
         "for the practitioner baseline."),
        ("Evals: ",
         "Ragas docs; LangSmith evaluation docs; Hamel Husain's error-analysis methodology; "
         "trajectory-vs-outcome eval debate in LangChain's blog."),
        ("Reliability: ",
         "Kleppmann (again) for state; Temporal docs for durable execution semantics; the "
         "token-bucket pattern (Module 1D) for API discipline."),
    ])

    H(doc, "Canonical Code Pattern 6.1 - Advanced Hybrid RAG (Dense + BM25 + RRF + Cross-Encoder)", 3)
    P(doc,
      "The single most requested production pattern in GenAI interviews. Full pipeline: dual "
      "retrieval, Reciprocal Rank Fusion, cross-encoder re-ranking, citation-preserving answer "
      "synthesis. (Cloud-adapted variant: Module 2D; failure modes: Module 6D end.)")
    CODE(doc, r'''
from __future__ import annotations

import logging
import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

import numpy as np

logger = logging.getLogger("genai.hybridrag")


@dataclass(frozen=True)
class Chunk:
    doc_id: str
    chunk_id: str
    text: str
    embedding: np.ndarray


@dataclass(frozen=True)
class RetrievedChunk:
    chunk: Chunk
    fused_score: float
    rerank_score: float | None = None


class HybridRetriever:
    """Dense (cosine) + sparse (BM25) retrieval fused with Reciprocal Rank
    Fusion, re-ranked by a cross-encoder. Component-based so each stage is
    testable and replaceable (swap Qdrant/pgvector/ES without touching logic).
    """

    RRF_K = 60          # standard constant from Cormack et al. 2009
    DENSE_CANDIDATES = 50
    SPARSE_CANDIDATES = 50
    RERANK_TOP = 25
    FINAL_TOP = 6

    def __init__(self, chunks: list[Chunk], query_embedder, bm25_index,
                 cross_encoder) -> None:
        if not chunks:
            raise ValueError("corpus must be non-empty")
        self.chunks = chunks
        self.embed = query_embedder
        self.bm25 = bm25_index          # object with .search(text, k) -> ids
        self.cross_encoder = cross_encoder  # callable(list[(q, doc)]) -> scores

    # ---------- stage 1: dense ----------
    def _dense_search(self, query: str) -> list[str]:
        q = np.asarray(self.embed(query), dtype=np.float32)
        norms = np.linalg.norm(self._matrix(), axis=1) * (np.linalg.norm(q) or 1.0)
        sims = (self._matrix() @ q) / norms
        top = np.argsort(-sims)[: self.DENSE_CANDIDATES]
        return [self.chunks[i].chunk_id for i in top]

    def _matrix(self) -> np.ndarray:
        if not hasattr(self, "_emb_matrix"):
            self._emb_matrix = np.vstack([c.embedding for c in self.chunks])
        return self._emb_matrix

    # ---------- stage 2: sparse ----------
    def _sparse_search(self, query: str) -> list[str]:
        return self.bm25.search(query, k=self.SPARSE_CANDIDATES)

    # ---------- stage 3: fusion ----------
    @staticmethod
    def _rrf(*ranked: list[str]) -> dict[str, float]:
        fused: dict[str, float] = defaultdict(float)
        for lst in ranked:
            for rank, cid in enumerate(lst):
                fused[cid] += 1.0 / (HybridRetriever.RRF_K + rank + 1)
        return dict(fused)

    # ---------- stage 4: cross-encoder rerank ----------
    def _rerank(self, query: str, candidates: list[str]) -> list[RetrievedChunk]:
        by_id = {c.chunk_id: c for c in self.chunks}
        pool = [by_id[c] for c in candidates[: self.RERANK_TOP]]
        pairs = [(query, c.text) for c in pool]
        scores = self.cross_encoder(pairs)
        ranked = sorted(zip(pool, scores), key=lambda t: -t[1])
        return [RetrievedChunk(chunk=c, fused_score=0.0, rerank_score=float(s))
                for c, s in ranked[: self.FINAL_TOP]]

    def retrieve(self, query: str) -> list[RetrievedChunk]:
        try:
            dense = self._dense_search(query)
        except Exception:
            logger.exception("dense retrieval failed; degrading to sparse")
            dense = []
        try:
            sparse = self._sparse_search(query)
        except Exception:
            logger.exception("sparse retrieval failed; degrading to dense")
            sparse = []
        if not dense and not sparse:
            logger.warning("both retrievers failed for query")
            return []
        fused = self._rrf(dense, sparse)
        candidates = [c for c, _ in sorted(fused.items(), key=lambda kv: -kv[1])]
        return self._rerank(query, candidates)


def build_context(results: Iterable[RetrievedChunk], max_chars: int = 6000) -> str:
    """Citation-preserving context block with per-chunk budgeting."""
    parts, used = [], 0
    for r in results:
        piece = f"[{r.chunk.doc_id}#{r.chunk.chunk_id}] {r.chunk.text}"
        if used + len(piece) > max_chars:
            logger.info("context budget reached at %d chunks", len(parts))
            break
        parts.append(piece)
        used += len(piece)
    return "\n\n".join(parts)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # wire a real corpus + models here; the class contract is the examinable part
    print("HybridRetriever: dense + BM25 -> RRF -> cross-encoder -> top-k")
''', caption="Code 6.1 - hybrid_rag.py: dense + sparse + RRF + cross-encoder rerank")

    H(doc, "Canonical Code Pattern 6.2 - LangGraph Supervisor Workflow with HITL Approval", 3)
    P(doc,
      "The canonical stateful multi-agent supervisor with human-in-the-loop breakpoints: typed "
      "state, supervisor routing, worker nodes, an interrupt() approval gate before any risky "
      "action, Postgres checkpointer for durability, and loop protection. This is the pattern to "
      "reproduce whiteboard-fresh.")
    CODE(doc, r'''
from __future__ import annotations

import logging
import operator
from typing import Annotated, Any, Literal, TypedDict

from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt, Command
from pydantic import BaseModel, Field

logger = logging.getLogger("genai.supervisor")


class AgentState(TypedDict):
    """Typed, append-heavy state. Every node reads/writes this dict."""
    messages: Annotated[list[AnyMessage], operator.add]   # reducer: append
    ticket: dict[str, Any]
    findings: Annotated[list[dict], operator.add]
    pending_action: dict[str, Any] | None                 # set by operator agent
    loop_guard: int


class Route(BaseModel):
    """Structured supervisor decision - never parse free text for routing."""
    next: Literal["retriever", "analyst", "operator", "respond", "end"] = Field(
        description="The next node to execute.")
    rationale: str = Field(description="One sentence why.")


def make_llm() -> ChatOpenAI:
    return ChatOpenAI(model="gpt-4o", temperature=0, max_retries=2)


SUPERVISOR_PROMPT = SystemMessage(content=(
    "You route a support-automation workflow. Workers: retriever (KB lookup), "
    "analyst (diagnosis), operator (state-changing actions - requires approval). "
    "Prefer retriever first, analyst second, operator ONLY for remediation. "
    "respond when the user's question is answered; end when nothing is left."))


def supervisor_node(state: AgentState) -> dict:
    state["loop_guard"] += 1
    if state["loop_guard"] > 12:                       # recursion protection
        logger.error("loop guard tripped; forcing end ticket=%s", state["ticket"].get("id"))
        return {"next": "end"}
    llm = make_llm().with_structured_output(Route)
    route = llm.invoke([SUPERVISOR_PROMPT, *state["messages"]])
    logger.info("supervisor -> %s (%s)", route.next, route.rationale)
    return {"messages": [HumanMessage(content=f"[route] {route.next}")], "next": route.next}


def retriever_node(state: AgentState) -> dict:
    kb_hits = fake_kb_search(state["ticket"]["subject"])     # hybrid RAG 6.1 lives here
    return {"findings": [{"source": "kb", "hits": kb_hits}]}


def analyst_node(state: AgentState) -> dict:
    summary = make_llm().invoke(
        [SystemMessage(content="Diagnose from findings. Cite sources."),
         *[HumanMessage(content=f"finding: {f}") for f in state["findings"]]])
    return {"messages": [summary]}


def operator_node(state: AgentState) -> dict:
    """Proposes a state-changing action and pauses for human approval."""
    action = {"tool": "refund_customer", "args": {"amount": 45.0, "currency": "USD"}}
    decision = interrupt({                     # graph PAUSES here (checkpointer
        "prompt": "Approve this action?",      # persists state) until resumed
        "action": action,
        "findings_count": len(state["findings"]),
    })
    if decision.get("approved"):
        result = fake_execute(action)          # audited, idempotent execution
        return {"messages": [HumanMessage(content=f"[action done] {result}")],
                "pending_action": None}
    return {"messages": [HumanMessage(content="[action rejected] propose alternative")],
            "pending_action": None}


def respond_node(state: AgentState) -> dict:
    answer = make_llm().invoke(
        [SystemMessage(content="Answer the user from findings; cite sources."),
         *state["messages"]])
    return {"messages": [answer], "next": "end"}


def route_after_supervisor(state: AgentState) -> Literal[
        "retriever", "analyst", "operator", "respond", "__end__"]:
    return {"retriever": "retriever", "analyst": "analyst", "operator": "operator",
            "respond": "respond", "end": END}[state["next"]]


def fake_kb_search(q: str) -> list[str]:
    return ["KB-1182: refunds auto-approve under $50"]
def fake_execute(action: dict) -> str:
    return f"{action['tool']} ok"


def build_graph():
    g = StateGraph(AgentState)
    g.add_node("supervisor", supervisor_node)
    g.add_node("retriever", retriever_node)
    g.add_node("analyst", analyst_node)
    g.add_node("operator", operator_node)
    g.add_node("respond", respond_node)
    g.add_edge(START, "supervisor")
    g.add_conditional_edges("supervisor", route_after_supervisor)
    for w in ("retriever", "analyst", "operator"):
        g.add_edge(w, "supervisor")            # workers report back
    g.add_edge("respond", END)
    return g.compile(checkpointer=PostgresSaver.from_conn_string(
        "postgresql://app:app@localhost:5432/agents"))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = build_graph()
    cfg = {"configurable": {"thread_id": "ticket-77120"}}
    app.invoke({"messages": [HumanMessage(content="Refund order 4521; item arrived damaged.")],
                "ticket": {"id": 77120, "subject": "damaged item refund"},
                "findings": [], "pending_action": None, "loop_guard": 0}, cfg)
    # resume the interrupted approval from a human queue:
    app.invoke(Command(resume={"approved": True}), cfg)
''', caption="Code 6.2 - supervisor_graph.py: typed state, routing, interrupt() HITL, checkpointer")

    H(doc, "Canonical Code Pattern 6.3 - Deterministic Tool-Calling with Pydantic Validation", 3)
    P(doc,
      "Structured output with validation and a bounded repair loop: the difference between a demo "
      "and a system. The model proposes; Pydantic disposes; one repair round-trip is budgeted; "
      "failures become structured tool errors the model can act on.")
    CODE(doc, r'''
from __future__ import annotations

import json
import logging
from typing import Literal, Type, TypeVar

from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger("genai.tools")

T = TypeVar("T", bound=BaseModel)


class TransferIntent(BaseModel):
    """The ONLY shape a transfer may take. Extra fields are forbidden."""
    action: Literal["internal_transfer"]
    from_account: str = Field(pattern=r"^ACC-[0-9]{10}$")
    to_account: str = Field(pattern=r"^ACC-[0-9]{10}$")
    amount_minor: int = Field(gt=0, le=2_000_000, description="cents; max $20k")
    currency: Literal["USD", "EUR", "INR"]
    reference: str = Field(min_length=4, max_length=140)
    idempotency_key: str = Field(min_length=16, max_length=64)


TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "internal_transfer",
        "description": "Move funds between accounts of the SAME customer. "
                       "Hard limits: <= $20,000 per transfer.",
        "parameters": TransferIntent.model_json_schema(),
    },
}


class ToolRuntime:
    """Executes validated tool calls with an audit log and no free-text paths."""

    def __init__(self, ledger: dict[str, str]) -> None:
        self.ledger = ledger          # idempotency_key -> result

    def execute(self, name: str, raw_args: str) -> dict:
        if name != "internal_transfer":
            return {"status": "error", "code": "unknown_tool", "message": f"{name} not allowed"}
        try:
            intent = TransferIntent.model_validate_json(raw_args)
        except ValidationError as exc:
            # structured error the MODEL can read and self-correct from
            return {"status": "validation_error",
                    "errors": [{"loc": list(e["loc"]), "msg": e["msg"]}
                               for e in exc.errors()]}
        if intent.idempotency_key in self.ledger:
            logger.info("replay suppressed key=%s", intent.idempotency_key[:8])
            return {"status": "ok", "result": self.ledger[intent.idempotency_key]}
        result = f"transferred {intent.amount_minor} {intent.currency} " \
                 f"{intent.from_account}->{intent.to_account}"
        self.ledger[intent.idempotency_key] = result
        logger.info("executed %s ref=%s", intent.action, intent.reference)
        return {"status": "ok", "result": result}


def extract_structured(prompt_to_model: str, model_fn, schema: Type[T],
                       max_repairs: int = 1) -> T:
    """Ask for JSON, validate, and (once) feed validation errors back for
    repair. Never silently coerce: bad data must fail loudly."""
    messages = [{"role": "user", "content": prompt_to_model}]
    for attempt in range(max_repairs + 1):
        raw = model_fn(messages)                       # returns JSON string
        try:
            return schema.model_validate_json(raw)
        except ValidationError as exc:
            if attempt == max_repairs:
                logger.error("structured extraction failed after %d attempts: %s",
                             attempt + 1, exc.errors())
                raise
            messages.append({"role": "assistant", "content": raw})
            messages.append({"role": "user", "content": json.dumps({
                "error": "schema_validation_failed",
                "issues": exc.errors(),
                "instruction": "Return ONLY corrected JSON matching the schema."})})
    raise AssertionError("unreachable")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ledger: dict[str, str] = {}

    def mock_model(messages) -> str:
        if len(messages) == 1:   # first pass: deliberately wrong field
            return json.dumps({"action": "internal_transfer", "from_account": "ACC-123",
                               "to_account": "ACC-0000000004", "amount_minor": 4500,
                               "currency": "USD", "reference": "INV-2026-42",
                               "idempotency_key": "a1b2c3d4e5f60718"})
        return json.dumps({"action": "internal_transfer", "from_account": "ACC-0000000001",
                           "to_account": "ACC-0000000004", "amount_minor": 4500,
                           "currency": "USD", "reference": "INV-2026-42",
                           "idempotency_key": "a1b2c3d4e5f60718"})

    intent = extract_structured("transfer 45.00 USD from ACC-0000000001 "
                                "to ACC-0000000004 ref INV-2026-42",
                                mock_model, TransferIntent)
    runtime = ToolRuntime(ledger)
    print(runtime.execute("internal_transfer", intent.model_dump_json()))
    print(runtime.execute("internal_transfer", intent.model_dump_json()))  # replay -> same result
''', caption="Code 6.3 - tool_calling.py: schema-validated tool execution with repair + idempotency")

    H(doc, "Failure Modes & Edge Cases (GenAI/Agentic)", 3)
    BULLETS(doc, [
        ("Agent recursion loops: ",
         "a tool that returns errors as prose invites infinite retries (RecursionLimit 25 by default "
         "is a cost bomb at scale). Return structured, actionable tool errors; add loop detection on "
         "state signatures; cap retries per tool."),
        ("Context window rot: ",
         "long-horizon agents degrade as history grows; stale assumptions poison later steps. "
         "Summarize-and-reset at budget thresholds; keep durable notes outside the window."),
        ("Lost-in-the-middle degradation: ",
         "critical tool outputs buried mid-context get ignored. Order context by importance (start "
         "and end), and re-state the active goal at the tail of the prompt."),
        ("Token budget runaways: ",
         "per-node budgets plus a per-run budget guard; when the guard trips, return the best "
         "partial answer with an explicit 'incomplete' status instead of burning the night."),
        ("Silent truncation: ",
         "stop_reason 'max_tokens' mid-JSON corrupts tool calls; auto-repair can flip semantics. "
         "Check stop reasons, fail loudly, and continue the completion explicitly."),
        ("State bleed across sessions: ",
         "a checkpointer thread reused across users leaks context (and PII). Enforce per-session "
         "thread ids, and scrub state on session close."),
        ("Memory poisoning: ",
         "attacker-controlled content written into long-term memory persists across sessions. "
         "Quarantine memory writes behind policy (Module 4D), scan before persist, keep an audit "
         "and a wipe tool."),
        ("Vector index staleness: ",
         "embeddings outlive their sources; the agent argues from deleted policy. Content-hash "
         "invalidation, freshness metadata, and 'as of' dates on retrieval."),
        ("Non-determinism in tests: ",
         "temperature > 0 flakes your CI. Pin temperature 0 for decisioning nodes, seed where "
         "supported, and eval on scenario suites rather than exact-string asserts."),
        ("Multi-tenant state confusion: ",
         "one shared knowledge base with per-tenant docs and no filters is a data leak. Tenant-id "
         "metadata filters enforced at the store layer, plus negative tests (Module 2 capstone)."),
    ])

    H(doc, "Module E - Interview Mechanics & Hidden Hiring Patterns", 2)
    H(doc, "ATS Screening Triggers", 3)
    BULLETS(doc, [
        ("Must-appear keywords: ",
         "LangGraph (or named alternative), multi-agent, tool calling / function calling, RAG, "
         "structured outputs, evals, guardrails, HITL/human-in-the-loop, token/cost, Python, "
         "async."),
        ("Phrasing that ranks: ",
         "'built a supervisor agent resolving 3,000 support tickets/week at 62% full resolution, "
         "$0.11 average token cost, HITL on refunds'; 'eval-gated releases: task success +5pt "
         "with cost flat'."),
        ("Immediate-rejection anti-patterns: ",
         "'prompt engineering enthusiast' with no state/eval vocabulary; frameworks listed with "
         "zero deployed artifact; no cost awareness anywhere; claims of 'autonomous agents' with "
         "no failure-mode story."),
    ])

    H(doc, "Interview Loop Breakdown", 3)
    TABLE(
        doc,
        ["Round", "Format", "What Is Actually Being Tested"],
        [
            ["Recruiter screen (30m)", "Portfolio walk", "One deployed agent story with numbers; repo/artifact proof"],
            ["Coding screen (60-75m)", "Live Python (async, pydantic, API)", "Production Python quality, not LeetCode: state, typing, error handling"],
            ["Agent design (60m)", "Design a multi-agent system on LangGraph", "Pattern selection, state design, HITL, budgets, failure modes"],
            ["Evals & ops (45m)", "Eval design + trace debugging", "Task-success metrics, regression gates, cost control, observability"],
            ["Behavioral (45m)", "Ownership stories", "Shipping under ambiguity; cross-team influence; honest post-mortems"],
        ],
        widths=[1.5, 1.9, 3.6],
        caption="Typical loop: 4-5 rounds",
    )

    H(doc, "Five Real Interview Questions with Model Answers", 3)
    NUMBERS(doc, [
        ("Design a multi-agent system for enterprise customer support: triage, retrieve, resolve, refund. Where do humans stay in the loop? ",
         "Model answer: supervisor graph (Code 6.2): triage classifies with structured output; "
         "retriever uses hybrid RAG with citations; analyst diagnoses; operator executes refunds - "
         "HITL interrupt() above $50 or any legal-sensitive action; respond synthesizes with "
         "citations. Durable checkpointer per ticket thread; budgets per run; eval suite per node "
         "plus end-to-end task success. Humans approve money, not text."),
        ("Your agent's token cost is 40x your estimate. Diagnose systematically. ",
         "Model answer: instrument per-node token accounting (LangSmith/Langfuse) - usually one "
         "node (retrieval stuffing) or a loop dominates; check recursion (loop guard), context "
         "growth per step (compaction), duplicate tool calls (cache + deterministic tools), and "
         "model tiering (small model for routing). Then set budgets: per-node caps, per-run caps, "
         "and alerting. Re-evaluate quality after each cut - cost work without evals is blind."),
        ("How do you prevent an agent from taking actions a user never asked for? ",
         "Model answer: authority design: tools scoped to the ticket's intent (structured intent "
         "object carried in state), allow-list policy engine per action class, HITL gates on "
         "state-changing tools, canary tokens for injection detection (Module 4D), and eval "
         "adversarial cases ('agent did something unrequested') in the release gate. Least "
         "privilege is the only robust layer; prompting is not a security boundary."),
        ("Explain how you'd implement memory for a personal-assistant agent without poisoning it. ",
         "Model answer: three tiers: working state (typed graph state), episodic summaries "
         "(per-thread compaction), long-term store (vector + structured) written only via policy: "
         "source-attributed, confidence-tagged, schema-constrained memories; scan writes for "
         "injection/PII (Module 4D); TTL and decay; user-visible memory inspector with edit/delete; "
         "retrieval scoped per query with provenance. Eval memory regressions (right recall, no "
         "hallucinated facts)."),
        ("When do you choose Temporal over a LangGraph checkpointer alone? ",
         "Model answer: LangGraph checkpointing covers single-graph state recovery and HITL resume "
         "within one process boundary; Temporal wins when the workflow spans services, must survive "
         "multi-day human delays with SLA timers, needs versioned workflow code migration, or "
         "requires per-activity retry/heartbeat semantics. Common enterprise shape: Temporal wraps "
         "the durable business workflow and calls agent graphs as activities; graphs stay "
         "single-responsibility."),
    ])

    H(doc, "Module F - Production Capstone Specifications", 2)
    H(doc, "Capstone 6.1 - Deep-Research Agent with Citation-Grade Output", 3)
    BULLETS(doc, [
        ("Architecture: ",
         "planner -> parallel researcher subgraphs (web + local corpus via Code 6.1 hybrid RAG) -> "
         "fact-aggregator with claim-evidence ledger (every claim keyed to sources) -> writer with "
         "citation enforcement -> critic node (faithfulness check, Code 5.1 judge) -> deliver. "
         "Checkpointer for resumability; per-run token budget guard; LangSmith tracing end to end."),
        ("Verification tests: ",
         "on a 50-topic suite: citation precision >= 0.9 (every claim resolvable), zero uncited "
         "factual assertions on sampled audits, budget guard trips correctly on an adversarial "
         "topic, resume-after-crash produces identical final state, cost per report reported and "
         "trending."),
    ])
    H(doc, "Capstone 6.2 - Multi-Agent Operations Copilot with Durable HITL", 3)
    BULLETS(doc, [
        ("Architecture: ",
         "support-ops copilot (Code 6.2 supervisor + analyst + operator) wired to a mock ITSM/CRM: "
         "Postgres checkpointer, approval queue UI (Slack-compatible webhook), SLA timers on "
         "approvals (auto-escalate on timeout), audit log hash-chained, red-team suite (Module 4 "
         "capstone) gating releases, and Ragas-based scenario evals (Code 5.1) in CI."),
        ("Verification tests: ",
         "task-success >= 85% on 200 scripted scenarios; zero unapproved state changes under an "
         "injection campaign; approval timeout escalates per SLA; replay of any historical run "
         "reproduces decisions from the audit log; p95 end-to-end < 45s for non-approval flows."),
    ])
    CALLOUT(
        doc,
        "Agentic hiring rewards the operator mindset: traces read like an ICU chart, budgets like a "
        "finance sheet, evals like a release gate. Your portfolio should show one agent system with "
        "all three disciplines attached - then the specific framework is a detail.",
        title="Portfolio packaging.",
    )
