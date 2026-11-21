# -*- coding: utf-8 -*-
"""Build the X-only India AI job-transition research pack from collected posts."""
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

ROOT = Path(__file__).resolve().parents[1]
F01 = ROOT / "01_Skills_Domains_Roadmap"
F02 = ROOT / "02_Job_Openings_Demand"
F03 = ROOT / "03_Interview_Questions_Patterns"
F04 = ROOT / "04_Projects_That_Hire"
F05 = ROOT / "05_Resume_And_Certifications"

HDR_FILL = PatternFill("solid", fgColor="1F4E79")
ALT_FILL = PatternFill("solid", fgColor="E8F1FA")
GAP_FILL = PatternFill("solid", fgColor="FFF2CC")
WARN_FILL = PatternFill("solid", fgColor="FCE4D6")
HDR_FONT = Font(name="Calibri", bold=True, color="FFFFFF", size=11)
CELL_FONT = Font(name="Calibri", size=10)
THIN = Border(
    left=Side(style="thin", color="BFBFBF"),
    right=Side(style="thin", color="BFBFBF"),
    top=Side(style="thin", color="BFBFBF"),
    bottom=Side(style="thin", color="BFBFBF"),
)
WRAP = Alignment(wrap_text=True, vertical="top")


def xurl(handle, pid):
    return f"https://x.com/{handle}/status/{pid}"


def write_sheet(wb, name, headers, rows, widths=None, gap_col=None):
    ws = wb.create_sheet(name)
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(headers))}1"
    for c, h in enumerate(headers, 1):
        cell = ws.cell(1, c, h)
        cell.fill = HDR_FILL
        cell.font = HDR_FONT
        cell.alignment = Alignment(wrap_text=True, vertical="center")
        cell.border = THIN
    for r, row in enumerate(rows, 2):
        for c, val in enumerate(row, 1):
            cell = ws.cell(r, c, val)
            cell.font = CELL_FONT
            cell.alignment = WRAP
            cell.border = THIN
            if r % 2 == 0:
                cell.fill = ALT_FILL
            text = str(val).upper() if val is not None else ""
            if "INSUFFICIENT" in text or "GAP" in text or str(val).startswith("GAPS"):
                cell.fill = GAP_FILL
            if gap_col and c == gap_col:
                if str(val) in ("Isolated claim", "News recap", "Talk not opening", "Promotional"):
                    cell.fill = WARN_FILL
    n = max(len(headers), 1)
    for i in range(1, n + 1):
        w = widths[i - 1] if widths and i - 1 < len(widths) else 22
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[1].height = 22
    for r in range(2, len(rows) + 2):
        ws.row_dimensions[r].height = 48
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    return ws


def save_wb(path, sheets):
    wb = Workbook()
    default = wb.active
    wb.remove(default)
    for name, headers, rows, widths in sheets:
        write_sheet(wb, name, headers, rows, widths)
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)


def set_doc_font(doc):
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(11)
    style.font.color.rgb = RGBColor(0x22, 0x22, 0x22)


def add_h(doc, text, level=1):
    p = doc.add_heading(text, level=level)
    for run in p.runs:
        run.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)


def add_p(doc, text):
    p = doc.add_paragraph(text)
    p.paragraph_format.space_after = Pt(8)
    return p


def add_b(doc, items):
    for it in items:
        p = doc.add_paragraph(it, style="List Bullet")
        p.paragraph_format.space_after = Pt(4)


def save_doc(path, title, builder):
    doc = Document()
    set_doc_font(doc)
    section = doc.sections[0]
    section.top_margin = Inches(0.9)
    section.bottom_margin = Inches(0.9)
    section.left_margin = Inches(1.0)
    section.right_margin = Inches(1.0)
    h = doc.add_heading(title, 0)
    for run in h.runs:
        run.font.color.rgb = RGBColor(0x1F, 0x4E, 0x79)
    add_p(
        doc,
        "Evidence window: public X posts only, 2026-03-11 to 2026-09-11 "
        "(queries used since:2026-03-11 until:2026-09-12). "
        "Not official Naukri/LinkedIn market data. Thin cells are labeled GAPS.",
    )
    builder(doc)
    path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(path)


