# Skill frequency / co-occurrence / exp / salary from MASTER corpus. 23 Aug 2026 harvest.
from __future__ import annotations
import csv, re, json
from collections import Counter, defaultdict
from pathlib import Path
from itertools import combinations

TSV = Path(r"C:\Users\manoj\ai-career-intel-2026\research\jd-raw\MASTER-india-ai-jd-corpus.tsv")
OUT = Path(r"C:\Users\manoj\ai-career-intel-2026\research\jd-raw\SKILL-FREQ.json")

# Patterns are word-boundary-ish; longer aliases first where needed.
SKILLS = [
    ("Python", r"\bpython\b"),
    ("Java", r"\bjava\b(?!\s*script)"),
    ("JavaScript", r"\bjavascript\b|\bjs/glide\b|\bglide\b"),
    ("TypeScript", r"\btypescript\b"),
    ("C# / .NET", r"\bc#\b|\.net\b|\bcsharp\b"),
    ("Go", r"\bgolang\b|\bgo lang\b"),
    ("SQL", r"\bsql\b|\bpostgres\b|\bpostgresql\b|\bmysql\b|\brdbms\b"),
    ("REST / APIs", r"\brest\b|\bfastapi\b|\bflask\b|\bopenapi\b|\bapi(s)?\b"),
    ("FastAPI", r"\bfastapi\b"),
    ("Docker", r"\bdocker\b"),
    ("Kubernetes", r"\bkubernetes\b|\bk8s\b|\baks\b|\beks\b|\bgke\b"),
    ("CI/CD", r"\bci/?cd\b|\bgithub actions\b|\bazure devops\b|\bjenkins\b"),
    ("Git", r"\bgit\b|\bgithub\b"),
    ("Terraform", r"\bterraform\b|\biac\b"),
    ("RAG", r"\brag\b|retrieval[- ]augmented"),
    ("LangChain", r"\blangchain\b"),
    ("LangGraph", r"\blanggraph\b|\blangraph\b"),
    ("LlamaIndex", r"\bllamaindex\b|\bllama index\b"),
    ("CrewAI", r"\bcrewai\b|\bcrew ai\b"),
    ("AutoGen", r"\bautogen\b"),
    ("Semantic Kernel", r"\bsemantic kernel\b"),
    ("MCP", r"\bmcp\b|model context protocol"),
    ("Agentic / agents", r"\bagentic\b|\bai agents?\b|\bmulti-agent\b|\btool calling\b|\bfunction calling\b"),
    ("Prompt engineering", r"\bprompt\b"),
    ("Vector DBs (any)", r"\bvector\b|\bpinecone\b|\bweaviate\b|\bfaiss\b|\bchroma\b|\bmilvus\b|\bqdrant\b|\bpgvector\b"),
    ("Pinecone", r"\bpinecone\b"),
    ("FAISS", r"\bfaiss\b"),
    ("Weaviate", r"\bweaviate\b"),
    ("Chroma", r"\bchroma\b|\bchromadb\b"),
    ("Milvus", r"\bmilvus\b"),
    ("Qdrant", r"\bqdrant\b"),
    ("Azure OpenAI / Azure AI", r"\bazure openai\b|\bazure ai\b|\bcopilot studio\b|\bazure ai foundry\b|\baifoundry\b"),
    ("Azure (cloud)", r"\bazure\b"),
    ("AWS / Bedrock", r"\baws\b|\bbedrock\b"),
    ("Bedrock", r"\bbedrock\b"),
    ("GCP / Vertex", r"\bgcp\b|\bvertex\b|\bgemini\b|\bgoogle cloud\b|\bgoogle adk\b"),
    ("OpenAI API", r"\bopenai\b|\bgpt-4\b|\bgpt-3\b"),
    ("Claude / Anthropic", r"\bclaude\b|\banthropic\b"),
    ("Hugging Face", r"\bhugging\s?face\b"),
    ("PyTorch", r"\bpytorch\b"),
    ("TensorFlow", r"\btensorflow\b"),
    ("Copilot Studio", r"\bcopilot studio\b|\bpower virtual agents?\b|\bpva\b"),
    ("Power Platform", r"\bpower automate\b|\bpower apps\b|\bpower platform\b|\bdataverse\b"),
    ("ServiceNow / Now Assist", r"\bservicenow\b|\bnow assist\b|\bnowassist\b|\bitil\b|\bitsm\b"),
    ("Now Assist", r"\bnow assist\b|\bnowassist\b"),
    ("ITIL / ITSM", r"\bitil\b|\bitsm\b"),
    ("AIOps", r"\baiops\b|\bai ops\b|\bai-ops\b"),
    ("MLOps", r"\bmlops\b"),
    ("LLMOps", r"\bllmops\b|\bllm ops\b"),
    ("Observability (Dynatrace/Splunk/Datadog)", r"\bdynatrace\b|\bsplunk\b|\bdatadog\b|\bmoogsoft\b|\bbigpanda\b|\bgrafana\b|\bprometheus\b"),
    ("Dynatrace", r"\bdynatrace\b"),
    ("Splunk", r"\bsplunk\b"),
    ("Datadog", r"\bdatadog\b"),
    ("n8n / RPA", r"\bn8n\b|\buipath\b|\bautomation anywhere\b|\bblue prism\b|\brpa\b"),
    ("Evals / guardrails", r"\beval\b|\bguardrail\b|\bragas\b|\blangfuse\b|\blangsmith\b"),
]

