import json
from pathlib import Path
d = json.loads(Path(r"C:\Users\manoj\ai-career-intel-2026\research\jd-raw\SKILL-FREQ.json").read_text(encoding="utf-8"))
print("=== COOC ===")
for x in d["cooc_top40"][:30]:
    print(f"{x['both']:3d}  {x['pct_of_N']:5.1f}%  {x['a']}  x  {x['b']}")
print("=== SALARIES ===")
for s in d["salary_rows"]:
    c = (s.get("company") or "")[:32]
    t = (s.get("title") or "")[:50]
    print(f"{s['salary']} | {c} | {t}")
print("=== EXP ===")
print(d["exp_buckets"])
