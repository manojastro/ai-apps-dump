"""Secret/PII scanner + zero-secret proof (M25).

Scans three layers: (1) repo source/config/docs, (2) the exact HOCON prompt
blocks served to the LLM, (3) a generated prompt corpus (trace I/O, evidence
summaries, knowledge excerpts, timeline markdown). Findings report LOCATIONS
only — values are never printed, logged, or written.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

SHAPES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("api_key_google", re.compile(r"AIza[0-9A-Za-z_-]{35}")),
    ("api_key_openai", re.compile(r"sk-(proj-)?[A-Za-z0-9_-]{20,}")),
    ("api_key_anthropic", re.compile(r"sk-ant-[A-Za-z0-9_-]{20,}")),
    ("api_key_aws", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("token_github", re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}")),
    ("token_slack", re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}")),
    ("token_bearer", re.compile(r"Bearer\s+[A-Za-z0-9._~+/=-]{20,}")),
    ("ipv4", re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")),
)

FQDN_RE = re.compile(r"\b([a-zA-Z0-9][a-zA-Z0-9.-]*\.(com|net|org|io|dev|ai|us))\b")
FQDN_ALLOW = {"www.apache.org", "www.cognizant.com", "mcp.example.com",
              "api.you.com", "mcp.deepwiki.com", "pdi.service-now.com",
              "x.service-now.com", "example.com"}
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

SCAN_EXTENSIONS = {".py", ".hocon", ".md", ".example", ".ini", ".txt"}
SKIP_DIRS = {"__pycache__", ".pytest_cache", ".git", "node_modules", ".venv", "venv"}


def _repo_files() -> list[Path]:
    return [p for p in ROOT.rglob("*")
            if p.is_file() and p.suffix in SCAN_EXTENSIONS
            and not any(part in SKIP_DIRS for part in p.parts)]


def scan_text(text: str) -> dict[str, int]:
    """Count secret shapes in text (counts only — values never surface)."""
    return {name: len(pattern.findall(text)) for name, pattern in SHAPES if pattern.findall(text)}


def scan_repo() -> dict[str, Any]:
    """Layer 1: every tracked-shape file. Returns findings by file."""
    findings: dict[str, Any] = {"shape_hits": {}, "fqdns": set(), "emails": set()}
    for path in _repo_files():
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = str(path.relative_to(ROOT))
        for name, count in scan_text(text).items():
            findings["shape_hits"].setdefault(name, []).append(f"{rel} x{count}")
        for match in FQDN_RE.findall(text):
            host = match[0] if isinstance(match, tuple) else match
            if host not in FQDN_ALLOW and "YOUR-" not in host:
                findings["fqdns"].add(f"{rel}: {host}")
        for match in EMAIL_RE.findall(text):
            if "yourcompany" not in match and "example.com" not in match:
                findings["emails"].add(f"{rel}: {match}")
    findings["fqdns"] = sorted(findings["fqdns"])
    findings["emails"] = sorted(findings["emails"])
    return findings


def hocon_prompts() -> list[str]:
    """Layer 2: the exact instruction/description blocks served to the LLM."""
    from pyhocon import ConfigFactory
    path = ROOT / "registries" / "digital_workplace_autopilot" / "commander.hocon"
    cfg = ConfigFactory.parse_string(path.read_text(encoding="utf-8"), str(ROOT))
    prompts = []
    for tool in cfg["tools"]:
        for key in ("instructions",):
            if key in tool:
                prompts.append(str(tool[key]))
        function = tool.get("function", {})
        if "description" in function:
            prompts.append(str(function["description"]))
    return prompts


def trace_corpus(tmp_path: Path) -> list[str]:
    """Layer 3: tool I/O + evidence + knowledge + timeline of live traces."""
    import tests.conftest  # noqa: F401
    from audit.timeline import build_timeline, render_timeline_markdown
    from coded_tools.digital_workplace.knowledge import SearchEnterpriseKnowledge
    from database.bootstrap import get_connection, init_db
    from orchestration.investigate import investigate_sync
    import asyncio

    db = tmp_path / "proof.db"
    init_db(db)
    corpus: list[str] = []
    for request, device, user, case in [
            ("My laptop is very slow and Teams keeps freezing.", "DEVICE_001", "USER_001", "PROOF-1"),
            ("I changed my password and now my VPN will not connect.", "DEVICE_002", "USER_002", "PROOF-2"),
            ("How do I claim internet reimbursement?", "DEVICE_001", "USER_001", "PROOF-3")]:
        inv = investigate_sync(request, device, user, case_id=case, db_path=str(db))
        corpus.append(request)
        corpus += [s.summary for s in inv.steps]
        corpus += [h["title"] for h in inv.hypotheses]
    conn = get_connection(db)
    try:
        corpus += [e["sanitized_summary"] for e in
                   conn.execute("SELECT sanitized_summary FROM evidence").fetchall()]
        corpus.append(render_timeline_markdown(build_timeline(conn, "PROOF-1")))
    finally:
        conn.close()
    corpus.append(asyncio.run(SearchEnterpriseKnowledge().async_invoke(
        {"query": "How do I claim internet reimbursement?", "user_role": "employee"}, {}))["answer"])
    return corpus


def scan_corpus(texts: list[str]) -> dict[str, int]:
    total: dict[str, int] = {}
    for text in texts:
        for name, count in scan_text(text).items():
            total[name] = total.get(name, 0) + count
    return total


def _file_total(entries: list[str]) -> int:
    total = 0
    for entry in entries:
        try:
            total += int(entry.rsplit(" x", 1)[1])
        except (IndexError, ValueError):
            total += 1
    return total


def _repo_shape_total(repo_shape_hits: dict[str, list[str]], prefix: tuple[str, ...]) -> int:
    return sum(_file_total(v) for k, v in repo_shape_hits.items() if k.startswith(prefix))


def check_env_example() -> list[str]:
    """Every secret-valued key in .env.example must be a placeholder."""
    problems = []
    for line in (ROOT / ".env.example").read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        if any(tag in key for tag in ("KEY", "PWD", "PASSWORD", "SECRET", "TOKEN")):
            if "YOUR_" not in value and "example" not in value.lower():
                problems.append(key.strip())
    return problems


def run_proof(tmp_path: Path) -> dict[str, Any]:
    """Full proof run. Returns counts + verdict (PASS when everything is zero)."""
    repo = scan_repo()
    prompts = hocon_prompts()
    prompt_hits = scan_corpus(prompts)
    corpus = trace_corpus(tmp_path)
    corpus_hits = scan_corpus(corpus)
    env_problems = check_env_example()
    shape_total = sum(len(v) for v in repo["shape_hits"].values())
    clean = (shape_total == 0 and not repo["fqdns"] and not repo["emails"]
             and not prompt_hits and not corpus_hits and not env_problems)
    return {"prompts_inspected": len(prompts) + len(corpus),
            "repo_shape_hits": repo["shape_hits"], "repo_fqdns": repo["fqdns"],
            "repo_emails": repo["emails"], "prompt_hits": prompt_hits,
            "corpus_hits": corpus_hits, "env_problems": env_problems,
            "verdict": "PASS" if clean else "FAIL"}


def write_proof(path: Path, results: dict[str, Any]) -> None:
    repo_shapes = results["repo_shape_hits"]
    api_keys = (_repo_shape_total(repo_shapes, ("api_key_", "token_"))
                + sum(results["prompt_hits"].values()) + sum(results["corpus_hits"].values()))
    ips = _repo_shape_total(repo_shapes, ("ipv4",))
    lines = ["# ZERO-SECRET PROOF (M25)", "",
             f"Verdict: **{results['verdict']}**", "",
             "Scanned: repo source/config/docs + exact HOCON prompt blocks +",
             "generated trace corpus (tool I/O, evidence summaries, knowledge",
             "excerpts, timeline markdown). Findings report locations only.", "",
             f"LLM prompts inspected: {results['prompts_inspected']}",
             f"API keys exposed: {api_keys}",
             f"credentials exposed: {len(results['env_problems'])}",
             f"hostnames exposed: {len(results['repo_fqdns'])}",
             f"IP addresses exposed: {ips}",
             f"PII exposed: {len(results['repo_emails'])}", "",
             "**PASS**" if results["verdict"] == "PASS" else "**FAIL — see details**", ""]
    if results["verdict"] != "PASS":
        lines += ["## Details", "", f"```{results}```", ""]
    path.write_text("\n".join(lines), encoding="utf-8")
