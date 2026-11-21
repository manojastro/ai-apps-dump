# 07 — SQL for AI Engineers

**What this chapter is for:** so you survive the coding round that is *not* LeetCode and *not* a DBA exam. You join `traces` to `eval_cases`, filter chunks by tenant, read `EXPLAIN`, and write a `ROW_NUMBER()` without melting the table.

**Roles that score this as core:** FDE / FDAIE, AIOps, Intelligent Automation (telemetry SQL). Skill-matrix 4s live here.

**Roles that still get asked:** GenAI and Agentic (metadata stores, eval warehouses, pgvector), Solutions Engineer, Solutions Architect, Cloud AI. AI Security probes RLS / tenant filters as a follow-up, not a 45-minute SQL drill.

PostgreSQL appears in **9.3%** of the ~889 January 2026 AI Engineer JDs — under-mentioned relative to how often FDE and applied coding rounds put a schema on the whiteboard. RAG is in **35.9%** of those JDs; the retrieval path still needs a relational source of truth for ACLs, documents, and evals.

If you prepared only window-function trivia on `employees.salary`, this chapter is the correction.

This is **SQL for AI engineers, not DBAs.** They will not hire you to recite autovacuum. They will fail you for a cartesian join, a missing `tenant_id`, or `OFFSET 500000` on traces. Dialect in this book: **Postgres.**

---

## Interviewer intent

| Signal | Pass | Fail |
| --- | --- | --- |
| Correct result shape | JOIN/ON, GROUP BY, window, LIMIT | Cartesian product; `SELECT *` |
| Tenant instinct | `tenant_id` in every query; RLS as defense in depth | “The app will filter after fetch” |
| Cost of the plan | Index, `EXPLAIN`, keyset pagination | Offset-deep pages; function on column |
| AI-shaped schema | chunks, traces, evals, cost, events | HR salary puzzles as the only fluency |
| NULLs / duplicates | `COUNT(*)` vs `COUNT(col)`; upsert keys | Silent double ingest |
| When *not* SQL | Point lookup vs RAG vs warehouse | “I’d have the LLM write the SQL and run it” |

**Highest-signal question:** *Show me the query that retrieves chunks for this user — including the ACL.*

---

## Probability ranking (applied AI loops, 2026)

| Rank | Topic | Likelihood | Depth they want |
| --- | --- | --- | --- |
| 1 | JOIN + GROUP BY / HAVING on traces, evals, tickets | Almost certain in FDE / AIOps coding | Working SQL |
| 2 | `tenant_id` / ACL filters in the query | Very high in enterprise | Filter *in* SQL, not after |
| 3 | Window functions (last row, top-N per group) | Very high | One CTE you can type |
| 4 | Indexes + reading `EXPLAIN` | High | Seq scan vs index; composite key |
| 5 | JSONB metadata / `@>` / GIN | High for GenAI | Filters, not jsonb_each essays |
| 6 | pgvector SQL (`<=>`, HNSW, LIMIT, filter) | High if Postgres/RAG JD | Query + filtered ANN |
| 7 | `ON CONFLICT` upserts / idempotent ingest | High | Chunk rebuild, tool outbox |
| 8 | Eval / cost analytics | High for GenAI / FDE | `$ / successful task` |
| 9 | Pagination (keyset vs OFFSET) | Medium–high | Traces, chat history |
| 10 | Transactions / isolation | Medium–high senior | No LLM call inside a txn |
| 11 | AIOps event windows / anti-joins | Core for AIOps | Time range + suppress |
| 12 | Recursive CTEs | Low unless messy-data FDE | Don’t lead with them |

---

## How to study this chapter

Cover the answer. Speak 30 seconds. Then 2 minutes. Then the senior cut. Write a 6-part card: concept, logic, structure, keywords, example, trade-off.

When they hand you a schema: restate **grain** (“one row per chunk, not per doc”), name join keys, write `WHERE tenant_id` first, then the SELECT list. Narrate NULLs and duplicates while you type.

---

## The one diagram you should be able to draw

```
ingest  docs ──► chunks (tenant_id, doc_id, ix, text, embedding, metadata JSONB, acl)
                 UPSERT (tenant_id, doc_id, ix)
                 HNSW(embedding); B-tree(tenant_id, created_at); GIN(metadata)

query   identity ──► SET LOCAL app.tenant_id
                 ──► WHERE tenant_id AND acl && :roles   ← in SQL, not after ANN
                 ──► ORDER BY embedding <=> :q  LIMIT k

ops     traces / eval_cases ──► GROUP BY slice, $/success
        events (AIOps)      ──► time bucket + anti-join suppressions
```

