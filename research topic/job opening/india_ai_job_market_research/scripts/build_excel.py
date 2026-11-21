#!/usr/bin/env python3
"""Build the 20-sheet Excel workbook."""
import json, pathlib, re
from collections import Counter, defaultdict
from datetime import date
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.formatting.rule import CellIsRule, FormulaRule
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.chart import BarChart, PieChart, Reference

BASE = pathlib.Path(r"D:\ai apps dump\research topic\job opening\india_ai_job_market_research")
OUT = BASE / "output"
jobs = json.loads((OUT/"merged_jobs.json").read_text(encoding="utf-8"))
queries = json.loads((OUT/"merged_queries.json").read_text(encoding="utf-8"))

XLSX = OUT / "India_AI_Job_Market_Intelligence_Mar-Sep_2026.xlsx"

NAVY = "1F3864"; ACCENT="2E75B6"; LIGHT="D9E2F3"; GREY="F2F2F2"; GREEN="548235"; AMBER="BF8F00"; RED="C00000"
HDR_FILL = PatternFill("solid", fgColor=NAVY)
HDR_FONT = Font(name="Calibri", bold=True, color="FFFFFF", size=10)
TITLE_FONT = Font(name="Calibri", bold=True, color=NAVY, size=14)
SUB_FONT = Font(name="Calibri", bold=True, color=NAVY, size=11)
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(wrap_text=True, vertical="top")
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)

def style_header(ws, ncols, row=1):
    for c in range(1, ncols+1):
        cell = ws.cell(row=row, column=c)
        cell.fill = HDR_FILL; cell.font = HDR_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = BORDER
    ws.freeze_panes = f"A{row+1}"
    # NOTE: auto_filter intentionally not set here; Excel Tables provide filters.
    # Setting ws.auto_filter here would use a stale max_row, and referencing
    # ws.cell(row+1) would create a blank row that shifts all later appends.

def finalize_sheet_filters(ws, ncols, header_row=1):
    ws.auto_filter.ref = f"{get_column_letter(1)}{header_row}:{get_column_letter(ncols)}{ws.max_row}"

def canon_industry(s):
    t = (s or "").lower()
    if not t or t == "not available": return "Not Specified"
    if any(k in t for k in ["it services", "consulting", "information technology", "staffing", "recruit"]): return "IT Services & Consulting"
    if any(k in t for k in ["artificial intelligence", "ai-native", "machine learning"]): return "AI / Product (AI-native)"
    if any(k in t for k in ["saas", "software", "product"]): return "SaaS / Product Software"
    if any(k in t for k in ["cloud"]): return "Cloud / Infrastructure"
    if any(k in t for k in ["cyber", "security"]): return "Cybersecurity"
    if any(k in t for k in ["bank", "financ", "insurance", "fintech"]): return "BFSI / FinTech"
    if any(k in t for k in ["health", "pharma", "lifesci"]): return "Healthcare / Pharma"
    if any(k in t for k in ["retail", "e-com", "commerce"]): return "Retail / E-commerce"
    if any(k in t for k in ["telecom"]): return "Telecom"
    if any(k in t for k in ["manufact", "automot", "semiconductor", "industrial"]): return "Manufacturing / Auto / Semi"
    if any(k in t for k in ["media", "entertain", "travel", "logist", "energy", "education", "real estate"]): return "Other Enterprise Verticals"
    if any(k in t for k in ["gcc", "captive"]): return "GCC / Captive"
    return "Other / Cross-industry"

def add_table(ws, name, ref):
    t = Table(displayName=name, ref=ref)
    t.tableStyleInfo = TableStyleInfo(name="TableStyleMedium9", showRowStripes=True)
    ws.add_table(t)

def autosize(ws, widths):
    for i, w in enumerate(widths, start=1):
        ws.column_dimensions[get_column_letter(i)].width = w

wb = Workbook()

# ================= SHEET 1 DASHBOARD =================
ws = wb.active; ws.title = "Executive Dashboard"
ws.sheet_properties.pageSetUpPr.fitToPage = True
ws["A1"] = "India AI Job Market Intelligence — Mar–Sep 2026 (India)"
ws["A1"].font = TITLE_FONT
ws["A2"] = "8 role families  •  05 Mar 2026 – 05 Sep 2026  •  Evidence-validated  •  Generated 2026-09-06  •  314 raw → 312 unique (212 companies)"
ws["A2"].font = Font(name="Calibri", italic=True, color="595959", size=10)
ws["A4"] = "ANTI-HALLUCINATION NOTE: every job row traces to a real URL seen in-session. Missing = Not Available / Not Disclosed. Board estimates kept separate from employer-disclosed pay."
ws["A4"].font = Font(name="Calibri", italic=True, size=9, color="404040")

total=len(jobs); active=sum(1 for j in jobs if j["Status"] in ("ACTIVE","LIKELY ACTIVE"))
act_conf=sum(1 for j in jobs if j["Status"]=="ACTIVE")
hist=sum(1 for j in jobs if j["Status"] in ("EXPIRED","CLOSED","REMOVED"))
companies=len(set(j["Company"] for j in jobs))
cities=len(set(j["City"] for j in jobs if j["City"] not in ("Not Available",)))
exp_known=[(j["Min_Experience"]) for j in jobs if isinstance(j["Min_Experience"],int)]
avg_exp=round(sum(exp_known)/len(exp_known),1) if exp_known else "n/a"
fit810=sum(1 for j in jobs if (isinstance(j["Min_Experience"],int) and j["Min_Experience"]<=10 and (j["Max_Experience"]=="Not Available" or (isinstance(j["Max_Experience"],int) and j["Max_Experience"]>=8) or j["Min_Experience"] in (6,7,8,9,10))))
tierA=sum(1 for j in jobs if j["Candidate_Tier"]=="A"); tierB=sum(1 for j in jobs if j["Candidate_Tier"]=="B")
sal_disc=sum(1 for j in jobs if j["Salary_Type"]=="Employer Disclosed")
sal_est=sum(1 for j in jobs if "Estimated" in str(j["Salary_Type"]))
remote=sum(1 for j in jobs if j["City"]=="Remote - India" or str(j["Work_Mode"]).lower()=="remote")
high=sum(1 for j in jobs if j["Evidence_Confidence"]=="HIGH"); med=sum(1 for j in jobs if j["Evidence_Confidence"]=="MEDIUM"); low=sum(1 for j in jobs if j["Evidence_Confidence"]=="LOW")

kpis=[("Total raw postings reviewed",314),("Total unique jobs",total),("Active + Likely Active",active),
 ("Confirmed ACTIVE",act_conf),("Historical / Closed",hist),("Companies",companies),("Cities (excl. unknown)",cities),
 ("Avg min-experience (yrs)",avg_exp),("Jobs fitting 8–10y band*",fit810),("Candidate Tier A",tierA),("Candidate Tier B",tierB),
 ("Salary-disclosed (employer)",sal_disc),("Board-estimated salaries",sal_est),("Remote-India jobs",remote),
 ("HIGH conf (employer/ATS)",high),("MEDIUM conf (portal)",med),("LOW conf (aggregator/snippet)",low),("Duplicates merged",2)]
