# -*- coding: utf-8 -*-
"""Role module 2: Cloud AI Engineer."""
from docx_builder import H, P, BULLETS, CODE, CALLOUT, TABLE, PAGEBREAK


def build_cloudai(doc):
    H(doc, "Role Module 2 - Cloud AI Engineer", 1, page_break_before=True)
    P(doc,
      "The Cloud AI Engineer productionizes generative AI on managed cloud platforms: AWS Bedrock, "
      "Azure AI Foundry / Azure OpenAI, and Google Vertex AI. The role is platform-first - model "
      "selection, provisioning economics, private networking, guardrails, and cost control - and it is "
      "the natural landing zone for DevOps and data engineers moving into AI.")

    H(doc, "Module A - Labor Telemetry & Hiring Dynamics", 2)
    H(doc, "Quantitative Openings by Geography", 3)
    TABLE(
        doc,
        ["Geography", "Est. Active Openings", "Demand Character"],
        [
            ["United States", "3,500 - 4,500", "Consulting delivery (AWS ProServe, Microsoft MCS, Slalom, EPAM) plus enterprise platform teams; cleared/federal variants add a distinct pocket."],
            ["Europe / EMEA", "1,200 - 1,800", "Data-residency-driven; Azure AI Foundry over-represents because EU enterprises are Microsoft estates."],
            ["India / APAC (GCC)", "4,000 - 6,000", "Largest absolute pool; hyperscaler partner ecosystems (Infosys Topaz, TCS, Wipro, Cognizant, HCLTech) plus GCC platform teams at banks and retailers."],
            ["Global Remote", "600 - 900", "AI-native startups (Writer, Moveworks, Pecan AI, Glean) hiring platform engineers on any cloud."],
        ],
        widths=[1.6, 1.5, 3.9],
        caption="Active openings estimate, September 2026",
    )

    H(doc, "Compensation Bands (Annual, Base Salary)", 3)
    TABLE(
        doc,
        ["Percentile", "US (USD)", "India (INR LPA)", "Europe (EUR)"],
        [
            ["25th", "$118,000", "14 - 18", "60,000 - 70,000"],
            ["50th (median)", "$150,000", "22 - 30", "80,000 - 95,000"],
            ["75th", "$185,000", "38 - 50", "105,000 - 120,000"],
            ["90th", "$225,000", "60 - 80", "140,000+"],
        ],
        widths=[1.5, 1.8, 1.8, 1.9],
        caption="Cloud AI Engineer base composites; US TTC typically +15-25% (bonus, RSUs)",
    )
    CALLOUT(
        doc,
        "Glassdoor places US total pay at roughly $190,000 for the title. Certification leverage is "
        "real and measurable here: AWS Certified Machine Learning Engineer - Associate, Azure AI "
        "Engineer (AI-102), and Google Professional ML Engineer keywords measurably raise recruiter "
        "contact rates - unlike most certifications elsewhere in AI.",
        title="Pay positioning.",
    )

    H(doc, "Top 15 Active Hiring Organizations", 3)
    TABLE(
        doc,
        ["Category", "Organizations"],
        [
            ["Hyperscalers & consultancies", "AWS Professional Services, Microsoft (MCS / Azure AI), Google Cloud Consulting, Accenture, Slalom, EPAM, Globant"],
            ["AI-native startups (Series B-D)", "Writer, Moveworks, Pecan AI, Cohere (deployment engineering), Fireworks AI, Glean (platform)"],
            ["Enterprise GCCs (India/APAC)", "JPMorganChase, Standard Chartered, Wells Fargo, Walmart Global Tech, Target India, Lowe's India, Optum"],
            ["Federally adjacent", "Peraton, Booz Allen Hamilton, Leidos (cleared Cloud AI Engineer postings)"],
        ],
        widths=[2.2, 4.8],
        caption="Where Cloud AI Engineers are being hired right now",
    )

    H(doc, "Experience Baseline & Transition Backgrounds", 3)
    BULLETS(doc, [
        ("Baseline: ",
         "4-6 years total engineering, of which 1-2 hands-on with a managed AI platform; "
         "government-style postings accept Bachelor's + 5 or Associate's + 7 years."),
        ("DevOps / Platform -> Cloud AI: ",
         "the dominant transition; IaC, IAM, and networking transfer 1:1 - add model APIs, RAG, and "
         "cost management."),
        ("Data Engineer -> Cloud AI: ",
         "pipeline and warehouse skills flow into retrieval engineering; add streaming inference and "
         "guardrails."),
        ("Backend Engineer -> Cloud AI: ",
         "API design transfers; must add cloud identity (STS, managed identities), private endpoints, "
         "and token economics."),
        ("IT Infrastructure / Service Desk -> Cloud AI: ",
         "longest path of the seven roles (12-24 months) but real: certification -> IaC portfolio -> "
         "platform-automation role -> AI workloads on that platform."),
    ])

    H(doc, "Module B - Role Taxonomy & Daily Operational Reality", 2)
    H(doc, "Boundary Mapping", 3)
    TABLE(
        doc,
        ["Adjacent Role", "They Own", "Cloud AI Owns", "Flashpoint"],
        [
            ["ML Engineer", "Custom training, fine-tuning jobs, model optimization", "Managed-API integration, provisioning, private networking, guardrail configuration", "Fine-tune vs retrieve-and-prompt decision"],
            ["Data Engineering", "Warehouse/lakehouse tables, data quality", "Retrieval pipelines over that data (chunking, embedding, index refresh)", "Who pays when a re-embed rips through 50M documents"],
            ["DevOps / SRE", "Cluster runtime, CI/CD", "AI-specific runtime: model gateways, autoscaling endpoints, token budgets", "p95 inference latency ownership during an incident"],
            ["Solutions Architect", "Customer-facing architecture patterns", "Hands-on in-tenant implementation of AI workloads", "Reference architectures that ignore cost reality"],
        ],
        widths=[1.5, 2.1, 2.2, 1.2],
        caption="Ownership boundaries",
    )

    H(doc, "Five Concrete Daily Operational Artifacts", 3)
    BULLETS(doc, [
        ("Terraform pull request for AI infrastructure: ",
         "a reviewed change creating a Bedrock knowledge base + OpenSearch Serverless collection, or an "
         "Azure AI Foundry project with private endpoints and a content-filter policy, with a cost-delta "
         "estimate in the PR description."),
        ("Model-selection memo: ",
         "a two-page comparison (quality on the golden set, p95 latency, per-1M-token cost, data "
         "residency, provider SLA) recommending one model with a stated kill-switch."),
        ("Provisioned-throughput utilization report: ",
         "weekly PTU/CRU utilization vs peak demand, driving a resize recommendation before the "
         "monthly FinOps review."),
        ("Guardrail / content-filter configuration: ",
         "versioned configuration of denied topics, PII masking entities, and word filters, mapped to "
         "the specific test cases that justify each rule."),
        ("Deployment runbook with rollback: ",
         "step-by-step private deployment (VPC-only endpoints, no internet route) including failure "
         "points, smoke tests, and exact rollback commands."),
    ])

    H(doc, "Core Daily Toolchain", 3)
    TABLE(
        doc,
        ["Layer", "Tools Used Daily"],
        [
            ["IDE / editors", "VS Code (+ Copilot), Cloud Shell / Cloud9, Jupyter for evals"],
            ["CLI / IaC", "AWS CLI, az CLI, gcloud, Terraform, CloudFormation / Bicep"],
            ["AWS AI", "Bedrock (Converse API, Agents, Knowledge Bases, Guardrails), SageMaker endpoints, Bedrock Agents SDK"],
            ["Azure AI", "Azure AI Foundry, Azure OpenAI (PTU + PAYG), AI Search, Document Intelligence, Content Safety"],
            ["GCP AI", "Vertex AI (Gemini, Model Garden, endpoints, pipelines), RAG Engine"],
            ["Serving / runtimes", "Managed inference endpoints, Lambda + API Gateway, Step Functions, Cloud Run"],
            ["Identity & network", "IAM / Entra ID, VPC endpoints / Private Link, KMS, SCPs"],
            ["Observability", "CloudWatch, Application Insights, model-invocation logs, LangSmith/Langfuse traces"],
            ["Cost", "AWS Cost Explorer, Azure Cost Management, per-tenant token metering"],
        ],
        widths=[1.5, 5.5],
        caption="Daily driver toolchain",
    )

    H(doc, "Module C - Exhaustive Technical Skills, Tools & Services Matrix", 2)
    TABLE(
        doc,
        ["Category", "Skill / Tool / Service", "Frequency"],
        [
            ["Core languages", "Python 3.11+ (boto3, azure-ai-* SDKs, google-genai SDK, tenacity)", "Critical"],
            ["Core languages", "TypeScript for streaming chat clients and edge integration", "High"],
            ["Core languages", "Terraform (module design, state management, policy-as-code)", "Critical"],
            ["AWS Bedrock", "Converse API, model catalog, cross-region inference profiles, Guardrails, Knowledge Bases, Agents, provisioned CRUs", "Critical"],
            ["AWS SageMaker", "JumpStart, real-time/serverless endpoints, target-tracking autoscaling, inference pipelines", "High"],
            ["Azure AI Foundry", "Azure OpenAI deployments (PTU vs PAYG, global vs regional), content filters, prompt flow, AI Search hybrid retrieval", "Critical"],
            ["GCP Vertex AI", "Gemini API, Model Garden, Vertex AI Search / RAG Engine, Pipelines, context caching", "High"],
            ["Retrieval on cloud", "OpenSearch k-NN, pgvector on RDS, AI Search (vector + BM25 + semantic ranker), Bedrock Knowledge Bases internals", "Critical"],
            ["LLMOps", "MLflow, LangSmith / Langfuse tracing, prompt versioning, A/B prompt deployment", "High"],
            ["Security & governance", "IAM least privilege for model access, KMS/CMK, VPC-only inference, data-residency configuration, audit logging", "Critical"],
            ["Cost engineering", "PTU/CRU math, provisioned vs on-demand break-even, semantic/prompt caching, Batch APIs for offline work", "High"],
            ["Networking", "Private endpoints, private DNS for AI services, egress control, multi-VPC quota topology", "High"],
            ["Observability", "Model invocation logging, token/cost dashboards, latency SLOs (TTFT, p95), throttling alarms", "High"],
            ["Agentic (shared)", "Function calling on cloud models, Bedrock AgentCore, AI Foundry agents, Step Functions durable orchestration", "Emerging"],
            ["Optimization", "ONNX Runtime, quantization awareness for self-hosted endpoints, GPU selection arithmetic", "Emerging"],
        ],
        widths=[1.7, 4.3, 1.0],
        caption="Skills matrix with market frequency (Critical / High / Emerging)",
    )

    H(doc, "Module D - Deep Technical Reference Manual (The Living Textbook)", 2)
    H(doc, "Deep Theory: Provisioning Economics (PTU / CRU Math)", 3)
    P(doc,
      "Cloud AI interviews increasingly test whether you can reason about managed-throughput "
      "economics. The model below is provider-agnostic; constants change, the reasoning does not.")
    CODE(doc, r"""
Provisioned units (Azure PTU, Bedrock CRUs) buy GUARANTEED capacity:
    units_needed = ceil(peak_tokens_per_minute / throughput_per_unit)
where throughput_per_unit depends on model + input/output mix (vendors publish
tables; GPT-4o-class deployments span ~2,500-25,000 input TPM per PTU).

Break-even reasoning:
    monthly_cost_payg  = tokens_monthly * price_per_1M / 1e6
    monthly_cost_prov  = units * unit_price * 730h
    Choose provisioned when:  cost_prov <= cost_payg  AND  utilization
    (used_capacity / bought_capacity) stays > ~0.55 across the month.
    Otherwise: buy on-demand, absorb throttling risk, and keep non-interactive
    traffic on Batch APIs (roughly half price) to protect interactive headroom.

Latency budget arithmetic (per agent turn):
    TTFT target        ~ 0.5-1.0 s   (user-perceived snappiness)
    completion stream  ~ 60-120 tok/s
    RAG adds           ~ 30 ms embed + 50 ms vector search + 200 ms rerank
    Guardrails add     ~ 50-150 ms per pass - budget BOTH directions
""", caption="Figure 2.1 - Provisioned throughput and latency budget arithmetic")

    H(doc, "Deep Theory: Retrieval on Managed Platforms", 3)
    P(doc,
      "Managed knowledge bases (Bedrock Knowledge Bases, Vertex RAG Engine, Azure AI Search) all "
      "reduce to the same pipeline: parse -> chunk -> embed -> index -> hybrid retrieve -> rank. The "
      "engineer's judgment lives in four decisions:")
    BULLETS(doc, [
        ("Chunking: ",
         "recursive character splitting (500-800 tokens, 10-15% overlap) is the default; semantic "
         "chunking (split at embedding-similarity boundaries) helps long-form prose; structure-aware "
         "splitting (Markdown headers, code blocks) is mandatory for technical corpora. Late chunking "
         "(embed the full document, pool per chunk) improves long-context embedding fidelity."),
        ("Hybrid retrieval: ",
         "dense (embeddings) + sparse (BM25) fused with Reciprocal Rank Fusion (k=60) beats either "
         "alone on enterprise corpora full of SKUs, error codes, and proper nouns. Azure AI Search "
         "exposes this natively (vector + keyword + semantic ranker)."),
        ("Reranking: ",
         "a cross-encoder (Cohere Rerank, Bedrock rerank, bge-reranker) over the top ~50 fused "
         "candidates, returning top 5-8, is the single highest-ROI quality upgrade in managed RAG."),
        ("Index freshness: ",
         "define a content-hash-based sync (docs changed -> re-chunk -> re-embed -> upsert by ID) plus "
         "a staleness SLO (e.g., 15 minutes for policy corpora). 'The sync job ran' is not a design."),
    ])

    H(doc, "Master Syllabus: What to Actually Study", 3)
    BULLETS(doc, [
        ("AWS: ",
         "Bedrock User Guide (Converse API, Guardrails, Knowledge Bases, Agents), Bedrock pricing and "
         "provisioned-throughput docs, SageMaker endpoint autoscaling, Well-Architected ML Lens, and "
         "the AWS ML Engineer - Associate exam outline."),
        ("Azure: ",
         "Azure AI Foundry docs (hubs/projects, deployments, content filters), Azure OpenAI PTU "
         "reservation guidance, AI Search hybrid + semantic ranking docs, AI-102 exam skills outline."),
        ("GCP: ",
         "Vertex AI docs (Gemini API, endpoints, context caching), Vertex AI Search, Professional ML "
         "Engineer certification syllabus."),
        ("Cross-cutting: ",
         "OWASP Top 10 for LLM Applications (2025) for guardrail design; NIST AI RMF for the "
         "governance vocabulary enterprise panels expect; provider model cards and licensing terms."),
        ("Papers: ",
         "Gao et al., 'Retrieval-Augmented Generation for Knowledge-Intensive NLP' (NeurIPS 2020); "
         "Robertson & Zaragoza, 'The Probabilistic Relevance Framework: BM25 and Beyond'; Cormack "
         "et al., 'Reciprocal Rank Fusion Outperforms Condorcet and Individual Rank Learning Methods' "
         "(SIGIR 2009)."),
    ])

    H(doc, "Canonical Code Pattern 2.1 - Bedrock Hybrid RAG with Guardrails and Retry Discipline", 3)
    P(doc,
      "The production shape of a Bedrock retrieval turn: client-side hybrid retrieval (dense k-NN + "
      "BM25 via OpenSearch) fused with RRF, cross-encoder rerank, guardrail attachment, Converse API "
      "streaming, bounded retries with full jitter (pattern 1.2), and structured token metering. The "
      "fuller Hybrid RAG deep-dive lives in Module 6D; this is the platform-adapted version.")
    CODE(doc, r'''
from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass
from typing import Iterator

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

logger = logging.getLogger("cloudai.rag")


@dataclass(frozen=True)
class RagConfig:
    """Immutable per-tenant configuration; construct from SSM/env at boot."""
    guardrail_id: str
    guardrail_version: str = "DRAFT"
    model_id: str = "anthropic.claude-3-7-sonnet-20250219-v1:0"
    max_tokens: int = 1024
    top_k: int = 50
    rerank_k: int = 6
    rrf_k: int = 60
    max_retries: int = 5
    base_delay: float = 0.4


class BedrockRagService:
    """Hybrid retrieval + guardrailed generation on AWS Bedrock.

    Retrieval: OpenSearch hybrid (knn dense + bm25), fused with Reciprocal
    Rank Fusion, then Bedrock rerank. Generation: Converse API with the
    tenant's guardrail attached. Throttles are retried with capped
    exponential backoff and full jitter - the application owns retries
    because botocore's internal retry budget hides sustained throttling.
    """

    def __init__(self, cfg: RagConfig, opensearch_client) -> None:
        self.cfg = cfg
        self.os = opensearch_client
        self.bedrock = boto3.client(
            "bedrock-runtime",
            config=Config(retries={"max_attempts": 0}),
        )
        self.bedrock_mgmt = boto3.client("bedrock-runtime")

    # ---------------------------------------------------------------- retrieval
    def _rrf_fuse(self, *ranked_lists: list[str]) -> list[str]:
        """Reciprocal Rank Fusion across ranked id lists (Cormack 2009)."""
        scores: dict[str, float] = {}
        for lst in ranked_lists:
            for rank, doc_id in enumerate(lst):
                scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (self.cfg.rrf_k + rank + 1)
        return [d for d, _ in sorted(scores.items(), key=lambda kv: -kv[1])][: self.cfg.top_k]

    def retrieve(self, index: str, query: str, query_embedding: list[float]) -> list[dict]:
        knn_body = {"size": self.cfg.top_k,
                    "query": {"knn": {"embedding": {"vector": query_embedding, "k": self.cfg.top_k}}}}
        bm25_body = {"size": self.cfg.top_k, "query": {"bool": {"should": [
            {"match": {"text": {"query": query}}},
            {"match_phrase": {"text": {"query": query, "slop": 2}}},
        ]}}}
        dense_ids = [h["_id"] for h in self.os.search(index=index, body=knn_body)["hits"]["hits"]]
        sparse_ids = [h["_id"] for h in self.os.search(index=index, body=bm25_body)["hits"]["hits"]]
        fused = self._rrf_fuse(dense_ids, sparse_ids)
        return self._rerank(index, query, fused)

    def _rerank(self, index: str, query: str, doc_ids: list[str]) -> list[dict]:
        if not doc_ids:
            return []
        docs = self.os.mget(index=index, body={"ids": doc_ids})["docs"]
        try:
            resp = self.bedrock_mgmt.rerank(
                queries=[{"textQuery": {"text": query}}],
                sources=[{"inlineDocumentSource": {
                    "type": "TEXT",
                    "textDocument": {"text": d["_source"]["text"][:4000]},
                }} for d in docs],
                rerankConfiguration={"modelArn": "amazon.rerank-v1:0"},
                topN=self.cfg.rerank_k,
            )
            order = [r["index"] for r in resp["results"]]
        except ClientError:
            logger.exception("rerank unavailable; falling back to RRF order")
            order = list(range(min(len(docs), self.cfg.rerank_k)))
        return [docs[i] for i in order]

    # ---------------------------------------------------------------- generation
    def _call_with_backoff(self, **converse_kwargs) -> dict:
        last_exc: Exception | None = None
        for attempt in range(self.cfg.max_retries):
            try:
                return self.bedrock.converse(**converse_kwargs)
            except ClientError as exc:
                code = exc.response.get("Error", {}).get("Code", "")
                if code not in ("ThrottlingException", "ServiceUnavailableException",
                                "ModelStreamErrorException"):
                    raise
                last_exc = exc
                cap = min(20.0, self.cfg.base_delay * (2 ** attempt))
                delay = random.uniform(0.0, cap)  # full jitter
                logger.warning("bedrock throttled (attempt %d), jitter sleep %.2fs",
                               attempt + 1, delay)
                time.sleep(delay)
        raise RuntimeError("bedrock exhausted retries") from last_exc

    def answer(self, tenant_id: str, question: str, context_docs: list[dict]) -> str:
        context = "\n\n".join(
            f"[{d['_source'].get('doc_id', 'doc')}] {d['_source']['text']}" for d in context_docs)
        system = [{"text":
                   "You are an enterprise assistant. Answer ONLY from the provided context. "
                   "Cite bracketed doc ids. If the context is insufficient, say so."}]
        messages = [{"role": "user",
                     "content": [{"text": f"Context:\n{context}\n\nQuestion: {question}"}]}]
        try:
            resp = self._call_with_backoff(
                modelId=self.cfg.model_id,
                system=system,
                messages=messages,
                guardrailConfig={"guardrailIdentifier": self.cfg.guardrail_id,
                                 "guardrailVersion": self.cfg.guardrail_version,
                                 "trace": "ENABLED"},
                inferenceConfig={"maxTokens": self.cfg.max_tokens, "temperature": 0.2},
            )
        except RuntimeError as exc:
            logger.error("generation failed for tenant=%s: %s", tenant_id, exc)
            return "The assistant is temporarily unavailable. Please retry shortly."
        usage = resp.get("usage", {})
        stop = resp.get("stopReason", "")
        logger.info("tenant=%s in=%d out=%d docs=%d stop=%s", tenant_id,
                    usage.get("inputTokens", -1), usage.get("outputTokens", -1),
                    len(context_docs), stop)
        if stop == "max_tokens":
            logger.warning("tenant=%s output truncated by token budget", tenant_id)
        return "".join(b.get("text", "") for b in
                       resp.get("output", {}).get("message", {}).get("content", []))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("wire your OpenSearch client and RagConfig from SSM; see capstone 2.1")
''', caption="Code 2.1 - bedrock_rag.py: hybrid retrieve -> rerank -> guardrailed Converse call")

    H(doc, "Failure Modes & Edge Cases (Cloud AI)", 3)
    BULLETS(doc, [
        ("Throttling at the worst moment: ",
         "on-demand capacity throttles exactly at peak. Provision the p95, overflow to on-demand, and "
         "queue non-interactive traffic into Batch APIs (about half price) to preserve interactive "
         "headroom."),
        ("PTU overprovisioning drift: ",
         "capacity bought for a launch spike decays to ~20% utilization - a silent six-figure annual "
         "waste. Instrument utilization weekly, resize on evidence, keep a resize runbook with owner "
         "and review date."),
        ("Private-endpoint DNS failures: ",
         "VPC-only deployments break on custom resolvers and split-horizon DNS; the symptom is "
         "intermittent timeouts from specific subnets. Test resolution from every subnet and pin "
         "service names in private hosted zones."),
        ("Knowledge-base staleness: ",
         "managed KB sync is a cron, not a guarantee - deleted policies keep answering until the next "
         "sync. Add content-hash freshness checks and an answer-level 'as of' date."),
        ("Guardrail over-blocking: ",
         "aggressive filters reject legitimate clinical/financial phrasing. Measure block rate per "
         "intent in production and maintain a red-team + benign green-team regression set for every "
         "filter change."),
        ("Cross-region inference surprise: ",
         "cross-region profiles route requests to other geographies - a residency violation for some "
         "tenants. Pin regional profiles per data-residency class and record it in the tenant design "
         "document."),
        ("Cost runaway from embeddings: ",
         "re-embedding 50M chunks is a real invoice line. Precompute cost before re-indexing, cache "
         "chunks by content hash, and schedule re-embeds in off-peak batch windows."),
        ("Silent truncation: ",
         "outputs hit max_tokens mid-sentence and finish with stop reason 'max_tokens' - users see a "
         "confident cut-off. Log the stop reason, alert on its rate, and surface continuations "
         "explicitly."),
    ])

    H(doc, "Module E - Interview Mechanics & Hidden Hiring Patterns", 2)
    H(doc, "ATS Screening Triggers", 3)
    BULLETS(doc, [
        ("Must-appear keywords: ",
         "Bedrock or Azure OpenAI or Vertex AI (at least one by name), Terraform/IaC, IAM/KMS, RAG, "
         "guardrails or content filters, cost optimization, Python, CI/CD."),
        ("Phrasing that ranks: ",
         "'deployed a VPC-isolated Bedrock knowledge base serving 4,000 daily queries at under $1/day'; "
         "'cut inference spend 38% via prompt caching and a provisioned/on-demand split'."),
        ("Immediate-rejection anti-patterns: ",
         "certifications with zero project evidence; 'worked with ChatGPT'; no cloud named anywhere; "
         "a resume listing 12 clouds and 20 tools with no depth signal on any one of them."),
    ])

    H(doc, "Interview Loop Breakdown", 3)
    TABLE(
        doc,
        ["Round", "Format", "What Is Actually Being Tested"],
        [
            ["Recruiter screen (30m)", "Background + cert verification", "Named platform experience; whether certifications are backed by deployments"],
            ["Cloud/AI technical (60m)", "Rapid-fire architecture Q&A", "Bedrock/Azure/Vertex API mechanics, guardrails, PTU/CRU economics, private networking"],
            ["Live build (90m)", "Guided build: mini RAG on the platform of your choice", "SDK fluency, error handling, streaming, cost awareness while coding"],
            ["System design (60m)", "Multi-tenant GenAI platform design", "Tenant isolation, quota/budget enforcement, residency, observability, FinOps"],
            ["Behavioral (45m)", "Production incident deep-dive", "Throttle-storm story, rollback discipline, stakeholder communication"],
        ],
        widths=[1.5, 1.9, 3.6],
        caption="Typical loop: 4-5 rounds",
    )

    H(doc, "Five Real Interview Questions with Model Answers", 3)

    from docx_builder import NUMBERS
    NUMBERS(doc, [
        ("Design a multi-tenant GenAI platform on Bedrock for 200 enterprise tenants with strict cost isolation. ",
         "Model answer: per-tenant IAM role plus tag-based cost allocation (cost-allocation tags on "
         "every invocation via model-invocation logs); application-layer token buckets per tenant in "
         "front of Bedrock; per-tenant index prefixes with document-level ACLs; provisioned baseline + "
         "per-tenant on-demand burst with metering-driven chargeback; guardrail configuration per "
         "tenant class; per-tenant token/cost dashboards with anomaly alerts."),
        ("PTU vs on-demand: your workload is 30M tokens/month with a 5x weekly peak. Choose and defend. ",
         "Model answer: compute both cost curves; at 30M tokens/month, on-demand dominates unless peak "
         "throttling breaches SLOs. Provision roughly the p90 of peak only if the SLA requires "
         "guaranteed capacity, keep p95-p100 on on-demand, and move non-interactive traffic to Batch. "
         "State the >= 55% utilization threshold that justifies provisioning and commit to monthly "
         "re-evaluation."),
        ("How do you make inference endpoints VPC-only, and what breaks? ",
         "Model answer: interface endpoints for bedrock-runtime/bedrock with private DNS, no internet "
         "route, CMK via KMS with a key policy scoped to the runtime role. What breaks: custom DNS "
         "resolvers (must forward to VPC DNS), egress-dependent token counters, third-party webhooks, "
         "and any SDK feature that calls home. Verify from every subnet; document failure modes in the "
         "runbook."),
        ("Your knowledge base answers go stale within hours after a policy update. Fix the architecture. ",
         "Model answer: event-driven sync (S3 event or CI hook on doc merge) -> chunk diff by content "
         "hash -> re-embed only changed chunks -> upsert by ID with soft-delete of vanished hashes -> "
         "index-alias swap for atomic visibility -> staleness SLO metric (age of newest doc vs newest "
         "chunk) with an alert. Never full-reindex per event; never trust the nightly cron alone."),
        ("Reduce this platform's GenAI cost by 40% without quality loss. Which levers, in what order? ",
         "Model answer: (1) measure per-feature cost first - usually one feature is 60% of spend; "
         "(2) prompt/response caching for repeated prefixes; (3) right-size models per task class "
         "(small model for routing/classification, large for synthesis); (4) batch offline jobs; "
         "(5) trim context via better retrieval (lower top_k, add rerank) since tokens are cost and "
         "latency simultaneously; (6) rebalance provisioned vs on-demand. Defend each lever with its "
         "measured delta and a regression eval proving quality held."),
    ])

    H(doc, "Module F - Production Capstone Specifications", 2)
    H(doc, "Capstone 2.1 - Enterprise Knowledge Base on Bedrock with Tenant Isolation", 3)
    BULLETS(doc, [
        ("Architecture: ",
         "S3 document store (per-tenant prefixes, SSE-KMS with per-tenant CMKs) -> event-driven "
         "pipeline (Lambda: chunk by content hash; Titan/Cohere embeddings; OpenSearch Serverless with "
         "document-level security) -> API Gateway + Lambda retrieval layer (hybrid + rerank, Code 2.1) "
         "-> Bedrock Converse with Guardrails -> DynamoDB token metering with per-tenant budgets -> "
         "CloudWatch dashboards for cost and latency per tenant."),
        ("Verification tests: ",
         "(1) isolation: tenant A can never retrieve tenant B's chunk (negative ACL tests); (2) budget "
         "enforcement: synthetic overspend is rejected with a clean 429 contract; (3) residency: "
         "regional profile pinned and asserted in tests; (4) freshness: a document delete propagates "
         "in under 15 minutes; (5) load: 50 concurrent users with p95 TTFT under 3 seconds; (6) "
         "guardrail regression: a 30-case suite passes."),
    ])
    H(doc, "Capstone 2.2 - Azure AI Foundry Agent Platform with FinOps Metering", 3)
    BULLETS(doc, [
        ("Architecture: ",
         "Azure AI Foundry project (private endpoints, Entra ID auth) -> Azure API Management gateway "
         "enforcing per-subscription quotas and SSE streaming -> prompt-flow orchestration with AI "
         "Search hybrid retrieval and Content Safety filters -> Application Insights plus a custom "
         "cost-metering function attributing tokens to product features -> a scheduled function "
         "producing a weekly PTU/PAYG rebalancing report."),
        ("Verification tests: ",
         "gateway enforces quota (429 with Retry-After); content-filter block rate per intent stays "
         "inside agreed bounds; the cost report reconciles with the Azure billing export within 2%; "
         "p95 TTFT under 1.2s during a 100-rps soak; failover deployment swap completes in under 60 "
         "seconds with zero in-flight loss."),
    ])
