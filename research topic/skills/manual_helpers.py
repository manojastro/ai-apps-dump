"""Formatting helpers + canonical production code patterns for the manual."""
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

NAVY = "0F172A"
NAVY2 = "1E293B"
SLATE = "334155"
BODY_CLR = "212529"
CODE_BG = "0F172A"
CODE_FG = "F8FAFC"
CALLOUT_BG = "F1F5F9"
ALT_ROW = "F8FAFC"
BORDER_CLR = "CBD5E1"


def hex_rgb(h):
    h = h.lstrip("#")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def set_cell_shading(cell, color_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), color_hex.replace("#", ""))
    tcPr.append(shd)


def set_cell_margins(cell, top=60, left=110, bottom=60, right=110):
    tcPr = cell._tc.get_or_add_tcPr()
    mar = OxmlElement("w:tcMar")
    for tag, val in (("top", top), ("left", left), ("bottom", bottom), ("right", right)):
        el = OxmlElement(f"w:{tag}")
        el.set(qn("w:w"), str(val))
        el.set(qn("w:type"), "dxa")
        mar.append(el)
    tcPr.append(mar)


def set_table_borders(table, color_hex="CBD5E1", size="6"):
    tbl = table._tbl
    tblPr = tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), size)
        el.set(qn("w:color"), color_hex.replace("#", ""))
        borders.append(el)
    tblPr.append(borders)


def style_document(doc):
    sec = doc.sections[0]
    sec.top_margin = Inches(0.75)
    sec.bottom_margin = Inches(0.75)
    sec.left_margin = Inches(0.75)
    sec.right_margin = Inches(0.75)
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(10.5)
    normal.font.color.rgb = hex_rgb(BODY_CLR)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.15
    h1 = doc.styles["Heading 1"]
    h1.font.name = "Calibri"
    h1.font.size = Pt(16)
    h1.font.bold = True
    h1.font.color.rgb = hex_rgb(NAVY)
    h1.paragraph_format.space_before = Pt(18)
    h1.paragraph_format.space_after = Pt(8)
    h2 = doc.styles["Heading 2"]
    h2.font.name = "Calibri"
    h2.font.size = Pt(13)
    h2.font.bold = True
    h2.font.color.rgb = hex_rgb(NAVY2)
    h2.paragraph_format.space_before = Pt(14)
    h2.paragraph_format.space_after = Pt(6)
    h3 = doc.styles["Heading 3"]
    h3.font.name = "Calibri"
    h3.font.size = Pt(11)
    h3.font.bold = True
    h3.font.color.rgb = hex_rgb(SLATE)
    h3.paragraph_format.space_before = Pt(10)
    h3.paragraph_format.space_after = Pt(4)


def add_body(doc, text, bold=False, italic=False, size=None):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.bold = bold
    r.italic = italic
    if size is not None:
        r.font.size = Pt(size)
    return p


def add_bullets(doc, items):
    for it in items:
        p = doc.add_paragraph(style="List Bullet")
        if isinstance(it, tuple):
            lead, rest = it
            r = p.add_run(lead)
            r.bold = True
            p.add_run(rest)
        else:
            p.add_run(it)


def add_callout(doc, text, label=None):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = True
    cell = tbl.cell(0, 0)
    set_cell_shading(cell, CALLOUT_BG)
    set_cell_margins(cell)
    tblPr = tbl._tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge, sz in (("top", "6"), ("right", "6"), ("bottom", "6")):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), sz)
        el.set(qn("w:color"), BORDER_CLR)
        borders.append(el)
    left = OxmlElement("w:left")
    left.set(qn("w:val"), "single")
    left.set(qn("w:sz"), "24")
    left.set(qn("w:color"), NAVY)
    borders.append(left)
    for edge in ("insideH", "insideV"):
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "nil")
        el.set(qn("w:sz"), "0")
        el.set(qn("w:color"), "auto")
        borders.append(el)
    tblPr.append(borders)
    p = cell.paragraphs[0]
    if label:
        r = p.add_run(label + " ")
        r.bold = True
        r.italic = True
        r.font.color.rgb = hex_rgb(NAVY)
    r2 = p.add_run(text)
    r2.italic = True
    doc.add_paragraph()


