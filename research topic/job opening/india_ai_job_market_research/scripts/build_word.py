#!/usr/bin/env python3
"""Build the Word intelligence report."""
import json, pathlib
from collections import Counter, defaultdict
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

BASE = pathlib.Path(r"D:\ai apps dump\research topic\job opening\india_ai_job_market_research")
OUT = BASE / "output"
jobs = json.loads((OUT/"merged_jobs.json").read_text(encoding="utf-8"))
queries = json.loads((OUT/"merged_queries.json").read_text(encoding="utf-8"))
N = len(jobs)
NAVY = RGBColor(0x1F, 0x38, 0x64)

doc = Document()
style = doc.styles["Normal"]
style.font.name = "Calibri"; style.font.size = Pt(10)
for i in range(1,4):
    doc.styles[f"Heading {i}"].font.color.rgb = NAVY

def h1(t): doc.add_heading(t, level=1)
def h2(t): doc.add_heading(t, level=2)
def h3(t): doc.add_heading(t, level=3)
def p(t, bold=False, italic=False, size=None):
    par = doc.add_paragraph()
    r = par.add_run(t); r.bold=bold; r.italic=italic
    if size: r.font.size=Pt(size)
    return par
def bullets(items):
    for it in items: doc.add_paragraph(it, style="List Bullet")
def table(headers, rows):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Light Grid Accent 1"; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i,hh in enumerate(headers): t.rows[0].cells[i].text = str(hh)
    for row in rows:
        cells = t.add_row().cells
        for i,v in enumerate(row): cells[i].text = str(v)
    doc.add_paragraph("")
    return t
def callout(t):
    par = doc.add_paragraph()
    r = par.add_run("CALLOUT: " + t); r.bold=True; r.font.color.rgb = RGBColor(0x2E,0x75,0xB6)
    return par

role_c = Counter(j["Standardized_Role"] for j in jobs)
status_c = Counter(j["Status"] for j in jobs)
conf_c = Counter(j["Evidence_Confidence"] for j in jobs)
tier_c = Counter(j["Candidate_Tier"] for j in jobs)
city_c = Counter(j["City"] for j in jobs)
skill_c = Counter(s for j in jobs for s in j["All_Skills"])
comp_c = Counter(j["Company"] for j in jobs)
active = status_c.get("ACTIVE",0)+status_c.get("LIKELY ACTIVE",0)
disc = [j for j in jobs if j["Salary_Type"]=="Employer Disclosed"]

# ---------- Cover ----------
t = doc.add_paragraph(); r=t.add_run("India AI Job Market Deep Research Report"); r.font.size=Pt(24); r.bold=True; r.font.color.rgb=NAVY
p("AIOps • Cloud AI • Intelligent Automation • AI Security • Forward Deployed AI • GenAI / Agentic AI • AI Solutions Engineering • AI Solutions Architecture", italic=True)
p("Geography: India (metros + non-metros + Remote/Pan-India)  •  Window: 05 March 2026 – 05 September 2026  •  Generated: 06 September 2026")
p(f"Evidence base: 314 raw postings reviewed → {N} unique canonical jobs → 212 companies → 202 logged queries → 64 HIGH / 167 MEDIUM / 81 LOW. Workbook: India_AI_Job_Market_Intelligence_Mar-Sep_2026.xlsx (20 sheets).", bold=True)
callout("Every job traces to a real URL seen in-session. Missing = Not Available / Not Disclosed. Board salary estimates are never mixed with employer-disclosed pay. LIKELY ACTIVE ≠ confirmed — verify before applying.")
p("Audience: an 8.5-year IT Operations / Service Desk / testing-automation professional (₹11 LPA) targeting AI engineering/architecture roles at ₹20–25+ LPA (path to ₹35+ LPA). The market is captured first; candidate fit is scored separately.", italic=True)

h1("1. Executive Summary")
bullets([
 f"Market shape ({N} evidence-backed uniques): Intelligent Automation 45, Cloud AI 44, AIOps 41, GenAI/Agentic 41, AI Solutions Architect 39, Forward Deployed 38, AI Security 31, AI Solutions Engineer 30 (+3 Adjacent). No single family dominates — demand is broad-based with a GenAI/agent overlay across all of them.",
 f"Where: Bengaluru 109 (35%), Hyderabad 45, Pune 38, Chennai 18, Remote-India 17, Mumbai 16, Gurugram 15, Noida 14. Non-metros (Kochi, Coimbatore, Ahmedabad, Jaipur, Kolkata, Lucknow, Indore) appear but thinly — metro concentration is real.",
 f"Status honesty: 87 confirmed ACTIVE + 199 LIKELY ACTIVE + 17 historical/closed + 9 unknown. HIGH confidence (employer/ATS) is only 20.5% because LinkedIn/Naukri/Foundit are login/bot-walled and WebSearch throttled (429s) mid-session — logged, not bypassed.",
 f"Money: employer-disclosed pay is rare (~{len(disc)} rows). Visible bands run ₹5–90 LPA; the credible 8–12y senior-engineer cluster sits ₹20–45 LPA, with platform/architect outliers to ₹70–90 LPA (e.g., Cartesia-type AI Platform) and AIOps COE ₹45–50 LPA. Board estimates are quarantined in the workbook.",
 f"Candidate headline: 92 Tier A + 71 Tier B = 163 of {N} (52%) are apply-now or 1–2-month-prep targets. Easiest doors: Intelligent Automation, AIOps, Cloud AI, AI Solutions Engineer (ops/automation/cloud adjacency). Hardest: AI Security specialist and 12y+ Architect. GenAI/Agentic is the highest-upside bridge — real hiring requirement, not just marketing (MCP/A2A now named in JDs).",
 f"80-day bet (data-driven): Python + APIs → RAG → LangChain/LangGraph + Azure OpenAI & Bedrock → Docker/K8s/CI-CD → vector DBs → LLMOps/evals/guardrails → 3 portfolio builds (RAG helpdesk, agentic ops runbook, secure AI gateway). Details in §27/§43-equivalent (§27).",
])
h2("Top-5 numbers to remember")
table(["Metric","Value"], [[f"Unique jobs",N],["Active + Likely Active",active],["Companies",212],
 ["Bengaluru share","35% (109)"],["Tier A+B for this candidate","163 (52%)"],["Employer-disclosed salaries",f"{len(disc)} (estimates kept separate)"]])