ACL source of truth is relational. The vector index is derived (Chapter 14). Mixing those up is how tenants leak.

**Default grain:** `tenants` → `users` → `documents` → `chunks` → `queries` / `traces` → `eval_cases` / `eval_runs`. AIOps adds `events` (fingerprint, service, ts). Always filter `tenant_id` first. Do not put secrets in `metadata` that retrieval will stuff into a prompt.

---

## Q1. SELECT, JOIN, GROUP BY, HAVING — evals and traces

**Why they ask.** Wrong join grain silently multiplies token cost. WHERE vs HAVING is a 30-second competence check. This is the FDE filter.

**What they expect.** INNER vs LEFT vs anti-join, ON vs WHERE, WHERE before aggregation / HAVING after, `COUNT(*)` vs `COUNT(col)`, an eval-shaped query.

**Answer structure keywords.** grain · INNER/LEFT/anti-join · WHERE vs HAVING · COUNT NULLs · no cartesian.

**30-second.** Pick the join from the *result grain*. INNER when you only want matches. LEFT when you must keep the left side (queries with zero retrievals). Anti-join (`NOT EXISTS`) for “alerts with no ack.” `WHERE` filters rows; `HAVING` filters groups. `COUNT(col)` skips NULLs; `COUNT(*)` does not.

**2-minute.**

```sql
SELECT e.slice, COUNT(*) AS n, AVG(e.faithfulness) AS faithfulness
FROM eval_cases e
JOIN traces t ON t.trace_id = e.trace_id
WHERE e.run_id = :run AND t.tenant_id = :tenant
GROUP BY e.slice
HAVING COUNT(*) >= 20;
```

`HAVING COUNT(*) >= 20` drops noisy tiny slices. `run_id` belongs in WHERE — it is not an aggregate. Joining `chunks` (many) onto traces without aggregating first explodes rows and `SUM(tokens)` lies. `NOT IN` with a NULL in the list returns unknown and drops everything; prefer `NOT EXISTS`. `NULL = NULL` is unknown; use `IS NULL`.

**Senior / deep.** Name **fan-out**: one trace has N tool spans. Aggregate the many-side first, then join 1:1. `FILTER (WHERE …)` beats `SUM(CASE WHEN …)`. Warehouse engines have `QUALIFY`; in Postgres wrap a window in a CTE (Q2). Gold-set recall: LEFT JOIN from questions to retrieved chunks so misses stay visible.

**Weak answer.** “GROUP BY is when you want totals. I always INNER JOIN.”

**Mistakes.**

- Joining at the wrong grain, then DISTINCT to “fix” it.
- `AVG(faithfulness) > 0.9` in WHERE.
- `COUNT(error_message)` as “number of traces.”

**Follow-ups + strong replies.**

- *INNER or LEFT for retrieval evals?* LEFT from gold questions so `chunk_id IS NULL` is a recall miss.
- *Join usage to traces?* On `trace_id`. If usage is per-span, sum in a CTE first.

**Example.** Typical RAG eval warehouse: 120 gold questions. A JOIN to `chunks` duplicated easy hits and reported faithfulness 0.97. Aggregating retrieval hits first fixed the grain.

---

## Q2. Window functions — last event, top-N per group, running cost

**Why they ask.** `ROW_NUMBER()` is how you get “latest trace per session” and “top 3 chunks per doc” without collapsing with GROUP BY.

**What they expect.** `PARTITION BY` + `ORDER BY` + filter on `rn`. `ROW_NUMBER` vs `RANK`, `LAG`, running `SUM`. Postgres `DISTINCT ON` as a last-row idiom.

**Answer structure keywords.** PARTITION BY · ORDER BY · ROW_NUMBER vs RANK · running SUM · LAG · CTE then filter.

**30-second.** A window computes per row using peers. `ROW_NUMBER() OVER (PARTITION BY doc_id ORDER BY score DESC)` then `WHERE rn <= 3` is top-N. `LAG(ts)` is time since last event. Running cost is `SUM(cost_usd) OVER (PARTITION BY tenant_id ORDER BY created_at)`. Windows do not collapse rows; GROUP BY does.

**2-minute.**

```sql
WITH ranked AS (
  SELECT c.*,
         ROW_NUMBER() OVER (
           PARTITION BY c.doc_id ORDER BY c.score DESC, c.chunk_ix
         ) AS rn
  FROM chunks c
  WHERE c.tenant_id = :tenant
)
SELECT chunk_id, doc_id, text, score FROM ranked WHERE rn <= 3;
```

