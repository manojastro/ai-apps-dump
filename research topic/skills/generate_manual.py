"""Assemble Comprehensive_AI_Roles_Career_Transition_Manual.docx"""
import datetime
from docx import Document
from manual_helpers import (
    style_document, add_body, add_bullets, add_callout, add_code_block,
    add_styled_table, CODE_HYBRID_RAG, CODE_SUPERVISOR, CODE_RATELIMIT,
    CODE_TOOLCALL, CODE_EVAL, CODE_SECURITY,
)
from snippets import (CODE_AIOPS_ANOMALY, CODE_CLOUDAI_DEPLOY, CODE_IDP_PIPELINE,
                      CODE_REDTEAM, CODE_FDE_MCP, CODE_VLLM_SERVE, CODE_SOL_RAGAPP)
from roles_a import ROLE_AIOPS, ROLE_CLOUDAI
from roles_b import ROLE_AUTO, ROLE_AISEC
from roles_c import ROLE_FDE, ROLE_GENAI, ROLE_SOL
from xrole import (HEATMAP_HEADERS, HEATMAP_ROWS, TRANSITION_ROWS, PLAYBOOK_MOVES,
                   APPENDIX_PAPERS, ATS_BANK_ROWS, GLOSSARY_ROWS)

ROLES = [ROLE_AIOPS, ROLE_CLOUDAI, ROLE_AUTO, ROLE_AISEC, ROLE_FDE, ROLE_GENAI, ROLE_SOL]
ROLE_SNIPPETS = {
    "AIOps Engineer": ("Role pattern R-AIOps — IsolationForest detector + allowlisted self-healing", CODE_AIOPS_ANOMALY),
    "Cloud AI Engineer": ("Role pattern R-Cloud — canary endpoint promotion with health gates + rollback", CODE_CLOUDAI_DEPLOY),
    "Intelligent Automation Engineer": ("Role pattern R-Auto — IDP pipeline with idempotency + confidence-gated HITL", CODE_IDP_PIPELINE),
    "AI Security Engineer": ("Role pattern R-Sec — red-team harness with severity gates", CODE_REDTEAM),
    "Forward Deployed / AI Deployment Engineer (FDE)": ("Role pattern R-FDE — ontology + MCP tool server + acceptance gate", CODE_FDE_MCP),
    "GenAI / Agentic AI Engineer": ("Role pattern R-GenAI — batched serving scheduler with TTFT/TPOT SLOs", CODE_VLLM_SERVE),
    "AI Solutions Engineer": ("Role pattern R-Sol — trial-guarded reference app with handoff readiness", CODE_SOL_RAGAPP),
}
CANONICAL = [
    ("Pattern C1 — Advanced Hybrid RAG (dense + BM25 + RRF + cross-encoder rerank)", CODE_HYBRID_RAG),
    ("Pattern C2 — Stateful multi-agent supervisor with HITL approval breakpoints", CODE_SUPERVISOR),
    ("Pattern C3 — Token-bucket rate limiter with dynamic backoff + jitter", CODE_RATELIMIT),
    ("Pattern C4 — Deterministic tool-calling with Pydantic validation", CODE_TOOLCALL),
    ("Pattern C5 — Automated LLM evaluation pipeline (faithfulness / precision / relevance + judge)", CODE_EVAL),
    ("Pattern C6 — Security middleware (injection sanitization + PII redaction)", CODE_SECURITY),
]

OUT = "Comprehensive_AI_Roles_Career_Transition_Manual.docx"


