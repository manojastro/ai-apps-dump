#!/usr/bin/env python3
"""Build India AI Job Market Intelligence outputs from stream JSONL files."""
import json, pathlib, re, collections, datetime
from collections import Counter, defaultdict

BASE = pathlib.Path(r"D:\ai apps dump\research topic\job opening\india_ai_job_market_research")
DATA = BASE / "data"
OUT = BASE / "output"
OUT.mkdir(parents=True, exist_ok=True)

CANDIDATE_EXP = 8.5

def norm(s):
    return re.sub(r"\s+", " ", (s or "").strip().lower())

def norm_city(c):
    c = (c or "").strip()
    cl = c.lower()
    mapping = {
        "bangalore": "Bengaluru", "bengaluru": "Bengaluru",
        "gurgaon": "Gurugram", "gurugram": "Gurugram",
        "new delhi": "Delhi", "delhi": "Delhi", "noida": "Noida",
        "mumbai": "Mumbai", "pune": "Pune", "hyderabad": "Hyderabad",
        "chennai": "Chennai", "kolkata": "Kolkata", "ahmedabad": "Ahmedabad",
        "jaipur": "Jaipur", "kochi": "Kochi", "coimbatore": "Coimbatore",
        "chandigarh": "Chandigarh", "indore": "Indore", "bhubaneswar": "Bhubaneswar",
        "mysuru": "Mysuru", "mysore": "Mysuru", "thiruvananthapuram": "Trivandrum",
        "trivandrum": "Trivandrum", "lucknow": "Lucknow",
    }
    if "remote" in cl: return "Remote - India"
    if "pan-india" in cl or "pan india" in cl or "india-wide" in cl: return "Pan-India"
    for k, v in mapping.items():
        if cl == k or cl.startswith(k + " ") or cl.startswith(k + "/") or cl.startswith(k + ","):
            return v
    # handle "Bengaluru / Pune" style -> take first
    if "/" in c:
        return norm_city(c.split("/")[0])
    return c if c else "Not Available"

def norm_state(city, state):
    m = {"Bengaluru":"Karnataka","Hyderabad":"Telangana","Pune":"Maharashtra","Mumbai":"Maharashtra",
         "Chennai":"Tamil Nadu","Coimbatore":"Tamil Nadu","Delhi":"Delhi","Gurugram":"Haryana","Noida":"Uttar Pradesh",
         "Kolkata":"West Bengal","Ahmedabad":"Gujarat","Jaipur":"Rajasthan","Kochi":"Kerala","Trivandrum":"Kerala",
         "Chandigarh":"Chandigarh","Indore":"Madhya Pradesh","Bhubaneswar":"Odisha","Mysuru":"Karnataka","Lucknow":"Uttar Pradesh"}
    if state and state not in ("", "Not Available"): return state
    return m.get(city, "Not Available")

CONF_RANK = {"HIGH":3,"MEDIUM":2,"LOW":1}
STATUS_ACTIVE = {"ACTIVE","LIKELY ACTIVE"}

# ---------- Load ----------
records = []
for f in sorted(DATA.glob("stream_*.jsonl")):
    for line in f.read_text(encoding="utf-8").splitlines():
        line=line.strip()
        if not line: continue
        try:
            r = json.loads(line)
            r["_file"] = f.name
            records.append(r)
        except Exception as e:
            print("JSON err", f.name, e)

raw_count = len(records)
print(f"Raw records: {raw_count}")