h1("2. Research Methodology")
h2("2.1 Multi-agent design (as executed)")
bullets([
 "Orchestrator split work into 8 streams (S1 AIOps, S2 Cloud AI, S3 Automation, S4 AI Security, S5 Forward Deployed, S6 GenAI/Agentic, S7 Solutions Engineer, S8 Architect). Each ran 12–20 logged queries (title variants × cities × months × ATS × employers) plus 15–30 page fetches.",
 "Source classes: general portals (Indeed, Shine, Foundit-probes, Glassdoor-probes), tech platforms (Instahyre/Cutshort/Wellfound/Hirist probes), company career sites + ATS (Greenhouse/Lever/Ashby/Workday/SuccessFactors — 64 HIGH records), aggregators as fallback (LOW). Public-only; no auth/CAPTCHA/paywall bypass.",
 "Extraction schema: 33 keys per record (title, role, company/type/industry, city/state/mode, dates + confidence, status, exp, salary + type/source, skills, summaries, education/certs, URLs, confidence, stream, notes). JDs summarized, not copied.",
 "Dedup: company+title+city canonical key → 314 raw → 312 unique (2 merged); cross-stream collisions merged with alternate-source preservation. Distinct req IDs / cities kept distinct.",
 "Scoring: Role Relevance /100 (title 25 + responsibilities 25 + AI-tech 20 + eng/arch relevance 15 + enterprise 10 + context 5, operationalized via role base + skill/AI-keyword bonuses); Candidate Fit /100 (exp 30 + transferability 35 + role-accessibility 20 + learnability 15); Tiers A–D; Difficulty 1–10; Data Quality /100 (source + date + JD + URL + exp/salary completeness).",
])
h2("2.2 Saturation & honesty")
bullets([
 "202 query-log lines preserved (Sheet 19). Three consecutive low-yield rounds were NOT cleanly achieved in every stream because throttling forced fallback discovery — so saturation is claimed per-stream, not globally. This is a large high-quality sample, not a census; target 1,500–3,000 was not reachable under access constraints.",
 "Red-team pass (§31 + Sheet 20) challenged source bias, repost inflation, agentic-marketing inflation, and date confusion; corrections applied (adjacent rows flagged, estimates quarantined, LIKELY vs ACTIVE separated).",
])

h1("3. Dataset Coverage")
table(["Dimension","Coverage"],
 [["Window","05-Mar-2026 → 05-Sep-2026; dated rows skew Jul–Sep (portals hide dates; see §12)"],
  ["Roles","All 8 families ≥30 uniques each (31–45)"],
  ["Geography","15+ cities + Remote + Pan-India; Bengaluru 35%, HYD/Pune next"],
  ["Sources","~90 distinct source-platform strings; Indeed + Shine + Greenhouse + employer sites dominate HIGH/MEDIUM"],
  ["Confidence","HIGH 64 (20.5%) / MEDIUM 167 (53.5%) / LOW 81 (26%)"],
  ["Status","ACTIVE 87 / LIKELY 199 / EXPIRED 8 / CLOSED 6 / REMOVED 3 / UNKNOWN 9"],
  ["Dedup","2 merged; consultancy reposts noted, not double-counted as demand"]])
callout("Do not cite LIKELY ACTIVE as confirmed openings. Re-verify the URL before applying.")

h1("4. Market Overview")
bullets([
 "The Indian AI-hiring market in-window is GenAI-permeated rather than GenAI-siloed: RAG, agents, LangChain-class tooling, and Azure OpenAI/Bedrock appear inside Cloud, Automation, AIOps, FDE, Solutions, and Architect JDs — not just GenAI-titled roles.",
 "IT Services/Consulting (TCS, Infosys, Wipro, Accenture, Capgemini, NTT DATA, Cognizant, EY/Deloitte) hire at volume across 3–12y bands; product/SaaS + AI-native startups (Sarvam, Krutrim, Fractal, Postman-class, BrowserStack-class) hire deeper but fewer; GCCs (banks, manufacturing, health) hire senior platform/architecture roles; hyperscalers (Microsoft, Google, AWS-channel partners like Quantiphi/Searce/Minfy) staff Cloud/FDE/architecture locally.",
 "Experience floor is senior-leaning: modal demand 5–12y; true junior (0–2y) is mostly automation-RPA and startup conversational roles. This structurally favors an 8.5y candidate.",
 "Opacity is the market's defining trait: dates hidden, salaries hidden, ATS fragmented. Any report claiming precise month-curves or salary medians from this window without caveats is overstating.",
])

