"""FastAPI app: /health, /v1/search, /v1/ask, /v1/sources/{doc_id}, / (tiny UI)."""

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from opscopilot.answer import compose_answer
from opscopilot.chunk import chunk_corpus
from opscopilot.corpus import load_corpus
from opscopilot.models import (
    AskRequest,
    AskResponse,
    Chunk,
    Document,
    HealthResponse,
    SearchHit,
    SearchRequest,
    SearchResponse,
    SourceResponse,
)
from opscopilot.retrieval import hybrid_search
from opscopilot.settings import get_settings

app = FastAPI(title="OpsCopilot P1 (mock-first)")

_DOCS: list[Document] = []
_CHUNKS: list[Chunk] = []
_LOADED_FROM: str = ""


def set_store(docs: list[Document], chunks: list[Chunk], source: str = "test") -> None:
    """Inject an in-memory store (used by tests and smoke eval)."""
    global _DOCS, _CHUNKS, _LOADED_FROM
    _DOCS = list(docs)
    _CHUNKS = list(chunks)
    _LOADED_FROM = source


def ensure_loaded() -> tuple[list[Document], list[Chunk]]:
    """Load data/corpus on first request (lazy so import stays cheap/offline)."""
    global _DOCS, _CHUNKS, _LOADED_FROM
    if _CHUNKS or _DOCS:
        return _DOCS, _CHUNKS
    settings = get_settings()
    root = Path(settings.corpus_dir)
    if not root.is_absolute():
        # Resolve relative to the repo root (parent of src/) then CWD as fallback.
        here = Path(__file__).resolve()
        repo_root = here.parent.parent.parent
        candidate = repo_root / settings.corpus_dir
        if candidate.exists():
            root = candidate
    docs = load_corpus(root)
    chunks = chunk_corpus(docs)
    _DOCS = docs
    _CHUNKS = chunks
    _LOADED_FROM = str(root)
    return _DOCS, _CHUNKS


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    docs, chunks = ensure_loaded()
    return HealthResponse(
        status="ok" if chunks else "empty",
        docs=len(docs),
        chunks=len(chunks),
        corpus_loaded=bool(chunks),
    )


@app.post("/v1/search", response_model=SearchResponse)
def v1_search(req: SearchRequest) -> SearchResponse:
    _, chunks = ensure_loaded()
    settings = get_settings()
    top_k = req.top_k or settings.top_k_default
    hits, debug = hybrid_search(
        req.question, chunks, top_k=top_k, rrf_k=settings.rrf_k,
        dim=settings.embedding_dim, service=req.service,
    )
    return SearchResponse(
        hits=[
            SearchHit(
                chunk_id=h.chunk_id, doc_id=h.doc_id, title=h.title,
                section=h.section, service=h.service, status=h.status,
                score=h.score, rank=h.rank, snippet=h.snippet,
            )
            for h in hits
        ],
        retrieval_debug=debug,
    )


@app.post("/v1/ask", response_model=AskResponse)
def v1_ask(req: AskRequest) -> AskResponse:
    _, chunks = ensure_loaded()
    settings = get_settings()
    top_k = req.top_k or settings.top_k_default
    hits, debug = hybrid_search(
        req.question, chunks, top_k=top_k, rrf_k=settings.rrf_k,
        dim=settings.embedding_dim, service=req.service,
    )
    answer, citations, confidence, refused = compose_answer(
        req.question, hits,
        refuse_threshold=settings.refuse_threshold,
        rerank_enabled=settings.rerank_enabled,
    )
    return AskResponse(
        answer=answer, citations=citations, confidence=confidence,
        refused=refused, retrieval_debug=debug,
    )


@app.get("/v1/sources/{doc_id}", response_model=SourceResponse)
def v1_source(doc_id: str) -> SourceResponse:
    docs, _ = ensure_loaded()
    for d in docs:
        if d.doc_id == doc_id:
            return SourceResponse(
                doc_id=d.doc_id, doc_type=d.doc_type, title=d.title,
                service=d.service, status=d.status,
                updated_at=d.updated_at, content=d.content,
            )
    raise HTTPException(status_code=404, detail=f"Unknown doc_id {doc_id}")


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>OpsCopilot P1 — mock-first</title>
<style>body{font-family:system-ui,Arial,sans-serif;max-width:760px;margin:2rem auto;padding:0 1rem}
textarea{width:100%;height:4rem}button{padding:.5rem 1rem;margin:.25rem .25rem .25rem 0}
pre{background:#f4f4f4;padding:.75rem;white-space:pre-wrap}.cite{color:#0b5fff}</style>
</head><body>
<h1>OpsCopilot P1 <small>(mock-first, offline)</small></h1>
<p>Synthetic Acme Retail Ltd data only. Answers cite <span class="cite">[DOC §Section]</span> or refuse.</p>
<label>Question<br/>
<textarea id="q">Outlook keeps asking for password after MFA reset, what is the fix?</textarea></label><br/>
<label>Service filter <select id="service"><option value="">(all)</option>
<option>outlook</option><option>vpn</option><option>wifi</option><option>printer</option>
<option>iam</option><option>laptop</option><option>pos</option><option>sharepoint</option></select></label>
<label><input type="checkbox" id="dbg"/> show retrieval debug</label><br/>
<button id="ask">Ask</button><button id="search">Search only</button>
<h2>Answer</h2><div id="answer">—</div>
<h2>Sources</h2><div id="sources">—</div>
<h2>Debug</h2><pre id="debug">—</pre>
<script>
async function post(path, body){const r=await fetch(path,{method:'POST',
headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});return r.json();}
function citeLinks(text){return text.replace(/\\[([A-Za-z0-9\\-]+)\\s*§([^\\]]+)\\]/g,
'<a class="cite" href="/v1/sources/$1">[$1 §$2]</a>');}
document.getElementById('ask').onclick=async()=>{
 const q=document.getElementById('q').value, svc=document.getElementById('service').value||null;
 const j=await post('/v1/ask',{question:q,service:svc});
 document.getElementById('answer').innerHTML=citeLinks(j.answer)+(j.refused?
' <b>(refused)</b>':'')+` <i>${j.confidence}</i>`;
 document.getElementById('sources').innerHTML=j.citations.map(c=>
`<a href="/v1/sources/${c.doc_id}">[${c.doc_id} §${c.section}]</a>`).join(' ')||'—';
 document.getElementById('debug').textContent=document.getElementById('dbg').checked?JSON.stringify(j.retrieval_debug,null,2):'—';
};
document.getElementById('search').onclick=async()=>{
 const q=document.getElementById('q').value, svc=document.getElementById('service').value||null;
 const j=await post('/v1/search',{question:q,service:svc,top_k:5});
 document.getElementById('answer').textContent='(search only — no answer)';
 document.getElementById('sources').innerHTML=j.hits.map(h=>
`<div><a href="/v1/sources/${h.doc_id}">[${h.doc_id} §${h.section}]</a>`
+` score=${h.score.toFixed(4)} <small>${h.snippet.slice(0,120)}…</small></div>`).join('')||'—';
 document.getElementById('debug').textContent=JSON.stringify(j.retrieval_debug,null,2);
};
</script></body></html>"""