def write_txt(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.strip() + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Distinct India hiring posts used for X-proxy mix (actual openings, not talk)
# intern_only posts are kept in Distinct_Hiring_Posts but excluded from mix %.
# ---------------------------------------------------------------------------
HIRING = [
    # AIOps / observability adjacent
    dict(pid="2085331204858093584", handle="AkshayKumar_JAK", date="2026-08-06", likes=42,
         company="IBM", role="AIOps Engineer", title="Software Developer - AIOps Developer",
         city="Hyderabad / Pune / Bengaluru", mode="Not stated", yoe="0-1", intern=False,
         actual=True, notes="Java, Python or similar; SQL/NoSQL; AI-assisted coding. Fresher band."),
    dict(pid="2090900574401368148", handle="TheArthiAI", date="2026-08-21", likes=0,
         company="CGI", role="AIOps Engineer", title="Agentic AI Engineer (Telco/OSS)",
         city="Chennai", mode="On-site", yoe="Not stated", intern=False,
         actual=True, notes="JD text on X names AIOps/MLOps, network anomaly detection. Aggregator, 0 likes."),
    dict(pid="2083492348177342630", handle="BHR300304", date="2026-08-01", likes=0,
         company="Infosys (payroll)", role="AIOps Engineer", title="Nutanix AOS Engineer",
         city="Hyderabad", mode="Not stated", yoe="7-12+", intern=False,
         actual=True, notes="AIOps listed as a skill with PowerShell/HCI, not an AIOps Engineer title."),
    dict(pid="2083440517434794495", handle="BHR300304", date="2026-08-01", likes=0,
         company="Infosys (payroll)", role="AIOps Engineer", title="Integrated Command Center Engineer",
         city="Hyderabad", mode="Not stated", yoe="7-12+", intern=False,
         actual=True, notes="ITIL, ServiceNow, Dynatrace, Splunk, incident management. Ops, not GenAI."),
    dict(pid="2067125499176898864", handle="jobwharf", date="2026-06-17", likes=0,
         company="Experian", role="AIOps Engineer", title="Senior Observability Engineer",
         city="Hyderabad", mode="Not stated", yoe="Senior (unstated)", intern=False,
         actual=True, notes="Title is Observability, mapped as AIOps-adjacent. Zero-engagement aggregator."),
    dict(pid="2090476316084883465", handle="jobs_posting", date="2026-08-20", likes=2,
         company="Point72", role="AIOps Engineer", title="Observability Engineer",
         city="Bengaluru", mode="Not stated", yoe="Not stated", intern=False,
         actual=True, notes="Observability in a tech/engineering team, not AIOps-titled."),
    # Cloud AI
    dict(pid="2096098136158806424", handle="VishalKumax4ekg", date="2026-09-05", likes=0,
         company="CGI", role="Cloud AI Engineer", title="AI Engineer",
         city="Bengaluru", mode="Hybrid (3 days office)", yoe="4-7", intern=False,
         actual=True, notes="Python, FastAPI, React, Azure AI Foundry, Azure OpenAI, RAG, Docker/K8s."),
    dict(pid="2093181895412707650", handle="careerdjobs", date="2026-08-28", likes=0,
         company="Cognizant", role="Cloud AI Engineer", title="AI Engineers | GenAI | Azure/GCP",
         city="Chennai / Bengaluru / Hyderabad / Pune", mode="Not stated", yoe="3.5-9", intern=False,
         actual=True, notes="Azure OpenAI, Vertex AI, LLMs, RAG, Python, SQL, AI Agents. Recruiter dump."),
    dict(pid="2092820945534890424", handle="careerdjobs", date="2026-08-27", likes=0,
         company="EY", role="Cloud AI Engineer", title="GenAI Developer",
         city="Bengaluru / Kolkata", mode="Not stated", yoe="2-6", intern=False,
         actual=True, notes="LangGraph/LangChain, Microsoft Agent SDK/Google ADK, Azure AI Services / GCP Document AI."),
    dict(pid="2089798307656970260", handle="offerscout", date="2026-08-18", likes=6,
         company="NTT DATA", role="Cloud AI Engineer", title="AI Engineer",
         city="Bengaluru", mode="Not stated", yoe="3+", intern=False,
         actual=True, notes="Python, Azure OpenAI, Agentic AI, MCP, Docker/K8s. Batch text says 2024/2025 grads AND 3+ years."),
    dict(pid="2098035243303485614", handle="agamin_ai", date="2026-09-10", likes=0,
         company="Agamin / Databricks req", role="Cloud AI Engineer", title="Databricks ML Engineer with GenAI/RAG",
         city="Bengaluru", mode="Not stated", yoe="10+", intern=False,
         actual=True, notes="Python, SQL, Databricks, MLflow, RAG, Vector DBs, Azure OpenAI. SQL named. Zero likes."),
    dict(pid="2095168999470604338", handle="arjun_gupta95", date="2026-09-02", likes=204,
         company="OpenAI", role="Cloud AI Engineer", title="Partner AI Deployment Engineer - AWS",
         city="India remote", mode="Remote-India", yoe="8+", intern=False,
         actual=True, notes="Also mapped to FDE. Thread: 8+ years technical consulting, AWS, coding, AI/ML deployment."),
    # Intelligent automation
    dict(pid="2056376428439200206", handle="ajay_2512x", date="2026-05-18", likes=79,
         company="Emplay", role="Intelligent Automation Engineer", title="Associate – Agentic AI Automation Engineer",
         city="Remote – India", mode="Remote-India", yoe="2+", intern=False,
         actual=True, notes="₹12–15 LPA. Same post also lists intern, DevOps, L2 Support."),
    dict(pid="2084152128407265734", handle="BratDotAI", date="2026-08-03", likes=17,
         company="Souveno AI", role="Intelligent Automation Engineer", title="AI Automation Engineer",
         city="Hyderabad", mode="Not stated", yoe="0-1", intern=False,
         actual=True, notes="Friend-of-founder post. Freshers to 1 YOE."),
    dict(pid="2053810460919742675", handle="insanekrishnaa", date="2026-05-11", likes=186,
         company="Spector AI", role="Intelligent Automation Engineer", title="Software Engineer – AI Solutions",
         city="PAN India", mode="Hybrid", yoe="Not stated (engineer)", intern=False,
         actual=True, notes="Also mapped to Solutions Engineer. Python, TF/PyTorch, predictive analytics, intelligent automation."),
    dict(pid="2097759793800966461", handle="TheArthiAI", date="2026-09-09", likes=1,
         company="MARS Cosmetics", role="Intelligent Automation Engineer", title="AI Workflow Engineer",
         city="Delhi", mode="On-site", yoe="Early-career", intern=False,
         actual=True, notes="n8n, Make, Zapier named with LangGraph/RAG. Aggregator, 1 like."),
    dict(pid="2082484516455948297", handle="Realized_Guy", date="2026-07-29", likes=1,
         company="Amazon", role="Intelligent Automation Engineer", title="RPA Engineer (AR Automation)",
         city="Hyderabad", mode="Not stated", yoe="Not stated", intern=False,
         actual=True, notes="UiPath + AI/ML/LLMs + Python. 'UiPath Certified better'. Telugu/Hinglish India post."),
    dict(pid="2095410001997443099", handle="careerdjobs", date="2026-09-03", likes=0,
         company="NTT DATA Business Solutions", role="Intelligent Automation Engineer", title="Senior Developer – UiPath (RPA)",
         city="PAN India", mode="Not stated", yoe="Senior (unstated)", intern=False,
         actual=True, notes="Classic RPA stack, not agentic. Zero-engagement dump."),
    dict(pid="2090071119986598320", handle="aier_india", date="2026-08-19", likes=0,
         company="AIER India", role="Intelligent Automation Engineer", title="UiPath RPA Developer",
         city="Bengaluru", mode="Not stated", yoe="Experienced (unstated)", intern=False,
         actual=True, notes="UiPath, SAP, Azure. ₹1.2 LPM claimed. Zero likes."),
    # AI Security
    dict(pid="2085996412278628584", handle="WhoShivaisnot", date="2026-08-08", likes=17,
         company="Unnamed (The Finder)", role="AI Security Engineer", title="AI Security Engineer",
         city="Bengaluru", mode="Not stated", yoe="3+", intern=False,
         actual=True, notes="Wants product-company background in AI Cyber Security. Company not named on X."),
    dict(pid="2089058867569402026", handle="TheArthiAI", date="2026-08-16", likes=0,
         company="HCLTech", role="AI Security Engineer", title="AI Security Engineer",
         city="Bengaluru", mode="Hybrid", yoe="Not stated", intern=False,
         actual=True, notes="GenAI/LLM security, RAG, prompt injection defense. Aggregator 0 likes."),
    dict(pid="2087863991116955883", handle="careerdjobs", date="2026-08-13", likes=0,
         company="Infosys", role="AI Security Engineer", title="AI Security (among a bundle)",
         city="PAN India", mode="Not stated", yoe="1-20", intern=False,
         actual=True, notes="Bundle post: GenAI, Agentic, LLMOps, AI Security, AI Architecture. Not a dedicated req."),
    # FDE
    dict(pid="2097537517621018912", handle="ajay_2512x", date="2026-09-09", likes=88,
         company="Lyzr", role="Forward Deployed / AI Deployment Engineer", title="Forward Deployed Engineer",
         city="Bengaluru", mode="On-site hiring day", yoe="Not required prior FDE; Applied AI/backend/cloud/solutions", intern=False,
         actual=True, notes="HackerRank → build working solution → interviews → Shark Tank showcase. Same-day offer claim."),
    dict(pid="2095905532418892025", handle="offerscout", date="2026-09-04", likes=14,
         company="Emergent", role="Forward Deployed / AI Deployment Engineer", title="Forward Deployed Engineer",
         city="Bengaluru", mode="5 days on-site + 1 WFH", yoe="1+ (2024/2025 passouts)", intern=False,
         actual=True, notes="Junior FDE. 6-day week. Not 6–10 YOE."),
    dict(pid="2095884787718509046", handle="nitesh_singh5", date="2026-09-04", likes=37,
         company="Katonic", role="Forward Deployed / AI Deployment Engineer", title="Forward Deployed AI Engineer",
         city="India", mode="Remote-India", yoe="Not stated", intern=False,
         actual=True, notes="Aggregator salary 20–35 LPA. Verify on source board."),
    dict(pid="2056370126379991399", handle="arjun_gupta95", date="2026-05-18", likes=380,
         company="OpenAI", role="Forward Deployed / AI Deployment Engineer", title="AI Deployment Engineer, Startups",
         city="Bengaluru", mode="Not stated (India hiring)", yoe="Ex-founders/CTOs/MLEs/SWEs welcome", intern=False,
         actual=True, notes="First-hand OpenAI Applied AI hiring manager post."),
    dict(pid="2090023873219825908", handle="ajay_2512x", date="2026-08-19", likes=328,
         company="AiPrise (YC S22)", role="Forward Deployed / AI Deployment Engineer", title="Forward Deployed Engineer",
         city="Bengaluru", mode="Not stated", yoe="New grads welcome (FDE); also SWE 6+ / Staff 8+", intern=False,
         actual=True, notes="FDE itself is junior-friendly; 8+ YOE sits on Staff SWE, not FDE title."),
    dict(pid="2091356841750212803", handle="ajay_2512x", date="2026-08-23", likes=173,
         company="RevRag AI", role="Forward Deployed / AI Deployment Engineer", title="FDE intern / FDE 2-3 / Senior FDE 4-5",
         city="Bengaluru (HSR)", mode="Mostly on-site", yoe="Intern; 2-3; 4-5+", intern=False,
         actual=True, notes="Senior FDE listed as opening soon in Aug 2026 post."),
    dict(pid="2083075915823587710", handle="officialdev_bml", date="2026-07-31", likes=132,
         company="ElevenLabs", role="Forward Deployed / AI Deployment Engineer", title="Forward Deployed Engineer",
         city="India / global remote", mode="Remote-India", yoe="Not stated", intern=False,
         actual=True, notes="Aggregator. Apply link in comments, not in post body."),
    dict(pid="2080519024719655376", handle="Ayushi_sharma02", date="2026-07-24", likes=48,
         company="Applied Computing", role="Forward Deployed / AI Deployment Engineer", title="ML Engineer – Forward Deployed",
         city="Bengaluru", mode="Not stated", yoe="0-2", intern=False,
         actual=True, notes="₹10–20 LPA. Junior."),
    dict(pid="2043536398817616163", handle="ajay_2512x", date="2026-04-13", likes=1398,
         company="Sarvam AI", role="Forward Deployed / AI Deployment Engineer", title="Forward Deployed SWE / Strategic Deployment Engineer",
         city="Bengaluru & Delhi", mode="On-site", yoe="Not stated on X", intern=False,
         actual=True, notes="Among 20 engineering roles. High-engagement aggregator, not first-hand recruiter."),
    dict(pid="2085231289200955556", handle="kapoor015", date="2026-08-06", likes=225,
         company="Unnamed (Aman / a16z speedrun)", role="Forward Deployed / AI Deployment Engineer", title="First FDE in India",
         city="India", mode="Not stated", yoe="Not stated", intern=False,
         actual=True, notes="First-hand founder/operator hire post. Client-facing + backend + token cost."),
    dict(pid="2097204914426642689", handle="vineeth_agi", date="2026-09-08", likes=3,
         company="Rhai", role="Forward Deployed / AI Deployment Engineer", title="Forward Deployed Engineer",
         city="Bengaluru", mode="Onsite with clients", yoe="Not stated", intern=False,
         actual=True, notes="Embed with clients, messy workflows, Google/Microsoft tenants, reversible automation."),
    dict(pid="2095937696724390373", handle="JesseisCooking", date="2026-09-04", likes=81,
         company="AiStudio", role="Forward Deployed / AI Deployment Engineer", title="Forward Deployed Engineer Intern",
         city="India", mode="Remote", yoe="Intern", intern=True,
         actual=True, notes="Intern + PPO. Excluded from mix %."),
    # GenAI / Agentic
    dict(pid="2094028909449011263", handle="JesseisCooking", date="2026-08-30", likes=25,
         company="Cognizant", role="GenAI / Agentic AI Engineer", title="Python Gen AI Engineer",
         city="Chennai", mode="Hybrid", yoe="Not stated", intern=False,
         actual=True, notes="Python, LangChain/LangGraph, LLMs, RAG. Official careers URL in post."),
    dict(pid="2084236353877967017", handle="mange_manali", date="2026-08-03", likes=68,
         company="Unnamed (ClanX / Manali)", role="GenAI / Agentic AI Engineer", title="Senior AI Engineer",
         city="Bengaluru", mode="Not stated", yoe="4+", intern=False,
         actual=True, notes="Python, LangGraph/LangChain/RAG, production agents, FastAPI. ₹40–60 LPA + ESOPs."),
    dict(pid="2088133675556966876", handle="mange_manali", date="2026-08-14", likes=251,
         company="ClanX / same Senior AI Engineer loop", role="GenAI / Agentic AI Engineer", title="AI Engineer Bangalore",
         city="Bengaluru", mode="Not stated", yoe="Must have chat-based agent like Claude Code/Cursor", intern=False,
         actual=True, notes="₹40–60 LPA. Coding-agent production experience. Counted as same cluster as previous; still a distinct post."),
    dict(pid="2096976608796242351", handle="Aakshayy12", date="2026-09-07", likes=6,
         company="Sarvam AI", role="GenAI / Agentic AI Engineer", title="Agent Engineer",
         city="Bengaluru", mode="On-site", yoe="3+", intern=False,
         actual=True, notes="LLMs, AI Agents, Python, System Design, Evals, APIs, Cloud."),
    dict(pid="2091909090704503119", handle="arjun_gupta95", date="2026-08-24", likes=251,
         company="OpenAI", role="GenAI / Agentic AI Engineer", title="Applied AI Engineer",
         city="Delhi (careers URL in thread)", mode="Not stated", yoe="Not stated on X", intern=False,
         actual=True, notes="First-hand. Thread also lists Applied AI Architect."),
    dict(pid="2097043045736939676", handle="offerscout", date="2026-09-07", likes=20,
         company="Syce.ai", role="GenAI / Agentic AI Engineer", title="Full Stack AI Engineer",
         city="India", mode="Remote / Hybrid", yoe="Not stated", intern=False,
         actual=True, notes="LLMs, RAG, agents, LangGraph/MCP nice-to-have, AI security & guardrails nice-to-have."),
    dict(pid="2087422706694406439", handle="ajay_2512x", date="2026-08-12", likes=378,
         company="Lexi", role="GenAI / Agentic AI Engineer", title="AI Engineer",
         city="India", mode="Remote-India", yoe="Not stated", intern=False,
         actual=True, notes="No skills listed on X. High-engagement aggregator."),
    dict(pid="2096101104794980556", handle="JesseisCooking", date="2026-09-05", likes=0,
         company="G2", role="GenAI / Agentic AI Engineer", title="AI Engineer",
         city="Bengaluru", mode="On-site", yoe="1-3+", intern=False,
         actual=True, notes="Python, GenAI, LLMs, RAG, cloud. ₹18–30 LPA. Zero likes."),
    dict(pid="2096100179367870469", handle="JesseisCooking", date="2026-09-05", likes=51,
         company="Tailored AI", role="GenAI / Agentic AI Engineer", title="SDE 1/2/3",
         city="Bengaluru", mode="On-site", yoe="SDE1 immediate; bands not fully stated", intern=False,
         actual=True, notes="RAG, Voice Agents, Text2SQL, Workflow Agents. SQL-shaped skill appears as Text2SQL."),
    dict(pid="2043620667883680212", handle="ajay_2512x", date="2026-04-13", likes=676,
         company="Riverline", role="GenAI / Agentic AI Engineer", title="AI Engineers (SDE 1/2/3)",
         city="Bengaluru", mode="In-person", yoe="SDE 1/2/3 (not 8 YOE specific)", intern=False,
         actual=True, notes="₹40–70 LPA. Voice/agent workflows. FastAPI, AWS, LLMs."),
    dict(pid="2090010590198862306", handle="TheArthiAI", date="2026-08-19", likes=0,
         company="LeadSquared", role="GenAI / Agentic AI Engineer", title="Senior AI/ML Engineer",
         city="Bengaluru", mode="On-site", yoe="Senior (unstated)", intern=False,
         actual=True, notes="Python, LLM agents, RAG, LangChain, evaluation, monitoring, guardrails."),
    dict(pid="2082732329433469430", handle="BunnyXVerse", date="2026-07-30", likes=149,
         company="Things Alive Solutions", role="GenAI / Agentic AI Engineer", title="Agentic AI Engineer",
         city="Bengaluru", mode="Not stated", yoe="0-1", intern=False,
         actual=True, notes="LangChain/LangGraph, FastAPI, RAG. Junior."),
    # Solutions Engineer
    dict(pid="2074816319426363696", handle="ajay_2512x", date="2026-07-08", likes=153,
         company="Bolna AI", role="AI Solutions Engineer", title="AI Solutions Engineer",
         city="Bengaluru", mode="On-site", yoe="0-2", intern=False,
         actual=True, notes="Junior. Same company also posted fresher version in April."),
    dict(pid="2092098138907807811", handle="ayushpranav3", date="2026-08-25", likes=218,
         company="BytePlus / ByteDance", role="AI Solutions Engineer", title="Solutions Architect (BytePlus India)",
         city="India", mode="Customer-facing (not stated WFH)", yoe="Not stated", intern=False,
         actual=True, notes="First-hand GTM. LLMs, RAG, agents, LangGraph/MCP, Python/FastAPI, PoCs. Mapped primarily here; also Architect-adjacent."),
    # Solutions Architect
    dict(pid="2077455887678185552", handle="WhoShivaisnot", date="2026-07-15", likes=4,
         company="Unnamed Deep Tech / T-HUB", role="AI Solutions Architect", title="AI Architect",
         city="Hyderabad", mode="Not stated", yoe="8+ overall; 2-3 agentic", intern=False,
         actual=True, notes="RBAC, chunking, agentic infra. One of few explicit 8 YOE AI Architect posts."),
    dict(pid="2067478308045099461", handle="Sampoorna_Jobs", date="2026-06-18", likes=0,
         company="Unnamed (Sampoorna client)", role="AI Solutions Architect", title="Agentic AI Architect",
         city="Hyderabad", mode="Not stated", yoe="7-12", intern=False,
         actual=True, notes="Recruiter listing, zero engagement, skills only 'AI, Architecture'."),
    dict(pid="2087830011449680076", handle="careerdjobs", date="2026-08-13", likes=0,
         company="TekWissen", role="AI Solutions Architect", title="AI Architect",
         city="Noida / Bangalore / Hyderabad / Chennai / Vadodara / PAN India", mode="Not stated", yoe="Not stated", intern=False,
         actual=True, notes="RAG, LLM, .NET, C#, Agentic AI. .NET/C# is a Java/SQL-class exception: named explicitly."),
]

TALK = [
    dict(pid="2054757616086348180", handle="asmah2107", date="2026-05-14", likes=660,
         topic="FDE postings +800% (Indeed, global)", kind="Talk not opening",
         takeaway="FDE talk is hotter than titled AIOps. Uses Indeed, not an India req."),
    dict(pid="2066876195493601369", handle="suraj_sharma14", date="2026-06-16", likes=613,
         topic="FDE hottest job; a16z fellowship", kind="Talk not opening",
         takeaway="High-engagement FDE hype. Fellowship, not an India job post."),
    dict(pid="2074072698272325711", handle="gkcs_", date="2026-07-06", likes=295,
         topic="FDE hottest role 2026", kind="Talk not opening",
         takeaway="Influencer definition: help companies build production AI apps."),
    dict(pid="2097249880553218154", handle="Sanjay_Sriv", date="2026-09-08", likes=29,
         topic="1807% FDE postings; TCS/Wipro/Infosys hire targets", kind="News recap",
         takeaway="Do NOT treat TCS 8,900 / Wipro 10,000 as X hiring posts. ET recap on X."),
    dict(pid="2088879535513358559", handle="MoneyWithSuresh", date="2026-08-16", likes=1,
         topic="50,000 AI security engineers in demand", kind="Isolated claim",
         takeaway="No method. Ignore as market size."),
    dict(pid="2083907885592121840", handle="TalentDataDrop", date="2026-08-02", likes=2,
         topic="15,000+ AI JDs across 25 countries", kind="Isolated claim",
         takeaway="Global scrape, US salaries. Not an India opening count."),
    dict(pid="2054498290289488067", handle="HitachiSysIndia", date="2026-05-13", likes=0,
         topic="Datadog Summit Bengaluru observability", kind="Talk not opening",
         takeaway="Observability-for-AI talk in Bengaluru, not a req."),
    dict(pid="2091202283585651060", handle="The_Tradesman1", date="2026-08-22", likes=2,
         topic="Proofpoint Hyderabad AI Security CoE, 200+ engineers", kind="News recap",
         takeaway="Headcount rumour/news, not a job post with a JD."),
    dict(pid="2072323154450780199", handle="BunnyXVerse", date="2026-07-01", likes=36,
         topic="AI & OPS intern Bangalore", kind="Talk not opening",
         takeaway="Intern stipend role. Not mid-senior AIOps."),
    dict(pid="2046665367527834030", handle="xBitcoin_Teej", date="2026-04-21", likes=623,
         topic="AI-900 / AI-102 career path", kind="Promotional",
         takeaway="US salaries, no-coding consultant path. Not India recruiter evidence."),
    dict(pid="2067248358561927239", handle="neil_xbt", date="2026-06-17", likes=211,
         topic="AI-900 is the credibility filter", kind="Promotional",
         takeaway="Claims hiring managers check AI-900 first. No India hiring-manager post backing this."),
]


def mix_rows():
    roles = [
        "AIOps Engineer",
        "Cloud AI Engineer",
        "Intelligent Automation Engineer",
        "AI Security Engineer",
        "Forward Deployed / AI Deployment Engineer",
        "GenAI / Agentic AI Engineer",
        "AI Solutions Engineer",
        "AI Solutions Architect",
    ]
    counted = [h for h in HIRING if h["actual"] and not h["intern"]]
    # Dedup mix by company+primary role (keep first)
    seen = set()
    uniq = []
    for h in counted:
        key = (h["company"].split("/")[0].strip(), h["role"])
        if key in seen:
            continue
        seen.add(key)
        uniq.append(h)
    total = len(uniq)
    rows = []
    for role in roles:
        n = sum(1 for h in uniq if h["role"] == role)
        pct = round(100.0 * n / total, 1) if total else 0
        rows.append([
            role,
            n,
            total,
            f"{pct}%",
            "X-proxy mix from distinct company+role actual India openings in this scrape. Not official market share.",
            "Thin titled volume" if n <= 3 else "Present in scrape",
        ])
    rows.append([
        "TOTAL (deduped company+role, intern excluded)",
        total,
        total,
        "100%",
        "Denominator = distinct company+primary-role pairs in HIRING list with intern=False.",
        "",
    ])
    return rows, total, uniq


def src_row(p, module, consensus, takeaway, useful):
    return [
        p.get("handle"),
        p.get("date"),
        takeaway,
        xurl(p.get("handle"), p.get("pid")),
        useful,
        p.get("likes"),
        consensus,
        module,
    ]


def build():
    mix, total, uniq = mix_rows()
    counted_n = sum(1 for h in HIRING if h["actual"] and not h["intern"])

    # ========== 02 Demand ==========
    role_map = [
        ["AIOps Engineer", "AIOps Developer, Agentic AI (Telco/OSS), Observability Engineer, Command Center, SRE with Datadog/Dynatrace/Splunk", "Strong title mismatch: few posts use AIOps Engineer; more ops/observability/HCI"],
        ["Cloud AI Engineer", "AI Engineer (Azure/GCP), GenAI Developer, Databricks ML + Azure OpenAI, Partner AI Deployment Engineer-AWS", "Azure OpenAI / Foundry / Vertex appear more than 'Cloud AI Engineer' title"],
        ["Intelligent Automation Engineer", "Agentic AI Automation Engineer, AI Automation Engineer, AI Workflow Engineer, UiPath RPA + LLM", "Split: agentic automation vs classic RPA. Do not treat as one market"],
        ["AI Security Engineer", "AI Security Engineer, GenAI/LLM security, Infosys bundle 'AI Security'", "Very thin distinct reqs"],
        ["Forward Deployed / AI Deployment Engineer", "FDE, Forward Deployed AI Engineer, AI Deployment Engineer, Partner AI Deployment Engineer, Strategic Deployment Engineer", "Clearest title cluster on X in this window"],
        ["GenAI / Agentic AI Engineer", "Python Gen AI Engineer, Senior AI Engineer, Agent Engineer, Applied AI Engineer, Agentic AI Engineer, Full Stack AI Engineer", "Largest raw post volume; many junior/startup"],
        ["AI Solutions Engineer", "AI Solutions Engineer, Software Engineer – AI Solutions, BytePlus Solutions Architect (customer PoCs)", "Bolna is 0-2 YOE; BytePlus is the stronger customer-facing signal"],
        ["AI Solutions Architect", "Applied AI Architect, AI Architect, Agentic AI Architect", "8+ YOE posts exist but sparse and often unnamed company"],
    ]
    distinct_rows = []
    for h in HIRING:
        distinct_rows.append([
            h["company"], h["title"], h["role"], h["city"], h["mode"], h["yoe"],
            "Intern" if h["intern"] else "FT/unspecified",
            "Actual opening post" if h["actual"] else "Not opening",
            h["notes"], h["handle"], h["date"], h["likes"], xurl(h["handle"], h["pid"]),
        ])
    city_rows = []
    for h in HIRING:
        if h["intern"]:
            continue
        city_rows.append([h["role"], h["city"], h["mode"], h["yoe"], h["company"], h["likes"], xurl(h["handle"], h["pid"])])
    talk_rows = []
    for t in TALK:
        talk_rows.append([t["topic"], t["kind"], t["takeaway"], t["handle"], t["date"], t["likes"], xurl(t["handle"], t["pid"])])
    companies = {}
    for h in HIRING:
        if h["intern"]:
            continue
        companies.setdefault(h["company"], {"roles": set(), "cities": set(), "posts": 0})
        companies[h["company"]]["roles"].add(h["title"])
        companies[h["company"]]["cities"].add(h["city"])
        companies[h["company"]]["posts"] += 1
    company_rows = [[c, ", ".join(sorted(v["roles"]))[:180], ", ".join(sorted(v["cities"]))[:120], v["posts"]] for c, v in sorted(companies.items(), key=lambda kv: -kv[1]["posts"])]
    gaps02 = [
        ["Official Naukri/LinkedIn opening counts", "X cannot provide. Do not invent % from memory."],
        ["Mid-senior (6–10 / 8+ YOE) AIOps Engineer title", "IBM post is 0-1 YOE. Infosys posts are HCI/command-center. CGI is aggregator 0 likes."],
        ["Coimbatore / Kochi named openings for these 8 titles", "No distinct hits in this scrape."],
        ["Salary bands for 8 YOE Service Desk → AI", "Scattered LPA on junior/startup posts only. OpenAI Partner 8+ has no INR on X."],
        ["Hybrid vs onsite mix", "Many posts omit work mode. Cannot compute a reliable %."],
        ["Dedup confidence", "Aggregator accounts (@ajay_2512x, @offerscout, @careerdjobs, @TheArthiAI) recycle the same reqs. Mix uses company+role dedup, still an X-proxy."],
    ]
    src02 = []
    for h in HIRING:
        src02.append(src_row(h, "M2", "Actual opening post" if not h["intern"] else "Intern opening",
                             f"{h['company']} | {h['title']} | {h['city']}", "India hiring evidence"))
    for t in TALK:
        src02.append(src_row(t, "M2", t["kind"], t["takeaway"], "Talk vs actual separator"))

    save_wb(F02 / "Job_Demand_Proxy.xlsx", [
        ("Role_Map", ["Primary role", "X title variants observed", "Mapping note"], role_map, [28, 70, 50]),
        ("Distinct_Hiring_Posts", ["Company", "Title on X", "Mapped role", "City", "Work mode", "YOE band", "Type", "Class", "Notes", "Handle", "Date", "Likes", "URL"], distinct_rows, [22, 36, 28, 28, 22, 22, 14, 18, 45, 18, 14, 10, 42]),
        ("City_WorkMode_YOE", ["Mapped role", "City", "Work mode", "YOE", "Company", "Likes", "URL"], city_rows, [32, 32, 24, 28, 28, 10, 42]),
        ("Demand_Mix_Percent", ["Role", "Distinct company+role posts (intern excluded)", "Denominator", "X-proxy %", "Method", "Caveat"], mix, [40, 28, 16, 14, 55, 28]),
        ("Talk_vs_Actual_Openings", ["Topic", "Class", "Takeaway", "Handle", "Date", "Likes", "URL"], talk_rows, [50, 18, 55, 18, 14, 10, 42]),
        ("Companies_Named", ["Company as posted", "Titles", "Cities", "Post count in scrape"], company_rows, [36, 70, 40, 16]),
        ("Source_Posts", ["Handle", "Date", "Takeaway", "URL", "Why useful", "Likes", "Consensus class", "Module"], src02, [18, 14, 50, 42, 28, 10, 20, 10]),
        ("Gaps", ["Gap", "What we actually found"], gaps02, [40, 80]),
    ])

    write_txt(F02 / "01_README.txt", f"""
01_README — Folder 02 Job openings / demand
Date window: 2026-03-11 to 2026-09-11. Queries: since:2026-03-11 until:2026-09-12.
Research date: 2026-09-11. Source: public X only.

HOW X-PROXY % WAS CALCULATED
- Collected India hiring posts that name a company (or clearly unnamed-but-real req) + role + India location.
- Mapped each to one of 8 primary roles.
- Excluded intern-only posts from the percentage denominator.
- Deduped by (company, primary role) so Bolna's two Solutions Engineer posts count once, Infosys bundle is one AI Security row, etc.
- Denominator in this scrape = {total} distinct company+role pairs.
- Raw actual-opening posts before intern filter / before company+role dedup = {counted_n} (see Distinct_Hiring_Posts).
- Label every percentage X-proxy. This is NOT official market share.

QUERIES USED (native then semantic)
Hiring pack from the brief (min_faves then dropped when thin):
1. ("AIOps Engineer" OR "AI Ops" OR AIOps) (hiring OR "we're hiring" OR "open role" OR opening) (India OR Bengaluru OR Bangalore OR Hyderabad OR Chennai OR Pune OR Coimbatore) min_faves:5
2. Same AIOps query without min_faves
3. ("Cloud AI Engineer" OR "Azure AI" OR "GCP AI Engineer") (hiring OR "open role") (India OR Bengaluru OR Hyderabad OR Chennai) min_faves:5  → ZERO HITS
4. Widened: ("Azure AI" OR "Azure OpenAI" OR "Cloud AI" OR "GCP AI" OR "Vertex AI") (hiring) (India OR Bengaluru OR Bangalore OR Hyderabad OR Chennai)
5. ("Intelligent Automation" OR "AI automation engineer" OR "automation + AI") (hiring OR "open role") (India OR Bengaluru OR Hyderabad OR Chennai) min_faves:5
6. ("n8n" OR UiPath OR "Power Automate" OR "intelligent automation") (hiring OR job OR engineer) (India OR Bengaluru OR Hyderabad OR Chennai)
7. ("AI Security Engineer" OR "GenAI security" OR "AI governance") (hiring OR "open role") (India OR Bengaluru OR Hyderabad) min_faves:5
8. ("prompt injection" OR guardrails OR "AI security") (hiring OR engineer OR job) (India OR Bengaluru OR Hyderabad)
9. ("Forward Deployed Engineer" OR FDE OR "AI deployment engineer" OR "forward deployed") (hiring OR "open role") (India OR Bengaluru OR Hyderabad OR Chennai) min_faves:5
10. ("Agentic AI" OR "GenAI Engineer" OR "AI Engineer") (hiring OR "we're hiring" OR "open role") (India OR Bengaluru OR Hyderabad OR Chennai OR Pune) min_faves:10
11. ("AI Solutions Engineer" OR "AI Solutions Architect" OR "GenAI architect") (hiring OR "open role") (India OR Bengaluru OR Hyderabad OR Chennai) min_faves:5
12. ("AI Solutions Architect" OR "Applied AI Architect" OR "GenAI architect" OR "AI architect") (hiring OR "we're hiring") (India OR Bengaluru OR Hyderabad OR Chennai)
13. ("LangGraph" OR FastAPI OR Langfuse OR "Azure AI Foundry") (hiring OR "we're hiring") (Bengaluru OR Bangalore OR Hyderabad OR Chennai OR India) min_faves:5
14. ("8 years" OR "8 yrs" OR "8+ years" OR "10 years") ("AI engineer" OR AIOps OR agentic OR GenAI) (India OR interview OR offer) min_faves:5
15. ("broke into AI" OR "transitioned to AI" OR "moved to AI" OR "from support to AI" OR "service desk to AI" OR "ITSM to AIOps") (India OR Indian OR Bengaluru OR Hyderabad) min_faves:10 -filter:replies
16. Semantic: India hiring AIOps / FDE / Solutions Architect / Cloud AI 2026

CONFIDENCE
- FDE and GenAI/Agentic actual posts: MEDIUM (many aggregator copies; several first-hand: OpenAI @arjun_gupta95, Lyzr, BytePlus @ayushpranav3, Aman @kapoor015, Manali @mange_manali).
- Cloud AI titled "Cloud AI Engineer": LOW. Azure/GCP GenAI JDs exist via aggregators.
- AIOps Engineer mid-senior: LOW.
- AI Security / Solutions Architect: LOW-MEDIUM, few posts.
- Switcher 8 YOE Service Desk→AI: INSUFFICIENT X evidence.

WHAT IS MISSING
See Gaps sheet. Do not fill with training memory or Naukri counts.
""")

    def doc02(doc):
        add_h(doc, "Which 2 roles look real on X vs which are hype")
        add_p(doc, "This snapshot uses only public X posts in-window. Counts are an X-proxy from this scrape, not official demand.")
        add_h(doc, "Roles that look real (actual openings, not just talk)", 2)
        add_b(doc, [
            "Forward Deployed / AI Deployment Engineer — densest cluster of distinct India companies: Lyzr, Emergent, Katonic, OpenAI (Startups Deployment + Partner AWS 8+ YOE), AiPrise, RevRag, ElevenLabs, Applied Computing, Sarvam, Rhai, plus a first-hand 'first FDE in India' hire post. Work mode mix is on-site Bengaluru or remote-India, not Coimbatore.",
            "GenAI / Agentic AI Engineer — largest raw hiring-post volume (Cognizant Chennai hybrid, Sarvam Agent Engineer 3+, Senior AI Engineer Bengaluru ₹40–60 LPA asking production agents + FastAPI, Riverline, G2, Tailored AI, LeadSquared, Lexi remote). Many are 0–4 YOE. 8 YOE is not the modal band on X.",
        ])
        add_h(doc, "Roles that are real but thinner, or title-mismatched", 2)
        add_b(doc, [
            "Cloud AI Engineer — the exact title barely appears. Azure OpenAI / Azure AI Foundry / Vertex show up inside CGI (4–7 YOE Bengaluru hybrid), Cognizant (3.5–9 YOE multi-city), EY, NTT DATA, and a 10+ YOE Databricks+Azure OpenAI post. OpenAI Partner AI Deployment Engineer-AWS is the only first-hand 8+ YOE cloud-deployment req.",
            "Intelligent Automation — split market. Emplay 'Agentic AI Automation Engineer' 2+ YOE remote-India and MARS 'n8n/Make/Zapier' workflow engineer vs classic UiPath RPA (NTT, AIER, Amazon Hyderabad UiPath+LLM). Do not treat UiPath RPA as the same job as LangGraph agents.",
            "AI Solutions Engineer — Bolna Bengaluru is 0–2 YOE. BytePlus/ByteDance Solutions Architect India is the serious customer-facing PoC role (first-hand).",
            "AI Solutions Architect — OpenAI Applied AI Architect (Delhi URL in thread) plus a Hyderabad 8+ YOE AI Architect post (unnamed company, agentic infra, RBAC, chunking). Volume is low.",
        ])
        add_h(doc, "Hype-heavy vs titled openings", 2)
        add_b(doc, [
            "FDE TALK is huge (a16z fellowship, Gaurav Sen, Ashutosh +800% Indeed, Sanjay/ET 1,807% and TCS/Wipro/Infosys headcount targets). Treat those as talk/news recap. Actual X reqs are mostly startups + OpenAI, not those IT-major headcount numbers.",
            "AIOps TALK (Datadog Summit Bengaluru, coaches promising AIOps switches) is louder than AIOps Engineer titles. Titled/adjacent actuals are IBM fresher AIOps Developer, CGI Telco/OSS aggregator, Infosys HCI/command-center 7–12 YOE, Experian/Point72 Observability. Insufficient evidence of a thick 6–10 YOE 'AIOps Engineer' India market on X.",
            "AI Security — one Bengaluru 3+ YOE unnamed req, HCLTech aggregator JD (prompt injection defense), Infosys bundle, Proofpoint Hyderabad CoE news. Isolated '50,000 AI security engineers in demand' post has 1 like and no method. GAPS on volume.",
        ])
        add_h(doc, "Implication for an 8 YOE Service Desk Lead", 2)
        add_p(doc, "Best X-fit is not 'apply to AIOps Engineer on Naukri.' Best X-fit is FDE / AI deployment (client + production + ops judgment), with a secondary Azure-named GenAI engineer path if Python+RAG+agents can be demonstrated. AIOps is the conceptual home but the titled mid-senior opening trail on X is thin.")

    save_doc(F02 / "Demand_Snapshot.docx", "Demand snapshot — India X-proxy, Mar–Sep 2026", doc02)

    # ========== 01 Skills ==========
    must = [
        ["Forward Deployed / AI Deployment Engineer", "Python + APIs (FastAPI), customer integration (SSO/OAuth), RAG over customer data with permissions, deploy (Docker), observability/SLA, incident debugging + customer comms, translate messy workflows", "Strong consensus across FDE roadmaps + Lyzr/Rhai/OpenAI posts", "suraj_sharma14; Alacritic_Super; vineeth_agi; arjun_gupta95"],
        ["GenAI / Agentic AI Engineer", "Python, RAG, LangChain/LangGraph, vector DBs, FastAPI, production agents, evals, Docker, cloud (AWS/GCP/Azure)", "Strong consensus from 342-JD graphic + India JDs (Cognizant, Sarvam, Manali 40-60 LPA, LeadSquared)", "GauriTripa94282; mange_manali; JesseisCooking; Aakshayy12"],
        ["Cloud AI Engineer", "Azure OpenAI and/or Azure AI Foundry or Vertex; Python; RAG; agents; containers", "India JDs cluster on Azure/GCP product names more than generic 'cloud'", "VishalKumax4ekg; careerdjobs; offerscout"],
        ["AIOps Engineer", "Observability stack (Dynatrace/Splunk/Datadog/Azure Monitor), incident/ITIL/ServiceNow, some Python/automation; AIOps often a skill not the title", "Mixed. Mid-senior posts are command-center/HCI/observability, not LLM-native", "BHR300304; jobwharf; HitachiSysIndia"],
        ["Intelligent Automation Engineer", "Either (a) agents + n8n/Make/Zapier/LangGraph workflow automation OR (b) UiPath + Python/LLM", "Mixed two markets", "ajay_2512x Emplay; TheArthiAI MARS; Realized_Guy Amazon"],
        ["AI Security Engineer", "LLM/RAG security at a defensive level (prompt injection defense, guardrails, monitoring agents), product-security background", "Isolated/thin India JDs. Do not study exploit construction", "WhoShivaisnot; TheArthiAI HCLTech"],
        ["AI Solutions Engineer", "Customer discovery, PoCs, RAG/agents demo, Python/FastAPI, explain to sales + customer", "BytePlus first-hand; Bolna junior", "ayushpranav3"],
        ["AI Solutions Architect", "Agentic infra, RBAC, chunking strategies, 8+ YOE + 2–3 YOE agentic (one Hyderabad post)", "Isolated but on-profile YOE", "WhoShivaisnot"],
    ]
    diff = [
        ["All / FDE", "Production debugging of agents: traces, tool-call history, failed trajectories, idempotent tools, evals from failures", "Strong consensus (interview post, not a JD)", "ConsciousRide"],
        ["GenAI", "MCP, Langfuse/observability, guardrails, cost/latency, harness around the model", "Strong consensus globally; India JDs name MCP at NTT DATA and Syce nice-to-have", "ishanxtwt; mayaislam_ai; offerscout"],
        ["FDE", "Identity/SSO, tenant isolation, reversible changes, onsite with client tenants (Google/Microsoft)", "Mixed-to-strong for FDE specifically", "suraj_sharma14; vineeth_agi"],
        ["Cloud AI", "Azure AI Foundry by name (CGI), Microsoft Agent SDK / Google ADK (EY)", "Isolated JDs, high value if targeting those firms", "VishalKumax4ekg; careerdjobs"],
        ["Solutions", "Live PoC + expansion motion with sales", "BytePlus first-hand", "ayushpranav3"],
        ["Security", "Prompt injection defense on a GenAI platform (HCLTech JD text)", "Isolated", "TheArthiAI"],
        ["Java/SQL flag", "Some JDs still name Java and/or SQL. Do not make them the study core. See Overrated + Concepts sheets.", "Role-specific exceptions only", "AkshayKumar_JAK; agamin_ai; careerdjobs Cognizant; Tailored AI Text2SQL"],
    ]
    tools = [
        ["LangGraph / LangChain", "GenAI, Automation, Solutions", "Cognizant, EY, Manali Senior AI, Things Alive, BytePlus, 342-JD graphic", "Must-have in agentic JDs"],
        ["Python / FastAPI", "GenAI, FDE, Cloud AI, Solutions", "CGI, Manali, Riverline, BytePlus, FDE roadmaps", "Must-have"],
        ["Azure OpenAI / Azure AI Foundry", "Cloud AI, GenAI", "CGI, NTT DATA, Cognizant, EY, Databricks req", "Azure-first in this scrape, then GCP Vertex"],
        ["AWS", "FDE, Cloud AI", "OpenAI Partner AI Deployment Engineer-AWS (8+ YOE, first-hand)", "Named for the only explicit 8+ YOE deployment req"],
        ["GCP / Vertex / Google ADK", "Cloud AI, GenAI", "Cognizant, EY", "Second cloud after Azure in aggregator JDs"],
        ["MCP", "GenAI, Cloud AI", "NTT DATA must-have; Syce nice-to-have; BytePlus", "Rising differentiator"],
        ["Langfuse / observability / OpenTelemetry", "GenAI, AIOps, FDE", "342-JD graphic (Langfuse); FDE roadmaps (tracing, SLA); Cisco tokenomics+observability talk", "Must-have concept, few India JDs name Langfuse"],
        ["Datadog / Dynatrace / Splunk / Azure Monitor", "AIOps", "Infosys command center; Concentric SRE; Hitachi Datadog Summit talk", "Classic ops tools, not LLM tools"],
        ["ServiceNow / ITIL", "AIOps", "Infosys command center", "Ops mapping, not GenAI hiring keyword"],
        ["n8n / Make / Zapier", "Intelligent Automation", "MARS AI Workflow Engineer Delhi", "Named only in that JD in this scrape"],
        ["UiPath", "Intelligent Automation", "Amazon Hyderabad RPA+LLM; NTT; AIER", "Classic RPA path; Amazon adds LLMs"],
        ["Power Automate / Power Platform", "Intelligent Automation", "Ecolab Dynamics CRM (not an AI role); EY analyst post mentions Power Automate", "Insufficient X evidence as a core AI hiring skill"],
        ["Docker / Kubernetes", "GenAI, Cloud AI, FDE", "CGI, NTT, 342 JDs, FDE lists", "Deployment hygiene"],
        ["Vector DBs / RAG stack", "GenAI, FDE, Solutions", "Nearly every agentic JD", "Must-have"],
        ["SQL / Text2SQL / Java", "See flag", "IBM AIOps fresher Java-or-Python + SQL; Cognizant list includes SQL; Agamin Databricks SQL; Tailored AI Text2SQL; TekWissen AI Architect .NET/C#", "Do not add as core study. Mention only if targeting that JD"],
    ]
    concepts = [
        ["Agent harness", "Permissions, budgets, review points, rollback, definition of done around an agent that can call tools and retry. Analogized to a fast junior with prod access.", "ConsciousRide 2026-09-11", "Strong consensus with TechWithTimm production-layer post"],
        ["RAG vs tools/MCP", "RAG for large, slow-changing, read-only data (docs, runbooks, policies, past tickets). MCP/tools for live or write actions (current ticket, create issue). Do not dump 12 MCP servers into context.", "FranklinSolum 2026-09-10", "Strong practical split for ops projects"],
        ["Evals from failed trajectories", "When a demo-perfect agent fails in prod: traces, tool-call history, model outputs, token usage, one failed trajectory; then evals + deterministic guardrails on critical steps.", "ConsciousRide 2026-07-24 (8+ YOE AI Engineer interview story)", "Best 8 YOE interview signal in this scrape"],
        ["Five layers of a production agent", "Interface, orchestration, LLM, data, infrastructure (deploy, monitor, security, CI/CD, governance). Model choice is one piece.", "shubhangi_HR_ 2026-09-11", "Mixed (creator post) but matches JD lists"],
        ["Observability / LLMOps-lite", "Langfuse named in 342-JD graphic; OpenTelemetry guide; Cisco: token cost + observability. FDE roadmap: tracing, customer health, SLA, alerting.", "GauriTripa94282; freeCodeCamp; Cisco; suraj_sharma14", "Strong concept, thin India-named tool JDs"],
        ["Guardrails / prompt injection (defensive)", "HCLTech JD: protect GenAI+CV platform, prompt injection defense. Syce nice-to-have AI security & guardrails. Interview q: agent 73 tools / $14 spend — production guardrails beyond token limits.", "TheArthiAI; offerscout; nikks_techie", "Keep defensive/policy. No exploit how-to"],
        ["Identity / SSO / tenant isolation", "FDE 6-month plan: OAuth2, SAML, SSO, PII redaction, audit logs, permission-filtered RAG.", "suraj_sharma14", "Direct map from Service Desk identity/MFA work"],
        ["ITSM → AIOps mapping", "Command-center JDs still list ITIL + ServiceNow + Dynatrace + incident. CGI Telco/OSS uses AIOps for anomaly/fault prediction. Insufficient X posts explaining a 6–10 YOE 'LLM AIOps engineer' skill graph.", "BHR300304; TheArthiAI", "GAPS on LLM-native AIOps curriculum"],
        ["Stakeholder / demo skill", "BytePlus: discovery → architecture → demos/PoCs → implementation → expansion. Rhai FDE: explain to non-technical, earn trust, adoption. Lyzr: Shark Tank-style showcase.", "ayushpranav3; vineeth_agi; lyzr__ai", "Strong for FDE/Solutions"],
        ["SQL/Java exception", "IBM AIOps Developer screens Java or Python and SQL/NoSQL. Databricks 10+ YOE names SQL. Cognizant multi-city dump lists SQL. Tailored AI names Text2SQL. TekWissen AI Architect names .NET/C#. Not a reason to make Java/SQL the study path.", "Multiple JDs", "Flag only"],
    ]
    study = [
        ["Days 1–30", "Python + FastAPI enough to expose a tool API; take one real runbook/ticket corpus and build RAG with citations; log traces (even CSV/Langfuse lite); write 10 eval questions from real incident types you already know", "ishanxtwt order (APIs then RAG); FranklinSolum RAG-for-runbooks; Service Desk domain"],
        ["Days 31–60", "Add an agent with 2–3 tools only (search runbook, classify ticket, escalate). Guardrails: schema-valid args, approval on write, idempotency. Demo a failed trajectory and the eval that caught it.", "ConsciousRide prod debug; nikks_techie cost/tool-loop; FranklinSolum tool selection"],
        ["Days 61–90", "Deploy on Azure OpenAI or a named cloud (CGI/NTT/Cognizant language). Add identity-aware retrieval if possible. Package a 5-min customer demo + one-pager. Optional: n8n wrapper if targeting automation JDs.", "CGI/NTT Azure JDs; BytePlus PoC motion; MARS n8n only if that path"],
        ["Do not spend 90 days on", "Java, SQL-as-core, LoRA/QLoRA unless a named JD requires it, UiPath cert unless targeting Amazon/NTT RPA, wallpaper AI-900 as a substitute for the project", "342 JDs mention LoRA but India mid-senior FDE/ops JDs do not; cert posts are promotional"],
    ]
    overrated = [
        ["Prompt-only / ChatGPT-on-resume", "Hiring talk and JD lists moved to production systems, evals, agents, observability", "GauriTripa94282; ishanxtwt; AiswaryaVenkit1"],
        ["Pure DSA as the AI interview", "Arsh Goyal: funded AI startups in India asking RAG, inference, system design, deployment, not pure DSA. Mixed: some SDE loops still exist (US AI security startup post listed DSA).", "arsh_goyal — Mixed"],
        ["Java as core for these 8 roles", "Only IBM fresher AIOps Developer listed Java or Python. TekWissen architect listed .NET/C#. Not a core path.", "Explicit exception list only"],
        ["SQL as core study", "Appears in some JDs (IBM, Cognizant dump, Databricks, Text2SQL). Not what FDE/agentic India posts lead with. Learn only enough to read ticket/CMDB extracts if a named JD requires it.", "Flag, do not roadmap"],
        ["Fine-tune/LoRA first", "On 342-JD graphic, not on FDE/OpenAI-India/Cognizant Chennai posts. Evals + RAG + tools first.", "Mixed / overrated for this profile"],
        ["ITIL certification as AI differentiator", "ITIL appears on Infosys command-center ops JD, not on OpenAI/Lyzr/Cognizant GenAI posts.", "Overrated for AI-titled roles"],
        ["Toy chatbot without evals or tools", "Interviewer @shrav_10 rejected vibe-coded medical chatbot without domain/data discipline. Franklin: demo≠prod.", "Strong"],
    ]
    src01 = [
        src_row(dict(handle="GauriTripa94282", date="2026-09-11", pid="2098221645777551855", likes=72), "M1", "Mixed (graphic of 342 JDs, method not shown)", "RAG, LangChain, FastAPI, vector DBs, prompt, Docker, AWS/GCP, LangGraph, LoRA, Langfuse", "Skill frequency proxy — not India-only"),
        src_row(dict(handle="ishanxtwt", date="2026-09-10", pid="2098027434822279381", likes=26), "M1", "Isolated but consistent with JDs", "Learn APIs, RAG, agents, MCP, evals+observability, routing, queues, auth, Docker/K8s, cost", "30/60/90 backbone"),
        src_row(dict(handle="mayaislam_ai", date="2026-09-10", pid="2097883049640051168", likes=54), "M1", "Mixed creator consensus", "Agents, MCP, evals, guardrails, observability, harness", "Overrated: prompts-only"),
        src_row(dict(handle="ConsciousRide", date="2026-07-24", pid="2080532465291280653", likes=50), "M1/M3", "Isolated first-hand interview story (8+ YOE, geography unstated)", "Prod agent failure: traces, tool history, evals, idempotency, guardrails", "Best 8 YOE technical bar found"),
        src_row(dict(handle="ConsciousRide", date="2026-09-11", pid="2098289647508144366", likes=25), "M1", "Isolated", "Harness = permissions, budgets, reviews, rollback", "Concept note"),
        src_row(dict(handle="shubhangi_HR_", date="2026-09-11", pid="2098256933124010487", likes=21), "M1", "Mixed creator", "Five layers of enterprise agent", "Architecture language for resume/interviews"),
        src_row(dict(handle="FranklinSolum", date="2026-09-10", pid="2098003961194148337", likes=31), "M1/M4", "Isolated practitioner", "RAG for runbooks/tickets; MCP for live writes; 2–3 tools", "Project design rule"),
        src_row(dict(handle="suraj_sharma14", date="2026-09-01", pid="2094771110399357188", likes=831), "M1", "Mixed (high-engagement roadmap, not a hiring manager)", "12-stage FDE plan including identity, RAG ACLs, SLA, incident comms", "FDE study map; maps to Service Desk"),
        src_row(dict(handle="Alacritic_Super", date="2026-07-04", pid="2073273575075975531", likes=751), "M1", "Mixed; includes SQL — flag", "FDE skill dump: Python/Go/Rust, APIs, SQL, k8s, RAG, agents, MCP, OTel, incident response", "Do not copy SQL as core because this list includes it"),
        src_row(dict(handle="nikks_techie", date="2026-09-10", pid="2097873616247599332", likes=26), "M1/M3", "Isolated interview question", "Agent $0.08 → $14 with 73 tools: guardrails beyond token cap", "Interview + production concept"),
        src_row(dict(handle="TechWithTimm", date="2026-09-04", pid="2095859432966283521", likes=21), "M1", "Mixed", "MCP, skills, sandbox, sub-agents, human approvals, observability", "Production agent checklist"),
        src_row(dict(handle="mange_manali", date="2026-08-03", pid="2084236353877967017", likes=68), "M1/M2", "Actual opening", "4+ YOE, Python, LangGraph, RAG, production agents, FastAPI, ₹40–60 LPA", "India mid-senior GenAI bar"),
        src_row(dict(handle="VishalKumax4ekg", date="2026-09-05", pid="2096098136158806424", likes=0), "M1/M2", "Actual opening (0 likes aggregator)", "CGI 4–7 YOE Azure AI Foundry + Azure OpenAI + RAG", "Azure-first Cloud AI"),
        src_row(dict(handle="AkshayKumar_JAK", date="2026-08-06", pid="2085331204858093584", likes=42), "M1", "Actual opening — Java/SQL exception", "IBM AIOps Developer fresher: Java or Python, SQL/NoSQL", "Do not generalize to 8 YOE study path"),
        src_row(dict(handle="AiswaryaVenkit1", date="2026-09-07", pid="2096788042212384792", likes=95), "M1/M6", "Mixed (Microsoft CSA in India; also selling a newsletter)", "Microsoft agent cert ladder, then: certificates don't make you expert; execution + projects do", "Cert humility"),
    ]
    save_wb(F01 / "Skills_Roadmap.xlsx", [
        ("Role_Map_Lite", ["Primary role", "X variants / adjacent titles", "Note"], role_map, [32, 70, 50]),
        ("Must_Have_Skills", ["Role", "Must-haves from X", "Consensus", "Handles"], must, [36, 70, 40, 40]),
        ("Differentiator_Skills", ["Role", "Differentiator", "Consensus", "Handles"], diff, [28, 70, 40, 40]),
        ("Tools_Platforms_Services", ["Tool / platform", "Roles", "Where named on X", "Use"], tools, [32, 28, 55, 36]),
        ("Concepts_Explained", ["Concept", "What X actually said", "Source", "Consensus"], concepts, [28, 70, 36, 36]),
        ("Study_30_60_90", ["Window", "Plan for this Service Desk lead", "Why (X)"], study, [16, 80, 50]),
        ("Overrated_Skills", ["Skill / habit", "What X said", "Consensus"], overrated, [32, 70, 36]),
        ("Source_Posts", ["Handle", "Date", "Takeaway", "URL", "Why useful", "Likes", "Consensus class", "Module"], src01, [18, 14, 55, 42, 28, 10, 36, 10]),
    ])
    write_txt(F01 / "01_README.txt", """
01_README — Folder 01 Skills, domains, roadmap
Window: 2026-03-11 to 2026-09-11. X only.

QUERIES
- ("AIOps" OR observability OR Datadog OR Dynatrace OR Splunk OR "Azure Monitor") (skills OR roadmap OR learn OR "must know") min_faves:15 -filter:replies
- ("agentic AI" OR LangGraph OR CrewAI OR AutoGen OR "AI agent") (skills OR roadmap OR production) min_faves:20 -filter:replies
- ("Cloud AI" OR "Azure AI Foundry" OR "Azure OpenAI" OR Bedrock OR Vertex) (India OR engineer OR skills) min_faves:10 -filter:replies  → mostly noise (ISRO "bedrock") until hiring queries used product names
- ("AI security" OR "prompt injection" OR "LLM guardrail" OR "AI governance") (skills OR hiring OR job) min_faves:10 -filter:replies
- Semantic: FDE skills India; Azure AI Foundry hiring
- (Java OR SQL) ("GenAI Engineer" OR "AI Engineer" OR AIOps) (must OR required OR screening) (India OR Bengaluru) → ZERO HITS. Exceptions came from JD bodies instead.

CONFIDENCE
- Production-agent skill list (Python, RAG, LangGraph, FastAPI, evals, observability): MEDIUM, repeating across JDs + creator posts.
- India-specific 6–10 YOE AIOps skill graph: LOW / GAPS.
- CrewAI/AutoGen: insufficient named India hiring signal vs LangGraph.
- Bedrock: insufficient in this India scrape vs Azure OpenAI / Vertex.

GAPS
- Almost no first-hand Service Desk → AIOps skill posts from India switchers.
- Azure Monitor rarely named vs Datadog/Dynatrace/Splunk on ops JDs.
- Power Platform as AI hiring skill: insufficient.
""")

    def doc01(doc):
        add_h(doc, "Who this plan is for")
        add_p(doc, "8+ years Service Desk / operations lead, Coimbatore/TN, large IT services, basic-to-intermediate AI, targeting India hybrid/WFH-friendly AI roles. Java/SQL are not the core path unless a named JD forces them.")
        add_h(doc, "What X actually said (not topic labels)", 2)
        add_b(doc, [
            "Ishan (2026-09-10): if learning AI engineering from scratch in 2026, do not start with prompting. Order: APIs+backend, RAG+vector search, agents+tool calling, MCP, evals+observability, inference+routing, queues, auth/security, Docker/K8s, cost+latency.",
            "Maya (2026-09-10): prompts are the beginning; 2026 skills are agents, MCP, evals, guardrails, observability, agent harness.",
            "Gauri graphic (2026-09-11): claimed 342 AI engineering JDs surface RAG, LangChain, FastAPI, vector DBs, prompt engineering, Docker, AWS/GCP, LangGraph, LoRA, Langfuse. Method not shown — Mixed.",
            "Akshay Shinde (2026-07-24): 8+ YOE AI Engineer interview. Missing MCP trivia did not matter. Debugging a demo-good / prod-bad agent did: traces, tool-call history, token usage, failed trajectory, context pollution, flaky tool, retries with side effects, evals, guardrails, idempotency.",
            "Franklin Solum (2026-09-10): RAG is for runbooks, policies, past tickets. Tools/MCP are for live ticket state and writes. Load 2–3 tools for the current state, not 12 MCP servers.",
            "Suraj Sharma FDE plan (high engagement): identity/SSO, tenant isolation, permissioned RAG, Docker/K8s, tracing, SLA dashboards, incident comms, runbooks, stakeholder translation, ROI. This is the closest published map to a Service Desk lead's existing muscles.",
            "CGI Bengaluru 4–7 YOE JD text: Python, FastAPI, Azure AI Foundry, Azure OpenAI, RAG, Docker/K8s. NTT DATA Bengaluru: Azure OpenAI + Agentic AI + MCP. Cognizant Chennai: Python + LangGraph + RAG.",
        ])
        add_h(doc, "30 / 60 / 90 for this profile", 2)
        add_h(doc, "Days 1–30 — APIs + one ops RAG", 3)
        add_b(doc, [
            "Python: functions, errors, HTTP, environment variables. FastAPI: one POST that classifies a dummy incident and one GET that retrieves a runbook chunk.",
            "Corpus: 20–50 anonymized runbook/SOP/incident-summary style documents (your domain: identity, MFA, monitoring alerts, P1 bridge language). No real customer PII.",
            "RAG: embeddings + retrieval with citations. Metric: recall@5 on 15 questions you write from real ticket types (password reset vs token expiry vs downstream app vs false alert).",
            "Trace every answer: query, chunks, model output. That is LLMOps-lite. Langfuse if you can; a JSON log if you cannot.",
        ])
        add_h(doc, "Days 31–60 — agent with a harness, not a chatbot", 3)
        add_b(doc, [
            "Agent tools (max three): retrieve_runbook, classify_and_route, escalate_or_open_ticket (dry-run). Schema-validate arguments.",
            "Harness from X: permission scopes, a spend/step budget, human review on writes, rollback/idempotency on ticket updates, definition of done.",
            "Break it on purpose: force a flaky tool and a retry. Show the failed trajectory and the eval that catches repeated side effects (Akshay Shinde bar).",
            "Add a cost guardrail inspired by the $0.08→$14 / 73-tool interview question: max tool calls, max tokens, abort-and-page-human.",
        ])
        add_h(doc, "Days 61–90 — deploy + demo like FDE/solutions", 3)
        add_b(doc, [
            "Deploy behind Azure OpenAI or Azure AI Foundry language if that is your cloud login world (CGI/NTT/Cognizant JDs). AWS only if you are aiming at the OpenAI Partner AWS 8+ role.",
            "Add identity-aware notes: what would SSO/RBAC change in retrieval (Suraj FDE stages 2–5). You already speak MFA/identity — phrase it as permission-filtered RAG, not 'I did L2 resets.'",
            "5-minute demo: one P1-style incident, retrieval citations, tool trace, a blocked write, eval score, cost. That is the Lyzr/BytePlus motion.",
            "Optional fork: wrap the same agent in n8n only if you chase AI Workflow / automation JDs (MARS named n8n/Make/Zapier). Do not start with UiPath unless you want Amazon/NTT RPA.",
        ])
        add_h(doc, "Java / SQL", 2)
        add_p(doc, "Do not study Java or SQL as core. Exceptions actually posted: IBM fresher AIOps Developer (Java or Python, SQL/NoSQL); Cognizant multi-city dump lists SQL; Databricks 10+ YOE names SQL; Tailored AI names Text2SQL; TekWissen AI Architect names .NET/C#. If you later target one of those JDs, add the named item then — not now.")
        add_h(doc, "GAPS", 2)
        add_p(doc, "Insufficient X evidence for a Service Desk-specific 6–10 YOE AIOps Engineer curriculum in India. CrewAI/AutoGen hiring signal was weaker than LangGraph. Power Platform was not a primary AI hiring skill in this scrape.")

    save_doc(F01 / "Concepts_And_Study_Plan.docx", "Concepts and 30/60/90 study plan — Service Desk lead", doc01)

    # ========== 03 Interviews ==========
    questions = [
        ["GenAI / Agentic", "Last GenAI project, architecture, retrieval pipeline, RAG eval metrics, Python coding, system design: AI interview platform", "kris_aieng", "2026-07-23", "2080198468283376070", "First-hand candidate. Geography unstated. Mixed for India."],
        ["GenAI / Agentic", "RAG vs Agents — what RAG can/can't do, tool calls, agentic RAG (Gaurav Sen says this was a real big-tech question)", "gkcs_", "2026-08-21", "2090906582544683020", "Educator restating an interview Q. Mixed."],
        ["GenAI / Agentic", "Dataset provenance + domain expert + false positive vs false negative on a medical chatbot. Rejected 'vibe-coded' answers.", "shrav_10", "2026-06-26", "2070543542846718391", "First-hand interviewer. India-likely. Strong on anti-toy-projects."],
        ["GenAI / Agentic", "Demo-good agent fails randomly in prod. Ask for traces, tool history, token usage, failed trajectory. Context pollution, flaky tool, retry side effects, evals, guardrails, idempotency.", "ConsciousRide", "2026-07-24", "2080532465291280653", "First-hand 8+ YOE story. Geo unstated. Strong technical bar."],
        ["GenAI / Agentic", "Agent cost $0.08 → $14, 73 tools, 40 LLM calls. Token limit is insufficient. Production guardrails?", "nikks_techie", "2026-09-10", "2097873616247599332", "Isolated interviewer-style post."],
        ["GenAI / Agentic", "Invalid LLM response mid 12-step agent task: fallback architecture (wrong format, hallucinated tool, refusal).", "system_monarch", "2026-05-09", "2053089698185400704", "Labeled Anthropic system design. Not India. Isolated/global."],
        ["GenAI / Agentic", "Candidate complaint: after DSA prep, interviews asked system design, agentic AI, machine coding, RAG project, pipelines, k8s, docker.", "riskyyy_ghost", "2026-09-02", "2095042314439950646", "Hinglish candidate. India-likely. Isolated, 14 likes."],
        ["Cloud / SSE India", "Cloudflare Bangalore SSE: HM behavioral; LLM batch processing + rate limiting design; scheduled HTTP ping; debugging/code review; GenAI usage + coding agents + limitations.", "ajay_2512x", "2026-04-14", "2043958845949743529", "India (Bangalore) loop recap. Not one of the 8 titles but useful round pattern. Comp figures are second-hand — do not treat as offer proof."],
        ["FDE", "Lyzr: Apply → HackerRank → build a working solution → structured interviews → Shark Tank-style showcase.", "ajay_2512x / lyzr__ai", "2026-09-09", "2097537517621018912", "First-party process on X. Strong for FDE India."],
        ["FDE / switcher", "Arsh Goyal: funded AI startup interviews in India center on RAG, inferencing, system design, deployment, fine-tuning — not pure DSA. Syllabus not standardized. Use first 3–5 interviews as calibration.", "arsh_goyal", "2026-07-17", "2078002357569479153", "India educator. Mixed (advice, not a scorecard). Replies disputed Naukri."],
        ["AIOps", "GAPS — no first-hand 'AIOps interview questions' India posts in this scrape.", "", "", "", "Insufficient X evidence in window"],
        ["AI Security", "GAPS — no first-hand India AI Security interview question bank. HCLTech JD implies prompt-injection defense conceptually.", "TheArthiAI", "2026-08-16", "2089058867569402026", "JD not interview"],
        ["Solutions / Architect", "BytePlus: customer-facing discovery → architecture → demo/PoC → implementation. Expect scenario + demo, not only coding.", "ayushpranav3", "2026-08-25", "2092098138907807811", "Inferred from first-hand JD, not a candidate recap"],
    ]
    rounds = [
        ["FDE (Lyzr Bengaluru)", "Screen / HackerRank", "Live or take-home build", "Structured interviews", "Shark Tank showcase (stakeholder)", "Offer same day claimed", "lyzr__ai"],
        ["Senior AI/ML (kris_aieng)", "Intro + last project", "Architecture + retrieval + RAG evals", "Python coding", "System design", "Unknown", "kris_aieng"],
        ["Cloudflare Bangalore SSE", "HM 30m behavioral", "90m LLM system design", "60m infra design", "Debug/review + GenAI-usage round", "C-suite pending in recap", "ajay_2512x"],
        ["AI Engineer interviewer (shrav_10)", "Screen implied", "Project interrogation (data, domain, risk)", "GAPS", "GAPS", "Reject on vibe-coded domain project", "shrav_10"],
        ["Generic India AI startup (arsh_goyal)", "Apply + cold DM", "RAG / inference / design / deploy discussion", "Not standardized", "GAPS", "GAPS", "arsh_goyal"],
        ["AIOps titled", "GAPS", "GAPS", "GAPS", "GAPS", "GAPS", "Insufficient X evidence"],
    ]
    switcher = [
        ["8 YOE software (not Service Desk) AI Engineer loop", "Prod failure debugging beat buzzword trivia", "ConsciousRide", "No Service Desk→AI first-hand India recap found"],
        ["Already-in-AI switchers", "Arsh: RAG/system design/deployment interviews; claims 20→40→60 LPA in 1–1.5 years for people already in AI", "arsh_goyal", "Advice is for people already in AI, not Service Desk leads"],
        ["Fresh / junior AI engineer", "Many JDs 0–3 YOE; intern FDE; Things Alive 0–1 LangGraph", "Multiple hiring posts", "Different bar: build demos vs ops judgment"],
        ["Service Desk 8 YOE → these 8 titles", "GAPS — no first-hand India interview recap in window", "", "Do not invent"],
    ]
    reject = [
        ["Vibe-coded domain project without data/domain discipline", "shrav_10", "2070543542846718391", "Strong (interviewer)"],
        ["Answers too long / not the question (system design heavy loop)", "kris_aieng", "2080198468283376070", "Isolated first-hand"],
        ["Starting system design by drawing boxes without scale/consistency questions", "venkateshdotdev", "2096896705543446554", "Generic SD advice, not AI-specific"],
        ["Relying on AI-tailored resume then failing human/AI screen", "_jaydeepkarale; ivyasaa", "2094116942135349558", "Mixed meme + article; not a hiring manager"],
        ["ChatGPT voice speaking during a live interview", "Madhav_XO", "2097390797838803227", "Isolated intern story"],
        ["Knowing MCP trivia but not prod traces (inverse: trivia did NOT reject)", "ConsciousRide", "2080532465291280653", "Isolated"],
        ["Service Desk resume with ChatGPT keywords", "", "", "GAPS — phrase not found as an India recruiter post in this scrape. Closest is AI-resume doom loop generally."],
    ]
    takehome = [
        ["Lyzr FDE", "Build a working solution before onsite; live evaluation + showcase", "Bengaluru", "2097537517621018912", "Strong FDE signal"],
        ["Retape AI founding MTS", "Take-home + 2 technical + culture", "Bengaluru", "2085230421248451049", "Adjacent AI role, 1–3 YOE"],
        ["Manali Senior AI Engineer", "Not stated as take-home; production agents + FastAPI required", "Bengaluru", "2084236353877967017", "Skill screen more than process"],
        ["OpenAI Partner AWS 8+", "Process not posted beyond apply/referral form", "India remote", "2095168999470604338", "GAPS on rounds"],
        ["AIOps", "GAPS", "", "", "Insufficient X evidence"],
    ]
    sd_adv = [
        ["Prod agent failed trajectory / traces / tool history", "You already do incident timelines, bridge calls, and RCA. Frame monitoring traces = agent traces.", "ConsciousRide"],
        ["Fallback when a 12-step workflow returns garbage", "ITSM escalation matrix, major-incident comms, known-error vs new incident.", "system_monarch (global Q) + your ops experience"],
        ["Guardrails when an agent loops 73 tools", "Change-control, spend limits, 'stop and page human' — same muscle as runaway automation/scripts.", "nikks_techie"],
        ["RAG over runbooks vs live ticket tool", "You already know stale runbook vs live ticket state. Franklin's split is your job."],
        ["Permission-filtered retrieval / SSO", "Identity, MFA, RBAC support work maps to FDE stages 2–5 (Suraj)."],
        ["Customer/stakeholder demo", "Client-facing Service Desk lead → BytePlus PoC motion / Lyzr showcase / Rhai 'earn trust'."],
        ["False positive vs missed incident", "Monitoring alert tuning. shrav_10 medical FP/FN is the same judgment in a different domain."],
        ["AIOps interview question bank", "GAPS — cannot list real AIOps questions from X India first-hand posts."],
    ]
    src03 = [
        src_row(dict(handle="arsh_goyal", date="2026-07-17", pid="2078002357569479153", likes=266), "M3", "Mixed India educator", "AI startup interviews = RAG/inference/design/deploy not pure DSA", "Switcher advice; not Service Desk specific"),
        src_row(dict(handle="kris_aieng", date="2026-07-23", pid="2080198468283376070", likes=304), "M3", "First-hand candidate, geo unstated", "Project architecture, RAG evals, Python, AI interview-platform design", "Round pattern"),
        src_row(dict(handle="ajay_2512x", date="2026-04-14", pid="2043958845949743529", likes=215), "M3", "Second-hand India loop", "Cloudflare Bangalore SSE including GenAI-usage round", "India onsite pattern"),
        src_row(dict(handle="shrav_10", date="2026-06-26", pid="2070543542846718391", likes=288), "M3", "First-hand interviewer", "Reject vibe-coded medical chatbot", "Project quality bar"),
        src_row(dict(handle="ConsciousRide", date="2026-07-24", pid="2080532465291280653", likes=50), "M3", "First-hand 8+ YOE", "Prod traces > buzzwords", "Best 8 YOE bar"),
        src_row(dict(handle="gkcs_", date="2026-08-21", pid="2090906582544683020", likes=533), "M3", "Educator", "RAG vs Agents interview Q", "Concept Q to practice"),
        src_row(dict(handle="system_monarch", date="2026-05-09", pid="2053089698185400704", likes=131), "M3", "Global / Isolated", "Agent fallback architecture", "Practice Q, not India"),
        src_row(dict(handle="nikks_techie", date="2026-09-10", pid="2097873616247599332", likes=26), "M3", "Isolated", "Runaway agent cost guardrails", "Ops-friendly Q"),
        src_row(dict(handle="lyzr__ai", date="2026-09-07", pid="2096930973544005806", likes=2), "M3", "First-party FDE process", "Build then Shark Tank showcase", "FDE India process"),
        src_row(dict(handle="amitiitbhu", date="2026-08-04", pid="2084492484986495400", likes=392), "M3", "Educator list", "LLM, RAG, agents, LLMOps, eval, safety, system design", "Syllabus dump, not first-hand"),
        src_row(dict(handle="riskyyy_ghost", date="2026-09-02", pid="2095042314439950646", likes=14), "M3", "Isolated candidate", "System design + agentic + RAG + k8s asked", "India-likely complaint"),
        src_row(dict(handle="_vmlops", date="2026-05-06", pid="2052068392249790975", likes=756), "M3", "Promotional PDF", "FDE interview roadmap/case studies file", "Talk; did not verify PDF contents as X text"),
    ]
    save_wb(F03 / "Interview_Bank.xlsx", [
        ("Questions_By_Role", ["Role cluster", "Question / theme", "Handle", "Date", "Post ID", "Notes"], questions, [28, 70, 18, 14, 22, 40]),
        ("Round_Pattern", ["Loop", "R1", "R2", "R3", "R4", "R5/outcome", "Source"], rounds, [28, 22, 28, 24, 28, 24, 16]),
        ("Switcher_vs_AI_Native", ["Candidate type", "What X said", "Handle", "Gap"], switcher, [40, 55, 18, 40]),
        ("Rejection_Reasons", ["Reason", "Handle", "Post ID", "Consensus"], reject, [55, 28, 22, 36]),
        ("Takehome_LiveBuild", ["Company/role", "Task", "Location", "Post ID", "Notes"], takehome, [28, 50, 18, 22, 36]),
        ("ServiceDesk_Advantage_Questions", ["Question theme", "How a Service Desk lead can answer without lying", "X hook"], [[a[0], a[1], a[2] if len(a)>2 else ""] for a in sd_adv], [40, 70, 36]),
        ("Source_Posts", ["Handle", "Date", "Takeaway", "URL", "Why useful", "Likes", "Consensus class", "Module"], src03, [18, 14, 50, 42, 28, 10, 28, 10]),
    ])
    write_txt(F03 / "01_README.txt", """
01_README — Folder 03 Interview questions / patterns
Window: 2026-03-11 to 2026-09-11. X only.

QUERIES
- ("AI interview" OR "AI engineer interview" OR "AIOps interview" OR "GenAI interview") (questions OR asked OR rejected OR "what they asked") (India OR Bengaluru OR Hyderabad) min_faves:10
  → almost no first-hand hits (NCS AI Interview Coach ad)
- ("system design" OR "case study" OR "take home") (GenAI OR agentic OR AIOps) interview min_faves:10
- ("take home" OR HackerRank OR "live build" OR assignment) (FDE OR "AI Engineer" OR "GenAI") (India OR Bengaluru OR Lyzr)
- Semantic: GenAI interview questions India; FDE interview India; career switch service desk AI

FIRST-HAND INTERVIEW POSTS COUNTED AS USEFUL
High: ConsciousRide (8+ YOE prod debug), kris_aieng (candidate), shrav_10 (interviewer), Lyzr process (company), arjun Cloudflare recap (India loop, second-hand), arsh_goyal (India market advice).
Low/noisy: NCS coach ad, educator dumps, Anthropic-branded SD questions, US PM system-design threads.

CONFIDENCE: LOW-MEDIUM overall. AIOps interview bank: INSUFFICIENT. Service Desk switcher recaps: INSUFFICIENT.
""")

    def doc03(doc):
        add_h(doc, "Confidence")
        add_p(doc, "There is no thick first-hand India bank of 'I interviewed for AIOps/FDE as an 8-year Service Desk lead.' What follows is a round pattern stitched from India FDE processes, India GenAI JDs, a few candidate/interviewer posts, and global questions that match those JDs. Gaps stay labeled.")
        add_h(doc, "Round-by-round pattern to prepare", 2)
        add_h(doc, "0. Recruiter / HM screen", 3)
        add_p(doc, "Why this role, why AI now, why not stay in operations. Translate: you ran enterprise incident/request operations, identity/MFA, monitoring, client comms; you are building production-shaped agents on that domain. Do not say you are an ML researcher. Arsh Goyal: syllabus is not standardized — treat the first interviews as reconnaissance.")
        add_h(doc, "1. Project interrogation (almost certain for GenAI/FDE)", 3)
        add_p(doc, "kris_aieng was asked: last GenAI project, architecture, retrieval pipeline, RAG eval metrics. shrav_10 asked where the dataset came from and whether a domain expert existed. Prepare one ops project (ticket/runbook agent) with: corpus, retrieval, tools, eval set, a failure, what you would not put in production.")
        add_h(doc, "2. Live build or take-home (FDE especially)", 3)
        add_p(doc, "Lyzr Bengaluru: HackerRank then build a working solution then a Shark Tank showcase. Practice a 90-minute slice: RAG over a folder of runbooks + one tool + a trace. Retape AI (adjacent) used take-home + 2 technical + culture.")
        add_h(doc, "3. Agentic system design", 3)
        add_b(doc, [
            "RAG vs Agents (Gaurav Sen / big-tech restatement).",
            "Fallback when step 6 of 12 is invalid (format / hallucinated tool / refusal).",
            "Runaway cost and tool loops (73 tools, $14).",
            "Demo-good / prod-bad agent: traces, context pollution, retries, idempotency (Akshay Shinde).",
            "Franklin split: retrieval for runbooks vs tools for live ticket writes.",
        ])
        add_h(doc, "4. Coding", 3)
        add_p(doc, "Python shows up (kris_aieng; Cognizant Python GenAI; FastAPI in JDs). Some candidate noise still mentions DSA. Arsh says funded AI startups are not pure DSA. Prepare Python: parse a JSON tool call, write a retry with idempotency key, sketch a FastAPI endpoint. Skip Java unless the JD named it.")
        add_h(doc, "5. Stakeholder / showcase", 3)
        add_p(doc, "Lyzr showcase, BytePlus PoC, Rhai 'explain to non-technical and get adoption.' 5-minute demo: incident in, cited runbook, proposed action, blocked write, eval, cost. This is your Service Desk lead advantage if you do not overclaim model internals.")
        add_h(doc, "Example answers framed for 8 YOE operations → AI", 2)
        add_h(doc, "Q: Design fallback when the agent returns an invalid tool call mid-incident.", 3)
        add_p(doc, "Stop the write path. Show the invalid call on a trace like a failed change. Retry once with schema repair. If still invalid, page the human in the same way a P1 bridge pages L3. Do not retry ticket-create without an idempotency key — that is the duplicate-incident problem we already know. Log the failed trajectory into the eval set (Akshay Shinde).")
        add_h(doc, "Q: RAG or an agent for this Service Desk use case?", 3)
        add_p(doc, "If the user needs a cited procedure from a runbook, RAG. If they need 'open a ticket / reset in the IdP / ack the alert,' that is a tool with auth. Franklin: do not stuff live write tools and the entire runbook corpus into one context window.")
        add_h(doc, "Q: How do you know it works?", 3)
        add_p(doc, "An eval set of real ticket types, retrieval recall, tool-receipt checks ('model said it used the tool' with no receipt), and a cost/step budget. Not a screenshot of ChatGPT.")
        add_h(doc, "What not to do", 2)
        add_b(doc, [
            "Do not invent ML math depth you do not have. X bars here are systems + agents + ops judgment more than derivations.",
            "Do not bring a vibe-coded medical/legal chatbot. Interviewers are already allergic (shrav_10).",
            "AIOps-specific question bank: Insufficient X evidence in window.",
        ])

    save_doc(F03 / "Interview_Playbook.docx", "Interview playbook — 8 YOE operations to AI", doc03)

    # ========== 04 Projects ==========
    ranked = [
        [1, "Incident / ticket copilot with runbook RAG + 2–3 tools + evals + traces", "High X hiring signal (JD cluster + Franklin + Rohith + interview bars). No India 'this got me the offer' post found.", "AIOps, FDE, GenAI, Automation", "Strong map from Service Desk", "Build first"],
        [2, "Permissioned knowledge RAG over runbooks/SOPs with citations and stale-doc flags", "Franklin explicitly names runbooks/policies/past tickets as RAG; FDE plan stages 5+9", "FDE, AIOps, Solutions", "Strong", "Same spine as #1 if timeboxed"],
        [3, "Customer-workflow agent (FDE-shaped): messy process → agent + human approval + rollback", "Lyzr live-build; Rhai FDE; BytePlus PoC; OpenAI deployment language", "FDE, Solutions Engineer", "Strong if you pick a workflow you have actually supported", "Second project"],
        [4, "Agent eval harness + tracing (failed trajectories, tool receipts, cost budget)", "Sarvam Agent Engineer lists Evals; ConsciousRide; nikks_techie; 342 JDs Langfuse", "GenAI, FDE, Cloud AI", "Medium-strong", "Can be the test suite of #1, not a separate toy"],
        [5, "Azure OpenAI / Foundry deployment of the ops agent (identity, logs, cost)", "CGI, NTT, Cognizant, EY JDs name Azure AI products", "Cloud AI Engineer", "Medium", "Days 61–90 wrapper"],
        [6, "Ticket classification + routing agent", "Rohith built intent classification + RAG + safety escalation (student, not 'got hired')", "Automation, AIOps, GenAI", "Medium", "Subset of #1"],
        [7, "AI security review checklist automation (defensive): prompt-injection test cases, logging, redaction", "HCLTech JD names prompt injection defense; Syce nice-to-have guardrails. Thin 'got hired' signal.", "AI Security", "Low/thin", "Only if targeting HCLTech-like JDs"],
        [8, "Cloud cost / anomaly agent", "Insufficient X India hiring/project-hire signal in this scrape", "Cloud AI", "GAPS", "Do not start here"],
        [9, "Classic UiPath RPA + LLM", "Amazon Hyderabad names UiPath+LLM; NTT/AIER are RPA-only", "Intelligent Automation (RPA fork)", "Role-specific", "Only if chasing RPA JDs"],
        [10, "Toy ChatGPT wrapper / generic chatbot", "shrav_10 reject; Franklin demo≠prod; Aiswarya projects>certs", "None", "Negative signal", "Do not build"],
    ]
    domain = [
        ["Incident copilot", "ITSM / enterprise ops", "Python, FastAPI, RAG, LangGraph or equivalent, 2–3 tools, tracing", "P1 language, runbooks, routing"],
        ["Runbook RAG", "Knowledge / major incident", "Vector DB, citations, stale flags", "SOP quality"],
        ["FDE workflow agent", "Client ops process (identity, access, monitoring noise)", "SSO notes, approval, rollback", "Client-facing"],
        ["Eval harness", "LLMOps-lite", "Langfuse or JSON traces, eval set, cost caps", "Quality engineering"],
        ["Azure deploy", "Cloud AI", "Azure OpenAI/Foundry, Docker, logs", "CGI/NTT language"],
        ["Defensive AI security checklist", "GenAI platform risk", "Logging, redaction, injection test prompts as tests not exploits", "HCLTech-like JDs only"],
    ]
    demo = [
        ["Incident copilot", "5 min: noisy alert → cited runbook → classified queue → blocked auto-write → eval score + token cost", "retrieval recall@5, % cited answers, duplicate-ticket rate, max tool-calls aborted", "Franklin + ConsciousRide + nikks_techie"],
        ["Runbook RAG", "5 min: two similar incidents, one stale SOP caught", "% answers with citation, stale-doc catch", "Franklin"],
        ["FDE workflow", "5 min: as-is messy process vs agent with human gate and undo", "time-to-first-successful-run, rollback demo", "Lyzr/Rhai/BytePlus"],
        ["Eval harness", "5 min: failing eval turned green after guardrail", "eval pass rate, cost per task", "Sarvam evals; 342 JDs Langfuse"],
    ]
    role_map_p = [
        ["Incident copilot", "AIOps Engineer", "Primary"],
        ["Incident copilot", "Forward Deployed / AI Deployment Engineer", "Primary"],
        ["Incident copilot", "GenAI / Agentic AI Engineer", "Primary"],
        ["Incident copilot", "Intelligent Automation Engineer", "Secondary"],
        ["Runbook RAG", "AIOps / FDE / Solutions", "Primary knowledge layer"],
        ["FDE workflow agent", "FDE / Solutions Engineer / Architect", "Primary"],
        ["Azure deploy wrapper", "Cloud AI Engineer", "Primary"],
        ["Defensive security checklist", "AI Security Engineer", "Only if targeting that title"],
        ["UiPath+LLM", "Intelligent Automation (RPA)", "Fork, not default"],
    ]
    trans = [
        ["L1/L2 password/MFA/identity", "Permissioned retrieval + SSO/MFA notes in the FDE identity stages", "Do not write 'built an IdP'. Write 'designed agent auth boundaries from identity-support experience'."],
        ["P1/P2 incident bridge", "Failed-trajectory evals, fallback, human page, comms during outage (FDE stage 8)", "Use anonymized patterns, not client names or unpublished MTTR."],
        ["Monitoring / alert noise", "Classify/route + cost/loop guardrails", "No fake 'reduced alerts 40%' unless you have the number."],
        ["Runbooks / SOP / known errors", "RAG corpus + stale-doc detection", "Best project fuel you already have."],
        ["Client/stakeholder updates", "5-min demo + Shark Tank/PoC language", "BytePlus/Lyzr."],
        ["Automation scripts / standard changes", "Idempotent tools, approval on writes", "Akshay Shinde retry side effects."],
    ]
    src04 = [
        src_row(dict(handle="FranklinSolum", date="2026-09-10", pid="2098003961194148337", likes=31), "M4", "Isolated practitioner", "RAG for runbooks/tickets; MCP for live writes", "Project architecture"),
        src_row(dict(handle="Rohith_Itagi", date="2026-09-10", pid="2098068365491528166", likes=16), "M4", "Isolated student build", "Support agent: intent + RAG + LLM eval + safety escalation", "Closest public build; not a hire story"),
        src_row(dict(handle="Al_Grigor", date="2026-09-09", pid="2097686529179279732", likes=22), "M4", "Promotional course list", "Docs RAG, FAQ assistant, tool agent, observable app, eval pipeline", "Curriculum = portfolio shape, not 'got hired'"),
        src_row(dict(handle="shrav_10", date="2026-06-26", pid="2070543542846718391", likes=288), "M4", "Interviewer", "Vibe-coded domain chatbot fails", "Negative ranking signal"),
        src_row(dict(handle="lyzr__ai", date="2026-09-07", pid="2096930973544005806", likes=2), "M4", "Hiring process", "Build working solution, defend it", "Why production-shaped work"),
        src_row(dict(handle="GauriTripa94282", date="2026-09-11", pid="2098221645777551855", likes=72), "M4", "Mixed JD graphic", "Production skills including Langfuse", "What to show"),
        src_row(dict(handle="suraj_sharma14", date="2026-09-01", pid="2094771110399357188", likes=831), "M4", "Mixed roadmap", "Portfolio/case studies as FDE stage 12", "FDE project wrapping"),
        src_row(dict(handle="ayushpranav3", date="2026-08-25", pid="2092098138907807811", likes=218), "M4", "Actual opening", "PoCs, RAG/agents, FastAPI, customer journey", "Solutions project"),
        src_row(dict(handle="Web3Sniper1", date="2026-08-28", pid="2093269054987305389", likes=59), "M4", "Isolated, not India AI hiring", "Personal job-search agent → interviews", "Not ranked for this profile"),
    ]
    save_wb(F04 / "Projects_That_Hire.xlsx", [
        ("Ranked_Projects", ["Rank", "Project", "X hiring signal", "Roles", "Service Desk map", "Action"], ranked, [8, 55, 55, 28, 28, 22]),
        ("Domain_UseCase_Tools", ["Project", "Domain", "Tools", "Ops mapping"], domain, [28, 28, 50, 28]),
        ("Demo_And_Metrics", ["Project", "5-min demo", "Metrics (only if you can measure)", "X hook"], demo, [22, 70, 40, 28]),
        ("Role_Mapping", ["Project", "Role", "Fit"], role_map_p, [28, 40, 28]),
        ("ServiceDesk_Translation", ["Ops work", "Project language", "Honesty rule"], trans, [32, 55, 50]),
        ("Source_Posts", ["Handle", "Date", "Takeaway", "URL", "Why useful", "Likes", "Consensus class", "Module"], src04, [18, 14, 50, 42, 28, 10, 28, 10]),
    ])
    write_txt(F04 / "01_README.txt", """
01_README — Folder 04 Projects that hire
Window: 2026-03-11 to 2026-09-11. X only.

RANKING METHOD
Ranked by (a) overlap with India JDs in this scrape, (b) interview bars (evals, traces, anti-toy), (c) explicit practitioner architecture (Franklin), (d) FDE live-build processes.
NOT ranked by coolness. NOT ranked by 'someone on X said this got them an India AI offer' — that evidence was INSUFFICIENT (query pack returned marketplace/domain-spam).

QUERIES
- ("AI portfolio" OR "agentic project" OR "built an agent" OR "AIOps project") (hired OR offer OR interview OR "got the job") min_faves:10 -filter:replies  → weak/irrelevant
- (RAG OR "incident copilot" OR "ticket classification" OR runbook) (agent OR GenAI) (project OR production) min_faves:10 -filter:replies
- Semantic: incident copilot ticket classification RAG hired

GAPS
- No first-hand India post in this scrape of the form 'this AIOps/incident copilot project got me the offer.'
- Cloud cost/anomaly agents: insufficient.
""")

    def doc04(doc):
        add_h(doc, "How these were ranked")
        add_p(doc, "Hiring signal on X in this window, not novelty. There were almost no 'this project got me an India AI offer' posts. Ranking uses JDs + interview bars + FDE processes.")
        add_h(doc, "Project 1 — Incident copilot (build this first)", 2)
        add_p(doc, "Target roles: AIOps-adjacent, FDE, GenAI, intelligent automation.")
        add_b(doc, [
            "Stack: Python, FastAPI, one LLM API (Azure OpenAI if you can), vector store, LangGraph or a simple tool loop, JSON/Langfuse traces.",
            "Integrations: dummy ticket store (CSV/SQLite), runbook folder, optional n8n webhook later. Do not hack production ServiceNow.",
            "5-min demo: alert in → cited runbook → route suggestion → write blocked for human → show eval + cost.",
            "Metric: retrieval recall, citation rate, aborted loops, duplicate-create attempts stopped.",
            "Why it hires: matches Franklin's runbook/ticket split, Cognizant/Sarvam/Manali agent+RAG JDs, and the 8 YOE prod-debug interview.",
            "Why it maps: this is your job, instrumented.",
        ])
        add_h(doc, "Project 2 — FDE-shaped workflow agent", 2)
        add_p(doc, "Pick one workflow you have supported (access request, monitoring-noise triage, knowledge gap). Embed with a fake customer brief. Discovery notes, architecture, PoC, adoption risks. Matches Lyzr build + BytePlus PoC + Rhai 'messy domain'.")
        add_h(doc, "Project 3 — Eval/observability harness (can be the test suite of #1)", 2)
        add_p(doc, "Failed trajectories, tool receipts, cost budget, one dashboard. 342-JD graphic names Langfuse; NTT/Syce name MCP/guardrails. Do not present this without Project 1.")
        add_h(doc, "Project 4 — Azure wrap (Cloud AI fork)", 2)
        add_p(doc, "Same agent on Azure OpenAI/Foundry with identity and logs. For CGI 4–7 YOE / NTT / Cognizant language. Optional, days 61–90.")
        add_h(doc, "Skip unless targeting a named JD", 2)
        add_b(doc, [
            "UiPath+LLM: Amazon Hyderabad / NTT RPA only.",
            "Defensive security checklist: HCLTech-like AI Security JDs only. Policy and tests, not exploits.",
            "Cloud cost anomaly agent: insufficient X signal.",
            "Generic chatbot: negative signal (shrav_10).",
        ])
        add_h(doc, "Honesty", 2)
        add_p(doc, "Do not invent employer metrics. If you do not have MTTR numbers, demo the method and evals instead.")

    save_doc(F04 / "Project_Build_Briefs.docx", "Project build briefs — ranked by X hiring signal", doc04)

    # ========== 05 Resume + certs ==========
    headlines = [
        ["A", "Operations Lead (8+ YOE) → AI deployment / AIOps — incident, identity, monitoring, and client operations; building production-shaped agents on Azure", "FDE, Cloud AI, AIOps-adjacent", "Uses X language (deployment, agents, Azure) without claiming a title you do not hold"],
        ["B", "Service Desk Lead targeting Forward Deployed / Applied AI roles — runbooks, major incident, identity/MFA, automation-adjacent delivery", "FDE, Solutions", "Closer to current title; weaker on 'AI engineer' ATS"],
    ]
    bullets = [
        [1, "Lead-tier Service Desk / operations for enterprise clients (monitoring, incident, request).", "Lead enterprise client operations spanning monitoring, incident, and request flows, including stakeholder comms during high-severity events.", "FDE stage 8/10; do not add fake MTTR"],
        [2, "L1/L2/L3 handling.", "Worked across L1–L3 operating model: intake, deep troubleshooting, and escalation — translating user impact into technical next actions.", "Stop dumping L1/L2/L3 as the headline"],
        [3, "SLA ownership.", "Owned operational commitments (response/resolve expectations) and used them to prioritize incident work. [add a real figure only if you have one]", "FDE SLA monitoring language; no invented %"],
        [4, "Monitoring / alerts.", "Operated monitoring and alert intake; distinguished noisy alerts from user-impacting incidents — the same judgment agent routing has to get right.", "Maps to classify/route project"],
        [5, "Identity / MFA support.", "Supported identity and MFA issues in enterprise cloud logins; this is the operational side of SSO/MFA/RBAC that FDE posts list as customer-integration skill.", "suraj_sharma14 stages 2–4; do not claim you designed IAM"],
        [6, "Automation-adjacent / scripts / standard changes.", "Built or ran automation-adjacent operational work with change control — the habit behind idempotent tools and human-approval on writes.", "ConsciousRide retry side effects"],
        [7, "Azure / cloud logins.", "Daily operator on enterprise cloud/identity surfaces; currently applying that context to Azure OpenAI/Foundry-style deployments of an ops assistant. [only if true]", "CGI/NTT keyword without lying"],
        [8, "Client-facing.", "Client-facing operations lead: explained outages and next steps to non-technical stakeholders — the FDE/solutions 'earn trust / PoC' motion.", "BytePlus; Rhai; Lyzr showcase"],
    ]
    kw = [
        ["Forward Deployed / AI Deployment Engineer", "deployment, customer workflow, PoC, RAG, agents, Python, APIs, observability, incident, identity/SSO, runbooks", "FDE, Palantir-style, research scientist"],
        ["Cloud AI Engineer", "Azure OpenAI, Azure AI Foundry, RAG, Python, FastAPI, Docker, agents, MCP (if true)", "Bedrock unless targeting AWS-named JD"],
        ["AIOps Engineer", "observability, incident, ServiceNow/ITSM (if true), Dynatrace/Splunk/Datadog (if true), automation, RAG over runbooks", "Java unless IBM-like JD"],
        ["Intelligent Automation Engineer", "agents, workflow automation, LangGraph, n8n (if true), evaluation", "UiPath unless RPA JD"],
        ["GenAI / Agentic AI Engineer", "Python, RAG, LangGraph, FastAPI, evals, guardrails, tracing", "LoRA/QLoRA unless JD"],
        ["AI Solutions Engineer / Architect", "PoC, solutioning, RAG, agents, stakeholder demo, architecture", "20 YOE architect posts are not this profile"],
        ["AI Security Engineer", "guardrails, prompt-injection defense (conceptual), logging, data leakage prevention, identity", "Exploit writeups"],
    ]
    stop = [
        ["Wall of L1/L2/L3 + ticket counts with no outcome", "Reads as support-only; X FDE/GenAI posts want shipped systems + customer impact language"],
        ["ChatGPT / Copilot as the only AI proof", "ishan's 'don't start with prompting'; 342 JDs are production stacks; AI-resume doom loop posts"],
        ["Keyword stuffing GenAI/LLMOps with no project", "ivyasaa doom loop; _jaydeepkarale 'rejected by AI after using AI'"],
        ["Java/SQL as headline skills for these 8 roles", "Not the lead skill in FDE/agentic India posts; add only for named JDs"],
        ["ITIL as the AI differentiator", "Appears on command-center ops JDs, not OpenAI/Lyzr/Cognizant GenAI"],
        ["Fake metrics", "Prompt forbids inventing employer metrics. X also punishes vibe-coded claims (shrav_10)"],
        ["US salary screenshots", "Out of market"],
    ]
    ats = [
        ["Tailor per role; do not one-shot 8 titles", "X doom-loop posts: AI-optimized resumes vs harsher filters", "ivyasaa; _jaydeepkarale"],
        ["Lead with one production-shaped project, then ops translation", "Lyzr tests what you built; Arsh: build then interview", "lyzr__ai; arsh_goyal"],
        ["Azure OpenAI / Foundry / LangGraph / RAG / evals / FastAPI if true", "Named in India JDs", "CGI, Cognizant, NTT, Manali"],
        ["Length: X did not state a page count for this profile", "GAPS", ""],
        ["'Support resume with ChatGPT keywords' as exact reject phrase", "GAPS — not found as an India recruiter post. Closest: general AI-resume backlash", ""],
        ["OpenAI Partner AWS 8+ : technical consulting, AWS, coding, AI/ML deployment", "First-hand thread", "arjun_gupta95"],
    ]
    src05r = [
        src_row(dict(handle="_jaydeepkarale", date="2026-08-30", pid="2094116942135349558", likes=767), "M5", "Mixed meme, high engagement", "Rejected by AI after using AI to tailor resume for AI-written JD", "Anti keyword-stuffing"),
        src_row(dict(handle="ivyasaa", date="2026-09-05", pid="2096057746504536079", likes=3), "M5", "News recap, low engagement", "AI resume vs AI filters doom loop", "ATS caution"),
        src_row(dict(handle="AiswaryaVenkit1", date="2026-09-07", pid="2096788042212384792", likes=95), "M5/M6", "Mixed", "Certs ≠ expert; execution + projects", "Resume/cert split"),
        src_row(dict(handle="arsh_goyal", date="2026-07-17", pid="2078002357569479153", likes=266), "M5", "Mixed", "Build, apply widely, cold DM, interviews as calibration", "Process, not bullet formulas"),
        src_row(dict(handle="arjun_gupta95", date="2026-09-02", pid="2095168999470604338", likes=204), "M5", "First-hand 8+ YOE req", "Technical consulting + AWS + coding + AI/ML deployment", "Headline target for 8 YOE"),
        src_row(dict(handle="suraj_sharma14", date="2026-09-01", pid="2094771110399357188", likes=831), "M5", "Mixed roadmap", "Identity, incident comms, runbooks, ROI as FDE skills", "Translation dictionary"),
        src_row(dict(handle="KisekiyaCodes", date="2026-04-12", pid="2043286803860648167", likes=6), "M5", "Isolated joke", "Resume rejected in 0.3 seconds", "Not actionable"),
    ]
    save_wb(F05 / "Resume_Rewrite.xlsx", [
        ("Headline_Options", ["ID", "Headline", "Best roles", "Why"], headlines, [8, 80, 28, 50]),
        ("Bullet_Rewrites", ["#", "Do not write", "Write instead (candidate voice)", "Guardrail"], bullets, [6, 40, 70, 36]),
        ("Keywords_By_Role", ["Role", "Use if true", "Avoid unless JD"], kw, [36, 60, 36]),
        ("Stop_Mentioning", ["Stop / minimize", "Why (X)"], [[s[0], s[1]] for s in stop], [50, 70]),
        ("ATS_Notes", ["Note", "Evidence", "Handle"], ats, [55, 40, 22]),
        ("Source_Posts", ["Handle", "Date", "Takeaway", "URL", "Why useful", "Likes", "Consensus class", "Module"], src05r, [18, 14, 50, 42, 28, 10, 22, 10]),
    ])

    certs = [
        ["AI-900 Azure AI Fundamentals", "Promotional global posts claim it is a hiring-manager filter", "Wallpaper / ATS-maybe", "US $165 exam in promo posts; no India recruiter first-hand in this scrape", "Skip as a plan"],
        ["AI-102 Azure AI Engineer Associate", "Same promotional threads; Azure product names ARE in CGI/NTT/Cognizant JDs", "ATS-adjacent Isolated", "Promo $165; time not stated by India recruiters", "Optional max-1 if targeting Azure services JDs AND you will still ship Project 1"],
        ["AZ-900", "CUBE intern/ASE post: sponsored AZ-900 (junior)", "Junior ATS", "Company-sponsored in one junior JD", "Not for 8 YOE AI switch"],
        ["Microsoft 'Agent Expert' ladder (AI-620 etc.)", "Aiswarya (Microsoft CSA, India) published a ladder then said certs don't make you an expert", "Mixed / vendor path", "Not costed on X", "Do not collect the whole ladder"],
        ["UiPath Certified", "Amazon Hyderabad RPA post: 'UiPath Certified better'", "Role-specific recruiter keyword", "Not costed", "Only if chasing that RPA+LLM JD"],
        ["ServiceNow cert", "PwC India ServiceNow roles: certification mandatory — those are ServiceNow jobs, not the 8 AI titles", "Wrong-role ATS", "", "Skip for this search"],
        ["ITIL", "Named as a skill on Infosys command-center JD, not as a respected AI cert", "Ops wallpaper for AI-titled roles", "", "Skip"],
        ["Google Skills / Gemini badges", "Thai-language explainer, not India recruiter signal", "Insufficient", "", "Skip"],
        ["Nebius $1 cloud ops cert + credits", "Promo", "Insufficient India hiring signal", "", "Skip"],
    ]
    rec_vs_eng = [
        ["AI-900", "Promo accounts say recruiters check it", "No engineer-respect post in this India scrape", "Wallpaper risk"],
        ["AI-102", "May echo Azure OpenAI/Foundry JD keywords", "Aiswarya: execution + projects > certificates", "Optional ATS, not proof"],
        ["UiPath", "Amazon line 'certified better'", "Not discussed as AI-engineer respect", "RPA fork only"],
        ["Project + GitHub/demo", "Lyzr tests what you built; Arsh: build", "Stronger than certs on X in this window", "Do this"],
    ]
    time_cost = [
        ["AI-900", "Promo: 10–20 hours, $165", "xBitcoin_Teej; neil_xbt", "Promotional, not India recruiter"],
        ["AI-102", "Promo: free prep, $165", "xBitcoin_Teej", "Promotional"],
        ["Microsoft agent ladder", "Not stated", "AiswaryaVenkit1", "No cost on X"],
        ["UiPath cert", "Not stated", "Realized_Guy", "Only 'better' adjective"],
    ]
    rec2 = [
        [1, "Do not take a cert this week. Ship Project 1 (incident copilot) and put it on the resume.", "Lyzr build-first; Aiswarya projects>certs; JD lists name tools not badge codes", "Take (work), not a cert"],
        [2, "If you will apply to CGI/NTT/Cognizant Azure-named JDs in 60–90 days AND the project is running, sit AI-102 only. Skip AI-900.", "Azure product names are in those JDs; AI-900 evidence is promotional US threads", "Optional single cert"],
        ["Skip", "ITIL, ServiceNow, Google wallpaper badges, full Microsoft agent-cert ladder, UiPath unless RPA JD", "Wrong-role or wallpaper", "Skip"],
    ]
    src05c = [
        src_row(dict(handle="AiswaryaVenkit1", date="2026-09-07", pid="2096788042212384792", likes=95), "M6", "Mixed India Microsoft CSA", "Agent cert roadmap + 'certs don't make you an expert'", "Strongest India-flavored cert post"),
        src_row(dict(handle="xBitcoin_Teej", date="2026-04-21", pid="2046665367527834030", likes=623), "M6", "Promotional US", "AI-900 then AI-102, US salaries, no coding", "Do not follow as India 8 YOE plan"),
        src_row(dict(handle="neil_xbt", date="2026-06-17", pid="2067248358561927239", likes=211), "M6", "Promotional", "AI-900 is the credibility filter hiring managers check first", "Unsupported for India AI Engineer loops"),
        src_row(dict(handle="Realized_Guy", date="2026-07-29", pid="2082484516455948297", likes=1), "M6", "Isolated JD comment", "Amazon HYD RPA: UiPath Certified better", "Role-specific"),
        src_row(dict(handle="careerdjobs", date="2026-08-31", pid="2094388373528228157", likes=0), "M6", "Wrong-role JD", "PwC ServiceNow cert mandatory", "Do not generalize"),
        src_row(dict(handle="offerscout", date="2026-08-08", pid="2086122724720820618", likes=59), "M6", "Junior JD", "CUBE sponsors AZ-900", "Not this profile"),
    ]
    save_wb(F05 / "Certifications.xlsx", [
        ("Cert_List", ["Cert", "What X said", "Bucket", "Cost/time if stated", "Action"], certs, [36, 55, 22, 40, 40]),
        ("Recruiter_vs_Engineer_Signal", ["Item", "Recruiter/ATS signal", "Engineer signal", "Call"], rec_vs_eng, [28, 40, 45, 22]),
        ("Time_Cost_If_Stated", ["Cert", "Time/cost on X", "Handle", "Caveat"], time_cost, [28, 36, 22, 36]),
        ("Recommend_Max_2", ["#", "Recommendation", "Why (X)", "Type"], rec2, [10, 70, 55, 20]),
        ("Source_Posts", ["Handle", "Date", "Takeaway", "URL", "Why useful", "Likes", "Consensus class", "Module"], src05c, [18, 14, 50, 42, 28, 10, 22, 10]),
    ])
    write_txt(F05 / "01_README.txt", """
01_README — Folder 05 Resume + certifications
Window: 2026-03-11 to 2026-09-11. X only.

QUERIES
- ("AI resume" OR "GenAI resume" OR "AIOps resume") (recruiter OR rejected OR shortlist OR ATS) (India OR Indian) min_faves:5 → ZERO HITS
- (resume OR CV OR ATS) (AI OR GenAI OR "AI engineer") (recruiter OR rejected OR keywords OR switcher) (India OR Bengaluru OR Indian) min_faves:5 → joke post
- Semantic: AI resume rejected recruiter ChatGPT keywords India
- ("Azure AI" OR "AWS AI" OR "Google Cloud" OR "Responsible AI" OR Databricks OR ITIL) (certification OR certified) ("worth it" OR recruiter OR hiring) min_faves:10 → ZERO HITS
- ("AI-102" OR "AI-900" OR "Azure AI Engineer" OR certification) (worth OR recruiter OR hiring OR ignore OR wallpaper) (India OR Azure OR GenAI)
- Semantic: Azure AI certification worth it India recruiter
- ("support resume" OR "service desk" OR ITSM OR "L2 support") (AI OR GenAI OR AIOps) (resume OR switch OR transition) (India OR Indian) → ZERO HITS

EVIDENCE LIMITS
- No first-hand India recruiter post in this scrape that rewrites an 8 YOE Service Desk resume for AI.
- Cert 'worth it' India evidence is thin; US promo threads are loud. Recommendations therefore default to skip wallpaper and optional AI-102 only as Azure ATS, max 2 including 'ship the project instead of cert 1'.
""")

    def doc05a(doc):
        add_h(doc, "Limits")
        add_p(doc, "X did not yield a first-hand India recruiter markup of a Service Desk→AI resume. Headlines and bullets below are translations into language that actually appears on India FDE/GenAI/Azure posts, without invented metrics.")
        add_h(doc, "Headline option A (preferred if Project 1 exists)", 2)
        add_p(doc, "Operations Lead (8+ YOE) → AI deployment / AIOps — incident, identity, monitoring, and client operations; building production-shaped agents on Azure")
        add_h(doc, "Headline option B (safer, more literal)", 2)
        add_p(doc, "Service Desk Lead targeting Forward Deployed / Applied AI roles — runbooks, major incident, identity/MFA, automation-adjacent delivery")
        add_h(doc, "Eight rewritten bullets (candidate voice)", 2)
        add_b(doc, [
            "Lead enterprise client operations spanning monitoring, incident, and request flows, including stakeholder comms during high-severity events.",
            "Worked across L1–L3 operating model: intake, deep troubleshooting, and escalation — translating user impact into technical next actions.",
            "Owned operational commitments (response/resolve expectations) and used them to prioritize incident work. [real figure only if you have one]",
            "Operated monitoring and alert intake; distinguished noisy alerts from user-impacting incidents — the same judgment agent routing has to get right.",
            "Supported identity and MFA issues in enterprise cloud logins; using that operational knowledge to reason about SSO/MFA/RBAC boundaries in agent tools (not claiming IAM architecture).",
            "Ran automation-adjacent operational work under change control — the habit behind idempotent tools and human approval on writes.",
            "Daily operator on enterprise cloud/identity surfaces; applying that context to an Azure OpenAI-style ops assistant with traces and evals. [only if true]",
            "Client-facing operations lead: explained outages and next steps to non-technical stakeholders — the same motion as an FDE/solutions PoC demo.",
        ])
        add_h(doc, "Stop mentioning as the lead story", 2)
        add_p(doc, "L1/L2/L3 as identity, ChatGPT as the AI project, ITIL as the AI cert, Java/SQL as core, US salaries, and any metric you cannot defend on a bridge call.")

    save_doc(F05 / "Resume_Headlines_And_Bullets.docx", "Resume headlines and bullets — this profile only", doc05a)

    def doc05b(doc):
        add_h(doc, "Max 2 for this profile (based on X, not brochures)")
        add_p(doc, "India recruiter first-hand evidence that 'this cert got an AI-switcher shortlisted' was not found. US promo threads claiming AI-900 is a universal filter are Promotional. A Microsoft CSA in India posted a long agent-cert ladder and then wrote: certificates don't make you an expert; execution + projects do.")
        add_h(doc, "Recommendation 1 — take the project, not a badge", 2)
        add_p(doc, "Ship the incident/runbook copilot with evals and traces. Lyzr's FDE drive tests what you built. JD language in this scrape names Python, RAG, LangGraph, Azure OpenAI, FastAPI, MCP — not AI-900.")
        add_h(doc, "Recommendation 2 — optional AI-102 only", 2)
        add_p(doc, "If, after the project is demoable, you apply to CGI / NTT DATA / Cognizant Azure-named GenAI JDs, AI-102 is the only cert that even loosely matches those product names. Skip AI-900 (wallpaper). Skip stacking the full Microsoft agent-cert ladder.")
        add_h(doc, "Skip", 2)
        add_b(doc, [
            "ITIL as an AI differentiator.",
            "ServiceNow certification (PwC posts are ServiceNow jobs).",
            "UiPath unless you specifically chase Amazon Hyderabad RPA+LLM or NTT RPA.",
            "Google wallpaper badges, $1 promo certs.",
        ])
        add_h(doc, "Why not two vendor certs", 2)
        add_p(doc, "The brief caps at two. X evidence does not support two. One optional ATS cert plus a project is already stretching Isolated promotional data.")

    save_doc(F05 / "Cert_Recommendation.docx", "Certification recommendation — max 2, X-only", doc05b)

    # ========== Master index + exec summary ==========
    index_rows = [
        ["Parent", "00_MASTER_INDEX.xlsx", "This file", "Index"],
        ["Parent", "00_EXEC_SUMMARY.docx", "15-line executive summary", "Read first"],
        ["01", "01_README.txt", "Queries, confidence, gaps for skills", "Module 1"],
        ["01", "Skills_Roadmap.xlsx", "Must-haves, tools, 30/60/90, overrated, sources", "Module 1"],
        ["01", "Concepts_And_Study_Plan.docx", "Readable plan with actual X concept notes", "Module 1"],
        ["02", "01_README.txt", "X-proxy % method", "Module 2"],
        ["02", "Job_Demand_Proxy.xlsx", "Distinct posts, mix %, talk vs actual, companies, gaps", "Module 2"],
        ["02", "Demand_Snapshot.docx", "Which 2 roles look real vs hype", "Module 2"],
        ["03", "01_README.txt", "Interview query log + first-hand count", "Module 3"],
        ["03", "Interview_Bank.xlsx", "Questions, rounds, rejections, take-home, SD advantage", "Module 3"],
        ["03", "Interview_Playbook.docx", "Round-by-round for 8 YOE ops → AI", "Module 3"],
        ["04", "01_README.txt", "Ranking method + project query gaps", "Module 4"],
        ["04", "Projects_That_Hire.xlsx", "Ranked projects, demos, role map, translation", "Module 4"],
        ["04", "Project_Build_Briefs.docx", "Build briefs for recommended projects", "Module 4"],
        ["05", "01_README.txt", "Resume + cert evidence limits", "Module 5–6"],
        ["05", "Resume_Rewrite.xlsx", "Headlines, bullets, keywords, stop list, ATS", "Module 5"],
        ["05", "Resume_Headlines_And_Bullets.docx", "2 headlines + 8 bullets", "Module 5"],
        ["05", "Certifications.xlsx", "Cert list, recruiter vs engineer, max 2", "Module 6"],
        ["05", "Cert_Recommendation.docx", "Take project; optional AI-102; skip wallpaper", "Module 6"],
        ["CALL", "Best-fit 2 roles", "1) Forward Deployed / AI Deployment Engineer  2) Cloud AI Engineer (Azure-named GenAI) with FDE as primary", "See folder 02"],
        ["CALL", "3 skills this week", "1) Python+FastAPI  2) RAG over runbooks with citations  3) Traces/evals/guardrails (harness)", "See folder 01"],
        ["CALL", "First project", "Incident/ticket copilot: runbook RAG + 2–3 tools + evals + traces", "See folder 04"],
        ["CALL", "Cert take-or-skip", "Skip certs this week. Optional later: AI-102 only. Skip AI-900/ITIL wallpaper.", "See folder 05"],
        ["CALL", "Biggest X-evidence gap", "No first-hand India Service Desk 8 YOE → AI offer/interview recaps; AIOps mid-senior titles thin; cert and resume-recruiter evidence thin; no official opening counts", "All READMEs"],
    ]
    save_wb(ROOT / "00_MASTER_INDEX.xlsx", [
        ("Index", ["Folder", "File", "What it contains", "Notes"], index_rows, [12, 40, 70, 28]),
    ])

    def doc00(doc):
        add_h(doc, "15-line executive summary")
        lines = exec_lines()
        for i, line in enumerate(lines, 1):
            add_p(doc, f"{i}. {line}")
        add_h(doc, "How to use the folders", 2)
        add_p(doc, "Master files are an index. Full evidence tables live in the five task folders. Every percentage in Folder 02 is an X-proxy from this scrape's distinct company+role openings, intern-excluded.")

    save_doc(ROOT / "00_EXEC_SUMMARY.docx", "Executive summary — X-only India AI transition research", doc00)
    print("Wrote pack under", ROOT)


def exec_lines():
    return [
        "Best-fit role 1 on X: Forward Deployed / AI Deployment Engineer — densest distinct India company cluster (Lyzr, OpenAI deployment roles including Partner AWS 8+ YOE, Sarvam, RevRag, Katonic, Rhai, ElevenLabs, plus first-hand 'first FDE in India' hire).",
        "Best-fit role 2: Cloud AI / Azure-named GenAI engineer (CGI 4–7 YOE Bengaluru hybrid Azure Foundry/OpenAI; NTT DATA Azure OpenAI+MCP; Cognizant multi-city 3.5–9 YOE) — the exact title 'Cloud AI Engineer' is rare.",
        "AIOps is the conceptual home for a Service Desk lead but titled mid-senior 'AIOps Engineer' openings on X are thin (IBM fresher; CGI telco aggregator; Infosys command-center/HCI; Observability at Experian/Point72). Do not treat coaching talk as demand.",
        "GenAI/Agentic has the largest raw post volume, often 0–4 YOE and coding-heavy (Python, LangGraph, FastAPI, ₹40–60 LPA senior bar wants production agents). Treat as a stretch if the project is real, not as the default 8 YOE landing.",
        "Intelligent automation on X is two markets: agentic/n8n/Emplay vs classic UiPath RPA. Amazon Hyderabad is the hybrid (UiPath+LLM). Pick one fork.",
        "AI Security and Solutions Architect exist but are sparse; one Hyderabad AI Architect post asks 8+ YOE with 2–3 years agentic (RBAC, chunking). Bolna Solutions Engineer is 0–2 YOE. BytePlus Solutions Architect is the serious customer-PoC signal.",
        "Skill 1 this week: Python + FastAPI (APIs) — repeated in CGI, Manali, FDE roadmaps, 342-JD graphic.",
        "Skill 2 this week: RAG over runbooks/tickets with citations — Franklin: RAG for docs/runbooks/past tickets; tools for live writes.",
        "Skill 3 this week: traces, evals, guardrails (agent harness) — 8+ YOE interview story plus runaway-cost question; Langfuse named on a JD-frequency graphic.",
        "Do not make Java or SQL the study path. Exceptions actually posted: IBM fresher AIOps (Java or Python + SQL), some Cognizant/Databricks/Text2SQL JDs. Flag, don't roadmap.",
        "First project: incident/ticket copilot (runbook RAG + 2–3 tools + evals + traces). No India 'this project got me the offer' post was found; ranking is JD+interview signal, not placement anecdotes.",
        "Interview pattern to practice: project interrogation, FDE live-build/showcase (Lyzr), RAG-vs-agent design, prod failure traces — not ML math. Service Desk→AI first-hand recaps: insufficient.",
        "Cert: skip this week. Optional later max-1: AI-102 if chasing Azure-named JDs. Skip AI-900 wallpaper, ITIL-as-AI, ServiceNow. India recruiter cert evidence is thin; US promo threads are loud.",
        "Resume: two headlines + eight bullets are in Folder 05. Lead with ops judgment + one real project. X shows AI-keyword resume backlash, not a Service Desk-specific recruiter markup.",
        "Biggest gap: X has almost no first-hand 8 YOE Service Desk/ITSM→AI India switcher posts; no official opening counts; AIOps mid-senior titles and cert/resume-recruiter evidence remain insufficient — labeled GAPS in every folder rather than filled from memory.",
    ]


if __name__ == "__main__":
    build()
    print("\n--- 15-LINE EXEC (chat) ---")
    for i, line in enumerate(exec_lines(), 1):
        print(f"{i}. {line}")