h1("5. Target Role Analysis (summary + per-family)")
table(["Role","n","Active","Avg min-exp","8–10y fit*","Tier A","Remote share","Difficulty avg"],
 [[r, sum(1 for j in jobs if j["Standardized_Role"]==r),
   sum(1 for j in jobs if j["Standardized_Role"]==r and j["Status"] in ("ACTIVE","LIKELY ACTIVE")),
   round(sum(j["Min_Experience"] for j in jobs if j["Standardized_Role"]==r and isinstance(j["Min_Experience"],int))/max(1,sum(1 for j in jobs if j["Standardized_Role"]==r and isinstance(j["Min_Experience"],int))),1),
   sum(1 for j in jobs if j["Standardized_Role"]==r and isinstance(j["Min_Experience"],int) and j["Min_Experience"]<=10),
   sum(1 for j in jobs if j["Standardized_Role"]==r and j["Candidate_Tier"]=="A"),
   f"{sum(1 for j in jobs if j['Standardized_Role']==r and j['City']=='Remote - India')/max(1,sum(1 for j in jobs if j['Standardized_Role']==r)):.0%}",
   round(sum(j["Transition_Difficulty"] for j in jobs if j["Standardized_Role"]==r)/max(1,sum(1 for j in jobs if j["Standardized_Role"]==r)),1)]
  for r in sorted(role_c)])
p("* 8–10y fit = min_exp ≤10 (heuristic). Full buckets in Sheet 11.", italic=True)

for sec, title, body in [
 ("6","GenAI / Agentic AI Market (n=41)","Hiring is concrete: production RAG pipelines, multi-agent systems (LangGraph/AutoGen/CrewAI), MCP integrations, fine-tuning, LLMOps, evals. Capco (Greenhouse-live, 6–10y, MCP explicit), IT-services GenAI practices (TCS/Infosys/Persistent/TechM/Birlasoft 3–12y), startups (Sarvam/Krutrim, onsite Bengaluru). Only 1 employer band captured (Birlasoft ₹35–70L, 10–15y) — senior GenAI pays. Gap: Mumbai/NCR thin; conversational/LLMOps titles underrepresented vs RAG/agent titles."),
 ("7","Forward Deployed AI Market (n=38)","Real and Bengaluru-concentrated (20/38). Three archetypes: frontier-lab deployment (OpenAI 4 India remote/hybrid), data-platform FDE (MongoDB 3 Gurugram/Remote; Databricks demand via employee posts, no open India req seen), consulting FDE factories (Accenture, Fractal 5 tracks incl. finance niche, GlobalLogic, Cognizant). Seniority 5–10y modal; customer-facing ownership (sponsor KPIs, saying no to scope, 25–30% travel) is an explicit screen. No salary disclosed in any FDE row — price via adjacent GenAI bands."),
 ("8","AI Solutions Engineering Market (n=30)","Customer-facing GenAI delivery core (RAG/agents/demos/POCs) from startups (Nanonets, Gnani.ai) to IT services (Cognizant, Accenture) to cloud-provider CE (Google 6–14y senior presales). Churn visible (Nanonets/Rhombus/Sutherland delisted in-window). Only 1 disclosed band (₹5–12L junior Lucknow); rest undisclosed/estimated. Snowflake/Elastic/MongoDB yielded architect/SA titles instead — counted in S8, not here."),
 ("9","AI Solutions Architecture Market (n=39)","Presales-plus-hands-on hybrid: NTT/Cognizant/Capgemini-BFSI/Deloitte weight RFPs/orals/estimations equally with RAG/agent delivery; TOGAF/SABSA mandatory only at Deloitte-SM level. Stack converged (LangGraph+RAG+vector DBs+Azure OpenAI/Bedrock in ~30/39); MCP/A2A explicit only in NTT/Deloitte-HC/Micron — frontier, not mainstream. Floor 8–15y (modal 10–12); startups demand Python/FastAPI code ownership (Lyzr 8y+), Big4/IT-services more advisory. BFSI dominates; only 1 pay row (Infinity ARC ₹15–30L). Frontier labs staff presales architects locally (Anthropic ×2 Bangalore, Databricks ×4)."),
 ("10","AIOps Market (n=41)","Volume hirer EY India (6 senior reqs: Moogsoft/BigPanda/Splunk ITSI/Dynatrace Davis/Datadog + ServiceNow ITOM, 5–9y, BLR/HYD/Noida/Kolkata/Kochi). AI-native SRE real in BLR product firms (Harness Staff+Principal AI-SRE Greenhouse-live; CrowdStrike AI-agent SRE ~Sep-02; Epam/Presidio platform builds). Remote-India exists but small (Fx31 ₹35–45L, Porch expired ₹24.75–34.65L, Nagarro, Jobgether). Churn (Northern Trust Pune, Porch removed in weeks). Only 4 pay rows — AIOps salary data is thinnest."),
 ("11","Cloud AI Market (n=44)","Dominant pattern is AI/ML Platform (eBay, UST, Quest Global, Cartesia ₹70–90L) in BLR/Pune/HYD. Tri-cloud explicit: Bedrock (Cloudbyz, SS&C Kolkata), Azure OpenAI/Copilot (Saarthee, Relevance Labs), Vertex AI (Techolution, SS&C). Hyperscalers hire direct (Google FDE/GenAI Gurugram/Mumbai/Pune 8y bar; Microsoft Data&AI BLR). Only 1 exact-date row (AstraZeneca Chennai 04-Sep-2026); 9 disclosed + 7 estimated bands (₹5–90L), 28 undisclosed."),
 ("12","Intelligent Automation Market (n=45)","UiPath + Power Platform dominate; RPA+GenAI+Agentic convergence explicit (Wells Fargo Sr SWE UiPath/GenAI/Agentic; UST agentic automation; Zensar Copilot Studio). Senior Power Platform (6–12y, Capgemini 6–9y posted 27-Aug-2026) vs junior RPA dev (1–5y, ₹2–6L). Only 2 ACTIVE confirmations (Capgemini ATS sole HIGH). No Accenture/Deloitte/EY/Coforge/Hexaware IPA reqs found — Capgemini the consulting exception. Automation Architect titles absent in-window."),
 ("13","AI Security Market (n=31)","Metro/remote-concentrated (BLR 13, HYD 4, Remote 7). Skill consensus: prompt injection, OWASP LLM Top 10, MITRE ATLAS, NIST AI RMF, guardrails, red-teaming, RAG/agents/MCP in 20+ JDs; AIRTP+/CAISF only in Finastra JD. Mix: Big4/GCC (KPMG, EY, Volvo, Bosch, SIXT, Finastra) + startups (Akto, 100MS) + staffing fronts. Pay thin (7 rows, ₹6.6–80L; top 100MS ₹50–80L). All dated rows Jul–Sep; nothing evidencing Mar–Jun directly. Traditional SOC volume dwarfs AI-meaningful roles ~10:1 — filtered out."),
]:
    h1(sec+". "+title); p(body)