# ---------- Dedup ----------
groups = collections.OrderedDict()
for r in records:
    key = (norm(r.get("company","")), norm(r.get("title","")), norm(r.get("city","")))
    if key not in groups:
        groups[key] = {"canonical": r, "alts": []}
    else:
        cur = groups[key]["canonical"]
        # keep higher confidence; merge alternate_sources + urls
        cand_url = r.get("primary_url","")
        if cand_url and cand_url != cur.get("primary_url",""):
            cur.setdefault("alternate_sources", []).append(f"{r.get('source_platform','')} | {cand_url}")
        for a in r.get("alternate_sources", []) or []:
            if a not in (cur.get("alternate_sources", []) or []):
                cur.setdefault("alternate_sources", []).append(a)
        # merge skills union
        s1 = set(s.lower() for s in (cur.get("skills",[]) or []))
        s2 = set(s.lower() for s in (r.get("skills",[]) or []))
        cur["skills"] = sorted(s1 | s2)
        # keep better confidence record's core? keep earliest canonical but note dup
        if CONF_RANK.get(r.get("evidence_confidence","LOW"),1) > CONF_RANK.get(cur.get("evidence_confidence","LOW"),1):
            # swap canonical but preserve merged alts/skills
            old_url = cur.get("primary_url","")
            if old_url: cur.setdefault("alternate_sources", []).append(f"{cur.get('source_platform','')} | {old_url}")
            merged_alts = cur.get("alternate_sources", [])
            merged_skills = cur.get("skills", [])
            new_can = r
            new_can["alternate_sources"] = merged_alts
            new_can["skills"] = merged_skills
            groups[key]["canonical"] = new_can
        groups[key]["alts"].append(r.get("primary_url",""))

dup_removed = raw_count - len(groups)
print(f"Unique: {len(groups)}, dupes merged: {dup_removed}")

canon = list(groups.values())

# ---------- Scoring ----------
TRANSFERABLE = {"python","sql","apis","rest api","linux","shell","git","docker","kubernetes","ci/cd","jenkins","github actions",
  "terraform","ansible","aws","azure","gcp","azure openai","aws bedrock","vertex ai","servicenow","servicenow itom",
  "splunk","datadog","dynatrace","new relic","elastic","prometheus","grafana","opentelemetry","pagerduty",
  "uipath","power automate","power platform","automation anywhere","blue prism","selenium","testing","test automation",
  "itil","itsm","incident management","root cause analysis","monitoring","alerting","fastapi","flask","javascript","typescript","java","c#","go"}
DEEP_SPECIALIST = {"phd","research","cryptography","red teaming","threat modeling","reinforcement learning","computer vision",
  "pytorch","tensorflow","jax","cuda","distributed training","ml theory","mathematics","statistics phd"}
ARCH_HEAVY = {"togaf","sabse","enterprise architecture","presales","rpp","c-suite"}

ROLE_BASE = {
  "GenAI / Agentic AI Engineer": 88,
  "Cloud AI Engineer": 84,
  "Forward Deployed Engineer": 83,
  "AI Solutions Engineer": 81,
  "AI Solutions Architect": 85,
  "AIOps Engineer": 80,
  "Intelligent Automation Engineer": 78,
  "AI Security Engineer": 80,
  "Adjacent AI Role": 48,
}

def role_relevance(r):
    base = ROLE_BASE.get(r.get("standardized_role",""), 60)
    skills = [s.lower() for s in (r.get("skills",[]) or [])]
    bonus = min(len(skills), 12) * 0.4
    ai_kw = {"generative ai","llms","rag","agentic ai","langchain","langgraph","azure openai","aws bedrock","vertex ai",
             "prompt engineering","fine-tuning","vector databases","mcp","ai agents","llmops","mlops","aiops","ai governance","llm"}
    ai_hits = sum(1 for s in skills if s in ai_kw)
    bonus += min(ai_hits, 6) * 0.8
    summ = (r.get("responsibilities_summary","") or "") + " " + (r.get("mandatory_requirements","") or "")
    if re.search(r"\b(ai|genai|llm|rag|agent)\b", summ.lower()): bonus += 2
    else: bonus -= 4
    if r.get("standardized_role") == "Adjacent AI Role": bonus -= 3
    score = round(max(25, min(99, base + bonus)))
    return score