`RANK` ties share a rank and can return 4 rows for “top 3.” Use `ROW_NUMBER` plus a tie-break for a hard cap. `DISTINCT ON (session_id) … ORDER BY session_id, ts DESC` is the Postgres last-row form; the window ports to other engines. Filter `rn` in an outer query — you cannot reference it in the same SELECT’s WHERE.

**Senior / deep.** Frames: default running `SUM` is `RANGE UNBOUNDED PRECEDING`; sliding is `ROWS BETWEEN 5 PRECEDING AND CURRENT ROW`. Do not window-sort 50M traces on the serving instance — warehouse or pre-aggregate. Index `(tenant_id, created_at DESC)` plus LATERAL last-N (Q10). `percentile_disc(0.95) WITHIN GROUP (ORDER BY latency_ms)` is p95; do not fake it with AVG.

**Weak answer.** “I’d GROUP BY and take MAX.” That loses the row you needed.

**Mistakes.**

- `ROW_NUMBER` without ORDER BY (undefined).
- Using `RANK` when the SLO is “exactly k.”
- Window over the whole table with no tenant partition.

**Follow-ups + strong replies.**

- *Top-N at 10M rows?* LATERAL from a driver table, or persist rank on ingest.
- *Dedup chunk ids keeping first order?* `ROW_NUMBER() PARTITION BY chunk_id ORDER BY ordinal` then `rn = 1`.

**Example.** Chat session store: latest user message plus a running token total. Window CTE, not a Python loop over `fetchall()`.

---

## Q3. Indexes and EXPLAIN — slow RAG metadata query

**Why they ask.** Production instinct. They want a procedure, not “add an index.”

**What they expect.** B-tree vs GIN vs HNSW, leftmost prefix, functions on columns defeat indexes, Seq Scan vs Index Scan, `LIMIT` as part of the plan.

**Answer structure keywords.** EXPLAIN ANALYZE · seq vs index · composite (tenant_id, created_at) · leftmost prefix · GIN JSONB · HNSW.

**30-second.** `EXPLAIN (ANALYZE, BUFFERS)` on the slow SQL. Seq Scan on large `chunks` usually means a missing `(tenant_id, …)` predicate or an index the planner cannot use. B-tree for equality/range on leading columns. GIN for JSONB / arrays. HNSW for embeddings. Do not wrap the column in `lower()` without an expression index.

**2-minute.** Serving indexes: UNIQUE B-tree `(tenant_id, doc_id, chunk_ix)` for upserts; B-tree `(tenant_id, created_at DESC)` for pagination; GIN on `metadata` / `acl`; HNSW on `embedding vector_cosine_ops`. Read **rows estimated vs actual**, **Seq Scan** on millions, **Sort** spills, **Nested Loop** explosions. Composite B-tree is leftmost prefix: `(tenant_id, created_at)` helps `WHERE tenant_id =` and the pair; it does not help `WHERE created_at >` alone. `SELECT *` that pulls 1536-d vectors for a count query is an app bug.

**Senior / deep.** Selectivity first: `status` with 3 values is often useless; `tenant_id` is useful. Partial indexes (`WHERE deleted_at IS NULL`) match live retrieve. For pgvector, a highly selective filter can collapse HNSW recall — overfetch or partition by tenant (Q5). `pg_stat_statements` over guesswork. Do not create 12 indexes “just in case”; ingest pays.

**Weak answer.** “I’d add more indexes until it’s fast.”

**Mistakes.**

- B-tree on `vector`.
- Leading-wildcard `LIKE '%policy%'` expecting a B-tree win.
- Trusting `EXPLAIN` without `ANALYZE` on prod-like cardinality.

**Follow-ups + strong replies.**

- *Why fast in staging?* 10k rows hide seq scans. Ask cardinality.
- *ORM generated this.* Log SQL. If it wraps columns or drops tenant, rewrite.

**Example.** Retrieve p95 jumped after `WHERE metadata->>'department' = 'legal'`. No GIN, planner seq-scanned. Fix: GIN, or promote `department` to a column.

---

## Q4. JSON / JSONB — traces, tool args, metadata

**Why they ask.** 2026 AI schemas are half-relational, half-JSON. They want operators, indexes, and a reason you did *not* put everything in JSONB.

**What they expect.** `jsonb` over `json`, `@>`, `->` vs `->>`, GIN, generated columns for hot keys, size caps on tool payloads.

**Answer structure keywords.** jsonb · @> · -> vs ->> · GIN · generated column · size cap · schema at boundary.