h1("14. Top Employers")
h2("Top 25 by relevant postings (evidence-set volume, not total hiring)")
rows=[]
for comp,cnt in comp_c.most_common(25):
    rs=[j for j in jobs if j["Company"]==comp]
    act=sum(1 for j in rs if j["Status"] in ("ACTIVE","LIKELY ACTIVE"))
    roles=", ".join([r for r,_ in Counter(j["Standardized_Role"] for j in rs).most_common(2)])
    rows.append([comp,cnt,act,rs[0]["Company_Type"],roles])
table(["Company","Jobs","Active","Type","Top roles"], rows)
callout("Volume ≠ quality. For targeting, see §28 Tier 1/2/3 which re-ranks by fit + pay evidence + learning value.")

h1("15. GCC Opportunity Analysis")
bullets([
 "GCCs appear across banks (Citi-class, Northern Trust Pune — churned), manufacturing (Siemens, Bosch, Volvo), health (UHG — 404-churned), and tech captives. Roles skew senior platform/architecture/automation with regulated-domain flavor (BFSI insurance/P&C, health).",
 "GCC quality vs peers: pay evidence is sparse but senior bands (₹35–70L where visible) beat IT-services equivalents; learning depth (platform ownership) beats staffing-firm roles; hiring velocity is slower and reqs churn (404s) — apply fast, track req IDs.",
 "For this candidate: GCC automation/platform and BFSI GenAI delivery roles are strong Tier B targets — domain process knowledge from ops transfers well.",
])

h1("16. City Analysis")
table(["City","Jobs","Share","Note"],
 [[c,cnt,f"{cnt/N:.1%}",{"Bengaluru":"HQ for all 8 families; only market with FDE+Arch+GenAI depth","Hyderabad":"Agentic/MCP junior roles + platform hiring","Pune":"Services+SaaS balance","Chennai":"GCC/services pocket","Mumbai":"BFSI/HQ, thinner AI-platform depth","Gurugram":"NCR consulting+cloud","Noida":"Services+GCC","Remote - India":"~5%: real (FDE, AIOps, security) but competitive","Kolkata":"EY AIOps spillover + SS&C Bedrock"}.get(c,"Thin — verify per-role; non-metro = first-mover advantage if present")]
  for c,cnt in city_c.most_common(12)])
p("Rank by family: GenAI → Bengaluru > Hyderabad > Pune. FDE → Bengaluru ≫ Mumbai/HYD/Gurugram. AIOps → Bengaluru + EY multi-city. Automation → BLR/Pune/HYD/Noida. Security → BLR + Remote. Architect → BLR/Noida/Pune + Delhi-CE.", italic=True)

h1("17. Experience Analysis")
exps = [(j["Job_ID"],j["Min_Experience"]) for j in jobs if isinstance(j["Min_Experience"],int)]
table(["Bucket","Jobs","Read"],
 [["0–2",sum(1 for _,e in exps if 0<=e<2),"Mostly RPA-junior + startup conversational; mostly below candidate band"],
  ["2–4",sum(1 for _,e in exps if 2<=e<4),"RPA dev + early GenAI; Tier C stepping stones"],
  ["4–6",sum(1 for _,e in exps if 4<=e<6),"Bridge band; strong Tier B hunting ground"],
  ["6–8",sum(1 for _,e in exps if 6<=e<8),"★ Sweet spot lower edge"],
  ["8–10",sum(1 for _,e in exps if 8<=e<10),"★ Bullseye for 8.5y"],
  ["10–12",sum(1 for _,e in exps if 10<=e<12),"★ Reach withleadership framing"],
  ["12–15",sum(1 for _,e in exps if 12<=e<15),"Architect-heavy; Tier C/D unless presales strength"],
  ["15+",sum(1 for _,e in exps if e>=15),"Practice-lead; mostly D"],
  ["Unspecified",N-len(exps),"Read JD; many are active platform roles"]])