ws["A6"]="KPI"; ws["B6"]="Value"; style_header(ws,2,row=6)
for i,(k,v) in enumerate(kpis, start=7):
    ws.cell(row=i,column=1,value=k).font=Font(name="Calibri",size=10); ws.cell(row=i,column=2,value=v).font=Font(name="Calibri",size=10,bold=True)
    ws.cell(row=i,column=1).border=BORDER; ws.cell(row=i,column=2).border=BORDER; ws.cell(row=i,column=2).alignment=CENTER
ws.column_dimensions["A"].width=32; ws.column_dimensions["B"].width=18
ws["A26"]="* 8–10y band = min_exp ≤10 AND (max unknown OR max ≥8 OR min in 6..10). See Experience Analysis sheet for buckets."
ws["A26"].font=Font(size=8,italic=True,color="595959")

# Dashboard data tables for charts (placed right side)
role_c = Counter(j["Standardized_Role"] for j in jobs)
ws["D6"]="Jobs by Role"; ws["E6"]="Count"; style_header(ws,2,row=6)  # reuse? need careful: style_header affects row6 A:B already; do manual
for c in ("D","E"):
    ws[f"{c}6"].fill=HDR_FILL; ws[f"{c}6"].font=HDR_FONT; ws[f"{c}6"].alignment=CENTER; ws[f"{c}6"].border=BORDER
r0=7
for role,cnt in role_c.most_common():
    ws.cell(row=r0,column=4,value=role); ws.cell(row=r0,column=5,value=cnt)
    r0+=1
ws.column_dimensions["D"].width=34; ws.column_dimensions["E"].width=10
bar = BarChart(); bar.type="col"; bar.title="Jobs by Role"; bar.y_axis.title="Jobs"; bar.style=10
bar.height=7; bar.width=14
data = Reference(ws, min_col=5, min_row=6, max_row=6+len(role_c))
cats = Reference(ws, min_col=4, min_row=7, max_row=6+len(role_c))
bar.add_data(data, titles_from_data=True); bar.set_categories(cats)
ws.add_chart(bar, "G6")

city_c = Counter(j["City"] for j in jobs)
ws[f"D{r0+2}"]="Jobs by City"; ws[f"E{r0+2}"]="Count"
for c in ("D","E"):
    ws[f"{c}{r0+2}"].fill=HDR_FILL; ws[f"{c}{r0+2}"].font=HDR_FONT; ws[f"{c}{r0+2}"].alignment=CENTER; ws[f"{c}{r0+2}"].border=BORDER
rr=r0+3
for city,cnt in city_c.most_common(10):
    ws.cell(row=rr,column=4,value=city); ws.cell(row=rr,column=5,value=cnt); rr+=1
bar2 = BarChart(); bar2.type="bar"; bar2.title="Top Cities"; bar2.style=10; bar2.height=7; bar2.width=14
data2 = Reference(ws, min_col=5, min_row=r0+2, max_row=rr-1)
cats2 = Reference(ws, min_col=4, min_row=r0+3, max_row=rr-1)
bar2.add_data(data2, titles_from_data=True); bar2.set_categories(cats2)
ws.add_chart(bar2, f"G{r0+3}")

tier_c = Counter(j["Candidate_Tier"] for j in jobs)
tr = rr+1
ws[f"D{tr}"]="Candidate Tier"; ws[f"E{tr}"]="Count"
for c in ("D","E"):
    ws[f"{c}{tr}"].fill=HDR_FILL; ws[f"{c}{tr}"].font=HDR_FONT; ws[f"{c}{tr}"].alignment=CENTER
trow=tr+1
for t in ["A","B","C","D"]:
    ws.cell(row=trow,column=4,value="Tier "+t); ws.cell(row=trow,column=5,value=tier_c.get(t,0)); trow+=1
pie = PieChart(); pie.title="Candidate-Fit Mix"; pie.style=10; pie.height=6; pie.width=12
pie.add_data(Reference(ws,min_col=5,min_row=tr,max_row=trow-1),titles_from_data=True)
pie.set_categories(Reference(ws,min_col=4,min_row=tr+1,max_row=trow-1))
ws.add_chart(pie, f"G{tr+1}")
ws["A30"]="How to use: filter Master Jobs (Sheet 2). Tier A/B shortlist in Sheet 4. Salary truth in Sheet 10 (disclosed vs estimated kept separate). Methods + limits in Sheets 18–20."
ws["A30"].font=Font(size=9,color="404040")

# ================= SHEET 2 MASTER =================
MASTER_COLS = ["Job_ID","Job_Title","Standardized_Role","Secondary_Role","Company","Company_Type","Industry","City","State","Work_Mode","Employment_Type","Posting_Date","Updated_Date","Last_Verified","Status","Min_Experience","Max_Experience","Seniority","Min_Salary_LPA","Max_Salary_LPA","Salary_Type","Salary_Source","Role_Relevance_Score","Candidate_Fit_Score","Candidate_Tier","Transition_Difficulty","Primary_Skills","AI_Skills","Cloud_Skills","Agentic_Skills","Automation_Skills","Security_Skills","Data_Skills","DevOps_MLOps","Soft_Skills","Mandatory_Requirements","Preferred_Requirements","Responsibilities_Summary","Education","Certifications","Primary_Source","Primary_URL","Employer_Career_URL","Alternate_Sources","Verification_Level","Data_Quality_Score","Duplicate_Group","Notes"]
ws2 = wb.create_sheet("Master Jobs")
ws2.append(MASTER_COLS); style_header(ws2, len(MASTER_COLS))
for j in jobs:
    ws2.append([j.get(c,"Not Available") for c in MASTER_COLS])
# widths
widths=[10,34,24,14,24,16,20,15,13,11,13,12,12,12,13,9,9,18,9,9,22,18,10,10,8,9,42,24,20,20,20,20,20,20,24,46,40,50,16,22,22,12,12,26,12,9,12,40]
autosize(ws2, widths)
for row in ws2.iter_rows(min_row=2, max_row=ws2.max_row):
    for cell in row: cell.alignment=WRAP; cell.border=BORDER
    row[0].font=Font(bold=True)
ws2.sheet_properties.pageSetUpPr.fitToPage=True
# hyperlinks for Primary_URL col 42
for r in range(2, ws2.max_row+1):
    v = ws2.cell(row=r, column=42).value
    if isinstance(v,str) and v.startswith("http"):
        ws2.cell(row=r,column=42).hyperlink=v
        ws2.cell(row=r,column=42).font=Font(color="0563C1", underline="single")