**30-second.** `jsonb` is parsed, binary, indexable. Store *variable* payloads there: tool args, provider blobs, metadata you are not ready to columnize. Query with `metadata @> '{"source":"policy"}'` so GIN works. `->` returns JSON; `->>` returns text. Hot filters (`tenant_id`, `source`) become real columns.

**2-minute.**

```sql
SELECT trace_id, payload #>> '{usage,prompt_tokens}'
FROM traces
WHERE tenant_id = :tenant
  AND payload @> '{"model":"gpt-x"}'
  AND created_at >= :start;
```

Validate JSON on ingest (Pydantic). Traces are **append-only**. GIN `jsonb_path_ops` is smaller and supports `@>`. ACL is cleaner as `text[]` with `acl && :roles` than as nested JSON. Do not store embeddings as JSON number arrays.

**Senior / deep.** JSONB on the retrieve hot path is a latency tax. Promote keys in every `WHERE` to columns or generated stored columns plus a B-tree. Cap tool-result size before insert (injection + TOAST bloat). Dual write: columns for invariants, JSONB for the rest. Snapshot a schema version on the row.

**Weak answer.** “Postgres can be Mongo if we use JSONB for everything.”

**Mistakes.**

- `json` type (no GIN).
- `WHERE payload::text LIKE '%legal%'`.
- API keys inside `payload`.

**Follow-ups + strong replies.**

- *Tags contain `hr`?* `metadata @> '{"tags":["hr"]}'` or `metadata -> 'tags' ? 'hr'`. Index it.
- *Why not a document DB?* We join ACL, transactions, and pgvector. JSONB is a column, not the architecture.

**Example.** Trace table: real columns for `tenant_id`, `model`, `latency_ms`, `cost_usd`; JSONB for provider-specific usage and redacted tool I/O. Dashboards never `jsonb_each` the whole table.

---

## Q5. pgvector at the SQL level

**Why they ask.** Can you write the retrieve query, pin a metric, and not treat `ORDER BY embedding <=> q` as magic.

**What they expect.** Distance operators, `LIMIT`, same-model contract, tenant/ACL in the `WHERE`, HNSW, honesty about filtered ANN.

**Answer structure keywords.** <=> cosine · <-> L2 · <#> IP · same model · LIMIT · HNSW · filter-in-query · overfetch.

**30-second.** pgvector stores `vector(n)` and searches with a distance operator. Cosine distance is `<=>` (usually on L2-normalized vectors). `ORDER BY embedding <=> :q LIMIT k` **and** `WHERE tenant_id = :t` in the same statement. Add `USING hnsw (embedding vector_cosine_ops)` once brute-force p95 dies. Exact search is fine for small tenants.

**2-minute.**

```sql
SELECT chunk_id, doc_id, text, 1 - (embedding <=> :q) AS cosine_sim
FROM chunks
WHERE tenant_id = :tenant
  AND deleted_at IS NULL
  AND metadata @> :filters
  AND acl && :roles
ORDER BY embedding <=> :q
LIMIT 20;
```

`:q` comes from the **same** embedding model as ingest. Mixing models is undefined. `SET hnsw.ef_search = 40` trades latency for recall. Hybrid still wins on IDs/SKUs: BM25/`tsvector` plus dense, then RRF (Chapters 10 and 14).

**Senior / deep.** **Filtered ANN** is the interview. A global HNSW plus a selective `tenant_id` may over-retrieve then discard — or return too few valid neighbors. Mitigate: partition by tenant, iterative scans, overfetch `LIMIT k*10` then filter, exact kNN for tiny tenants. **Never** fetch top-200 globally and drop other tenants in Python — ACL leak and billing leak. Re-embed on model change; the old index is a different space.

**Weak answer.** “I’d SELECT all embeddings and cosine in numpy.”

**Mistakes.**

- No `LIMIT`. Filter after fetch in the app.
- B-tree on `vector`. Index `vector_l2_ops` with `<=>` queries.

**Follow-ups + strong replies.**

- *IVFFlat vs HNSW?* HNSW default at moderate scale; IVFFlat lower memory, needs lists training. Measure recall@k.
- *When leave Postgres?* RAM, QPS, or hybrid features. ACL can stay here.

**Example.** Typical internal RAG: ~2M chunks in Postgres+pgvector, cosine HNSW, `WHERE tenant_id` + GIN metadata. Gold-set recall@20 is the gate, not blog QPS.

---

## Q6. Transactions, isolation, idempotent upserts

**Why they ask.** Ingest, alias swaps, and tool writes are concurrency problems. Retrying an agent without upserts double-inserts chunks and double-charges.