callout("Strongest volume for 6–10y is GenAI, Cloud AI, Automation, and Solutions Engineer — exactly the transition corridor.")

h1("18. Compensation Analysis (disclosed-only)")
if disc:
    from collections import defaultdict as dd
    bands = Counter()
    for j in disc:
        try: mx=float(j["Max_Salary_LPA"])
        except: continue
        bands["<15" if mx<15 else ("15–20" if mx<20 else ("20–25" if mx<25 else ("25–30" if mx<30 else ("30–35" if mx<35 else ("35–50" if mx<50 else "50+")))))]+=1
    table(["Band (max LPA)","Disclosed postings"], [[b,bands.get(b,0)] for b in ["<15","15–20","20–25","25–30","30–35","35–50","50+"]])
    table(["Example disclosed datapoint","Detail"],
     [["Cartesia-type AI Platform (Cloud AI)","₹70–90 LPA range"],
      ["Birlasoft GenAI (10–15y)","₹35–70 LPA"],
      ["Fx31 Remote AIOps","₹35–45 LPA"],
      ["Michael Page AIOps COE","₹45–50 LPA"],
      ["100MS AI-agents compliance lead","₹50–80 LPA"],
      ["Porch AIOps (expired)","₹24.75–34.65 LPA"],
      ["Infinity ARC Architect","₹15–30 LPA"],
      ["Junior RPA / Lucknow SE","₹2–12 LPA"]])
else:
    p("No disclosed salaries.")
callout(f"Only {len(disc)}/{N} postings disclose pay — medians are fragile and role-conditional. Path to ₹20–25L: senior Automation / AIOps / Cloud AI / GenAI delivery (6–10y). Path to ₹30–35L+: platform ownership, agentic delivery, presales architecture, or GCC/BFSI senior bands. Sheet 10 keeps estimates quarantined.")
p("Role families most likely toward ₹20–35L+ (evidence + band logic): GenAI/Agentic delivery, Cloud AI Platform, AIOps senior/COE, FDE (imputed via GenAI bands), Solutions Architect (12y+). Security pays at the top end but gates on specialist proofs.", italic=True)

h1("19. Top Skills (frequency)")
table(["#","Skill","Jobs","Share"],
 [[i+1,s,c,f"{c/N:.1%}"] for i,(s,c) in enumerate(skill_c.most_common(30))])

h1("20. Emerging Skills")
bullets([
 "Explicit in-JD growth signals: MCP (Capco, Birlasoft, TCS-Arch, Qualcomm), A2A (Capco/TCS-Arch), LangGraph + multi-agent orchestration, agent observability/evals, guardrails/content-filtering, AI governance/NIST-RMF/ATLAS, vector DBs + knowledge-graph RAG, multimodal + small-language-model delivery (Snowflake Cortex mentions).",
 "MCP/A2A are past buzzword: they appear as required integrations, not taglines — but still in a minority of JDs (frontier signal). Weight them P1, not P0.",
 "Model-context management, agent gateways, and LLM-eval harnesses co-occur with senior GenAI/FDE reqs — strong Tier-B differentiators.",
])

h1("21. Skill Combinations (what employers actually buy as stacks)")
combo_defs = [["Python + LangChain + Azure OpenAI"],["Python + AWS Bedrock + RAG"],["LangGraph + LLM + Agents"],["Azure + OpenAI + Kubernetes"],["Databricks + GenAI"],["ServiceNow + AIOps"],["Dynatrace + AIOps"],["UiPath + GenAI"],["AI Security + Cloud Security + LLM"],["Python + Docker + K8s + CI/CD"],["RAG + Vector DBs + Embeddings"],["MCP + Agentic AI + LangChain"]]
rows=[]
for combo in combo_defs:
    js=[j for j in jobs if all(c.lower() in j["All_Skills"] for c in combo)]
    rows.append([" + ".join(combo),len(js),f"{len(js)/N:.1%}",len(set(j["Standardized_Role"] for j in js))])
table(["Combination","Jobs","Share","Roles"], rows)
callout("Interview implication: be able to whiteboard one full stack end-to-end (e.g., Python + LangChain + Azure OpenAI + RAG + pgvector + Docker + evals + guardrails), not just list tools.")

h1("22. Certifications (only what JDs actually name)")
bullets([
 "Certs rarely gate these roles. Explicit asks cluster in: Cloud AI / Architect (Azure AI Engineer Associate / Solutions Architect Expert, AWS ML Specialty / Solutions Architect, GCP Professional ML Engineer), ITSM/ITOM (ITIL, ServiceNow CSA/CAD), automation (UiPath Certified), data (Databricks/Snowflake), security (CISSP/CCSP rarely; AIRTP+/CAISF once).",
 "TOGAF/SABSA mandatory only at Deloitte-SM architect level. CKA/CKAD help platform roles but seldom required.",
 "Verdict: one cloud-AI cert (Azure AZ-104/AI-102 or AWS SAA/MLA) justifies investment only if paired with a shipped RAG/agent project; otherwise project evidence beats badges. Full frequency in Sheet 14.",
])

h1("23. Candidate Fit Analysis")
table(["Tier","n","Meaning"],
 [["A — Apply Now",tier_c.get("A",0),"In-band exp + transferable stack; 0–2 wks polish"],
  ["B — Minor upskill",tier_c.get("B",0),"1–2 months focused prep"],
  ["C — Strategic",tier_c.get("C",0),"3–6 months projects"],
  ["D — Future",tier_c.get("D",0),"Specialist/12y+ gap"]])