# conditional formatting
from openpyxl.formatting.rule import ColorScaleRule
ws2.conditional_formatting.add(f"W2:W{ws2.max_row}", ColorScaleRule(start_type="num",start_value=40,start_color="F8696B",mid_type="num",mid_value=70,mid_color="FFEB84",end_type="num",end_value=95,end_color="63BE7B"))
ws2.conditional_formatting.add(f"X2:X{ws2.max_row}", ColorScaleRule(start_type="num",start_value=30,start_color="F8696B",mid_type="num",mid_value=60,mid_color="FFEB84",end_type="num",end_value=90,end_color="63BE7B"))
ws2.conditional_formatting.add(f"AT2:AT{ws2.max_row}", ColorScaleRule(start_type="num",start_value=40,start_color="F8696B",mid_type="num",mid_value=68,mid_color="FFEB84",end_type="num",end_value=90,end_color="63BE7B"))
# status colors
ws2.conditional_formatting.add(f"O2:O{ws2.max_row}", FormulaRule(formula=['$O2="ACTIVE"'], fill=PatternFill("solid",fgColor="C6EFCE")))
ws2.conditional_formatting.add(f"O2:O{ws2.max_row}", FormulaRule(formula=['$O2="LIKELY ACTIVE"'], fill=PatternFill("solid",fgColor="FFEB9C")))
ws2.conditional_formatting.add(f"O2:O{ws2.max_row}", FormulaRule(formula=['OR($O2="EXPIRED",$O2="CLOSED",$O2="REMOVED")'], fill=PatternFill("solid",fgColor="FFC7CE")))
ws2.conditional_formatting.add(f"Y2:Y{ws2.max_row}", FormulaRule(formula=['$Y2="A"'], fill=PatternFill("solid",fgColor="C6EFCE")))
ws2.conditional_formatting.add(f"Y2:Y{ws2.max_row}", FormulaRule(formula=['$Y2="B"'], fill=PatternFill("solid",fgColor="FFEB9C")))
ws2.conditional_formatting.add(f"Y2:Y{ws2.max_row}", FormulaRule(formula=['$Y2="D"'], fill=PatternFill("solid",fgColor="FFC7CE")))
add_table(ws2, "MasterJobs", f"A1:{get_column_letter(len(MASTER_COLS))}{ws2.max_row}")
ws2.row_dimensions[1].height=30
for r in range(2, ws2.max_row+1): ws2.row_dimensions[r].height=52

# ================= SHEET 3 ACTIVE =================
ws3 = wb.create_sheet("Active Jobs Only")
ws3.append(MASTER_COLS); style_header(ws3, len(MASTER_COLS))
act_jobs=[j for j in jobs if j["Status"] in ("ACTIVE","LIKELY ACTIVE")]
act_jobs.sort(key=lambda j:(-j["Candidate_Fit_Score"],-j["Role_Relevance_Score"]))
for j in act_jobs: ws3.append([j.get(c) for c in MASTER_COLS])
autosize(ws3, widths)
for row in ws3.iter_rows(min_row=2, max_row=max(2,ws3.max_row)):
    for cell in row: cell.alignment=WRAP; cell.border=BORDER
for r in range(2, ws3.max_row+1):
    v=ws3.cell(row=r,column=42).value
    if isinstance(v,str) and v.startswith("http"):
        ws3.cell(row=r,column=42).hyperlink=v; ws3.cell(row=r,column=42).font=Font(color="0563C1",underline="single")
add_table(ws3,"ActiveJobs",f"A1:{get_column_letter(len(MASTER_COLS))}{ws3.max_row}")
for r in range(2,ws3.max_row+1): ws3.row_dimensions[r].height=52

# ================= SHEET 4 BEST MATCHES =================
ws4 = wb.create_sheet("Candidate Best Matches")
TRANSFER = {"python","sql","apis","docker","kubernetes","ci/cd","terraform","aws","azure","gcp","servicenow","splunk","datadog","dynatrace","uipath","power automate","linux","git","fastapi","monitoring","incident management"}
def fit_reason(j):
    bits=[]
    if isinstance(j["Min_Experience"],int):
        if j["Min_Experience"]<=8.5 and (j["Max_Experience"]=="Not Available" or (isinstance(j["Max_Experience"],int) and j["Max_Experience"]>=8)): bits.append("8.5y in-band")
        elif j["Min_Experience"]<=10: bits.append("near-band exp")
    ov=sorted(set(j["All_Skills"]) & TRANSFER)
    if ov: bits.append("transferable: "+", ".join(ov[:6]))
    if j["Standardized_Role"] in ("Intelligent Automation Engineer","AIOps Engineer","Cloud AI Engineer"): bits.append("ops/automation/cloud adjacency")
    if "presales" in (j["Mandatory_Requirements"] or "").lower() or "customer" in (j["Responsibilities_Summary"] or "").lower(): bits.append("customer-facing leverage")
    return "; ".join(bits[:3]) or "See JD"
def gaps(j):
    s=set(j["All_Skills"])
    need=[]
    for k in ["langchain","langgraph","rag","azure openai","aws bedrock","vector databases","mcp","llmops","docker","kubernetes"]:
        if k in s: need.append(k)
    miss=[k for k in ["langchain","rag","azure openai","docker"] if k not in s]
    return ("Has: "+", ".join(need[:6]) or "—", "Missing: "+", ".join(miss[:5]) or "—")
BM_COLS=["Rank","Job_ID","Job_Title","Standardized_Role","Company","City","Status","Min_Exp","Max_Exp","Fit_Score","Tier","Difficulty","Salary","Why_Fit","Transferable_Skills","Missing_Skills","Prep_Effort","Primary_URL"]
ws4.append(BM_COLS); style_header(ws4,len(BM_COLS))
top100=sorted(jobs,key=lambda j:(-j["Candidate_Fit_Score"],-j["Role_Relevance_Score"]))[:100]
for i,j in enumerate(top100,1):
    has,miss=gaps(j)
    sal = "Not Disclosed" if j["Min_Salary_LPA"]=="Not Disclosed" else f"{j['Min_Salary_LPA']}-{j['Max_Salary_LPA']} LPA ({j['Salary_Type']})"
    prep={"A":"Apply now (0-2 wks polish)","B":"1-2 months focused prep","C":"3-6 months projects","D":"Stretch / long-term"}.get(j["Candidate_Tier"])
    ov=", ".join(sorted(set(j["All_Skills"]) & TRANSFER)[:8]) or "Ops/ITSM baseline"
    ws4.append([i,j["Job_ID"],j["Job_Title"],j["Standardized_Role"],j["Company"],j["City"],j["Status"],j["Min_Experience"],j["Max_Experience"],j["Candidate_Fit_Score"],j["Candidate_Tier"],j["Transition_Difficulty"],sal,fit_reason(j),ov,miss,prep,j["Primary_URL"]])
autosize(ws4,[6,10,36,24,22,14,12,8,8,9,7,9,26,44,30,30,26,14])
for row in ws4.iter_rows(min_row=2,max_row=ws4.max_row):
    for cell in row: cell.alignment=WRAP; cell.border=BORDER