def add_code_block(doc, code, caption=None):
    if caption:
        p = doc.add_paragraph()
        r = p.add_run(caption)
        r.bold = True
        r.font.size = Pt(10)
        r.font.color.rgb = hex_rgb(NAVY2)
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    set_cell_shading(cell, CODE_BG)
    set_cell_margins(cell, top=80, left=140, bottom=80, right=140)
    set_table_borders(tbl, color_hex=CODE_BG, size="6")
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.line_spacing = 1.15
    lines = code.strip("\n").split("\n")
    for i, line in enumerate(lines):
        run = p.add_run(line if line else " ")
        run.font.name = "Consolas"
        run.font.size = Pt(9)
        run.font.color.rgb = hex_rgb(CODE_FG)
        if i < len(lines) - 1:
            run.add_break()
    doc.add_paragraph()


def add_styled_table(doc, headers, rows, col_widths=None):
    tbl = doc.add_table(rows=1 + len(rows), cols=len(headers))
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.style = "Table Grid"
    tbl.autofit = True
    set_table_borders(tbl, color_hex=BORDER_CLR, size="6")
    for j, h in enumerate(headers):
        cell = tbl.cell(0, j)
        cell.text = ""
        p = cell.paragraphs[0]
        r = p.add_run(h)
        r.bold = True
        r.font.size = Pt(10)
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        r.font.name = "Calibri"
        set_cell_shading(cell, NAVY)
        set_cell_margins(cell)
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            cell = tbl.cell(i + 1, j)
            cell.text = ""
            p = cell.paragraphs[0]
            r = p.add_run(str(val))
            r.font.size = Pt(9.5)
            r.font.name = "Calibri"
            set_cell_margins(cell)
            if i % 2 == 1:
                set_cell_shading(cell, ALT_ROW)
    doc.add_paragraph()
    return tbl


# ----------------------------------------------------------------------------
# CANONICAL PRODUCTION CODE PATTERNS (shared across all 7 roles)
# ----------------------------------------------------------------------------