p("Fit is independent of market relevance: a high-relevance frontier-research role can be Tier D for this candidate, and a mid-relevance automation role can be Tier A. Sheet 4 ranks all 100 best fits with reasons, transferable/missing skills, and prep effort.", italic=True)

h1("24. Career-Transition Opportunities (25 questions, answered from data)")
qa = [
 ("Q1. Highest demand family?","Intelligent Automation (45) edges Cloud AI (44); AIOps + GenAI tie at 41. But demand is flat-ish across families — the GenAI/agent layer inside every family matters more than the title ranking."),
 ("Q2. Strongest for 6–10y?","GenAI delivery, Cloud AI Platform, Automation senior tracks, Solutions Engineer, and AIOps senior — all show dense 5–12y bands overlapping 8.5y."),
 ("Q3. Strongest salary upside?","Cloud AI Platform (₹70–90L outlier) > GenAI senior (₹35–70L) > AIOps COE (₹45–50L) > Security lead (₹50–80L, gated) > Architect (₹30L+ but 12y+). FDE upside imputed via GenAI bands (no direct disclosures)."),
 ("Q4. Easiest transition from ops/automation/testing?","Intelligent Automation (UiPath/Power Platform + GenAI) → AIOps (ServiceNow/Splunk/Dynatrace/Datadog + Python) → Cloud AI (Azure/AWS + RAG) → Solutions Engineer (delivery + presales)."),
 ("Q5. Skills spanning most families?","Python, RAG, LangChain-class, Azure OpenAI/Bedrock, Docker/K8s/CI-CD, vector DBs, prompt engineering, guardrails, Databricks/Snowflake, ServiceNow/observability."),
 ("Q6. Top 20 to learn?","Python, REST APIs/FastAPI, RAG, LangChain, LangGraph, Azure OpenAI, AWS Bedrock, prompt engineering, fine-tuning basics, vector DBs (pgvector/Qdrant), Docker, Kubernetes, Terraform, CI/CD, LLMOps/evals, guardrails, Databricks/Snowflake basics, ServiceNow ITOM concepts, UiPath/Power Automate, solution storytelling."),
 ("Q7. 10 max cross-role employability?","Python, RAG, LangChain, Azure OpenAI, AWS Bedrock, Docker, Kubernetes, vector DBs, prompt engineering, guardrails/evals."),
 ("Q8. Emerging → more valuable?","MCP, A2A, multi-agent orchestration, agent observability, LLM eval harnesses, AI gateways, knowledge-graph RAG, multimodal/SLM delivery."),
 ("Q9. Is Agentic AI real hiring or marketing?","Real: agent frameworks + MCP + evals + multi-agent delivery appear as required/build duties in GenAI, FDE, and Architect JDs (Capco, Birlasoft, TCS-Arch, Qualcomm, NTT). Marketing gloss exists, but the build expectation is concrete."),
 ("Q10. How often MCP / multi-agent / frameworks?","MCP named in a handful of senior JDs (minority but growing); LangChain/LangGraph in the plurality of GenAI/FDE/Arch rows; AutoGen/CrewAI/LlamaIndex/Haystack/Semantic Kernel as second ring. Sheet 6/13 has counts."),
 ("Q11. Which cloud leads: AWS / Azure / GCP?","Azure (OpenAI/Foundry/Copilot) slightly densest, AWS (Bedrock/SageMaker) essentially tied, GCP/Vertex third but present (Techolution, SS&C, NTT). Tri-cloud literacy wins; specialize Azure-first for services/GCC, AWS-first for platform/startup."),
 ("Q12. Top GenAI platforms?","Azure OpenAI + AI Foundry, AWS Bedrock (+SageMaker), Vertex AI/Gemini, Snowflake Cortex (niche), Databricks Mosaic-class (platform context)."),
 ("Q13. Top agent frameworks?","LangChain > LangGraph > LlamaIndex > AutoGen ≈ CrewAI > Semantic Kernel/Haystack; MCP/A2A as integration protocols; OpenAI Agents SDK / Google ADK nascent."),
 ("Q14. Companies to prioritize?","See §28 Tier 1/2/3 — tuned to fit+pay+learning, not just logo size."),
 ("Q15. Best cities?","Bengaluru ≫ Hyderabad > Pune > Chennai/NCR; Remote ~5% competitive. Non-metros opportunistic."),
 ("Q16. How significant is Remote-India?","17/312 (5.4%) + 4 Pan-India: genuine (FDE, AIOps, security) but thin and contested — treat as a channel, not a strategy."),
 ("Q17. Advanced ML math vs app-level GenAI?","Overwhelmingly app-level GenAI engineering (RAG/agents/APIs/cloud). From-scratch ML theory/PhD math gates <10% (research/security-deep/arch-one-offs). This favors the candidate."),
 ("Q18. Do architect roles want hands-on coding?","Bimodal: startups/product demand Python/FastAPI ownership; Big4/IT-services weight presales/advisory with lighter code. ~Half explicitly want both."),
 ("Q19. Do FDE/Solutions roles require customer-facing?","Yes — near-universal: sponsor management, demos/POCs, scope control, travel. Ops stakeholder + testing-demo experience transfers directly."),
 ("Q20. Most realistic to ₹20–25L+?","Senior Automation, AIOps senior, Cloud AI delivery, GenAI delivery, Solutions Engineer (6–10y bands)."),
 ("Q21. Path to ₹30–35L+?","Platform ownership (Cloud/GenAI), agentic delivery depth, presales architecture, GCC/BFSI senior bands, security-lead (gated). Typically needs 10–12y framing + shipped production proofs."),
 ("Q22. Genuine gaps vs easy tooling?","Genuine: production RAG evals, agentic orchestration at scale, cloud landing-zone depth, security red-team/governance proofs. Easy tooling: prompt tricks, demo-only LangChain, badge-only cloud certs, vector-DB hello-worlds."),
 ("Q23. Certs worth it?","One cloud-AI cert max (Azure AI-102 or AWS MLA/SAA) + ITIL/ServiceNow if chasing AIOps; UiPath if chasing automation. Otherwise projects > badges."),
 ("Q24. Portfolio with max cross-role coverage?","(1) Enterprise RAG helpdesk (ITSM-grounded) → covers GenAI/Cloud/Solutions/FDE. (2) Agentic ops runbook resolver (MCP + evals + guardrails) → covers GenAI/FDE/AIOps/Security. (3) Secure AI gateway + cost/quality dashboard → covers Security/Cloud/Architect. All Docker/K8s-deployed with CI-CD."),
 ("Q25. 80-day priority?","Days 1–20 Python/APIs/RAG/LangChain + 1 shipped RAG; 21–45 LangGraph/agents + Bedrock + Azure OpenAI + vector DB + Docker + evals/guardrails + 2nd build; 46–65 K8s/Terraform/CI-CD + LLMOps + security + 3rd build + cert sprint; 66–80 apply blitz (Tier A/B), referrals, interview reps. §27 details."),
]
for q,a in qa:
    h3(q); p(a)