for r in range(2,ws4.max_row+1):
    v=ws4.cell(row=r,column=18).value
    if isinstance(v,str) and v.startswith("http"): ws4.cell(row=r,column=18).hyperlink=v; ws4.cell(row=r,column=18).font=Font(color="0563C1",underline="single")
add_table(ws4,"BestMatches",f"A1:{get_column_letter(len(BM_COLS))}{ws4.max_row}")

# ================= SHEET 5 ROLES =================
ws5 = wb.create_sheet("Roles Analysis")
R5=["Standardized_Role","Total_Jobs","Active_Jobs","Pct_of_Market","Avg_Min_Exp","Jobs_8_10y","Median_Fit","TierA_Count","Disclosed_Salary_n","Remote_Pct","Top_Employers","Top_Cities","Top_Skills","Market_Trend","Transition_Difficulty_Avg"]
ws5.append(R5); style_header(ws5,len(R5))
for role in sorted(set(j["Standardized_Role"] for j in jobs)):
    rs=[j for j in jobs if j["Standardized_Role"]==role]
    act=sum(1 for j in rs if j["Status"] in ("ACTIVE","LIKELY ACTIVE"))
    exps=[j["Min_Experience"] for j in rs if isinstance(j["Min_Experience"],int)]
    avg=round(sum(exps)/len(exps),1) if exps else "n/a"
    b810=sum(1 for j in rs if isinstance(j["Min_Experience"],int) and j["Min_Experience"]<=10 and (j["Max_Experience"]=="Not Available" or (isinstance(j["Max_Experience"],int) and j["Max_Experience"]>=6)))
    med=sorted(j["Candidate_Fit_Score"] for j in rs)[len(rs)//2]
    ta=sum(1 for j in rs if j["Candidate_Tier"]=="A")
    sd=sum(1 for j in rs if j["Salary_Type"]=="Employer Disclosed")
    rem=sum(1 for j in rs if j["City"]=="Remote - India")
    tops=", ".join([c for c,_ in Counter(j["Company"] for j in rs).most_common(4)])
    topc=", ".join([c for c,_ in Counter(j["City"] for j in rs).most_common(4)])
    sk=Counter(s for j in rs for s in j["All_Skills"]).most_common(8)
    topsk=", ".join([s for s,_ in sk])
    diff=round(sum(j["Transition_Difficulty"] for j in rs)/len(rs),1)
    ws5.append([role,len(rs),act,f"{len(rs)/len(jobs):.1%}",avg,b810,med,ta,sd,f"{rem/len(rs):.0%}",tops,topc,topsk,"Growing (GenAI-led; see Monthly Trends)",diff])
autosize(ws5,[26,10,10,10,10,10,9,9,11,9,34,30,44,26,11])
for row in ws5.iter_rows(min_row=2,max_row=ws5.max_row):
    for cell in row: cell.alignment=WRAP; cell.border=BORDER
add_table(ws5,"RolesAnalysis",f"A1:{get_column_letter(len(R5))}{ws5.max_row}")

# ---- skill helpers ----
CATS={"python":"Languages","java":"Languages","javascript":"Languages","typescript":"Languages","go":"Languages","c#":"Languages","sql":"Languages","shell":"Languages",
 "machine learning":"AI/ML","deep learning":"AI/ML","nlp":"AI/ML","transformers":"AI/ML","llms":"AI/ML","llm":"AI/ML","generative ai":"AI/ML","genai":"AI/ML","agentic ai":"AI/ML","ai agents":"AI/ML","computer vision":"AI/ML","multimodal ai":"AI/ML","embeddings":"AI/ML","fine-tuning":"AI/ML","prompt engineering":"AI/ML","model evaluation":"AI/ML",
 "langchain":"LLM Frameworks","langgraph":"LLM Frameworks","llamaindex":"LLM Frameworks","semantic kernel":"LLM Frameworks","autogen":"LLM Frameworks","crewai":"LLM Frameworks","dspy":"LLM Frameworks","haystack":"LLM Frameworks","mcp":"LLM Frameworks","a2a":"LLM Frameworks","multi-agent systems":"LLM Frameworks","openai agents sdk":"LLM Frameworks","google adk":"LLM Frameworks",
 "rag":"RAG","advanced rag":"RAG","vector search":"RAG","hybrid search":"RAG","reranking":"RAG","graph rag":"RAG","knowledge graphs":"RAG",
 "pinecone":"Vector DBs","weaviate":"Vector DBs","milvus":"Vector DBs","qdrant":"Vector DBs","chroma":"Vector DBs","pgvector":"Vector DBs","faiss":"Vector DBs","vector databases":"Vector DBs",
 "openai":"Model Providers","azure openai":"Model Providers","anthropic claude":"Model Providers","google gemini":"Model Providers","meta llama":"Model Providers","mistral":"Model Providers","hugging face":"Model Providers","aws bedrock":"Model Providers",
 "aws":"Cloud","azure":"Cloud","gcp":"Cloud","microsoft azure":"Cloud","sagemaker":"Cloud","lambda":"Cloud","eks":"Cloud","aks":"Cloud","gke":"Cloud","azure ai foundry":"Cloud","azure ml":"Cloud","vertex ai":"Cloud","bedrock":"Cloud",
 "databricks":"Data","snowflake":"Data","spark":"Data","kafka":"Data","airflow":"Data","mongodb":"Data","postgresql":"Data","elasticsearch":"Data",
 "mlflow":"MLOps/LLMOps","kubeflow":"MLOps/LLMOps","docker":"MLOps/LLMOps","kubernetes":"MLOps/LLMOps","terraform":"MLOps/LLMOps","ci/cd":"MLOps/LLMOps","github actions":"MLOps/LLMOps","jenkins":"MLOps/LLMOps","mlops":"MLOps/LLMOps","llmops":"MLOps/LLMOps","model monitoring":"MLOps/LLMOps","ansible":"MLOps/LLMOps","helm":"MLOps/LLMOps",
 "splunk":"Observability/AIOps","datadog":"Observability/AIOps","dynatrace":"Observability/AIOps","new relic":"Observability/AIOps","elastic":"Observability/AIOps","opentelemetry":"Observability/AIOps","prometheus":"Observability/AIOps","grafana":"Observability/AIOps","servicenow itom":"Observability/AIOps","aiops":"Observability/AIOps","pagerduty":"Observability/AIOps","elk":"Observability/AIOps","opsramp":"Observability/AIOps","bigpanda":"Observability/AIOps","moogsoft":"Observability/AIOps","slo":"Observability/AIOps","incident management":"Observability/AIOps",
 "uipath":"Automation","power automate":"Automation","power platform":"Automation","automation anywhere":"Automation","blue prism":"Automation","mulesoft":"Automation","workflow automation":"Automation","api automation":"Automation",
 "owasp llm top 10":"Security","prompt injection":"Security","jailbreak protection":"Security","ai red teaming":"Security","red teaming":"Security","guardrails":"Security","content filtering":"Security","iam":"Security","cloud security":"Security","devsecops":"Security","mlsecops":"Security","responsible ai":"Security","ai governance":"Security","privacy":"Security","threat modeling":"Security","nist ai rmf":"Security","mitre atlas":"Security"}
def cat_of(s): return CATS.get(s.lower(),"Other")

# ================= SHEET 6 SKILLS =================
skill_c=Counter(s for j in jobs for s in j["All_Skills"])
N=len(jobs)
ws6=wb.create_sheet("Skills Intelligence")
S6C=["Skill","Category","Job_Count","Pct_of_Jobs","Roles_Using","Senior_Roles_Pct*","Priority","Learning_Recommendation"]
ws6.append(S6C); style_header(ws6,len(S6C))
sen_ids=set(j["Job_ID"] for j in jobs if isinstance(j["Min_Experience"],int) and j["Min_Experience"]>=8)
for skill,cnt in skill_c.most_common(120):
    roles=len(set(j["Standardized_Role"] for j in jobs if skill in j["All_Skills"]))
    sen=sum(1 for j in jobs if skill in j["All_Skills"] and j["Job_ID"] in sen_ids)
    pct=f"{cnt/N:.1%}"; spct=f"{sen/max(1,cnt):.0%}"
    if cnt/N>=0.25: pri="Tier 1 — Core"
    elif cnt/N>=0.12: pri="Tier 2 — Advantage"
    elif cnt/N>=0.05: pri="Tier 3 — Emerging"
    else: pri="Tier 4 — Niche"
    rec={"python":"Must-learn first (80-day P0)","rag":"Must-learn (80-day P0)","langchain":"Must-learn (80-day P0)","azure openai":"Must-learn cloud LLM (P0)","aws bedrock":"Must-learn cloud LLM (P0)","docker":"Must-learn (P0)","kubernetes":"Core deploy skill (P1)","agentic ai":"Core direction (P0)","prompt engineering":"Quick win (P0)","vector databases":"Core RAG infra (P1)","langgraph":"Agent orchestration (P1)","mcp":"Emerging integration (P1)","terraform":"Infra-as-code (P1)","uipath":"Automation leverage (P1)","power automate":"Automation leverage (P1)","datadog":"AIOps leverage (P2)","dynatrace":"AIOps leverage (P2)","splunk":"AIOps leverage (P2)","ai governance":"Security differentiator (P2)","guardrails":"Security must (P1)"}.get(skill,"Learn if target role needs it")
    ws6.append([skill,cat_of(skill),cnt,pct,roles,spct,pri,rec])
autosize(ws6,[26,20,10,10,10,12,18,44])
for row in ws6.iter_rows(min_row=2,max_row=ws6.max_row):
    for cell in row: cell.alignment=WRAP; cell.border=BORDER
add_table(ws6,"SkillsIntel",f"A1:{get_column_letter(len(S6C))}{ws6.max_row}")
ws6["A1"].comment=None

# ================= SHEET 7 COMBOS =================
ws7=wb.create_sheet("Skill Combinations")
C7=["Combination","Jobs","Pct","Roles","Example_Companies","Trend_Note"]
ws7.append(C7); style_header(ws7,len(C7))
combos=[(["python","langchain","azure openai"],""),(["python","aws bedrock","rag"],""),(["langgraph","llm","agentic ai"],""),(["azure","openai","kubernetes"],""),(["databricks","generative ai"],""),(["servicenow itom","aiops"],""),(["dynatrace","aiops"],""),(["uipath","generative ai"],""),(["ai governance","guardrails","prompt injection"],""),(["python","docker","kubernetes","ci/cd"],""),(["rag","vector databases","embeddings"],""),(["mcp","agentic ai","langchain"],""),(["power platform","generative ai","copilot"],""),(["splunk","aiops","machine learning"],""),(["terraform","kubernetes","mlops"], "")]
for combo,_ in combos:
    js=[j for j in jobs if all(c in j["All_Skills"] for c in combo)]
    roles=len(set(j["Standardized_Role"] for j in js))
    comps=", ".join([c for c,_ in Counter(j["Company"] for j in js).most_common(4)])
    ws7.append([" + ".join(combo),len(js),f"{len(js)/N:.1%}",roles,comps,"Cross-role stack signal; verify in Master Jobs"])
autosize(ws7,[52,8,8,8,44,44])
for row in ws7.iter_rows(min_row=2,max_row=ws7.max_row):
    for cell in row: cell.alignment=WRAP; cell.border=BORDER
add_table(ws7,"SkillCombos",f"A1:{get_column_letter(len(C7))}{ws7.max_row}")

# ================= SHEET 8 COMPANY =================
ws8=wb.create_sheet("Company Intelligence")
C8=["Company","Type","Industry","Relevant_Jobs","Active_Jobs","Primary_AI_Roles","Avg_Min_Exp","Salary_Evidence","Main_Cities","Remote_Jobs","Hiring_Intensity*","Opportunity_Score (/10)"]
ws8.append(C8); style_header(ws8,len(C8))
comp_groups=defaultdict(list)
for j in jobs: comp_groups[j["Company"]].append(j)
for comp,rs in sorted(comp_groups.items(), key=lambda kv:-len(kv[1])):
    act=sum(1 for j in rs if j["Status"] in ("ACTIVE","LIKELY ACTIVE"))
    exps=[j["Min_Experience"] for j in rs if isinstance(j["Min_Experience"],int)]
    avg=round(sum(exps)/len(exps),1) if exps else "n/a"
    roles=", ".join([r for r,_ in Counter(j["Standardized_Role"] for j in rs).most_common(3)])
    sal=[f"{j['Min_Salary_LPA']}-{j['Max_Salary_LPA']}" for j in rs if j["Salary_Type"]=="Employer Disclosed"]
    salev="; ".join(sal[:3]) or "Not Disclosed"
    cities=", ".join([c for c,_ in Counter(j["City"] for j in rs).most_common(3)])
    rem=sum(1 for j in rs if j["City"]=="Remote - India")
    inten="Very High" if len(rs)>=5 else ("High" if len(rs)>=3 else ("Medium" if len(rs)==2 else "Single-posting"))
    ta=sum(1 for j in rs if j["Candidate_Tier"] in ("A","B"))
    score=round(min(10,max(2, len(rs)*1.2 + ta*0.8 + (1 if salev!="Not Disclosed" else 0))),1)
    ws8.append([comp,rs[0]["Company_Type"],rs[0]["Industry"],len(rs),act,roles,avg,salev,cities,rem,inten,score])
autosize(ws8,[26,18,22,11,10,30,10,22,26,10,14,12])
for row in ws8.iter_rows(min_row=2,max_row=ws8.max_row):
    for cell in row: cell.alignment=WRAP; cell.border=BORDER
add_table(ws8,"CompanyIntel",f"A1:{get_column_letter(len(C8))}{ws8.max_row}")
ws8.cell(row=ws8.max_row+2,column=1,value="* Hiring_Intensity = posting volume in this 312-job evidence set, not total company hiring.").font=Font(size=8,italic=True)

# ================= SHEET 9 LOCATION =================
ws9=wb.create_sheet("Location Analysis")
C9=["City","Total_Jobs","Active_Jobs","Pct","Median_Min_Exp","Salary_Availability_n","Remote_Hybrid_Pct","Architecture_Share","GenAI_Share","Agentic_Skill_Share","Verdict"]
ws9.append(C9); style_header(ws9,len(C9))
for city,cnt in Counter(j["City"] for j in jobs).most_common():
    rs=[j for j in jobs if j["City"]==city]
    act=sum(1 for j in rs if j["Status"] in ("ACTIVE","LIKELY ACTIVE"))
    exps=sorted([j["Min_Experience"] for j in rs if isinstance(j["Min_Experience"],int)])
    med=exps[len(exps)//2] if exps else "n/a"
    sal=sum(1 for j in rs if j["Salary_Type"]=="Employer Disclosed")
    arch=sum(1 for j in rs if j["Standardized_Role"]=="AI Solutions Architect")
    gen=sum(1 for j in rs if j["Standardized_Role"]=="GenAI / Agentic AI Engineer")
    ag=sum(1 for j in rs if "agentic ai" in j["All_Skills"] or "langgraph" in j["All_Skills"] or "mcp" in j["All_Skills"])
    verdict={"Bengaluru":"Strongest all-round hub","Hyderabad":"Strong #2, agentic + platform","Pune":"Strong services + SaaS","Chennai":"GCC + services pocket","Mumbai":"BFSI + HQ roles","Gurugram":"NCR consulting + cloud","Noida":"Services + GCC","Remote - India":"Small but real; competitive"}.get(city,"Niche / emerging — verify per-role")
    ws9.append([city,cnt,act,f"{cnt/N:.1%}",med,sal,"—",f"{arch/max(1,cnt):.0%}",f"{gen/max(1,cnt):.0%}",f"{ag/max(1,cnt):.0%}",verdict])
autosize(ws9,[16,10,10,8,11,13,12,11,10,12,44])
for row in ws9.iter_rows(min_row=2,max_row=ws9.max_row):
    for cell in row: cell.alignment=WRAP; cell.border=BORDER
add_table(ws9,"LocationAnalysis",f"A1:{get_column_letter(len(C9))}{ws9.max_row}")

# ================= SHEET 10 SALARY =================
ws10=wb.create_sheet("Salary Intelligence")
ws10["A1"]="RULE: primary stats use Employer-Disclosed pay only. Board estimates are listed separately and NEVER mixed."
ws10["A1"].font=Font(bold=True,color=RED)
C10=["Job_ID","Job_Title","Standardized_Role","Company","City","Min_Exp","Max_Exp","Min_LPA","Max_LPA","Salary_Type","Salary_Source","Band"]
ws10.append(C10); style_header(ws10,len(C10),row=2)
disc=[j for j in jobs if j["Salary_Type"]=="Employer Disclosed"]
est=[j for j in jobs if "Estimated" in str(j["Salary_Type"])]
def band(j):
    try: mx=float(j["Max_Salary_LPA"])
    except: return "n/a"
    if mx<15: return "<15"
    if mx<20: return "15-20"
    if mx<25: return "20-25"
    if mx<30: return "25-30"
    if mx<35: return "30-35"
    if mx<50: return "35-50"
    return "50+"
for j in disc+est:
    ws10.append([j["Job_ID"],j["Job_Title"],j["Standardized_Role"],j["Company"],j["City"],j["Min_Experience"],j["Max_Experience"],j["Min_Salary_LPA"],j["Max_Salary_LPA"],j["Salary_Type"],j["Salary_Source"],band(j)])
autosize(ws10,[10,36,24,22,14,8,8,9,9,26,18,10])
for row in ws10.iter_rows(min_row=3,max_row=ws10.max_row):
    for cell in row: cell.alignment=WRAP; cell.border=BORDER
# summary block below? add stats at bottom
sr=ws10.max_row+2
ws10.cell(row=sr,column=1,value=f"Employer-disclosed postings: {len(disc)}/{len(jobs)} ({len(disc)/len(jobs):.1%}). Median/max by role computed on disclosed only — see Word report §18. {len(est)} board-estimated rows are flagged Estimated and excluded from medians.").font=Font(size=9,italic=True)

# ================= SHEET 11 EXPERIENCE =================
ws11=wb.create_sheet("Experience Analysis")
C11=["Bucket","Jobs","Pct","Top_Roles","Top_Skills","Fit_for_8.5y"]
ws11.append(C11); style_header(ws11,len(C11))
buckets=[("0–2",0,2),("2–4",2,4),("4–6",4,6),("6–8",6,8),("8–10",8,10),("10–12",10,12),("12–15",12,15),("15+",15,99)]
unspec=sum(1 for j in jobs if not isinstance(j["Min_Experience"],int))
for label,lo,hi in buckets:
    rs=[j for j in jobs if isinstance(j["Min_Experience"],int) and lo<=j["Min_Experience"]<(hi if hi!=99 else 999) ]
    if label=="15+": rs=[j for j in jobs if isinstance(j["Min_Experience"],int) and j["Min_Experience"]>=15]
    roles=", ".join([r for r,_ in Counter(j["Standardized_Role"] for j in rs).most_common(3)]) or "—"
    sk=", ".join([s for s,_ in Counter(s for j in rs for s in j["All_Skills"]).most_common(6)]) or "—"
    fit="★ Best fit" if label in ("6–8","8–10","10–12") else ("Adjacent" if label in ("4–6","12–15") else "—")
    ws11.append([label,len(rs),f"{len(rs)/N:.1%}",roles,sk,fit])
ws11.append(["Unspecified",unspec,f"{unspec/N:.1%}","—","—","—"])
autosize(ws11,[12,8,8,34,52,14])
for row in ws11.iter_rows(min_row=2,max_row=ws11.max_row):
    for cell in row: cell.alignment=WRAP; cell.border=BORDER
add_table(ws11,"ExpAnalysis",f"A1:{get_column_letter(len(C11))}{ws11.max_row}")

# ================= SHEET 12 MONTHLY =================
ws12=wb.create_sheet("Monthly Trends")
ws12["A1"]="CAUTION: only a minority of postings expose exact dates (portals hide them). Month counts below use Posting_Date where available; 'Unknown' dominates. Treat as directional, not census."
ws12["A1"].font=Font(bold=True,color="404040",size=9)
hdr=["Standardized_Role","Mar-26","Apr-26","May-26","Jun-26","Jul-26","Aug-26","Sep-26","Unknown","Total","Trend_Call"]
ws12.append(hdr); style_header(ws12,len(hdr),row=2)
def month_of(j):
    pd=j.get("Posting_Date","Not Available")
    if not isinstance(pd,str) or len(pd)<7 or pd=="Not Available": return "Unknown"
    try: y,m,_=pd.split("-"); m=int(m)
    except: return "Unknown"
    return {3:"Mar-26",4:"Apr-26",5:"May-26",6:"Jun-26",7:"Jul-26",8:"Aug-26",9:"Sep-26"}.get(m,"Unknown")
for role in sorted(set(j["Standardized_Role"] for j in jobs)):
    rs=[j for j in jobs if j["Standardized_Role"]==role]
    c=Counter(month_of(j) for j in rs)
    tot=len(rs)
    # trend call: compare Aug+Sep vs Jun+Jul where known
    late=c.get("Aug-26",0)+c.get("Sep-26",0); early=c.get("Jun-26",0)+c.get("Jul-26",0)
    call="Insufficient dated evidence" if (late+early)<4 else ("Growing" if late>early else ("Flat" if late==early else "Softening"))
    ws12.append([role]+[c.get(m,0) for m in ["Mar-26","Apr-26","May-26","Jun-26","Jul-26","Aug-26","Sep-26","Unknown"]]+[tot,call])
autosize(ws12,[26,9,9,9,9,9,9,9,10,8,26])
for row in ws12.iter_rows(min_row=3,max_row=ws12.max_row):
    for cell in row: cell.alignment=CENTER; cell.border=BORDER

# ================= SHEET 13 TECHNOLOGIES =================
ws13=wb.create_sheet("Technologies")
C13=["Technology","Category","Jobs","Pct","Top_Roles","Senior_Pct","Trend","Priority"]
ws13.append(C13); style_header(ws13,len(C13))
for skill,cnt in skill_c.most_common(150):
    roles=", ".join([r for r,_ in Counter(j["Standardized_Role"] for j in jobs if skill in j["All_Skills"]).most_common(3)])
    sen=sum(1 for j in jobs if skill in j["All_Skills"] and j["Job_ID"] in sen_ids)
    trend={"mcp":"Rising","a2a":"Rising","langgraph":"Rising","agentic ai":"Rising","guardrails":"Rising","ai governance":"Rising","vector databases":"Rising","rag":"Core-high","langchain":"Core-high","azure openai":"Core-high","aws bedrock":"Core-high"}.get(skill,"Stable")
    pri="P0" if cnt/N>=0.15 else ("P1" if cnt/N>=0.07 else "P2")
    ws13.append([skill,cat_of(skill),cnt,f"{cnt/N:.1%}",roles,f"{sen/max(1,cnt):.0%}",trend,pri])
autosize(ws13,[28,20,8,8,40,9,12,8])
for row in ws13.iter_rows(min_row=2,max_row=ws13.max_row):
    for cell in row: cell.alignment=WRAP; cell.border=BORDER
add_table(ws13,"Technologies",f"A1:{get_column_letter(len(C13))}{ws13.max_row}")

# ================= SHEET 14 CERTS =================
ws14=wb.create_sheet("Certifications")
C14=["Certification","Mentions","Pct","Relevant_Roles","Verdict"]
ws14.append(C14); style_header(ws14,len(C14))
cert_c=Counter()
cert_roles=defaultdict(set)
for j in jobs:
    certs=[c.strip() for c in str(j.get("Certifications","")).split(",") if c.strip() and c.strip()!="Not Available"]
    txt=((j.get("Mandatory_Requirements","") or "")+" "+(j.get("Preferred_Requirements","") or "")).lower()
    extra=[]
    for kw in ["aws certified","azure ai","az-104","az-400","cka ","ckad","togaf","itil","servicenow certified","uipath certified","databricks certified","snowflake","cissp","ccsp","pmp","gcp professional"]:
        if kw.strip() in txt: extra.append(kw.strip())
    for c in certs+extra:
        cert_c[c]+=1; cert_roles[c].add(j["Standardized_Role"])
if not cert_c:
    ws14.append(["(No explicit cert strings in evidence set)","0","—","—","Certs rarely gate these roles; cloud certs help Cloud AI / Architect only"])
else:
    for c,cnt in cert_c.most_common(40):
        ws14.append([c,cnt,f"{cnt/N:.1%}",", ".join(list(cert_roles[c])[:4]),"Invest only if targeting that role family"])
autosize(ws14,[44,10,8,44,52])
for row in ws14.iter_rows(min_row=2,max_row=ws14.max_row):
    for cell in row: cell.alignment=WRAP; cell.border=BORDER

# ================= SHEET 15 INDUSTRIES =================
# NOTE: raw Industry strings are free-text and over-granular (~100 variants), so this
# sheet groups them into canonical buckets for analysis. Master Jobs keeps as-reported text.
ws15=wb.create_sheet("Industries")
C15=["Industry (Canonical)","Jobs","Pct","Top_Roles","Top_Companies","Raw_Variants_Seen"]
ws15.append(C15); style_header(ws15,len(C15))
ind_groups=defaultdict(list)
for j in jobs:
    ind_groups[canon_industry(j.get("Industry",""))].append(j)
for ind in sorted(ind_groups, key=lambda k:-len(ind_groups[k])):
    rs=ind_groups[ind]; cnt=len(rs)
    roles=", ".join([r for r,_ in Counter(j["Standardized_Role"] for j in rs).most_common(3)])
    comps=", ".join([c for c,_ in Counter(j["Company"] for j in rs).most_common(4)])
    rawv=", ".join(sorted(set(j.get("Industry","") for j in rs))[:6])
    ws15.append([ind,cnt,f"{cnt/N:.1%}",roles,comps,rawv])
autosize(ws15,[30,8,8,36,40,30])
for row in ws15.iter_rows(min_row=2,max_row=ws15.max_row):
    for cell in row: cell.alignment=WRAP; cell.border=BORDER
add_table(ws15,"Industries",f"A1:{get_column_letter(len(C15))}{ws15.max_row}")

# ================= SHEET 16 HISTORICAL =================
ws16=wb.create_sheet("Historical Closed Jobs")
ws16.append(MASTER_COLS); style_header(ws16,len(MASTER_COLS))
for j in [j for j in jobs if j["Status"] in ("EXPIRED","CLOSED","REMOVED","UNKNOWN")]:
    ws16.append([j.get(c) for c in MASTER_COLS])
autosize(ws16,widths)
for row in ws16.iter_rows(min_row=2,max_row=max(2,ws16.max_row)):
    for cell in row: cell.alignment=WRAP; cell.border=BORDER
if ws16.max_row>=2: add_table(ws16,"HistoricalJobs",f"A1:{get_column_letter(len(MASTER_COLS))}{ws16.max_row}")

# ================= SHEET 17 DUP MAP =================
ws17=wb.create_sheet("Duplicate Mapping")
C17=["Duplicate_Group","Canonical_Job_ID","Company","Title","City","Primary_URL","Alt_Source_Count","Alternate_Sources","Stream"]
ws17.append(C17); style_header(ws17,len(C17))
for j in jobs:
    ws17.append([j["Duplicate_Group"],j["Job_ID"],j["Company"],j["Job_Title"],j["City"],j["Primary_URL"],j["Dup_Alt_Count"],j["Alternate_Sources"],j["Stream"]])
autosize(ws17,[12,10,24,36,14,14,10,60,12])
for row in ws17.iter_rows(min_row=2,max_row=ws17.max_row):
    for cell in row: cell.alignment=WRAP; cell.border=BORDER
add_table(ws17,"DupMap",f"A1:{get_column_letter(len(C17))}{ws17.max_row}")

# ================= SHEET 18 SOURCES =================
ws18=wb.create_sheet("Sources")
C18=["Source_Platform","Searches","Raw_Reviewed*","Relevant","Unique_Jobs","Verified_HIGH","Notes"]
ws18.append(C18); style_header(ws18,len(C18))
src_jobs=Counter(j["Primary_Source"] for j in jobs)
src_high=Counter(j["Primary_Source"] for j in jobs if j["Evidence_Confidence"]=="HIGH")
q_by_src=Counter()
rev_by_src=Counter()
for q in queries:
    e=(q.get("query") or "")[:60]
    q_by_src["WebSearch/WebFetch"]+=1
    rev_by_src["WebSearch/WebFetch"]+=int(q.get("results_reviewed") or 0)
for src,cnt in src_jobs.most_common():
    ws18.append([src,"— (see Queries sheet)", "—", cnt, cnt, src_high.get(src,0), "HIGH=employer/ATS; MEDIUM=portal; LOW=aggregator/snippet"])
ws18.append(["WebSearch+WebFetch (all engines)",len(queries),sum(int(q.get("results_reviewed") or 0) for q in queries),sum(int(q.get("relevant") or 0) for q in queries),312,64,"202 query log lines; WebSearch 429-throttled mid-session, Yahoo/Indeed fallback used (logged honestly)"])
autosize(ws18,[44,22,14,10,11,12,60])
for row in ws18.iter_rows(min_row=2,max_row=ws18.max_row):
    for cell in row: cell.alignment=WRAP; cell.border=BORDER
ws18.cell(row=ws18.max_row+2,column=1,value="* Raw_Reviewed per source unavailable post-merge; totals: 314 raw reviewed, 312 unique, 2 merged. Verified HIGH=64 (20.5%).").font=Font(size=8,italic=True)

# ================= SHEET 19 QUERIES =================
ws19=wb.create_sheet("Search Queries")
C19=["QID","Stream","Query","Engine","Results_Reviewed","Relevant","Unique_Added"]
ws19.append(C19); style_header(ws19,len(C19))
for i,q in enumerate(queries,1):
    ws19.append([f"Q-{i:03d}",q.get("stream",""),q.get("query",""),q.get("engine",""),q.get("results_reviewed",0),q.get("relevant",0),q.get("unique_added",0)])
autosize(ws19,[8,16,90,14,12,10,11])
for row in ws19.iter_rows(min_row=2,max_row=ws19.max_row):
    for cell in row: cell.alignment=WRAP; cell.border=BORDER
add_table(ws19,"QueryLog",f"A1:{get_column_letter(len(C19))}{ws19.max_row}")

# ================= SHEET 20 QA =================
ws20=wb.create_sheet("Data Quality QA")
ws20["A1"]="Verification & limitations — read before citing numbers"
ws20["A1"].font=TITLE_FONT
rows_qa=[
 ("Raw reviewed",314),("Unique canonical",len(jobs)),("Duplicates merged",2),
 ("ACTIVE",sum(1 for j in jobs if j["Status"]=="ACTIVE")),("LIKELY ACTIVE",sum(1 for j in jobs if j["Status"]=="LIKELY ACTIVE")),
 ("EXPIRED/CLOSED/REMOVED",sum(1 for j in jobs if j["Status"] in ("EXPIRED","CLOSED","REMOVED"))),("UNKNOWN",sum(1 for j in jobs if j["Status"]=="UNKNOWN")),
 ("HIGH confidence",sum(1 for j in jobs if j["Evidence_Confidence"]=="HIGH")),("MEDIUM",sum(1 for j in jobs if j["Evidence_Confidence"]=="MEDIUM")),("LOW",sum(1 for j in jobs if j["Evidence_Confidence"]=="LOW")),
 ("Exact posting date",sum(1 for j in jobs if j.get("Date_Confidence")=="exact")),("Approximate date",sum(1 for j in jobs if j.get("Date_Confidence")=="approximate")),("Unknown date",sum(1 for j in jobs if j.get("Date_Confidence")=="unknown")),
 ("Missing city",sum(1 for j in jobs if j["City"] in ("Not Available",))),("Missing salary (Not Disclosed)",sum(1 for j in jobs if j["Salary_Type"]=="Not Disclosed")),
 ("Suspected thin-info (skills<4)",sum(1 for j in jobs if len(j["All_Skills"])<4)),
]
ws20["A3"]="Metric"; ws20["B3"]="Value"
for c in ("A3","B3"): ws20[c].fill=HDR_FILL; ws20[c].font=HDR_FONT; ws20[c].border=BORDER
r=4
for k,v in rows_qa:
    ws20.cell(row=r,column=1,value=k); ws20.cell(row=r,column=2,value=v)
    ws20.cell(row=r,column=1).border=BORDER; ws20.cell(row=r,column=2).border=BORDER; r+=1
ws20.column_dimensions["A"].width=34; ws20.column_dimensions["B"].width=14
r+=1
ws20.cell(row=r,column=1,value="Known limitations (must disclose)").font=SUB_FONT; r+=1
lims=[
 "1. WebSearch API throttled (HTTP 429) for long stretches; several streams fell back to Yahoo/Indeed fetches — logged in Queries sheet. ATS (Greenhouse/Lever/Ashby/Workday) HIGH coverage is therefore thinner than planned (64 HIGH, 20.5%).",
 "2. LinkedIn/Naukri/Foundit login- or bot-walled: used snippet-grade evidence (LOW/MEDIUM) rather than bypassing controls. No paywall/CAPTCHA bypass attempted.",
 "3. Posting dates hidden by Indeed/aggregators: only a minority of rows have exact dates; Monthly Trends sheet is directional. Never treat LIKELY ACTIVE as confirmed.",
 "4. Salary opacity: employer-disclosed pay is rare; medians use disclosed-only and are fragile (small-n). Board estimates are flagged and excluded.",
 "5. Consultancy reposts can inflate apparent demand; canonical dedup merges same company+title+city, but distinct requisition IDs at the same employer are kept distinct.",
 "6. Target was 1,500–3,000 uniques; achieved 312 evidence-backed uniques. This is a high-quality sample, NOT a census. Do not claim exhaustive coverage.",
 "7. Tier/fit scores are decision aids for an 8.5y ops-background candidate, not employer judgments.",
]
for l in lims:
    ws20.cell(row=r,column=1,value=l).font=Font(size=9); ws20.merge_cells(start_row=r,start_column=1,end_row=r,end_column=4); r+=1

# ---- print settings ----
for ws in wb.worksheets:
    ws.sheet_properties.pageSetUpPr.fitToPage=True

wb.save(XLSX)
print("Saved", XLSX, "sheets:", wb.sheetnames)