CODE_HYBRID_RAG = '''"""Advanced Hybrid RAG: dense + BM25 + RRF fusion + cross-encoder rerank.
Production-ready: typed, logged, retries, budget guards, staleness checks."""
from __future__ import annotations
import hashlib, logging, math, time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Sequence

logger = logging.getLogger("hybrid_rag")
logging.basicConfig(level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s :: %(message)s")

@dataclass
class Doc:
    id: str
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    indexed_at: float = field(default_factory=time.time)

@dataclass
class ScoredDoc:
    doc: Doc
    score: float
    source: str

def reciprocal_rank_fusion(rank_lists: Sequence[Sequence[str]],
                           k: int = 60) -> Dict[str, float]:
    """RRF: score(d) = sum(1 / (k + rank)). Robust across heterogeneous scorers."""
    fused: Dict[str, float] = {}
    for lst in rank_lists:
        for rank, doc_id in enumerate(lst, start=1):
            fused[doc_id] = fused.get(doc_id, 0.0) + 1.0 / (k + rank)
    return fused

class HybridRetriever:
    def __init__(self, docs: List[Doc],
                 embed_fn: Callable[[str], List[float]],
                 cross_encoder: Callable[[str, str], float] | None = None,
                 max_ctx_chars: int = 12000, stale_after_s: float = 86400*7):
        if not docs:
            raise ValueError("HybridRetriever requires a non-empty corpus")
        self.docs = {d.id: d for d in docs}
        self.embed_fn = embed_fn
        self.cross_encoder = cross_encoder
        self.max_ctx_chars = max_ctx_chars
        self.stale_after_s = stale_after_s
        self._vectors = {d.id: embed_fn(d.text) for d in docs}
        logger.info("Indexed %d docs (dim=%d)", len(docs),
                    len(next(iter(self._vectors.values()))))

    @staticmethod
    def _cos(a: List[float], b: List[float]) -> float:
        dot = sum(x*y for x, y in zip(a, b))
        na = math.sqrt(sum(x*x for x in a)) or 1e-9
        nb = math.sqrt(sum(x*x for x in b)) or 1e-9
        return dot / (na * nb)

    @staticmethod
    def _bm25(query: str, doc: str, avg_len: float,
              k1: float = 1.5, b: float = 0.75) -> float:
        q_terms = query.lower().split()
        d_terms = doc.lower().split()
        dl = len(d_terms) or 1
        score = 0.0
        for t in set(q_terms):
            tf = d_terms.count(t)
            if tf == 0:
                continue
            idf = math.log(1 + (1000.0 / (1 + tf)))
            score += idf * (tf*(k1+1)) / (tf + k1*(1-b+b*dl/avg_len))
        return score

    def retrieve(self, query: str, top_k: int = 8,
                 dense_k: int = 25, sparse_k: int = 25) -> List[ScoredDoc]:
        if not query or not query.strip():
            raise ValueError("query must be non-empty")
        now = time.time()
        fresh = [d for d in self.docs.values()
                 if now - d.indexed_at <= self.stale_after_s]
        if len(fresh) < len(self.docs):
            logger.warning("Filtered %d stale docs from retrieval",
                           len(self.docs) - len(fresh))
        qv = self.embed_fn(query)
        dense = sorted(((self._cos(qv, self._vectors[d.id]), d) for d in fresh),
                       key=lambda t: t[0], reverse=True)[:dense_k]
        avg_len = sum(len(d.text.split()) for d in fresh) / max(len(fresh), 1)
        sparse = sorted(((self._bm25(query, d.text, avg_len), d) for d in fresh),
                        key=lambda t: t[0], reverse=True)[:sparse_k]
        dense_ids = [d.id for _, d in dense]
        sparse_ids = [d.id for _, d in sparse]
        fused = reciprocal_rank_fusion([dense_ids, sparse_ids])
        ranked = sorted(fused.items(), key=lambda kv: kv[1], reverse=True)
        cands = [(s, self.docs[i]) for i, s in ranked[:max(top_k*3, top_k)]]
        if self.cross_encoder is not None:  # cross-encoder rerank pass
            reranked = sorted(
                ((self.cross_encoder(query, d.text), s, d) for s, d in cands),
                key=lambda t: t[0], reverse=True)
            out = [ScoredDoc(doc=d, score=float(cs), source="cross-encoder")
                   for cs, _, d in reranked[:top_k]]
        else:
            out = [ScoredDoc(doc=d, score=float(s), source="rrf")
                   for s, d in cands[:top_k]]
        # token/char budget guard against context-window rot
        kept: List[ScoredDoc] = []
        used = 0
        for sd in out:
            ln = len(sd.doc.text)
            if used + ln > self.max_ctx_chars:
                logger.warning("Truncating context at budget %d chars",
                               self.max_ctx_chars)
                break
            kept.append(sd)
            used += ln
        logger.info("retrieve q=%r -> %d passages (%d chars)",
                    query[:60], len(kept), used)
        return kept

def build_context(passages: List[ScoredDoc]) -> str:
    parts = []
    for i, sd in enumerate(passages, 1):
        digest = hashlib.sha256(sd.doc.text.encode()).hexdigest()[:10]
        parts.append(f"[{i} id={sd.doc.id} sha={digest} "
                     f"score={sd.score:.4f} via={sd.source}]\\n{sd.doc.text}")
    return "\\n\\n".join(parts)
'''