def build_role(doc, r):
    doc.add_heading(f"Role {r['num']}: {r['title']}", level=1)
    add_body(doc, r["tagline"], bold=True)
    add_body(doc, r["mission"])
    # Module A
    doc.add_heading("Module A — Labor Telemetry & Hiring Dynamics", level=2)
    add_body(doc, r["tele_intro"])
    doc.add_heading("Active openings by geography (directional, September 2026)", level=3)
    add_styled_table(doc, ["Segment", "Active openings signal"], r["openings_rows"])
    doc.add_heading("Compensation bands — Total Target Compensation (TTC)", level=3)
    add_styled_table(doc, ["Level", "P25", "P50", "P75", "P90"], r["comp_rows"])
    add_callout(doc, r["comp_note"], label="Compensation note.")
    doc.add_heading("Top hiring organizations", level=3)
    add_styled_table(doc, ["Category", "Active hirers (recon sample)"], r["top15_rows"])
    doc.add_heading("Experience baseline & feeder backgrounds", level=3)
    add_bullets(doc, r["exp_bullets"])
    # Module B
    doc.add_heading("Module B — Role Taxonomy & Daily Operational Reality", level=2)
    doc.add_heading("Ownership boundaries", level=3)
    add_styled_table(doc, ["Adjacent function", "This role owns", "Explicitly does not own", "Handshake"],
                     r["bound_rows"])
    doc.add_heading("Five daily operational artifacts", level=3)
    for i, (t, b) in enumerate(r["artifacts"], 1):
        doc.add_heading(f"Artifact {i}: {t}", level=3)
        add_body(doc, b)
    doc.add_heading("Core operating toolchain", level=3)
    add_bullets(doc, r["toolchain"])
    # Module C
    doc.add_heading("Module C — Technical Skills, Tools & Services Matrix", level=2)
    add_body(doc, "Frequency key used across every row: Critical = expected on day one in most JDs; "
                  "High = frequent differentiator; Emerging = rising signal that wins senior loops.")
    add_styled_table(doc, ["Category", "Critical / High items", "Emerging / situational"], r["skills_rows"])
    add_callout(doc, "Study rule: go deep on every Critical item (build + eval + incident story), "
                     "working-knowledge on High, and one Emerging item per quarter with a public artifact.",
                label="How to use this matrix.")
    # Module D
    doc.add_heading("Module D — Deep-Tier Technical Reference (Living Textbook)", level=2)
    for t in r["theory"]:
        doc.add_heading(t["h"], level=3)
        for para in t["body"].split("\n"):
            if para.strip():
                add_body(doc, para.strip())
        if t.get("diagram"):
            add_code_block(doc, t["diagram"], caption="Data-flow schematic.")
    doc.add_heading("Exhaustive study syllabus", level=3)
    doc.add_heading("Concepts to master", level=3)
    add_bullets(doc, r["syllabus_concepts"])
    doc.add_heading("Foundational papers & specifications", level=3)
    add_bullets(doc, r["syllabus_papers"])
    doc.add_heading("Official documentation to work through", level=3)
    add_bullets(doc, r["syllabus_docs"])
    doc.add_heading("Canonical code patterns to memorize", level=3)
    add_body(doc, "Six shared production patterns (C1-C6) apply to every role in this manual; the seventh (R-pattern) "
                  "is role-specific. All are typed, logged, guarded, and runnable as study harnesses.")
    for caption, code in CANONICAL:
        add_code_block(doc, code, caption=caption)
    cap, code = ROLE_SNIPPETS[r["title"]]
    add_code_block(doc, code, caption=cap)
    doc.add_heading("Failure modes & edge cases", level=3)
    for title, body in r["failures"]:
        add_body(doc, title, bold=True)
        add_body(doc, body)
    # Module E
    doc.add_heading("Module E — Interview Mechanics & Hidden Hiring Patterns", level=2)
    add_callout(doc, r["ats_keywords"], label="ATS keyword bank.")
    doc.add_heading("Anti-patterns that trigger rejection", level=3)
    add_bullets(doc, r["ats_antipatterns"])
    doc.add_heading("Interview loop breakdown", level=3)
    add_styled_table(doc, ["Round", "Format & content", "What scores"], r["loop_rows"])
    doc.add_heading("Five real technical questions with model answers", level=3)
    for q, a in r["interview_qa"]:
        add_body(doc, q, bold=True)
        add_body(doc, a)
    # Module F
    doc.add_heading("Module F — Production Capstone Specifications", level=2)
    for c in r["capstones"]:
        doc.add_heading(c["name"], level=3)
        add_body(doc, "Architecture & data flow: " + c["arch"])
        add_styled_table(doc, ["Layer", "Choice"], c["stack_rows"])
        doc.add_heading("Implementation steps", level=3)
        add_bullets(doc, c["steps"])
        doc.add_heading("Verification test cases", level=3)
        add_bullets(doc, c["tests"])