**What they expect.** Short transactions, Read Committed default, `ON CONFLICT`, **no LLM I/O inside a txn**.

**Answer structure keywords.** ACID · read committed · ON CONFLICT · outbox · don’t txn the LLM · SET LOCAL.

**30-second.** Keep transactions **short**. Postgres default is Read Committed. Upsert chunks with `INSERT … ON CONFLICT (tenant_id, doc_id, chunk_ix) DO UPDATE`. Never hold a row lock while waiting on a model. Stronger isolation or a single-row CAS for money and index-pointer swaps.

**2-minute.**

```sql
INSERT INTO chunks (tenant_id, doc_id, chunk_ix, text, embedding, metadata)
VALUES (:t, :d, :i, :text, :emb, :meta)
ON CONFLICT (tenant_id, doc_id, chunk_ix)
DO UPDATE SET text = EXCLUDED.text,
              embedding = EXCLUDED.embedding,
              updated_at = now();
```

Re-chunk a doc in **one** transaction so retrieve never sees a hole *and* duplicates. Swap `corpus_alias` with one UPDATE of a tiny pointer table. `SELECT … FOR UPDATE` when two workers claim the same outbox row.

**Senior / deep.** At-least-once workers + unique constraints = exactly-once *effect*. Outbox: insert `tool_intent(idempotency_key)` first, commit, call the API, store the remote id. Serializable is for low-contention money, not 100k-chunk ingest (you will retry aborts). `SET LOCAL statement_timeout` and `SET LOCAL app.tenant_id` so pooled connections do not leak (Q8). Analytics snapshots belong on a replica or warehouse.

**Weak answer.** “I wrap the whole request, including OpenAI, in a transaction so it’s safe.”

**Mistakes.**

- No unique key, so retries duplicate chunks.
- `ON CONFLICT DO NOTHING` when embeddings needed a refresh.
- Using `timestamp` as a unique key.

**Follow-ups + strong replies.**

- *Two ingest workers, same doc?* Unique constraint; advisory lock if delete+insert must be exclusive.
- *Read-your-writes?* On the primary. Replicas lag; retrieve from primary or wait LSN after ingest.

**Example.** Typical ingest: embed batch → upsert 64 rows → commit. Crash retries the batch; `ON CONFLICT` makes it safe. The LLM that wrote a summary is outside the txn.

---

## Q7. Pagination — traces, chunks, eval sets, chat

**Why they ask.** OFFSET is the junior default and falls over. Chat and traces are infinite scrolls.

**What they expect.** Keyset/cursor pagination, stable ORDER BY including unique id, why OFFSET scans and discards.

**Answer structure keywords.** keyset · (created_at, id) · no deep OFFSET · stable sort · opaque cursor.

**30-second.** Do not `OFFSET 100000 LIMIT 50` on traces. Seek: `WHERE (created_at, id) < (:ts, :id) ORDER BY created_at DESC, id DESC LIMIT 50`. The cursor is those two values. OFFSET throws away skipped rows and drifts when inserts land.

**2-minute.** Chat history: `WHERE session_id = :s AND seq < :cursor ORDER BY seq DESC LIMIT 50`. Frozen eval sets for annotators: paginate a monotonic `case_ix` on a snapshot `run_id`, not live `ORDER BY random()`. `LIMIT/OFFSET` is fine for page 1–3 of 40 gold questions. Do not `COUNT(*)` every page on a huge table.

**Senior / deep.** ORDER BY must be **unique** (`created_at, id`) or pages skip/duplicate. Include `tenant_id` equality so the index applies. HTTP returns `next_cursor`, not page numbers (Chapter 08). `ORDER BY embedding <=> q` does not keyset — cap k; do not page ANN to 10,000.

**Weak answer.** `page * page_size` OFFSET.

**Mistakes.**

- Non-unique ORDER BY.
- Changing sort between pages.
- Returning embeddings on a list endpoint.

**Follow-ups + strong replies.**

- *PM wants page numbers?* Snapshot `case_ix` 1..N on the frozen run.
- *Deletes mid-page?* Keyset may skip a deleted row. That is acceptable; OFFSET duplicates too.

**Example.** On-call trace viewer: latest 50, then `(created_at, id)` cursors. OFFSET was already seconds at page 20.

---

## Q8. Multi-tenant RLS and RAG metadata filters

**Why they ask.** Multi-tenant retrieval is a **critical** 2026 topic (Chapter 04). SQL is where the leak is prevented or caused.

**What they expect.** `tenant_id` in the query, RLS as defense in depth, ACL *inside* retrieve, identity from the request not the model, no post-filter-only story.