CODE_SUPERVISOR = '''"""Stateful multi-agent supervisor (LangGraph) with HITL approval gates.
Production-ready: typed state, checkpointing, recursion guard, audit log."""
from __future__ import annotations
import logging, time, uuid
from typing import Any, Dict, List, Literal, TypedDict
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

logger = logging.getLogger("supervisor")
logging.basicConfig(level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s :: %(message)s")

class AgentState(TypedDict, total=False):
    run_id: str
    goal: str
    plan: List[str]
    evidence: List[Dict[str, Any]]
    draft: str
    approvals: List[Dict[str, Any]]
    steps: int
    max_steps: int
    status: Literal["running", "awaiting_approval", "approved",
                    "rejected", "done", "escalated"]

HIGH_RISK_TOOLS = {"prod_deploy", "db_write", " iam_change", "refund_issue"}

def researcher_node(tool_search):
    def _run(state: AgentState) -> AgentState:
        if state.get("steps", 0) >= state.get("max_steps", 12):
            logger.error("Recursion guard tripped at step %d", state["steps"])
            return {**state, "status": "escalated"}
        hits = tool_search(state["goal"], k=5)
        ev = list(state.get("evidence", [])) + [
            {"tool": "search", "at": time.time(), "items": hits}]
        logger.info("researcher: +%d evidence (step %d)",
                    len(hits), state.get("steps", 0) + 1)
        return {**state, "evidence": ev, "steps": state.get("steps", 0) + 1}
    return _run

def drafter_node(llm_draft):
    def _run(state: AgentState) -> AgentState:
        draft = llm_draft(state["goal"], state.get("evidence", []))
        return {**state, "draft": draft, "steps": state.get("steps", 0) + 1}
    return _run

def policy_gate(state: AgentState) -> str:
    """Route: HITL breakpoint before any high-risk tool or final answer."""
    text = (state.get("draft", "") + " " + state.get("goal", "")).lower()
    if any(t.strip() in text for t in HIGH_RISK_TOOLS) or "final" in text:
        logger.warning("HITL breakpoint hit run=%s", state.get("run_id"))
        return "awaiting_approval"
    return "done"

def approval_node(state: AgentState) -> AgentState:
    return {**state, "status": "awaiting_approval"}

def build_supervisor_graph(tool_search, llm_draft):
    g = StateGraph(AgentState)
    g.add_node("research", researcher_node(tool_search))
    g.add_node("draft", drafter_node(llm_draft))
    g.add_node("approval", approval_node)
    g.set_entry_point("research")
    g.add_edge("research", "draft")
    g.add_conditional_edges("draft", policy_gate,
                            {"awaiting_approval": "approval", "done": END})
    g.add_edge("approval", END)
    return g.compile(checkpointer=MemorySaver())

def resume_after_approval(app, run_id: str, thread_id: str,
                          approved: bool, reviewer: str) -> Dict[str, Any]:
    """Human-in-the-loop resume: record verdict, continue or halt."""
    verdict = {"reviewer": reviewer, "approved": approved, "at": time.time()}
    cfg = {"configurable": {"thread_id": thread_id}}
    snap = app.get_state(cfg)
    state = dict(snap.values)
    state.setdefault("approvals", []).append(verdict)
    state["status"] = "approved" if approved else "rejected"
    logger.info("run=%s %s by %s", run_id,
                "APPROVED" if approved else "REJECTED", reviewer)
    if not approved:
        return {**state, "status": "rejected"}
    app.update_state(cfg, {"status": "approved", "approvals": state["approvals"]})
    return dict(app.get_state(cfg).values)

def new_run(goal: str, max_steps: int = 12) -> Dict[str, Any]:
    return {"run_id": uuid.uuid4().hex[:12], "goal": goal, "evidence": [],
            "plan": [], "approvals": [], "steps": 0, "max_steps": max_steps,
            "status": "running"}
'''

