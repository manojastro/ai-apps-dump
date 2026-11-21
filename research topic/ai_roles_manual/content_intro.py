# -*- coding: utf-8 -*-
"""Front matter: cover, methodology, reading guide, market context."""
from docx_builder import H, P, BULLETS, CODE, CALLOUT, TABLE, PAGEBREAK, RICH, COVER


def build(doc):
    COVER(
        doc,
        ["Comprehensive AI Roles", "Career & Transition Manual"],
        "A Living Textbook for Seven Global AI Engineering Roles",
        [
            "AIOps Engineer  |  Cloud AI Engineer  |  Intelligent Automation Engineer",
            "AI Security Engineer  |  Forward Deployed Engineer  |  GenAI / Agentic AI Engineer",
            "AI Solutions Engineer",
            "",
            "Labor Telemetry  |  Role Taxonomy  |  Skills & Tools Matrix",
            "Deep Technical Reference  |  Interview Mechanics  |  Capstone Specifications",
            "Cross-Role Comparison & Transition Matrix",
            "",
            "Edition: September 2026  |  Compiled from live JD sampling + published compensation datasets",
        ],
    )

    H(doc, "How to Read This Manual", 1)
    P(doc,
      "This compendium is organized around seven AI engineering roles that now anchor hiring across "
      "hyperscalers, frontier AI labs, AI-native startups, Tier-1 enterprises, and Global Capability "
      "Centers (GCCs) in India and APAC. Each role receives a complete module with six sections:")
    TABLE(
        doc,
        ["Section", "What It Contains"],
        [
            ["A. Labor Telemetry", "Openings by geography, compensation percentiles (USD and INR), top hiring organizations, experience baselines, and transition backgrounds."],
            ["B. Role Taxonomy", "Ownership boundaries against adjacent roles, five real daily operational artifacts, and the core daily toolchain."],
            ["C. Skills & Tools Matrix", "Exhaustive categorized tool/service inventory with market frequency ratings (Critical / High / Emerging)."],
            ["D. Deep Technical Reference", "Underlying mathematics, architecture trade-offs, data-flow diagrams, a master syllabus of papers/RFCs/docs, canonical production code patterns, and failure-mode analysis."],
            ["E. Interview Mechanics", "ATS screening triggers, rejection anti-patterns, interview loop breakdown, and five real interview questions with model answers."],
            ["F. Capstone Specifications", "Two enterprise-grade portfolio projects per role with architecture, stack, and verification tests."],
        ],
        widths=[2.0, 5.0],
        caption="Module structure used for every role",
    )
    P(doc,
      "The six canonical production code patterns required by the living-textbook standard (Hybrid RAG, "
      "LangGraph supervisor with human-in-the-loop, token-bucket rate limiter, deterministic tool-calling, "
      "LLM evaluation pipelines, and prompt-injection/PII security middleware) appear in full in the modules "
      "where they are most canonical, and are cross-referenced from every other role. The final two chapters "
      "provide the cross-role skills heatmap, transition vectors from an IT Service Desk / Infrastructure "
      "background into each role, and the differentiator playbook for operations-heavy candidates.")

    H(doc, "Methodology, Sources, and Limitations", 1)
    P(doc,
      "Compensation and demand figures in this manual are composites built from three evidence layers, "
      "triangulated in September 2026. They are directional planning numbers, not offers.")
    BULLETS(doc, [
        ("Layer 1 - Live JD sampling. ",
         "Structured queries against job aggregators (LinkedIn Jobs, Indeed, ZipRecruiter, Wellfound, "
         "Y Combinator Work at a Startup, Levels.fyi) and enterprise ATS endpoints (greenhouse.io, "
         "lever.co, myworkdayjobs.com, smartrecruiters.com, Workday career sites). Representative live "
         "postings reviewed include DHL's AI Security Red Team Engineer, Check Point's AI Security "
         "Engineer, Wilson Sonsini's Senior AI Security Engineer, OpenAI's Forward Deployed Software "
         "Engineer (SF), Palantir FDSE, Peraton's Cloud AI Engineer, Columbia University's AI Solutions "
         "Engineer, and Crescendo Global / Sopra Steria agentic-AI postings in Gurgaon and Noida."),
        ("Layer 2 - Published compensation datasets. ",
         "Bloomberry's analysis of 1,000+ Forward Deployed Engineer postings (median base $173,816); "
         "Glassdoor (AI Security Engineer US average $182,810; Cloud AI Engineer ~$190,635 total pay); "
         "ZipRecruiter (AI Solutions Engineer ~$123,284 average, $123K-$185K range); Levels.fyi bands for "
         "Palantir ($135K-$200K base, $171K-$295K+ TTC) and OpenAI (~$350K-$550K TTC); Indian market "
         "studies from Scaler, SCDL, and IIT KGP for agentic-AI LPA bands."),
        ("Layer 3 - Practitioner telemetry. ",
         "LangChain's State of Agent Engineering survey (1,300+ professionals), LangGraph job-board "
         "concentration data (agentic-engineering-jobs.com, 40+ mid-level LangGraph US listings at "
         "$80K-$300K), OWASP Top 10 for LLM Applications 2025, MITRE ATLAS, and vendor documentation "
         "for the toolchains listed in each skills matrix."),
    ])
    CALLOUT(
        doc,
        "Openings counts are reconstructed from aggregator search-result volumes during the sampling "
        "window and should be read as order-of-magnitude estimates (a role showing 2,400 US openings is "
        "meaningfully smaller than one showing 4,000+). Salary percentiles are US national composites; "
        "Bay Area / NYC / Seattle typically prices 15-25% above these figures, EMEA 15-35% below, and "
        "India figures are quoted separately in LPA (lakhs per annum). The AI hiring market reprices "
        "quarterly; refresh the telemetry chapter every 2-3 months.",
        title="Statistical honesty note.",
    )

    H(doc, "The 2026 Market Context in One Page", 1)
    P(doc,
      "Five structural shifts define every role in this manual. First, agentic AI moved from demo to "
      "production: postings demanding LangGraph, CrewAI, AutoGen, or OpenAI Agents SDK rose sharply from "
      "late 2025 onward, and LangGraph is the single most in-demand framework keyword. Second, forward-deployed "
      "models won: FDE postings spiked ~800% from their pre-LLM baseline and median base pay ($173.8K) now "
      "exceeds most senior backend roles, because frontier labs discovered that enterprise revenue requires "
      "engineers embedded at customer sites. Third, security became a board topic: AI-specific security roles "
      "(red team, guardrails, model supply chain) pay $200K-$280K+ at the specialist level, driven by OWASP "
      "LLM Top 10 awareness, NIST AI RMF, and the EU AI Act. Fourth, the RPA-installed base is converting: "
      "Intelligent Automation postings are the highest-volume AI-adjacent channel into engineering for "
      "GCC-based candidates, as deterministic bots are re-platformed onto LLM-equipped pipelines. Fifth, "
      "AIOps is being rebuilt around LLM-assisted incident response, which converts classic monitoring "
      "skills (Prometheus, Splunk, ITIL) into a gateway role for infrastructure engineers.")
    CALLOUT(
        doc,
        "Across all seven roles, the same three-skill core decides who gets hired: (1) production-grade "
        "Python with real async and error handling, (2) retrieval + evaluation literacy, and (3) evidence "
        "that something you shipped survived contact with real users. Every module in this manual is "
        "engineered to build exactly those three assets.",
        title="The through-line.",
    )