**Answer structure keywords.** tenant_id · RLS USING · SET LOCAL · acl overlap · filter-in-query · connection pool leak.

**30-second.** Every retrieve includes `tenant_id = :tenant` from the authenticated principal, plus an ACL predicate. RLS enforces the same if a bug drops the WHERE. `SET LOCAL app.tenant_id` in a transaction on a pooled connection. Never ask the model which tenant it is. Never take top-k globally and drop other tenants in Python.

**2-minute.**

```sql
ALTER TABLE chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE chunks FORCE ROW LEVEL SECURITY;
CREATE POLICY tenant_iso ON chunks
  USING (tenant_id = current_setting('app.tenant_id')::uuid);

SELECT chunk_id, text, doc_id FROM chunks
WHERE metadata @> :filters
  AND (acl && :roles OR owner_id = :user)
ORDER BY embedding <=> :q
LIMIT 20;
```

`FORCE` so a table-owner app role cannot bypass. Metadata filters are **in addition to** tenancy. Shared libraries get an explicit share table, not `tenant_id IS NULL` unless that is a locked design.

**Senior / deep.** **Pooling is the RLS footgun.** `SET` without `LOCAL` leaks to the next checkout. Defense in depth: JWT → tenant, bind param, RLS. **Confused deputy:** an agent tool querying as a superuser. Pass the request identity (Chapters 11, 19). Canary document in tenant B must never appear in tenant A’s traces, including ANN overfetch.

**Weak answer.** “We’ll put tenant_id in metadata and filter in LangChain.”

**Mistakes.**

- RLS without `FORCE` on a table-owner role.
- ACL only in the prompt.
- Shared HNSW with post-filter as the only control.

**Follow-ups + strong replies.**

- *50k tenants?* RLS + leading `tenant_id` index, or partition noisy tenants. Not one-schema-per-tenant unless compliance demands it.
- *Canary doc?* Ingest `TENANT_B_SECRET` into B; nightly query as A; any hit is Sev-1.

**Example.** Typical B2B copilot: one `chunks` table, RLS, groups mapped to `acl`. Prompt injection “ignore ACLs” does nothing at SQL.

---

## Q9. Analytics SQL for evals and cost

**Why they ask.** Evaluation is the 2026 differentiator. They want `$ / successful task` and slices, not a vibe dashboard.

**What they expect.** Join evals to traces, `FILTER`, percentiles, group by prompt/model/index version, frozen `run_id`.

**Answer structure keywords.** frozen run_id · slice · faithfulness · $/success · percentile · versions pinned.

**30-second.** An eval is a batch with frozen `run_id` and pinned `prompt_version`, `model_id`, `index_version`. Roll up quality **and** cost: success rate, faithfulness, p95, `SUM(cost) FILTER (WHERE success) / n_success`. Slice by intent and doc type. Do not average a live production table and call it a ship bar.

**2-minute.**

```sql
SELECT e.slice,
       COUNT(*) AS n,
       AVG(e.faithfulness) AS faithfulness,
       COUNT(*) FILTER (WHERE e.task_success)::float / COUNT(*) AS success,
       percentile_disc(0.95) WITHIN GROUP (ORDER BY t.latency_ms) AS p95_ms,
       SUM(t.cost_usd) FILTER (WHERE e.task_success)
         / NULLIF(COUNT(*) FILTER (WHERE e.task_success), 0) AS usd_per_success
FROM eval_cases e
JOIN traces t ON t.trace_id = e.trace_id
WHERE e.run_id = :run
GROUP BY e.slice
HAVING COUNT(*) >= 20;
```

Cost without success in the denominator is how a cheaper, dumber prompt “wins.” Also track `empty_retrieval_rate` and `refuse_rate`.

**Senior / deep.** Credit assignment: join span-level errors so a drop after a retriever change attributes to retrieve (Chapter 17). Snapshot `usd_rate` on the trace or you cannot reconstruct bills. Agents: same `$/success`, plus `steps` and `cap_hit_rate` (Chapter 11). Regression: pair `case_id` against `baseline_run_id`. No PII as a GROUP BY key.

**Weak answer.** “Average tokens.” Or a live table dump to a spreadsheet.

**Mistakes.**

- Live table as the eval (data moves under you).
- No slice — FAQ wins hide policy losses.
- Joining at span grain and multiplying cost.

**Follow-ups + strong replies.**

- *LLM-as-judge in SQL?* Store the numeric grade. Do not recompute here.
- *Tiny n?* `HAVING COUNT(*) >= 20`. Do not fake significance.

