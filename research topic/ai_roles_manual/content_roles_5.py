# -*- coding: utf-8 -*-
"""Role module 7: AI Solutions Engineer."""
from docx_builder import H, P, BULLETS, NUMBERS, CODE, CALLOUT, TABLE, PAGEBREAK


def build_solutions(doc):
    H(doc, "Role Module 7 - AI Solutions Engineer", 1, page_break_before=True)
    P(doc,
      "The AI Solutions Engineer is the technical trust-builder in the sales and adoption motion: "
      "discovery, demos, POCs, reference architectures, security-questionnaire support, and the "
      "translation layer between what the product does and what the enterprise needs. It is the "
      "highest-communication band role in this manual and the classic exit for support engineers, "
      "pre-sales SEs, and data engineers with client instincts.")

    H(doc, "Module A - Labor Telemetry & Hiring Dynamics", 2)
    H(doc, "Quantitative Openings by Geography", 3)
    TABLE(
        doc,
        ["Geography", "Est. Active Openings", "Demand Character"],
        [
            ["United States", "2,000 - 3,000", "Data/AI platforms (Databricks, Snowflake, Confluent, Elastic, Pinecone) and AI-native vendors (OpenAI, Anthropic, Glean, Writer, Moveworks) expanding go-to-market engineering."],
            ["Europe / EMEA", "800 - 1,200", "Enterprise software GTM in London/Amsterdam/Munich; data-residency expertise is the differentiator."],
            ["India / APAC (GCC)", "1,500 - 2,500", "GCC pre-sales and solutions pods for global products; APAC field coverage from Singapore/Bengaluru."],
            ["Global Remote", "400 - 700", "DevTools and API-first AI companies with remote solutions teams."],
        ],
        widths=[1.6, 1.5, 3.9],
        caption="Active openings estimate, September 2026",
    )

    H(doc, "Compensation Bands (Annual, Base + OTE)", 3)
    TABLE(
        doc,
        ["Percentile", "US Base (USD)", "US OTE (USD)", "India (INR LPA)"],
        [
            ["25th", "$115,000", "$130,000 - $145,000", "18 - 24"],
            ["50th (median)", "$150,000", "$170,000 - $190,000", "28 - 40"],
            ["75th", "$185,000", "$210,000 - $235,000", "48 - 65"],
            ["90th", "$220,000", "$250,000 - $300,000", "70 - 95"],
        ],
        widths=[1.5, 1.7, 1.9, 1.7],
        caption="AI Solutions Engineer composites. Anchors: ZipRecruiter US average ~$123,284 (skews junior); FDE Academy range $123K-$185K; platform vendors pay above AI-native startups at base",
    )
    CALLOUT(
        doc,
        "OTE (on-target earnings) adds 20-40% variable on top of base in vendor roles; internal "
        "solutions roles (deploying for your own company's teams) pay base-only but carry equity. "
        "Enterprise AI-platform vendors (Databricks/Snowflake tier) run the richest plans in the "
        "category.",
        title="Pay positioning.",
    )

    H(doc, "Top 15 Active Hiring Organizations", 3)
    TABLE(
        doc,
        ["Category", "Organizations"],
        [
            ["Frontier labs (Solutions Eng)", "OpenAI, Anthropic, Google (Gemini GTM), Cohere (Solutions Architect)"],
            ["Data & AI platforms", "Databricks, Snowflake, Confluent, Elastic, MongoDB, Pinecone, Weaviate"],
            ["AI-native vendors", "Glean, Writer, Moveworks, Jasper, Cresta, Vectara"],
            ["Enterprise / GCC", "Accenture Song, Infosys Topaz pre-sales, Standard Chartered, Microsoft partner orgs"],
        ],
        widths=[2.2, 4.8],
        caption="Where AI Solutions Engineers are being hired right now",
    )

    H(doc, "Experience Baseline & Transition Backgrounds", 3)
    BULLETS(doc, [
        ("Baseline: ",
         "3-6 years mixing engineering with client exposure; demos and writing samples are screened "
         "harder than code."),
        ("Pre-sales SE / Sales Engineer -> AI Solutions: ",
         "natural upgrade; add GenAI architecture and demo-craft depth."),
        ("Data Engineer / Analytics Engineer -> AI Solutions: ",
         "strong for platform vendors; add LLM-stack breadth and narrative skills."),
        ("Support Engineer / Solutions Support -> AI Solutions: ",
         "the classic IT-exit path: deep product fluency + troubleshooting discipline converts to "
         "technical trust; add demo development and reference-architecture writing."),
        ("Fullstack Engineer -> AI Solutions: ",
         "works for API-first vendors where the demo IS the product; requires willingness to move "
         "from IC-building to influence-selling."),
    ])

    H(doc, "Module B - Role Taxonomy & Daily Operational Reality", 2)
    H(doc, "Boundary Mapping", 3)
    TABLE(
        doc,
        ["Adjacent Role", "They Own", "AI Solutions Owns", "Flashpoint"],
        [
            ["Account Executive", "Commercial deal, pricing", "Technical validation and architecture truth", "The AE who promised a feature at 4:59pm"],
            ["Forward Deployed Engineer", "Post-sale in-tenant deployment", "Pre-sale technical motion: demo, POC, RFP, security review support", "The handoff: POC promises vs deployable reality"],
            ["Product Management", "Roadmap", "Aggregate field requirements and competitive intel", "One customer's 'must-have' vs the platform"],
            ["Core Engineering", "Product code", "Demo/POC code, integration examples, reference architectures", "POC code quality - it always leaks into prod somewhere"],
        ],
        widths=[1.5, 2.1, 2.2, 1.2],
        caption="Ownership boundaries",
    )

    H(doc, "Five Concrete Daily Operational Artifacts", 3)
    BULLETS(doc, [
        ("Technical validation (POC) plan: ",
         "a two-page doc: customer use case, success criteria (measurable), data requirements, "
         "timeline (2-4 weeks), and explicit non-goals - signed by the customer champion."),
        ("Reference architecture document: ",
         "a per-industry architecture (with diagram) covering identity, data residency, retrieval "
         "topology, guardrails, and cost model, maintained as versioned collateral."),
        ("Demo script with fallbacks: ",
         "a rehearsed narrative with live data paths, recorded fallback for every live step, and "
         "the objection-handling appendix ('what if it hallucinates?')."),
        ("RFP/security-questionnaire response: ",
         "technical sections answered with evidence links (SOC 2 scope, ZDR terms, eval results), "
         "not adjectives - the artifact that unblocks procurement."),
        ("POC retrospective: ",
         "a written handoff to AE/CS: what was proven with numbers, what was not, risks, and the "
         "production plan - the document that converts POCs to contracts."),
    ])

    H(doc, "Core Daily Toolchain", 3)
    TABLE(
        doc,
        ["Layer", "Tools Used Daily"],
        [
            ["Demo build", "Python/FastAPI, TypeScript (Next.js + Vercel AI SDK), Streamlit for fast POCs"],
            ["Platform demos", "Vendor consoles (Bedrock/AI Foundry/Vertex), Databricks/Snowflake notebooks, Pinecone/Qdrant clouds"],
            ["Architecture", "Excalidraw/draw.io/Figma for diagrams, Notion/Confluence for collateral, Pitch/Slides"],
            ["Discovery & CRM", "Gong/Chorus call reviews, Salesforce/HubSpot hygiene, Slack customer channels"],
            ["Evals in POCs", "Ragas quick-evals, golden-set mini-harnesses, latency/cost meters"],
            ["Security support", "SOC 2 reports, trust centers, CAIQ/SIG questionnaires, DPIA templates"],
        ],
        widths=[1.5, 5.5],
        caption="Daily driver toolchain",
    )

    H(doc, "Module C - Exhaustive Technical Skills, Tools & Services Matrix", 2)
    TABLE(
        doc,
        ["Category", "Skill / Tool / Service", "Frequency"],
        [
            ["Core engineering", "Python + TypeScript for demo/POC construction", "Critical"],
            ["Core engineering", "REST/SDK integration patterns; API design fluency to answer 'how would we integrate?'", "Critical"],
            ["AI architecture", "RAG, agents, fine-tuning trade-offs - able to draw and defend any of the three in 10 minutes", "Critical"],
            ["Cloud AI platforms", "Bedrock + Azure AI Foundry + Vertex AI at demo depth (one at production depth)", "Critical"],
            ["Data platforms", "Databricks/Snowflake integration patterns; vector databases (Pinecone, Qdrant, pgvector)", "High"],
            ["Security & compliance", "SOC 2 / ISO 27001 basics, GDPR/HIPAA data-handling patterns, SSO (SAML/OIDC), RBAC, data residency", "Critical"],
            ["Evaluation", "POC success-criteria design; mini eval harnesses that make accuracy a number, not a vibe", "High"],
            ["Cost modeling", "Usage-based pricing models, token-cost estimation per customer workload", "High"],
            ["Integration patterns", "SSO, webhooks, CRM/ITSM connectors, data-sync strategies, multi-tenant isolation options", "High"],
            ["Communication", "Discovery questioning, technical storytelling, written one-pagers, executive demos", "Critical"],
            ["Competitive positioning", "Build-vs-buy analysis, migration paths, honest competitive comparisons", "High"],
            ["Observability", "Demo-to-production observability story (tracing, cost dashboards)", "Emerging"],
            ["Agentic depth", "Agent POCs with guardrails and HITL as demos, plus honest autonomy guidance", "Emerging (fast-rising)"],
        ],
        widths=[1.7, 4.3, 1.0],
        caption="Skills matrix with market frequency",
    )

    H(doc, "Module D - Deep Technical Reference Manual (The Living Textbook)", 2)
    H(doc, "Deep Theory: The POC Success-Criteria Contract", 3)
    P(doc,
      "Pilot purgatory - POCs that never end - is solved with a written contract before any code: "
      "success criteria must be measurable, customer-owned, and bounded in time.")
    CODE(doc, r"""
POC CONTRACT TEMPLATE (fill before writing code)
------------------------------------------------
Use case:        "Draft claim adjuster summaries from FNOL packets"
Success metric:  >= 80% of 50 real packets produce summaries rated
                 'usable with < 2 min edit' by 2 adjusters (blind)
Data:            50 anonymized packets (their formats!), provided by day 3
Timeline:        3 weeks; weekly checkpoint with named sponsor
Non-goals:       no ERP write-back, no fine-tuning, no multi-language
Cost ceiling:    < $500 total inference during POC (metered + reported)
Exit rule:       metric met -> production scoping doc in week 4;
                 metric missed -> written findings + revisit trigger
""", caption="Figure 7.1 - The POC contract: the artifact that ends pilot purgatory")
    BULLETS(doc, [
        ("Demo-to-production gap management: ",
         "every demo is built on production-shaped data (their formats, their noise). The sentence "
         "'this is a curated demo' must never need saying - and the honest version ('here is exactly "
         "what changes with your data and why') is the trust-builder."),
        ("Build-vs-buy framing: ",
         "the reference architecture includes the honest build option with its TCO (people, evals, "
         "guardrails, maintenance) vs your platform. Credibility on build-vs-buy is what makes the "
         "buy decision safe."),
        ("Security-questionnaire mastery: ",
         "know the difference between SOC 2 Type I/II, ISO 27001 scope, GDPR DPA terms, HIPAA BAA "
         "availability, and data-residency guarantees for YOUR product cold. Procurement stalls die "
         "here."),
    ])

    H(doc, "Master Syllabus: What to Actually Study", 3)
    BULLETS(doc, [
        ("Architecture patterns: ",
         "this manual's Modules 2D and 6D (managed RAG and agents) at whiteboard depth; be able to "
         "draw the hybrid-RAG and supervisor-agent diagrams from memory."),
        ("Evaluation: ",
         "Module 5D eval-first methodology - the POC plan's success criteria borrow its golden-set "
         "discipline in miniature."),
        ("Security/compliance: ",
         "SOC 2 and ISO 27001 overviews, GDPR data-processing terms, HIPAA BAA basics; your "
         "company's trust center documents verbatim."),
        ("Comms craft: ",
         "'The Mom Test' for discovery questioning; 'Made to Stick' for demo narratives; vigorous "
         "practice writing one-page docs - the FDE one-pager standard (Module 5B) applies."),
        ("Market: ",
         "your top 3 competitors' architectures and pricing pages cold; Gartner/Forrester AI "
         "platform notes for the enterprise vocabulary."),
    ])

    H(doc, "Canonical Code Pattern 7.1 - Usage Metering and Cost-Attribution Middleware", 3)
    P(doc,
      "The Solutions Engineer's engineering signature: make cost a first-class, per-customer, "
      "per-feature number. This middleware meters tokens per tenant/feature, enforces quota "
      "contracts, and produces the usage report that turns POCs into pricing conversations. (The "
      "token-bucket admission control it composes with lives in Module 1D pattern 1.2.)")
    CODE(doc, r'''
from __future__ import annotations

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Awaitable, Callable

from fastapi import HTTPException, Request, Response

logger = logging.getLogger("solutions.metering")


@dataclass
class UsageRecord:
    tenant_id: str
    feature: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    cost_usd: float


class PriceBook:
    """Per-model pricing in USD per 1M tokens (input, output)."""

    def __init__(self, prices: dict[str, tuple[float, float]]) -> None:
        self.prices = prices

    def cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        if model not in self.prices:
            raise KeyError(f"unpriced model: {model}")
        pin, pout = self.prices[model]
        return (input_tokens * pin + output_tokens * pout) / 1_000_000


class UsageLedger:
    """In-memory accumulator; swap for Postgres/ClickHouse in production."""

    def __init__(self) -> None:
        self._by_tenant: dict[str, list[UsageRecord]] = defaultdict(list)

    def add(self, rec: UsageRecord) -> None:
        self._by_tenant[rec.tenant_id].append(rec)

    def report(self, tenant_id: str) -> dict:
        recs = self._by_tenant.get(tenant_id, [])
        by_feature: dict[str, dict] = defaultdict(lambda: {"calls": 0, "tokens": 0, "usd": 0.0})
        total_usd = 0.0
        for r in recs:
            f = by_feature[r.feature]
            f["calls"] += 1
            f["tokens"] += r.input_tokens + r.output_tokens
            f["usd"] += r.cost_usd
            total_usd += r.cost_usd
        return {"tenant": tenant_id, "total_usd": round(total_usd, 4),
                "by_feature": {k: {"calls": v["calls"], "tokens": v["tokens"],
                                   "usd": round(v["usd"], 4)}
                               for k, v in by_feature.items()}}


class QuotaExceeded(HTTPException):
    def __init__(self, tenant_id: str, limit_usd: float) -> None:
        super().__init__(status_code=429,
                         detail=f"tenant {tenant_id} exceeded monthly budget ${limit_usd}")


def metering_middleware(price_book: PriceBook, ledger: UsageLedger,
                        budget_usd: float = 500.0):
    """Attaches metering to every AI call: records tokens/cost/latency per
    tenant+feature, enforces the POC budget contract (Figure 7.1)."""

    async def middleware(request: Request,
                         call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        tenant = request.headers.get("X-Tenant-Id", "unknown")
        feature = request.headers.get("X-Feature", "unclassified")
        started = time.monotonic()
        response = await call_next(request)
        usage = getattr(response, "headers", {}).get("X-Token-Usage")  # set by AI layer
        if usage:
            model, tin, tout = (usage.split(":") + ["0", "0", "0"])[:3]
            cost = price_book.cost(model, int(tin), int(tout))
            ledger.add(UsageRecord(tenant_id=tenant, feature=feature, model=model,
                                   input_tokens=int(tin), output_tokens=int(tout),
                                   latency_ms=(time.monotonic() - started) * 1000,
                                   cost_usd=cost))
            spent = sum(r.cost_usd for r in ledger._by_tenant[tenant])
            if spent > budget_usd:
                logger.warning("tenant=%s over budget: $%.2f", tenant, spent)
                raise QuotaExceeded(tenant, budget_usd)
        return response
    return middleware


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    prices = PriceBook({"gpt-4o": (2.50, 10.00), "gpt-4o-mini": (0.15, 0.60)})
    ledger = UsageLedger()
    ledger.add(UsageRecord("acme", "summarize", "gpt-4o", 12000, 800, 900.0,
                           prices.cost("gpt-4o", 12000, 800)))
    ledger.add(UsageRecord("acme", "classify", "gpt-4o-mini", 300000, 100, 150.0,
                           prices.cost("gpt-4o-mini", 300000, 100)))
    import json
    print(json.dumps(ledger.report("acme"), indent=2))
''', caption="Code 7.1 - metering.py: per-tenant, per-feature token/cost attribution with budget enforcement")

    H(doc, "Failure Modes & Edge Cases (AI Solutions)", 3)
    BULLETS(doc, [
        ("Demo overfit: ",
         "the demo corpus is hand-picked; the customer's data behaves differently. Always demo on "
         "production-shaped data and say what is synthetic."),
        ("Unquantified accuracy promises: ",
         "'95% accurate' without a measurement definition becomes a contractual liability. Promise "
         "measured metrics on defined suites, or nothing."),
        ("Compliance discovered late: ",
         "security review in week 6 of a 6-week deal kills it. Raise SOC 2/residency/BAA in the "
         "first technical call; carry the evidence."),
        ("Pilot purgatory: ",
         "no exit rule means the POC drifts; use the Figure 7.1 contract with a named sponsor and "
         "a decision date."),
        ("Scope mismatch after handoff: ",
         "FDE inherits a POC whose shortcuts (hardcoded tenant, no evals) become production debt. "
         "Write the POC-to-production delta list before the demo, not after."),
        ("The 'yes engineer' trap: ",
         "the AE promises; you are expected to nod. Technical honesty is the product; escalate "
         "instead of committing to impossible timelines - credibility compounds."),
        ("Cost surprises in POC: ",
         "an unmetered POC runs a $4k bill and an awkward conversation. Meter from call one (Code "
         "7.1) and report usage weekly."),
        ("Multi-tenant demo leaks: ",
         "demo tenants share a vector store and one customer's documents surface in another's "
         "demo. Tenant-filter everything, even in demos - it is also the security demo."),
    ])

    H(doc, "Module E - Interview Mechanics & Hidden Hiring Patterns", 2)
    H(doc, "ATS Screening Triggers", 3)
    BULLETS(doc, [
        ("Must-appear keywords: ",
         "solutions engineer / pre-sales, POC / proof of concept, RFP, demo, discovery, reference "
         "architecture, RAG/agents (architectural fluency), SSO/RBAC, SOC 2 or GDPR, Python or "
         "TypeScript."),
        ("Phrasing that ranks: ",
         "'ran 25 technical validations with a 60% conversion to contract'; 'wrote the reference "
         "architecture used by the field team'; 'unblocked procurement by owning the security "
         "questionnaire end to end'."),
        ("Immediate-rejection anti-patterns: ",
         "pure-builder resume with zero customer signal; long code blocks in lieu of artifacts; "
         "no demo link or writing sample; vague 'worked with stakeholders' without a named motion."),
    ])

    H(doc, "Interview Loop Breakdown", 3)
    TABLE(
        doc,
        ["Round", "Format", "What Is Actually Being Tested"],
        [
            ["Recruiter + HM (45m)", "Story + motion fit", "Client instincts, curiosity, revenue empathy"],
            ["Technical screen (60m)", "Architecture Q&A + light coding", "RAG/agent architecture fluency; integration-pattern instincts"],
            ["Demo round (45-60m)", "Prepare and deliver a demo of the company's product", "Narrative control, recovery from failure, objection handling"],
            ["Discovery role-play (45m)", "Run a mock discovery call", "Question quality, technical honesty, qualification instincts"],
            ["Panel / exec (45m)", "Present a POC plan or retrospective", "Written thinking, business framing, calibration of promises"],
        ],
        widths=[1.5, 1.9, 3.6],
        caption="Typical loop: 4-5 rounds; writing sample often requested before onsite",
    )

    H(doc, "Five Real Interview Questions with Model Answers", 3)
    NUMBERS(doc, [
        ("Run discovery for a hospital chain that wants an AI assistant over clinical guidelines. What do you ask, and what are the red flags? ",
         "Model answer: quantify the workflow (who answers guideline questions today, how often, "
         "error cost), the data (where do guidelines live, versions, update cadence), integration "
         "(EHR in scope?), and constraints (PHI - is a BAA needed? on-prem or cloud with BAAs?), "
         "plus the decision process (who signs, timeline, budget). Red flags: 'just a chatbot' "
         "framing with no named clinical owner, PHI handling undecided, no measurable success "
         "concept, and procurement unknown. Close with a proposed POC contract sketch."),
        ("Design a POC for a bank that wants to check regulatory compliance of marketing copy. ",
         "Model answer: Figure 7.1 contract: 100 real historical copies (compliance-approved vs "
         "flagged), success = recall on violations >= 90% at FPR <= 5% as judged by their compliance "
         "team on a blind set; retrieval over their rule corpus with citations to the exact rule; "
         "no write-back; cost ceiling metered; 3 weeks with weekly checkpoints; exit rule "
         "pre-agreed. Mention the eval design explicitly - this is the differentiator."),
        ("The customer says 'your model hallucinated' in a pilot review. Your move? ",
         "Model answer: thank, capture, reproduce: take the example with its trace, classify the "
         "failure live if possible (retrieval miss / grounding / stale source / genuinely out of "
         "scope); show the measurement plan: this class is 3 of 50 in the suite; the fix lands in "
         "the next release with before/after numbers; and where the metric stands overall. Never "
         "argue adjectives - move the conversation to the number."),
        ("How do you position build-vs-buy when the customer's engineers are eager to build? ",
         "Model answer: make the build path real and costed: 2 engineers, eval harness, guardrails, "
         "model-ops, and the maintenance curve as models change - show the honest TCO; then show "
         "what buying buys: time-to-value, maintained evals/compliance, and their engineers "
         "redeployed to the differentiating layer. Give them the credit for architectural control "
         "(APIs, export, residency options). The close: a phased path where they own the parts "
         "that are truly theirs."),
        ("Your POC hit its accuracy target but the deal stalls. Diagnose. ",
         "Model answer: POC success is necessary but not sufficient - diagnose the buying "
         "mechanics: was there a named economic buyer and success owner from day one (the contract "
         "requires it)? Is the retrospective in business terms (hours saved, risk retired) or "
         "metrics? Is security/procurement unblocked? Propose the production scoping doc with a "
         "phased rollout and a commercial path; if the champion went quiet, requalify honestly "
         "rather than discounting."),
    ])

    H(doc, "Module F - Production Capstone Specifications", 2)
    H(doc, "Capstone 7.1 - Industry Reference Architecture Library with Working POC", 3)
    BULLETS(doc, [
        ("Architecture: ",
         "three industry reference architectures (healthcare with BAA/HIPAA constraints, financial "
         "services with audit/residency, retail with seasonal scale) - each a versioned doc + "
         "diagram + cost model + security-questionnaire answer pack, backed by ONE working POC "
         "codebase (hybrid RAG + guardrails + Code 7.1 metering) that can be re-skinned per "
         "industry via configuration."),
        ("Verification tests: ",
         "each architecture doc passes a 'stranger test' (a peer deploys the POC from the doc alone "
         "in < 1 day); cost model reconciles with metered usage within 10%; security pack answers "
         "a standard CAIQ section without improvisation."),
    ])
    H(doc, "Capstone 7.2 - Demo Platform with Synthetic Multi-Tenant Data", 3)
    BULLETS(doc, [
        ("Architecture: ",
         "a scripted demo environment: three synthetic tenants with distinct data shapes (contracts, "
         "claims, tickets), tenant-isolated retrieval, a Next.js + Vercel AI SDK demo UI with "
         "streaming, pre-recorded fallback for every live path, objection-handling appendix, and "
         "per-demo usage metering so every demo doubles as a pricing conversation."),
        ("Verification tests: ",
         "zero cross-tenant leakage under adversarial demo prompts; every live step has a tested "
         "fallback (kill-switch drill); demo runs end-to-end in < 8 minutes with a cost report "
         "generated per run; reset script restores clean state in < 5 minutes."),
    ])
    CALLOUT(
        doc,
        "Solutions hiring reads artifacts like an investment committee: one great reference "
        "architecture doc, one recorded demo with graceful failure recovery, and one POC "
        "retrospective with numbers outweigh a full GitHub of toy projects. Writing quality is "
        "the technical skill here.",
        title="Portfolio packaging.",
    )
