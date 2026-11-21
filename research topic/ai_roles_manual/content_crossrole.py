# -*- coding: utf-8 -*-
"""Cross-role comparison, transition matrix, differentiator playbook, sources."""
from docx_builder import H, P, BULLETS, NUMBERS, CODE, CALLOUT, TABLE, PAGEBREAK


def build(doc):
    H(doc, "Cross-Role Comparison & Career Transition Matrix", 1, page_break_before=True)

    H(doc, "Unified Skills Heatmap", 2)
    P(doc,
      "The matrix cross-tabulates the seven roles against fifteen core capabilities. Ratings: "
      "C = Critical (screened hard, absent = reject), H = High (differentiator), "
      "E = Emerging (fast-rising premium). Read rows to compare roles; read columns to see which "
      "capability to build for which destination.")
    # C / H / E / (blank = not core)
    TABLE(
        doc,
        ["Capability", "AIOps", "Cloud AI", "Int. Auto", "AI Sec", "FDE", "GenAI/Ag", "AI Sol"],
        [
            ["Production Python (async, typing, testing)", "H", "C", "C", "C", "C", "C", "H"],
            ["Async / concurrency discipline", "H", "H", "H", "H", "H", "C", "E"],
            ["LLM APIs & prompt/context engineering", "E", "C", "C", "H", "C", "C", "C"],
            ["Agentic frameworks (LangGraph et al.)", "E", "E", "H", "H", "H", "C", "H"],
            ["RAG / vector databases", "E", "C", "H", "H", "C", "C", "C"],
            ["Managed cloud AI platforms", "H", "C", "H", "H", "H", "H", "C"],
            ["LLMOps & evaluation harnesses", "E", "H", "H", "C", "C", "C", "H"],
            ["Observability (Prometheus/Datadog/OTel)", "C", "H", "H", "H", "E", "H", "E"],
            ["IaC & Kubernetes", "H", "C", "E", "H", "H", "H", "E"],
            ["Security engineering (threat models, AppSec)", "E", "H", "E", "C", "H", "H", "H"],
            ["RPA / BPM / process mining", "E", "-", "C", "-", "-", "H", "-"],
            ["GPU / inference optimization (vLLM, CUDA)", "E", "E", "-", "E", "E", "H", "-"],
            ["Data engineering (SQL, pipelines, warehousing)", "H", "H", "H", "E", "C", "H", "H"],
            ["Client-facing communication", "H", "H", "H", "H", "C", "H", "C"],
            ["Compliance & governance (SOC 2, HIPAA, EU AI Act)", "E", "H", "H", "C", "H", "E", "C"],
        ],
        widths=[2.6, 0.63, 0.63, 0.63, 0.63, 0.63, 0.68, 0.57],
        caption="Unified skills heatmap: C = Critical, H = High, E = Emerging, blank = not core",
        font_size=8.5, header_size=8.5,
    )
    CALLOUT(
        doc,
        "The three universal C-cells across every role: production Python, LLM literacy, and "
        "client-facing communication. A candidate strong on exactly those three can pass screens "
        "in all seven roles; the remaining cells determine which loop you survive to the offer "
        "stage.",
        title="Reading the heatmap.",
    )

    H(doc, "Transition Strategy: IT Service Desk / Infrastructure into Each Role", 2)
    P(doc,
      "Operations backgrounds convert best where operational instinct is the differentiator rather "
      "than overhead. Each vector below is staged in 0-6, 6-12, and 12-24 month horizons, with the "
      "portfolio artifact that unlocks the next stage.")
    TABLE(
        doc,
        ["Destination", "0-6 Months", "6-12 Months", "12-24 Months", "Gateway Artifact"],
        [
            ["AIOps Engineer", "Python basics; one metrics stack (Prometheus + Grafana) lab; SRE book ch. on alerting", "Detector service (Code 1.1); alert-quality report from your current queue data; ITIL v4 foundation", "Capstone 1.1 deployed; MTTR story with numbers; apply to NOC-adjacent AIOps teams", "Backtested anomaly detector + page-volume reduction report"],
            ["Cloud AI Engineer", "Terraform fundamentals; AWS/Azure free tier; AI-102 or AWS ML Engineer syllabus start", "IaC portfolio: Bedrock/AI Foundry KB with private endpoints; cost dashboard", "Capstone 2.1; FinOps report; platform-automation role or Cloud AI junior role", "VPC-isolated RAG deployment with cost dashboard"],
            ["Intelligent Automation Engineer", "Python + UiPath (or Power Automate) certification; Excel-to-automation wins at current job", "Invoice worker (Code 3.1); process-mining mini-study of your own ticket queue", "Capstone 3.1; STP-rate story; IA/RPA developer role in services or GCC", "HITL invoice automation with exception taxonomy"],
            ["AI Security Engineer", "OWASP LLM Top 10 + MITRE ATLAS study; Burp basics; Python hardening", "Red-team lab (Garak/PyRIT) against your own demo agents; one published writeup", "Capstone 4.1 platform; CTF/bounty wins; AppSec-adjacent role with AI scope", "Published red-team report with ASR/FPR numbers"],
            ["Forward Deployed Engineer", "Python + SQL depth; eval literacy (Ragas); start writing one-pagers on your ops wins", "Capstone 5.1-style deployment on synthetic tenant; demo-craft practice", "Customer-facing role (support eng -> solutions support) then FDE track at an AI vendor", "Deployment runbook + eval harness + written retrospectives"],
            ["GenAI / Agentic AI Engineer", "Python async; LangChain/LangGraph quickstarts; API backend basics (FastAPI)", "Code 6.2 supervisor agent over your real ticket data; evals (Code 5.1); LangSmith traces", "Capstone 6.2; agent features shipped in a product role; senior GenAI applications", "Working multi-agent system with eval gate + cost report"],
            ["AI Solutions Engineer", "Demo-craft: build one polished demo of ANY product; discovery-question practice", "Reference-architecture writing; mini POC with success criteria (Fig 7.1); Gong-style call review habits", "Capstone 7.1; pre-sales/solutions role at a platform vendor; field-SE track", "Reference architecture pack + recorded demo with fallbacks"],
        ],
        widths=[1.15, 1.55, 1.55, 1.55, 1.2],
        caption="Transition vectors from IT Service Desk / Infrastructure, staged by horizon",
        font_size=8.5, header_size=8.5,
    )
    P(doc,
      "Sequencing principle: service desk engineers should target the roles where ticket fluency is "
      "an asset in the interview itself. AIOps and Intelligent Automation interviewers treat incident "
      "war stories and SLA pressure as domain expertise; Cloud AI interviews treat them as neutral; "
      "FDE and AI Solutions interviews treat them as the communication foundation. The weakest fit "
      "is a direct jump to GenAI research-adjacent work - route through AIOps or IA first and pivot "
      "internally after 12-18 months.")

    H(doc, "The Differentiator Playbook: Winning as the Operations Candidate", 2)
    P(doc,
      "Academic and frontend-heavy candidates out-credential you on paper. The counter is to make "
      "production stability, operational resilience, and troubleshooting rigor the explicit theme "
      "of every artifact you submit - because that is precisely what the AI industry's production "
      "gap needs.")
    NUMBERS(doc, [
        ("Lead with incidents, not projects. ",
         "Your best story is the 3am outage you diagnosed with partial telemetry. Frame every "
         "resume bullet and interview answer around fault isolation: hypothesis, evidence, fix, "
         "prevention. AI teams are drowning in builders; they hire people who have been paged."),
        ("Convert tickets into telemetry. ",
         "Before leaving any operations role, ship one measurable improvement to the process "
         "itself: a runbook automation, an alert dedup, a deflection bot. 'Cut recurring password-"
         "reset tickets 70% with a self-service flow' is a stronger AI-portfolio line than a "
         "completed course."),
        ("Make reliability your technical brand. ",
         "Every portfolio artifact ships with failure modes documented, backtests reported, and "
         "a rollback plan. The recurring reviewer comment on ops-flavored candidates is 'thinks "
         "in failure modes' - manufacture that comment deliberately."),
        ("Master the vocabulary of the destination. ",
         "Each role has a shibboleth set: precision/recall for AIOps, PTU/CRU for Cloud AI, STP "
         "rate for IA, ASR/FPR for AI Security, golden set for FDE, task-success and token "
         "budget for GenAI, POC contract for Solutions. Using the right number-nouns signals "
         "insider status instantly."),
        ("Bring the ITIL-grade process lens to AI governance. ",
         "Change management, incident process, and audit trails are exactly what enterprise AI "
         "adoption lacks. An ops candidate who presents an agent release process modeled on "
         "change management is instantly differentiated against pure builders."),
        ("Write one page for every artifact. ",
         "Ops people are trusted communicators by trade; formalize it. Every capstone gets a "
         "one-page executive summary with the three numbers that matter. This single habit "
         "closes the gap with academic candidates faster than any certification."),
    ])

    H(doc, "Appendix - Source Register", 1)
    P(doc,
      "Primary anchors consulted during the September 2026 compilation window. Live postings move; "
      "re-verify before relying on any single figure.")
    BULLETS(doc, [
        "Bloomberry - 'What I learned analyzing 1K forward deployed engineer jobs' (median base $173,816; FDE demand growth).",
        "Paraform - 'Forward Deployed Software Engineer Guide' (Palantir FDSE $171K-$415K; skill profile).",
        "fde.academy - OpenAI Forward Deployed Engineer compensation and role guide ($350K-$550K estimates).",
        "Exponent - Palantir FDE compensation and interview breakdown ($135K-$200K posted base).",
        "Practical DevSecOps - AI Security Engineer Roadmap 2026 (LLM security specialist $200K-$280K+).",
        "JobZone Risk - AI Security Engineer salary aggregates (Glassdoor average $182,810).",
        "Live postings reviewed: DHL AI Security Red Team Engineer; Check Point AI Security Engineer; Wilson Sonsini Senior AI Security Engineer; OpenAI FDSE (SF).",
        "Glassdoor - Cloud AI Engineer salary (~$190,635 total pay).",
        "ZipRecruiter - AI Solutions Engineer salary (~$123,284 average; $123K-$185K range).",
        "Peraton Cloud AI Engineer and Columbia University AI Solutions Engineer postings (experience structures).",
        "Scaler / SCDL / IIT KGP - Agentic AI salary studies India (entry 5-14 LPA; mid 12-30; senior 35-60+; leaders 80+).",
        "agentic-engineering-jobs.com - LangGraph job concentration, US ranges $80K-$300K (specialists to $500K).",
        "LangChain - State of Agent Engineering survey (1,300+ practitioners).",
        "OWASP - Top 10 for LLM Applications (2025); MITRE ATLAS; NIST AI Risk Management Framework.",
        "Google SRE Book & Workbook (alerting chapters); OpenTelemetry specification; Prometheus documentation.",
        "Kleppmann, 'Designing Data-Intensive Applications' (idempotency, exactly-once semantics).",
        "Liu et al. (2023) 'Lost in the Middle'; Yao et al. (2022) 'ReAct'; Du et al. (OSDI 2018) 'DeepLog'; Cormack et al. (SIGIR 2009) Reciprocal Rank Fusion.",
    ])
    CALLOUT(
        doc,
        "This manual is a living document. Re-run the telemetry layer quarterly: refresh salary "
        "anchors from Levels.fyi and Glassdoor, re-sample 5-10 postings per role, and update the "
        "skills matrices with any framework that appears in more than a third of fresh postings. "
        "The structural chapters (theory, code patterns, failure modes, transition strategy) "
        "age slowly; the telemetry ages in months.",
        title="Maintenance protocol.",
    )