**Example.** Typical GenAI loop: 80 gold questions, four slices. A prompt change dropped `$/success` and faithfulness 0.02 on FAQ but 0.11 on policies. The slice table stopped the ship.

---

## Q10. AIOps event tables — windows, correlation, suppressions

**Why they ask.** AIOps / Intelligent Automation loops are SQL-ish telemetry, not RAG theater. They want a time window and an anti-join, not “I’d embed the logs.”

**What they expect.** Time-range predicates, fingerprints, LATERAL last-N, anti-join to acks/suppressions, LLM *after* this reduce.

**Answer structure keywords.** time range · fingerprint · LATERAL last-N · anti-join · bucket · LLM after SQL.

**30-second.** Events are rows: `ts`, `service`, `severity`, `fingerprint`, `host`. Filter time first, collapse by fingerprint, anti-join suppressions and acks, then feed a **small** packet to a model if you even need one. Correlation is a join on `deployment_id` / `trace_id` / time bucket, not cosine on log lines as the default.

**2-minute.**

```sql
SELECT a.alert_id, a.service, a.fingerprint, a.fired_at
FROM alerts a
WHERE a.fired_at > now() - INTERVAL '1 hour'
  AND a.severity >= 2
  AND NOT EXISTS (
    SELECT 1 FROM suppressions s
    WHERE s.fingerprint = a.fingerprint
      AND a.fired_at BETWEEN s.starts_at AND s.ends_at
  );

SELECT h.host, m.ts, m.cpu
FROM hosts h
CROSS JOIN LATERAL (
  SELECT ts, cpu FROM metrics
  WHERE host = h.host AND ts > now() - INTERVAL '30 minutes'
  ORDER BY ts DESC LIMIT 5
) m;
```

Index `(fingerprint, fired_at)` and `(host, ts DESC)`. Bucket with `date_bin`.

**Senior / deep.** The copilot fails when you dump 10k raw lines into context. SQL is the **reduce** step: top fingerprints, deploys in `[t-30m, t]`, prior incidents with the same fingerprint. Gated automation (Chapter 18) uses a write tool with HITL; this SQL stays read-only. `GROUP BY raw_message` explodes; `GROUP BY fingerprint` does not. Hot metrics may live in a TSDB; Postgres holds tickets/incidents.

**Weak answer.** “I’d put all logs in a vector DB and RAG the incident.”

**Mistakes.**

- No time filter. CROSS JOIN on timestamp equality (never equal).
- Feeding unreduced logs to the model.

**Follow-ups + strong replies.**

- *Join deploys?* `service` match and `deploy.ts BETWEEN alert.ts - 30m AND alert.ts`. Cap the window.
- *10k duplicate pages?* Collapse fingerprint; `COUNT(*)` per fingerprint.

**Example.** Typical AIOps copilot: SQL builds a 20-row packet (alert, last deploys, last 5 samples, open ticket). The model drafts an RCA comment. It does not `kubectl delete` from a query.

---

## Weak vs strong posture

| Weak | Strong |
| --- | --- |
| `SELECT * FROM chunks` then cosine in app | `WHERE tenant_id AND acl && roles ORDER BY embedding <=> :q LIMIT k` |
| OFFSET pagination | Keyset on `(created_at, id)` |
| “The ORM handles it” | Logged SQL, `EXPLAIN ANALYZE`, grain stated |
| JSONB for `tenant_id` | Real column + RLS + bind param |
| Average tokens as the eval | Frozen `run_id`, slices, `$/success` |
| Embed all the logs | Time-window SQL reduce, then maybe an LLM |
| LLM-generated SQL on `chunks` | Don’t. Read-only view + RLS + timeout if analysts insist |

---

# Exercises

Narrate grain → tenant filter → SELECT. Do not invent 200 rows of data.

---

## Exercise 1 — Top-N chunks per document

| | |
| --- | --- |
| **Difficulty** | Easy–medium |
| **Expected time** | 10–15 min |
| **Concept tested** | Windows, tenant filter, ties |

**Problem.**
`chunks(chunk_id, tenant_id, doc_id, chunk_ix, text, score)`. Return at most **3** chunks per `doc_id` for one tenant, highest score first. Tie-break `chunk_ix` ascending. Exclude `score IS NULL`.

**Hints.** `ROW_NUMBER()` in a CTE; `WHERE tenant_id = :t` **before** the window; `RANK()` can return more than 3 on ties.

**Solution.**