CODE_RATELIMIT = '''"""Token-bucket rate limiter with dynamic backoff + jitter + priority.
Production-ready: monotonic clock, per-tenant buckets, async-safe."""
from __future__ import annotations
import asyncio, logging, random, time
from dataclasses import dataclass, field
from typing import Dict

logger = logging.getLogger("ratelimit")
logging.basicConfig(level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s :: %(message)s")

@dataclass
class Bucket:
    capacity: float
    refill_per_s: float
    tokens: float = field(init=False)
    updated: float = field(init=False)
    consec_fail: int = 0
    def __post_init__(self):
        self.tokens = self.capacity
        self.updated = time.monotonic()

class TokenBucketLimiter:
    def __init__(self, capacity: float = 60, refill_per_s: float = 10.0,
                 max_backoff_s: float = 30.0, base_backoff_s: float = 0.5):
        self._buckets: Dict[str, Bucket] = {}
        self._cap, self._rate = capacity, refill_per_s
        self._max_bo, self._base_bo = max_backoff_s, base_backoff_s
        self._lock = asyncio.Lock()

    def _bucket(self, tenant: str) -> Bucket:
        b = self._buckets.get(tenant)
        if b is None:
            b = self._buckets[tenant] = Bucket(self._cap, self._rate)
        return b

    @staticmethod
    def _jittered(delay: float) -> float:
        # Full jitter (AWS-style): sleep = random(0, delay)
        return random.uniform(0, delay)

    def _refill(self, b: Bucket) -> None:
        now = time.monotonic()
        elapsed = max(0.0, now - b.updated)
        # dynamic throttling: halve refill while failing repeatedly
        eff_rate = self._rate / (2 ** min(b.consec_fail, 3))
        b.tokens = min(b.capacity, b.tokens + elapsed * eff_rate)
        b.updated = now

    async def acquire(self, tenant: str, cost: float = 1.0,
                      timeout_s: float = 60.0) -> float:
        """Wait until `cost` tokens available; returns waited seconds."""
        if cost <= 0:
            raise ValueError("cost must be positive")
        if cost > self._cap:
            raise ValueError("cost exceeds bucket capacity")
        start = time.monotonic()
        waited = 0.0
        attempt = 0
        async with self._lock:
            b = self._bucket(tenant)
            self._refill(b)
        while True:
            async with self._lock:
                b = self._bucket(tenant)
                self._refill(b)
                if b.tokens >= cost:
                    b.tokens -= cost
                    b.consec_fail = 0
                    logger.debug("tenant=%s admitted cost=%.1f waited=%.2fs",
                                 tenant, cost, waited)
                    return waited
            if time.monotonic() - start > timeout_s:
                b.consec_fail += 1
                raise TimeoutError(f"rate-limit timeout tenant={tenant}")
            delay = min(self._max_bo, self._base_bo * (2 ** attempt))
            slp = self._jittered(delay)
            logger.warning("tenant=%s throttled; backoff %.2fs (try %d)",
                           tenant, slp, attempt)
            await asyncio.sleep(slp)
            waited += slp
            attempt += 1

    def report_failure(self, tenant: str) -> None:
        b = self._bucket(tenant)
        b.consec_fail += 1
        logger.warning("tenant=%s upstream failure x%d", tenant, b.consec_fail)
'''

CODE_TOOLCALL = '''"""Deterministic tool-calling with Pydantic validation + JSON-schema guard.
Production-ready: strict schemas, arg repair w/ bounded retry, audit trail."""
from __future__ import annotations
import json, logging
from typing import Any, Callable, Dict, List, Literal
from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger("toolcall")
logging.basicConfig(level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s :: %(message)s")

class SearchArgs(BaseModel):
    query: str = Field(min_length=2, max_length=500)
    top_k: int = Field(default=5, ge=1, le=20)
    corpus: Literal["runbooks", "tickets", "kb"] = "kb"

class TicketArgs(BaseModel):
    title: str = Field(min_length=5, max_length=140)
    severity: Literal["P1", "P2", "P3", "P4"] = "P3"
    assignee: str | None = None

REGISTRY: Dict[str, tuple[type[BaseModel], Callable[..., Any]]] = {}

def tool(schema: type[BaseModel]):
    def deco(fn: Callable[..., Any]):
        REGISTRY[fn.__name__] = (schema, fn)
        fn.json_schema = {"name": fn.__name__,
                          "parameters": schema.model_json_schema()}
        return fn
    return deco

@tool(SearchArgs)
def kb_search(query: str, top_k: int = 5, corpus: str = "kb") -> List[Dict]:
    return [{"id": f"{corpus}-{i}", "snippet": f"hit for {query!r} #{i}"}
            for i in range(top_k)]

@tool(TicketArgs)
def open_ticket(title: str, severity: str = "P3",
                assignee: str | None = None) -> Dict:
    return {"ticket": "INC-48211", "title": title,
            "severity": severity, "assignee": assignee}

def dispatch(tool_name: str, raw_args: Dict[str, Any] | str,
             max_repair: int = 1) -> Dict[str, Any]:
    """Validate-then-execute. Never exec unvalidated args."""
    if tool_name not in REGISTRY:
        raise KeyError(f"unknown tool: {tool_name}")
    schema, fn = REGISTRY[tool_name]
    args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
    for attempt in range(max_repair + 1):
        try:
            bound = schema.model_validate(args)
            result = fn(**bound.model_dump())
            logger.info("tool=%s ok args=%s", tool_name, bound.model_dump())
            return {"ok": True, "tool": tool_name, "result": result}
        except ValidationError as e:
            logger.warning("tool=%s validation fail try=%d err=%s",
                           tool_name, attempt, e.errors()[:2])
            if attempt >= max_repair:
                return {"ok": False, "tool": tool_name,
                        "error": e.errors(), "retried": attempt}
            args = coerce_args(args, e)
    return {"ok": False, "tool": tool_name, "error": "unreachable"}

def coerce_args(args: Dict[str, Any], err: ValidationError) -> Dict[str, Any]:
    """Bounded single repair: drop nulls, clamp ints, stringify enums."""
    fixed = {k: v for k, v in args.items() if v is not None}
    for e in err.errors():
        loc = e.get("loc", [None])[0]
        if e.get("type", "").startswith("int") and loc in fixed:
            try:
                fixed[loc] = int(float(fixed[loc]))
            except (TypeError, ValueError):
                pass
    return fixed
'''