h1("25. Top Opportunity Shortlist — Top 100 (Top 20 highlighted)")
p("Sheet 4 holds the ranked 100 with fit reasons, transferable/missing skills, prep effort, and URLs. Top 20 logic: Tier A/B + 6–12y band + transferable ops/cloud/automation overlap + ACTIVE/LIKELY + learning value (not logo size).", italic=True)
top = sorted(jobs, key=lambda j:(-j["Candidate_Fit_Score"],-j["Role_Relevance_Score"]))[:20]
rows=[[i+1,f"{j['Job_Title']} @ {j['Company']} ({j['City']})",j["Standardized_Role"],j["Candidate_Fit_Score"],j["Status"]] for i,j in enumerate(top)]
table(["#","Role @ Company (City)","Family","Fit","Status"], rows)
p("Open Sheet 4 → filter Tier A → sort Fit desc → verify URL live → tailor resume with the row's Primary_Skills keywords → apply + referral in parallel. Re-verify status; LIKELY ≠ confirmed.", italic=True)

h1("26. Top Employer Target List")
h2("Tier 1 — Immediate (fit + volume + accessible bands)")
bullets([
 "EY India (AIOps ×6 multi-city, 5–9y) — closest skill bridge (ITOM/observability + ServiceNow).",
 "Capgemini (Power Platform 6–9y, live ATS) + Automation peers (UST, Zensar, Birlasoft) — automation→agentic corridor.",
 "Cloud-channel partners (Quantiphi/Searce/Minfy-class via Cloud AI rows: Cloudbyz, SS&C, Techolution, Saarthee) — Bedrock/Vertex/Azure delivery at 6–10y.",
 "Cognizant/Accenture AI delivery +/w FDE tracks — customer-facing ops background valued.",
 "Mid-size SaaS/product GenAI hirers (Capco/Wells Fargo-class delivery, Nanonets/Gnani-class builders) — ship-and-show culture.",
])
h2("Tier 2 — Strong (higher bar, higher upside)")
bullets([
 "Microsoft / Google / AWS-channel platform teams + Databricks/MongoDB ecosystem — Cloud/FDE/architecture; needs production proofs.",
 "Harness / CrowdStrike / Epam / Presidio (AI-SRE/platform) — AIOps depth + Python/K8s bar.",
 "GCCs (banks, Siemens/Bosch/Volvo-class, health) — senior platform/automation; slower but better bands.",
 "Fractal / Mu Sigma-class + frontier-lab deployment (OpenAI remote) — FDE craft + travel tolerance needed.",
])
h2("Tier 3 — Stretch (12y+/specialist or frontier)")
bullets(["NTT DATA / Deloitte Architect tracks, Anthropic/Databricks presales architects, 100MS/Akto-class security leads, Cartesia-class platform outliers — target after 2–3 shipped builds + cloud cert."])
p("Per-employer skills/bands/cities/pay live in Sheet 8. Always confirm the req ID is still open.", italic=True)

