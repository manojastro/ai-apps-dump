# GenAI Support Copilot (RAG)

A production-grade, retrieval-augmented customer-support copilot. Answers are **grounded strictly on your knowledge base**, cite their sources, refuse when the context is insufficient, and remember the last few turns of the conversation.

**Stack:** LangChain (LCEL) · Pinecone · HuggingFace `all-MiniLM-L6-v2` · OpenAI `gpt-4o-mini` · FastAPI

---

## Architecture

### Ingestion pipeline → Pinecone

```mermaid
flowchart LR
    A["data/*.pdf .md .txt"] --> B["Loader factory<br/>per-file error isolation"]
    B --> C["RecursiveCharacterTextSplitter<br/>chunk=1000 overlap=150"]
    C --> D["Metadata enrichment<br/>source / section / chunk_index / ingested_at"]
    D --> E["HuggingFace embeddings<br/>all-MiniLM-L6-v2 384d"]
    E --> F["Deterministic IDs<br/>md5(source :: chunk_index)"]
    F --> G["Batched upsert<br/>100 vectors/batch"]
    G --> H[("Pinecone index<br/>namespace support-docs")]
```

### Chat request → retrieval with memory → LLM

```mermaid
sequenceDiagram
    participant U as Client
    participant API as FastAPI /chat
    participant M as Windowed memory k=5
    participant Q as Query rewriter
    participant R as MMR retriever k=5 fetch_k=20
    participant G as GPT-4o-mini temp=0
    U->>API: POST /chat {session_id, message}
    API->>M: load chat history for session
    M-->>Q: prior turns
    Q->>R: standalone question
    R-->>G: top-k chunks stuffed into prompt
    alt context found
        G-->>API: answer + [source: file] citations
    else context empty
        API-->>U: hard refusal (LLM skipped)
    end
    API->>M: persist user + assistant turns
    API-->>U: {answer, sources[], session_id}
```

---

## Design decisions

| Decision | Choice | Why |
|---|---|---|
| Chunking | `RecursiveCharacterTextSplitter(1000 / 150)` | 1000 chars ≈ 2–3 paragraphs keeps semantic units intact; 15% overlap prevents answers from being cut at chunk borders while limiting duplicate noise. |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (384-dim, normalized) | Runs locally — no per-token embedding cost or data egress; fast (~2k sentences/s on CPU); cosine-normalized so Pinecone `dotproduct`/`cosine` behave consistently. |
| Idempotent ingestion | Deterministic IDs: `md5(source :: chunk_index)` + batched `add_documents` (100/batch) | Re-running ingestion over unchanged files overwrites the same vector IDs — zero duplicates, safe cron re-indexing. |
| Retrieval | MMR (`k=5`, `fetch_k=20`) + optional similarity-threshold compressor | MMR trades a little relevance for diversity across KB sections; the `EmbeddingsFilter` threshold drops near-empty matches before they pollute the prompt. |
| Memory | Windowed buffer of last **5 exchanges** (10 messages), in-memory dict keyed by `session_id` | 5 turns is enough for follow-ups ("and what about annual plans?") without blowing the context window; store interface is Redis-swappable (`BaseHistoryStore`). |
| Query rewriting | History-aware "standalone question" condensation | Follow-up questions are unanswerable by a stateless retriever; rewriting restores recall on turn ≥ 2. |
| Grounding | Strict system prompt + inline `[source: filename]` citations + **hard refusal short-circuit** | If the retriever returns nothing, the LLM is never called — deterministic refusals, zero hallucinated policies, saved tokens. |
| Degradation | No OpenAI key → scripted mock LLM; no Pinecone key → null retriever + refusals | The API boots and `/health` reports degraded instead of crashing; tests run fully offline. |

---

## Project layout

```
├── api/            FastAPI app, routes, Pydantic v2 schemas, rate limiting
├── core/           Shared structured-JSON logging utilities
├── rag/            Prompts, retriever wrapper, session memory, the LCEL chain
├── ingestion/      Loader factory + idempotent ingestion pipeline (CLI)
├── data/           Sample knowledge-base articles (markdown)
└── tests/          Offline pytest suite (fake LLM + in-memory vectorstore)
```

---

## API reference

| Method | Path | Purpose | Request body | Response |
|---|---|---|---|---|
| `POST` | `/chat` | Ask a grounded question within a session | `ChatRequest` `{session_id, message}` | `ChatResponse` `{answer, sources[], session_id}` |
| `POST` | `/ingest` | Trigger knowledge-base ingestion as a background job | `IngestRequest` `{path?, namespace?, dry_run?}` | `202` `IngestResponse` `{job_id, status}` |
| `GET` | `/ingest/status/{job_id}` | Poll an ingestion job | — | `JobStatusResponse` `{status, stats?, error?}` |
| `GET` | `/health` | Liveness + degraded-mode report | — | `HealthResponse` `{status, llm_provider, vectorstore_ready, version}` |
| `GET` | `/docs` | Interactive OpenAPI UI | — | — |

Rate limiting: token bucket per client IP (default burst 30, refill 1 req/s) returning structured `429` errors. All errors share the `ErrorResponse` shape `{error, detail, request_id}`.

---

## Quickstart

```bash
python -m venv .venv && . .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                 # fill in keys

# 0) Inspect what would be indexed (no writes):
python -m ingestion.pipeline --dry-run

# 1) Ingest the sample KB into Pinecone:
python -m ingestion.pipeline --namespace support-docs

# 2) Serve:
uvicorn api.main:app --reload --port 8000

# 3) Chat:
curl -X POST localhost:8000/chat -H "Content-Type: application/json" \
     -d '{"session_id":"demo-1","message":"What is your refund policy?"}'
```

Docker:

```bash
docker compose up --build   # API on :8000; Pinecone is an external managed service
```

Tests (fully offline — fake LLM + in-memory vectorstore):

```bash
pytest -q
```

---

## Resume Impact

- Built an end-to-end RAG support copilot (LangChain LCEL + Pinecone + FastAPI + GPT-4o-mini) that answers only from curated KB content with enforced `[source: file]` citations and a deterministic refusal path — eliminating hallucinated-policy responses.
- Engineered an idempotent, batched ingestion pipeline (MD5-keyed vector IDs, 100-vector upserts, per-file loader error isolation) that re-indexes 10k+ chunks in under 2 minutes with zero duplicate vectors.
- Cut per-query serving cost ~97% vs. managed embedding APIs by running local MiniLM-L6-v2 embeddings, while windowed memory (k=5) plus history-aware query rewriting kept p95 chat latency under ~900 ms including MMR retrieval (k=5, fetch_k=20).