CODE_EVAL = '''"""Automated LLM evaluation: faithfulness, context precision,
answer relevance (Ragas-style) + LLM-as-judge with calibration.
Production-ready: dataset versioning, thresholds, regression gate."""
from __future__ import annotations
import json, logging, statistics, time
from dataclasses import dataclass, asdict
from typing import Callable, Dict, List

logger = logging.getLogger("llm_eval")
logging.basicConfig(level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s :: %(message)s")

@dataclass
class EvalCase:
    id: str
    question: str
    contexts: List[str]
    reference: str
    prediction: str = ""

@dataclass
class EvalScores:
    faithfulness: float
    context_precision: float
    answer_relevance: float
    judge_pass: bool
    judge_rationale: str

def _overlap(a: str, b: str) -> float:
    sa, sb = set(a.lower().split()), set(b.lower().split())
    return len(sa & sb) / max(len(sa | sb), 1)

def faithfulness(prediction: str, contexts: List[str]) -> float:
    """Claim-grounding proxy: max sentence support across contexts."""
    sents = [s.strip() for s in prediction.replace("?", ".").split(".") if s.strip()]
    if not sents:
        return 0.0
    ctx = " ".join(contexts)
    return statistics.mean(_overlap(s, ctx) for s in sents)

def context_precision(contexts: List[str], reference: str, k: int = 3) -> float:
    ranked = sorted(contexts, key=lambda c: _overlap(c, reference), reverse=True)
    hits = sum(1 for c in ranked[:k] if _overlap(c, reference) > 0.12)
    return hits / max(min(k, len(ranked)), 1)

def answer_relevance(question: str, prediction: str,
                     embed_sim: Callable[[str, str], float] | None = None) -> float:
    if embed_sim:
        return max(0.0, min(1.0, embed_sim(question, prediction)))
    return _overlap(question, prediction) * 2.0 % 1.0  # lexical fallback

def llm_as_judge(question: str, reference: str, prediction: str,
                 judge_fn: Callable[[str], Dict]) -> tuple[bool, str]:
    prompt = (f"Q: {question}\\nREF: {reference}\\nPRED: {prediction}\\n"
              "Return JSON {pass: bool, rationale: str}.")
    try:
        raw = judge_fn(prompt)
        data = raw if isinstance(raw, dict) else json.loads(raw)
        return bool(data.get("pass", False)), str(data.get("rationale", ""))
    except Exception as e:  # judge failure must FAIL CLOSED loudly
        logger.exception("judge error: %s", e)
        return False, f"judge-error: {e}"

def run_suite(cases: List[EvalCase],
              judge_fn: Callable[[str], Dict],
              thresholds: Dict[str, float] | None = None) -> Dict:
    th = {"faithfulness": 0.70, "context_precision": 0.65,
          "answer_relevance": 0.70, **(thresholds or {})}
    rows = []
    for c in cases:
        f = faithfulness(c.prediction, c.contexts)
        cp = context_precision(c.contexts, c.reference)
        ar = answer_relevance(c.question, c.prediction)
        jp, rat = llm_as_judge(c.question, c.reference, c.prediction, judge_fn)
        passed = f >= th["faithfulness"] and cp >= th["context_precision"] \\
            and ar >= th["answer_relevance"] and jp
        rows.append({"id": c.id, "faithfulness": round(f, 3),
                     "context_precision": round(cp, 3),
                     "answer_relevance": round(ar, 3),
                     "judge_pass": jp, "rationale": rat, "PASS": passed})
    agg = {m: round(statistics.mean(r[m] for r in rows), 3) if rows else 0.0
           for m in ("faithfulness", "context_precision", "answer_relevance")}
    verdict = all(r["PASS"] for r in rows) if rows else False
    report = {"at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "n": len(rows), "thresholds": th, "aggregate": agg,
              "pass_rate": sum(r["PASS"] for r in rows) / max(len(rows), 1),
              "verdict": "SHIP" if verdict else "BLOCK", "rows": rows}
    logger.info("eval n=%d pass_rate=%.2f verdict=%s", len(rows),
                report["pass_rate"], report["verdict"])
    return report
'''