def candidate_fit(r):
    skills = set(s.lower() for s in (r.get("skills",[]) or []))
    minexp = r.get("min_experience"); maxexp = r.get("max_experience")
    # experience component (0-30)
    exp_score = 12
    if minexp is not None and maxexp is not None:
        if minexp <= CANDIDATE_EXP <= maxexp: exp_score = 30
        elif minexp <= CANDIDATE_EXP + 1.5 and maxexp is None: exp_score = 26
        elif abs(((minexp+maxexp)/2) - CANDIDATE_EXP) <= 2: exp_score = 27
        elif abs(((minexp+maxexp)/2) - CANDIDATE_EXP) <= 4: exp_score = 20
        elif (minexp or 0) > 12: exp_score = 6
        elif (maxexp or 99) < 4: exp_score = 10
    elif minexp is not None:
        d = minexp - CANDIDATE_EXP
        if d <= 0: exp_score = 28
        elif d <= 1.5: exp_score = 24
        elif d <= 3.5: exp_score = 17
        elif d <= 6: exp_score = 10
        else: exp_score = 5
    elif maxexp is not None:
        exp_score = 22 if maxexp >= CANDIDATE_EXP else 12
    # transferability (0-35)
    overlap = len(skills & TRANSFERABLE)
    trans_score = min(35, 8 + overlap * 3.2)
    # role accessibility (0-20): arch & deep specialist penalized, solutions/FDE/automation/cloud rewarded for ops background
    role = r.get("standardized_role","")
    role_acc = {"Intelligent Automation Engineer":18,"Cloud AI Engineer":17,"AIOps Engineer":17,"AI Solutions Engineer":16,
                "Forward Deployed Engineer":15,"GenAI / Agentic AI Engineer":14,"AI Security Engineer":10,"AI Solutions Architect":9,"Adjacent AI Role":12}.get(role,12)
    summ = ((r.get("mandatory_requirements","") or "") + " " + (r.get("preferred_requirements","") or "")).lower()
    if "phd" in summ: role_acc -= 5
    if "15+" in summ or "12+ years" in summ: role_acc -= 3
    if "c-suite" in summ and role in ("AI Solutions Architect",): role_acc -= 1
    # seniority adjustment
    sen = (r.get("seniority","") or "").lower()
    if "principal" in sen or "12+" in sen: role_acc -= 3
    if "intern" in sen or "junior" in sen: role_acc -= 2
    role_acc = max(2, min(20, role_acc))
    # skill-gap difficulty penalty inverted as learnability (0-15)
    hard = len([s for s in skills if s in {"pytorch","tensorflow","reinforcement learning","computer vision","cuda","jax"}])
    sec_hard = len(skills & {"red teaming","threat modeling","cryptography","reverse engineering"})
    learn = 15 - min(10, hard*2 + sec_hard*2.5)
    if "python" in skills: learn += 1
    learn = max(3, min(16, learn))
    total = round(exp_score + trans_score + role_acc + learn)
    return max(5, min(98, total))

def tier_and_difficulty(fit, r):
    skills = set(s.lower() for s in (r.get("skills",[]) or []))
    summ = ((r.get("mandatory_requirements","") or "") + " " + (r.get("preferred_requirements","") or "")).lower()
    hard_flags = ("phd" in summ) or (r.get("min_experience") or 0) >= 13 or len(skills & {"red teaming","cryptography","cuda","reinforcement learning"}) >= 2
    if fit >= 72 and not hard_flags: tier="A"
    elif fit >= 60: tier="B"
    elif fit >= 45: tier="C"
    else: tier="D"
    # difficulty 1-10
    diff = round(max(1, min(10, 11 - fit/10 + (2 if hard_flags else 0) + (1 if (r.get("min_experience") or 0) >= 12 else 0))))
    diff = max(1, min(10, diff))
    # clamp: A=>1-3, B=>3-6, C=>5-7, D=>7-10 roughly
    return tier, diff

def data_quality(r):
    c = r.get("evidence_confidence","LOW")
    base = {"HIGH":82,"MEDIUM":68,"LOW":50}.get(c,50)
    if r.get("date_confidence")=="exact": base+=6
    elif r.get("date_confidence")=="approximate": base+=2
    summ = r.get("responsibilities_summary","") or ""
    if len(summ) > 150: base+=4
    if r.get("primary_url","").startswith("http"): base+=3
    if (r.get("min_experience") is not None): base+=2
    if (r.get("min_salary_lpa") is not None): base+=2
    if len(r.get("skills",[]) or []) >= 8: base+=2
    return max(30, min(99, base))