```sql
WITH ranked AS (
  SELECT chunk_id, doc_id, chunk_ix, text, score,
         ROW_NUMBER() OVER (
           PARTITION BY doc_id ORDER BY score DESC, chunk_ix ASC
         ) AS rn
  FROM chunks
  WHERE tenant_id = :tenant_id AND score IS NOT NULL
)
SELECT chunk_id, doc_id, chunk_ix, text, score
FROM ranked
WHERE rn <= 3
ORDER BY doc_id, rn;
```

**Interviewer follow-ups.** Join `documents` for title (same `tenant_id`). At 10M rows: LATERAL from a driver table or persist rank on ingest.

---

## Exercise 2 — Eval slice dashboard with `$/success`

| | |
| --- | --- |
| **Difficulty** | Medium |
| **Expected time** | 12–18 min |
| **Concept tested** | JOIN grain, HAVING, FILTER, cost per success |

**Problem.**
`eval_cases(run_id, case_id, slice, task_success, faithfulness, trace_id)` and `traces(trace_id, tenant_id, latency_ms, cost_usd)`. For `:run_id`, one row per `slice`: `n`, `success_rate`, `avg_faithfulness`, `p95_latency_ms`, `usd_per_success`. Drop slices with `n < 20`. Do not double-count cost.

**Hints.** 1:1 on `trace_id`. Denominator for `$/success` is **successful** cases only. `percentile_disc(0.95) WITHIN GROUP (ORDER BY latency_ms)`.

**Solution.**

```sql
SELECT e.slice,
       COUNT(*) AS n,
       AVG(e.faithfulness) AS avg_faithfulness,
       COUNT(*) FILTER (WHERE e.task_success)::float / COUNT(*) AS success_rate,
       percentile_disc(0.95) WITHIN GROUP (ORDER BY t.latency_ms) AS p95_latency_ms,
       SUM(t.cost_usd) FILTER (WHERE e.task_success)
         / NULLIF(COUNT(*) FILTER (WHERE e.task_success), 0) AS usd_per_success
FROM eval_cases e
JOIN traces t ON t.trace_id = e.trace_id
WHERE e.run_id = :run_id
GROUP BY e.slice
HAVING COUNT(*) >= 20
ORDER BY usd_per_success NULLS LAST;
```

**Interviewer follow-ups.** LEFT JOIN if traces can be missing. Pair `case_id` to a baseline `run_id` for regressions. Say why `HAVING 20`.

---

## Exercise 3 — Tenant-safe pgvector retrieve

| | |
| --- | --- |
| **Difficulty** | Medium |
| **Expected time** | 10–15 min |
| **Concept tested** | pgvector SQL, metadata, ACL in-query |

**Problem.**
`chunks(chunk_id, tenant_id, doc_id, text, embedding vector(1536), metadata jsonb, acl text[], deleted_at)`. Retrieve by cosine to `:query_embedding`, tenant `:tenant_id`, metadata contains `"source": "policy"`, ACL overlaps `:roles`, not deleted. 20 rows with similarity. Do **not** post-filter in the app.

**Hints.** `<=>` + `ORDER BY` + `LIMIT 20`. `metadata @> '{"source":"policy"}'::jsonb`. `acl && :roles`. Similarity: `1 - (embedding <=> :q)` if cosine-normalized.

**Solution.**

```sql
SELECT chunk_id, doc_id, text,
       1 - (embedding <=> :query_embedding) AS cosine_sim
FROM chunks
WHERE tenant_id = :tenant_id
  AND deleted_at IS NULL
  AND metadata @> '{"source": "policy"}'::jsonb
  AND acl && :roles::text[]
ORDER BY embedding <=> :query_embedding
LIMIT 20;
```

Keep `tenant_id` in the query even if RLS `SET LOCAL app.tenant_id` is on.

**Interviewer follow-ups.** Index: `USING hnsw (embedding vector_cosine_ops)` plus B-tree `(tenant_id)` and GIN on `metadata`/`acl`. If filters kill recall: overfetch, partition by tenant, or exact search — do not drop the filter. Hybrid: mention a `tsvector` CTE + RRF; don’t implement unless asked.

---

## Map to the rest of the handbook

- Filtered ANN, pgvector vs dedicated engines: [14-vector-databases.md](14-vector-databases.md)
- ACL in retrieve, not after: Chapter 10 RAG
- `$/success`, frozen runs: [17-llmops.md](17-llmops.md)
- Agent tools that are *not* raw SQL: [11-agentic-ai.md](11-agentic-ai.md)
- HTTP cursors for these queries: [08-apis.md](08-apis.md)

Next drill: type Exercise 1 and 3 while saying the tenant filter out loud. Speak Q5, Q8, Q9. Add Q10 if the title is AIOps.