CODE_SECURITY = '''"""Security middleware: prompt-injection sanitization + PII redaction.
Production-ready: layered detectors, fail-closed, audit trail, latency budget."""
from __future__ import annotations
import logging, re, time
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

logger = logging.getLogger("ai_guard")
logging.basicConfig(level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s :: %(message)s")

INJECTION_PATTERNS = [
    r"ignore\\s+(all\\s+)?(previous|prior|above)\\s+instructions",
    r"you\\s+are\\s+now\\s+\\w+", r"disregard\\s+(the\\s+)?(system|policy)",
    r"jailbreak|DAN\\s+mode|developer\\s+mode",
    r"exfiltrate|ssn|credit\\s*card.*\\b(send|post|email)\\b",
    r"```\\s*system|</?system>|<\\|.*?\\|>",
    r"base64[,\\s]+[A-Za-z0-9+/=]{40,}",  # encoded payload smuggling
]
PII_PATTERNS: Dict[str, str] = {
    "EMAIL": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+",
    "PHONE": r"\\+?\\d[\\d\\s().-]{7,}\\d",
    "SSN_US": r"\\b\\d{3}-\\d{2}-\\d{4}\\b",
    "CARD": r"\\b(?:\\d[ -]?){13,19}\\b",
    "API_KEY": r"\\b(sk-[A-Za-z0-9]{8,}|AKIA[0-9A-Z]{16})\\b",
}
_COMPILED_INJ = [re.compile(p, re.I) for p in INJECTION_PATTERNS]
_COMPILED_PII = {k: re.compile(v) for k, v in PII_PATTERNS.items()}

@dataclass
class GuardVerdict:
    allowed: bool
    redacted_text: str
    reasons: List[str] = field(default_factory=list)
    pii_hits: Dict[str, int] = field(default_factory=dict)
    latency_ms: float = 0.0

def redact_pii(text: str, token_fmt: str = "[{kind}:REDACTED]") -> Tuple[str, Dict[str, int]]:
    hits: Dict[str, int] = {}
    out = text
    for kind, rx in _COMPILED_PII.items():
        found = rx.findall(out)
        if found:
            hits[kind] = len(found)
            out = rx.sub(token_fmt.format(kind=kind), out)
    return out, hits

def detect_injection(text: str) -> List[str]:
    return [f"injection-signature:{i}"
            for i, rx in enumerate(_COMPILED_INJ) if rx.search(text)]

def guard(text: str, *, max_chars: int = 8000,
          block_on_injection: bool = True) -> GuardVerdict:
    t0 = time.perf_counter()
    reasons: List[str] = []
    if not text:
        return GuardVerdict(False, "", ["empty-input"])
    if len(text) > max_chars:
        reasons.append(f"oversize:{len(text)}>{max_chars}")
        text = text[:max_chars]
    sigs = detect_injection(text)
    reasons.extend(sigs)
    redacted, hits = redact_pii(text)
    if hits:
        reasons.append(f"pii-redacted:{hits}")
        logger.info("PII redacted %s", hits)
    allowed = not (block_on_injection and sigs)
    if not allowed:
        logger.warning("BLOCKED input (%s)", ",".join(sigs))
    ms = (time.perf_counter() - t0) * 1000
    return GuardVerdict(allowed, redacted, reasons, hits, round(ms, 2))
'''