# Build canonical job list
jobs = []
for idx, (key, g) in enumerate(groups.items(), start=1):
    r = g["canonical"]
    city = norm_city(r.get("city",""))
    state = norm_state(city, r.get("state",""))
    rr = role_relevance(r)
    cf = candidate_fit(r)
    tier, diff = tier_and_difficulty(cf, r)
    dq = data_quality(r)
    alt_srcs = r.get("alternate_sources", []) or []
    alt_str = " | ".join([a for a in alt_srcs if a]) if alt_srcs else "Not Available"
    # salary handling
    sal_type = r.get("salary_type","Not Disclosed") or "Not Disclosed"
    # responsibilities classification
    jobs.append({
        "Job_ID": f"AI-{idx:04d}",
        "Job_Title": r.get("title","Not Available"),
        "Standardized_Role": r.get("standardized_role","Not Available"),
        "Secondary_Role": "",
        "Company": r.get("company","Not Available"),
        "Company_Type": r.get("company_type","Not Available"),
        "Industry": r.get("industry","Not Available"),
        "City": city,
        "State": state,
        "Work_Mode": r.get("work_mode","Not Available"),
        "Employment_Type": r.get("employment_type","Not Available"),
        "Posting_Date": r.get("posting_date","Not Available"),
        "Date_Confidence": r.get("date_confidence","unknown"),
        "Date_Evidence": r.get("date_evidence",""),
        "Updated_Date": "Not Available",
        "Last_Verified": r.get("date_accessed","2026-09-05"),
        "Status": r.get("status","UNKNOWN"),
        "Min_Experience": r.get("min_experience") if r.get("min_experience") is not None else "Not Available",
        "Max_Experience": r.get("max_experience") if r.get("max_experience") is not None else "Not Available",
        "Seniority": r.get("seniority","Not Available"),
        "Min_Salary_LPA": r.get("min_salary_lpa") if r.get("min_salary_lpa") is not None else "Not Disclosed",
        "Max_Salary_LPA": r.get("max_salary_lpa") if r.get("max_salary_lpa") is not None else "Not Disclosed",
        "Salary_Type": sal_type,
        "Salary_Source": r.get("salary_source","") or ("Employer posting" if sal_type=="Employer Disclosed" else ("Board estimate" if "Estimated" in sal_type else "Not Available")),
        "Role_Relevance_Score": rr,
        "Candidate_Fit_Score": cf,
        "Candidate_Tier": tier,
        "Transition_Difficulty": diff,
        "Primary_Skills": ", ".join((r.get("skills",[]) or [])[:14]),
        "All_Skills": [s.lower() for s in (r.get("skills",[]) or [])],
        "AI_Skills": ", ".join([s for s in (r.get("skills",[]) or []) if s.lower() in {"generative ai","genai","llms","llm","rag","agentic ai","ai agents","prompt engineering","fine-tuning","embeddings","transformers","nlp","deep learning","machine learning","multimodal ai","computer vision","model evaluation","reinforcement learning"}][:10]),
        "Cloud_Skills": ", ".join([s for s in (r.get("skills",[]) or []) if s.lower() in {"aws","azure","gcp","microsoft azure","aws bedrock","azure openai","vertex ai","sagemaker","lambda","eks","aks","gke","azure ai foundry","azure ml","bedrock","gemini apis"}][:10]),
        "Agentic_Skills": ", ".join([s for s in (r.get("skills",[]) or []) if s.lower() in {"agentic ai","langchain","langgraph","llamaindex","semantic kernel","autogen","crewai","dspy","haystack","pydanticai","mcp","a2a","multi-agent systems"," CrewAI".strip().lower(),"openai agents sdk","google adk"}][:10]),
        "Automation_Skills": ", ".join([s for s in (r.get("skills",[]) or []) if s.lower() in {"uipath","power automate","power platform","automation anywhere","blue prism","mulesoft","api automation","workflow automation","servicenow itom","ansible"}][:10]),
        "Security_Skills": ", ".join([s for s in (r.get("skills",[]) or []) if s.lower() in {"owasp llm top 10","prompt injection","jailbreak protection","model security","ai red teaming","red teaming","guardrails","content filtering","data-loss prevention","iam","cloud security","devsecops","mlsecops","responsible ai","ai governance","privacy","threat modeling","nist ai rmf","mitre atlas"}][:10]),
        "Data_Skills": ", ".join([s for s in (r.get("skills",[]) or []) if s.lower() in {"databricks","snowflake","spark","kafka","airflow","dbt","bigquery","redshift","synapse","microsoft fabric","mongodb","postgresql","elasticsearch","vector databases","knowledge graphs","faiss","pinecone","weaviate","milvus","qdrant","chroma","pgvector"}][:10]),
        "DevOps_MLOps": ", ".join([s for s in (r.get("skills",[]) or []) if s.lower() in {"mlflow","kubeflow","docker","kubernetes","terraform","ci/cd","github actions","jenkins","model monitoring","experiment tracking","mlops","llmops","helm","argo"}][:10]),
        "Soft_Skills": "",
        "Mandatory_Requirements": r.get("mandatory_requirements","Not Available"),
        "Preferred_Requirements": r.get("preferred_requirements","Not Available"),
        "Responsibilities_Summary": r.get("responsibilities_summary","Not Available"),
        "Education": r.get("education","Not Available"),
        "Certifications": ", ".join(r.get("certifications",[]) or []) or "Not Available",
        "Primary_Source": r.get("source_platform","Not Available"),
        "Primary_URL": r.get("primary_url","Not Available"),
        "Employer_Career_URL": r.get("primary_url","Not Available") if r.get("evidence_confidence")=="HIGH" else "Not Available",
        "Alternate_Sources": alt_str,
        "Verification_Level": r.get("evidence_confidence","LOW"),
        "Evidence_Confidence": r.get("evidence_confidence","LOW"),
        "Data_Quality_Score": dq,
        "Duplicate_Group": f"DG-{idx:04d}" if g["alts"] else f"DG-{idx:04d}",
        "Dup_Alt_Count": len(g["alts"]),
        "Stream": r.get("stream",""),
        "Notes": r.get("notes",""),
    })