h1("27. Gap Analysis + 80-Day Market-Driven Plan")
h2("Already Transferable")
bullets(["Enterprise ops/ITSM: incident, RCA, change, SLA, stakeholder comms → AIOps/FDE/Solutions.", "Testing + automation mindset: test plans, regression, Selenium-class → evals, guardrails, automation.", "Infra literacy: Linux, SQL, monitoring, ITSM tools → Cloud/AIOps ramp.", "Client delivery: demos, docs, scope control → presales/FDE."])
h2("Quick Wins (weeks)")
bullets(["Python for APIs (FastAPI), Git, Docker, prompt engineering, RAG hello→production, Azure OpenAI + Bedrock basics, eval checklist, resume keywording."])
h2("Core Gaps (structured builds)")
bullets(["LangChain/LangGraph agents, vector DBs + hybrid/graph RAG, K8s + Terraform + CI/CD, LLMOps (prompt/version/eval/monitor), guardrails + PII/redaction, cost/latency tuning, architecture storytelling (RFP/POC→scale)."])
h2("Long-Term Gaps")
bullets(["12y+ architecture authority, security red-team/governance proofs, ML-theory depth, multi-region platform ownership — sequence after first AI role, not before applying."])
h2("80-day schedule (tied to demand)")
table(["Phase","Focus","Exit proof"],
 [["1–20","Python/APIs/RAG/LangChain + Azure OpenAI; eval basics","Shipped RAG helpdesk (Docker) + 15 Tier-B apps"],
  ["21–45","LangGraph/agents + Bedrock/Vertex + vector DB + guardrails","Agentic ops-resolver + MCP trace + eval report"],
  ["46–65","K8s/TF/CI-CD + LLMOps + security + cert sprint","Secure gateway + dashboard + cloud-AI cert"],
  ["66–80","Apply blitz + referrals + mocks","40+ tailored apps; 2–3 loops/week; offer push"]])
callout("Apply from day 20 in parallel — Tier A automation/AIOps/Solutions roles first; GenAI/Cloud/FDE as builds land.")

h1("28. Conclusions")
bullets([
 "Broad-based AI demand with a GenAI/agent substrate: all 8 families hire; the portable bet is RAG + agents + cloud-LLM + delivery engineering.",
 "An 8.5y ops/automation profile is structurally competitive for ~half the evidence set — lead with adjacent strengths, close with shipped builds.",
 "Pay transparency is poor; target bands not point estimates. ₹20–25L entry via senior delivery; ₹30–35L+ via platform/agentic/presales depth or GCC seniority.",
 "Geography is metro-led; Remote is a bonus channel. Verify every URL — churn is measurable in-window.",
])

h1("29. Methodology Limitations")
bullets([
 "Sample, not census: 312 uniques vs 1,500–3,000 aspiration. WebSearch 429s + login/bot walls capped HIGH coverage at 20.5%.",
 "Date sparsity: month curves directional only. Salary n small: disclosed-only medians fragile.",
 "Title-boundary judgment: Adjacent rows flagged; FDE-vs-Solutions-vs-Architect overlaps resolved by primary duties, logged in Notes.",
 "Scores are candidate-relative decision aids, not employer grades. Re-verify ACTIVE status at click time.",
])

h1("30. Source Appendix")
p(f"202 logged queries across WebSearch/WebFetch; ~90 source-platform strings. Top evidence: Indeed + Shine (MEDIUM), Greenhouse + employer ATS/SuccessFactors (HIGH), aggregators/snippets (LOW). Full log Sheets 18–19; QA Sheet 20. Raw JSONL retained under data/stream_*.jsonl; merged evidence: output/merged_jobs.json.", italic=True)
table(["Source class","Examples","Confidence"],
 [["Employer/ATS","Greenhouse, Lever, Ashby, Workday, SuccessFactors, company careers","HIGH"],
  ["Portals","Indeed, Shine, Foundit, Glassdoor, Hirist, Instahyre, Cutshort","MEDIUM"],
  ["Aggregators/snippets","Jobsora, Jooble, Talent.com, CareerJet, Yahoo-fallback","LOW"]])

h1("31. Red-Team Report (independent challenge + fixes)")
bullets([
 "Missed companies? TCS/Infosys/HCLTech direct AIOps reqs absent; KPMG/PwC architect absent; Snowflake/Elastic/MongoDB solutions-engineer absent (architect titles instead); Palantir/Anthropic-India FDE absent (global-only). Fixed by: explicit gap disclosure, not by inventing rows.",
 "Single-source overweight? Indeed+Shine heavy in MEDIUM/LOW. Mitigated: HIGH kept separate; dashboard shows 20.5% HIGH; conclusions avoid single-source claims.",
 "Agentic inflation? Checked: MCP/A2A/agent-eval rows required building, not buzzwords — but minority. Report labels them frontier, weights P1.",
 "Repost inflation? Canonical dedup on company+title+city + alternate-source merge; distinct req IDs kept distinct and labeled. Duplicate rate 0.6% post-merge is conservative and disclosed.",
 "Location bias? Bengaluru 35% reflects both reality and discoverability; non-metro thinness flagged as gap, not absence proof.",
 "Salary misread? Board estimates quarantined; medians disclosed-only; small-n fragility stated in three places.",
 "Date confusion? Access-date vs posting-date separated (Date_Confidence + Date_Evidence); Monthly sheet carries a caution banner.",
])
h1("32. Saturation Statement")
p(f"8 streams × 202 queries × ~90 sources × 314 reviews → 312 uniques. Additional searching would likely add long-tail variants (non-metro, Lever/Ashby startups, Mar–Jun backfill) but is unlikely to overturn the five load-bearing conclusions (broad demand, metro concentration, senior-leaning bands, opacity, 52% Tier-A/B fit). Next marginal hour is best spent verifying Tier-A URLs and shipping portfolio builds, not chasing a census.", italic=True)

# ---------- save ----------
DOCX = OUT / "India_AI_Job_Market_Deep_Research_Report_Mar-Sep_2026.docx"
doc.save(DOCX)
print("Saved", DOCX)