def blob(r):
    return " ".join([
        r.get("title") or "",
        r.get("snippet") or "",
        r.get("company") or "",
    ]).lower()

def parse_exp_mid(s):
    if not s:
        return None
    nums = [int(x) for x in re.findall(r"(\d{1,2})", s) if 0 <= int(x) <= 25]
    if not nums:
        return None
    if len(nums) == 1:
        return nums[0]
    return (min(nums) + max(nums)) / 2.0

def exp_bucket(mid):
    if mid is None:
        return "unspecified"
    if mid < 3:
        return "0–2"
    if mid < 6:
        return "3–5"
    if mid < 9:
        return "6–8"
    if mid < 13:
        return "9–12"
    return "13+"

rows = list(csv.DictReader(TSV.open(encoding="utf-8"), delimiter="\t"))
N = len(rows)

hits = {k: [] for k, _ in SKILLS}
for i, r in enumerate(rows):
    t = blob(r)
    for name, pat in SKILLS:
        if re.search(pat, t, re.I):
            hits[name].append(i)

freq = []
for name, _ in SKILLS:
    n = len(hits[name])
    freq.append({"skill": name, "n": n, "pct": round(100 * n / N, 1)})
freq.sort(key=lambda x: -x["n"])

# co-occurrence among top skills with n>=20
top = [f["skill"] for f in freq if f["n"] >= 20][:25]
idx = {s: set(hits[s]) for s in top}
cooc = []
for a, b in combinations(top, 2):
    both = len(idx[a] & idx[b])
    if both:
        cooc.append({
            "a": a, "b": b, "both": both,
            "pct_of_a": round(100 * both / max(1, len(idx[a])), 1),
            "pct_of_b": round(100 * both / max(1, len(idx[b])), 1),
            "pct_of_N": round(100 * both / N, 1),
        })
cooc.sort(key=lambda x: -x["both"])

# companies
co = Counter((r.get("company") or "").strip() or "(blank)" for r in rows)

# exp
eb = Counter()
mids = []
for r in rows:
    m = parse_exp_mid(r.get("exp") or "")
    eb[exp_bucket(m)] += 1
    if m is not None:
        mids.append(m)

# salary rows
sal = []
for r in rows:
    s = (r.get("salary") or "").strip()
    if not s:
        continue
    if s.lower() in ("not disclosed", "not disclosed.", "market range"):
        continue
    if "est" in s.lower() and "employer" not in s.lower():
        continue
    sal.append({"company": r.get("company"), "title": r.get("title"), "exp": r.get("exp"), "salary": s, "loc": r.get("location"), "url": r.get("url")})

# java sql
jy = sum(1 for r in rows if (r.get("java") or "") == "Y")
sy = sum(1 for r in rows if (r.get("sql") or "") == "Y")

out = {
    "N": N,
    "freq": freq,
    "cooc_top40": cooc[:40],
    "companies_top40": co.most_common(40),
    "exp_buckets": dict(eb),
    "exp_mid_n": len(mids),
    "java_Y": jy,
    "sql_Y": sy,
    "salary_n": len(sal),
    "salary_rows": sal,
}
OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
print("N", N)
print("TOP SKILLS")
for f in freq[:50]:
    print(f"{f['n']:4d}  {f['pct']:5.1f}%  {f['skill']}")
print("EXP", dict(eb))
print("COMPANIES")
for c, n in co.most_common(25):
    print(f"{n:3d}  {c}")
print("SALARY N", len(sal))
print("JAVA_Y", jy, "SQL_Y", sy)
print("wrote", OUT)