# Secondary role: simple heuristic
for j in jobs:
    s = set(j["All_Skills"])
    if j["Standardized_Role"]=="GenAI / Agentic AI Engineer" and s & {"aws","azure","gcp","aws bedrock","azure openai","vertex ai"}:
        j["Secondary_Role"]="Cloud AI"
    elif j["Standardized_Role"]=="Cloud AI Engineer" and s & {"langchain","rag","agentic ai"}:
        j["Secondary_Role"]="GenAI"
    elif j["Standardized_Role"] in ("Forward Deployed Engineer","AI Solutions Engineer") and "presales" in (j["Mandatory_Requirements"] or "").lower():
        j["Secondary_Role"]="Presales"
    else:
        j["Secondary_Role"]="Not Available"
    # soft skills extraction
    txt = ((j["Mandatory_Requirements"] or "")+" "+(j["Preferred_Requirements"] or "")+" "+(j["Responsibilities_Summary"] or "")).lower()
    softs=[]
    for kw in ["customer-facing","stakeholder management","consulting","presales","solution design","architecture","communication","mentoring","client delivery","proof-of-concept","poc","enterprise integration","workshop","documentation","c-suite","travel"]:
        if kw in txt: softs.append(kw if kw!="poc" else "proof-of-concept")
    j["Soft_Skills"]=", ".join(sorted(set(softs))[:8]) or "Not Available"

# Save merged JSON for reuse
(OUT/"merged_jobs.json").write_text(json.dumps(jobs, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"Merged jobs: {len(jobs)}")

# ---------- Query log merge ----------
qrows=[]
for f in sorted(DATA.glob("queries_*.jsonl")):
    for line in f.read_text(encoding="utf-8").splitlines():
        line=line.strip()
        if not line: continue
        try: qrows.append(json.loads(line))
        except: pass
print(f"Query lines: {len(qrows)}")
(OUT/"merged_queries.json").write_text(json.dumps(qrows, indent=1), encoding="utf-8")

# ---------- Stats for print ----------
from collections import Counter
print("By role:", Counter(j["Standardized_Role"] for j in jobs))
print("By status:", Counter(j["Status"] for j in jobs))
print("By conf:", Counter(j["Evidence_Confidence"] for j in jobs))
print("By tier:", Counter(j["Candidate_Tier"] for j in jobs))
print("Companies:", len(set(j["Company"] for j in jobs)))
print("Cities:", Counter(j["City"] for j in jobs).most_common(15))