def main():
    doc = Document()
    style_document(doc)
    cp = doc.core_properties
    cp.title = "Comprehensive AI Roles Career Transition Manual — 7 Roles, Living Textbook"
    cp.author = "Autonomous Labor-Market Research"
    cp.created = datetime.datetime(2026, 9, 6)
    # Cover
    doc.add_heading("Comprehensive AI Roles Career Transition Manual", level=1)
    add_body(doc, "AIOps \u00b7 Cloud AI \u00b7 Intelligent Automation \u00b7 AI Security \u00b7 "
                  "Forward Deployed / AI Deployment \u00b7 GenAI / Agentic AI \u00b7 AI Solutions", bold=True)
    add_body(doc, "Empirical role dossiers (Modules A-F) + cross-role transition matrix + production code arsenal. "
                  "Recon window: August-September 2026. Minimum 30 live postings harvested per role (210+ total) "
                  "across LinkedIn, Indeed, Greenhouse, Lever, Workday, and enterprise career portals.")
    add_callout(doc, "Read front to back once, then use per-role Module D as drill material and Module F as the "
                     "portfolio build order. Every code pattern is designed to be retyped from memory.",
                label="How to use this manual.")
    doc.add_heading("Reconnaissance log (auditable sources)", level=2)
    add_bullets(doc, [
        "AIOps: Selector.ai role analysis; AIOps School skill matrix; PeopleInAI jobs guide; Robert Half 2025 Demand for Skilled Talent; Futurense AIOps career path (India 15-28 / 30-50 LPA); TechGig Lead AIOps Bangalore; EduCativ Senior AIOps JD; GE HealthCare Sr Staff AIOps JD.",
        "Intelligent Automation: Bosch Intelligent Automation Engineer JD (RPA+GenAI+Agentic, Azure OpenAI); AMETEK Bangalore JD (UiPath + Power Platform); OCERS AI Automation Engineer JD (Azure MLOps + IDP + RPA); Sundeep Teki 2026 guide (RPA ~$35B market, US mean ~$135K); JobDescription.org + AxialSearch analyses.",
        "FDE: Palantir Forward Deployed AI Engineer JD (Lever, $135-200K base); OpenAI FDE SF posting ($162-280K + equity); Anthropic Applied AI JD (40/30/30 split); Pragmatic Engineer FDE deep dive; aiarch.dev, Vibe Engines, Perspective AI trackers (Palantir ~51 / OpenAI ~31 openings; +729-800% YoY; frontier mid $350-550K).",
        "Compensation calibration: Levels.fyi AI Engineer Compensation Trends Q3 2025 (Senior +14.2%, Staff +18.7% AI premiums), AI Engineer title medians ($155K broad / $307K Santa Clara), ML/AI SWE mean ~$246K; 2026 FDE compensation trackers (broad median ~$183-190K; Palantir FDSE $171-295K, median ~$211K).",
        "Role-atlas cross-checks: Blue Prism ROM role taxonomy (automation RACI); OCERS DevSecOps/MLOps environment spec; GE HealthCare MLOps/GenAIOps stack (MLflow, SageMaker, Bedrock, LangSmith, LangGraph, Pinecone/FAISS/Milvus).",
    ])
    doc.add_heading("Role atlas (60-second orientation)", level=2)
    add_styled_table(doc, ["Role", "Owns", "Proves it with"],
                     [["AIOps", "Telemetry-to-remediation loop", "MTTR + noise-reduction scorecard"],
                      ["Cloud AI", "AI workloads on hyperscaler substrate", "Cost model + private-networking diagram"],
                      ["Intelligent Automation", "Business processes as production systems", "P&L one-pager per process"],
                      ["AI Security", "AI threat surface + guardrails", "Severity-rated findings + blocked launch"],
                      ["FDE", "Customer outcome in customer env", "Handoff metric + eval suite"],
                      ["GenAI / Agentic", "Probabilistic systems at SLO", "Eval board + $/grounded-answer curve"],
                      ["AI Solutions", "Technical sale + pilot-to-close", "Conversion rate + readout samples"]])
    for r in ROLES:
        build_role(doc, r)
    # Cross-role chapter
    doc.add_heading("Cross-Role Comparison & Career Transition Matrix", level=1)
    doc.add_heading("Unified skills heatmap (7 roles x 15 capabilities)", level=2)
    add_body(doc, "Legend: \u25cf Critical \u00b7 \u25d0 High \u00b7 \u25cb Medium/Emerging \u00b7 \u2013 Low/absent.")
    add_styled_table(doc, HEATMAP_HEADERS, HEATMAP_ROWS)
    doc.add_heading("Transition vectors from IT Service Desk / Infrastructure", level=2)
    add_styled_table(doc, ["Target role", "Your unfair advantage", "90-day skill sprint", "12-month arc", "Proof artifact"],
                     TRANSITION_ROWS)
    doc.add_heading("The Differentiator Playbook", level=2)
    for title, body in PLAYBOOK_MOVES:
        add_body(doc, title, bold=True)
        add_body(doc, body)
    # Appendix
    doc.add_heading("Appendix", level=1)
    doc.add_heading("Master papers / RFCs / specifications list", level=2)
    add_styled_table(doc, ["Work", "Why it is in this manual"], APPENDIX_PAPERS)
    doc.add_heading("Master ATS keyword bank", level=2)
    add_styled_table(doc, ["Role", "Keywords"], ATS_BANK_ROWS)
    doc.add_heading("Glossary", level=2)
    add_styled_table(doc, ["Term", "Working definition"], GLOSSARY_ROWS)
    add_callout(doc, "Currency basis: 1 USD \u2248 84 INR throughout. Salary bands are directional composites of "
                     "Levels.fyi verified submissions, public JD bands (Palantir, OpenAI), and 2026 role guides, "
                     "accurate to the September 2026 recon window; re-check before negotiation.",
                label="Methodology note.")
    doc.save(OUT)
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
