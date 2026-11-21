# 06 — Python for AI Engineers

**What this chapter is for:** so you walk into a 2026 applied-AI coding round ready to parse JSON, retry a flaky LLM call, validate a payload, chunk documents, and write a test — not invert a binary tree.

Python appears in **82.5%** of 2026 AI Engineer JDs. The round is almost never competitive programming. Applied teams (and an increasing share of enterprise loops) hand you a broken client, a nested API payload, or a FastAPI stub and watch how you handle **timeouts, retries, types, and tests**.

If you prepared only LeetCode, this chapter is the correction.

---

## How the round actually runs

Typical 35–50 minutes:

1. **Warm-up (5 min)** — mutate a dict, explain a generator, spot a mutable default.
2. **Core task (25–35 min)** — one of: parse a provider response, implement backoff, write a chunker, stand up a POST endpoint, mock an LLM call.
3. **Follow-ups (5–10 min)** — “what if the file is 20 GB?”, “what if 200 tenants share this process?”, “how do you test this without spending money?”

What they score, in order:

| Signal | You show it by |
| --- | --- |
| Production instinct | Timeouts on every network call; no bare `except:` |
| Data hygiene | Defensive JSON access; explicit schema; no `obj["a"]["b"]["c"]` chains |
| Control of concurrency | Knowing when async helps and when it hides bugs |
| Testability | A mock, a fixture, an assertion on a failure path |
| Communication | Narrating trade-offs while typing, not after |

**MARKET OBSERVATION:** Frontier labs may still add an algorithms round. For GenAI / Agentic / FDE / Solutions loops, a candidate who writes a correct chunker with overlap and metadata beats a candidate who memorizes `lru_cache` trivia and cannot parse a tool-call payload.

---

## How to study a question in this chapter

Cover the answer. Speak 30 seconds. Then 2 minutes. Only then read the senior version. Write your own 6-part card: concept, logic, structure, keywords, example, trade-off.

Every major conceptual block below uses:

- **Why they ask** — the signal
- **30 seconds** — junior / screen bar
- **2 minutes** — mid-level bar
- **Senior** — what a staff/FDE answer adds
- **Weak answer** — the fail phrase
- **Follow-ups** — the real interview

---

# Part I — Language that shows up in AI work

## 1. Data types, mutability, and collections

You will not be asked to implement a hash map. You *will* be asked why a cached prompt template mutated, why a set of doc IDs is the right structure, and why a tuple is a valid dict key and a list is not.

### Q. Lists vs tuples vs dicts vs sets — when do you use each in an AI service?

**Why they ask.** They are checking whether you pick structures by *operation and invariant*, not by habit. RAG, evals, and tool loops are full of “membership, uniqueness, ordered window, lookup by id.”

**Keywords.** mutability, hashability, O(1) membership, insertion order (3.7+), JSON mapping, dataclass/Pydantic vs dict

**30 seconds.**
A **list** is an ordered, mutable sequence — chunk windows, message history, batch of texts. A **tuple** is ordered and immutable — a record you do not want accidentally mutated, a dict key, a function return of fixed fields. A **dict** is a keyed map — metadata, JSON objects, tool-call arguments. A **set** is unique, unordered membership — “have we seen this chunk_id / tool_call_id?” Lists and dicts are JSON-native; sets and tuples are not, so you convert at the boundary.

**2 minutes.**
In a retrieval service I keep:

- `messages: list[dict]` because order is the conversation
- `seen_doc_ids: set[str]` because I dedupe retrieved chunks
- `chunk_by_id: dict[str, Chunk]` because I join scores back to text
- `span: tuple[int, int]` as `(start, end)` offsets because I do not want a caller to append to it

Dicts preserve insertion order, which matters when I serialize a prompt or a JSON schema. Sets and tuples must be converted to lists before `json.dumps`. Tuple vs list is also a contract: if a function returns `(text, score, meta)` I am saying “three fields, not a growable sequence.”

Default args are evaluated once. `def add_msg(m, history=[])` shares one list across calls — a classic production bug in chat helpers. Use `None` and allocate inside.

**Senior.**
I treat Python collections as *in-process* structures and Pydantic models as *boundary* structures. Crossing an API, a queue, or a tool call, I want a schema, not a dict of dicts. I also distinguish:

- **Identity vs value:** two chunks with the same text are not the same chunk if `chunk_id` differs.
- **Cost of copying:** slicing a list copies references; for large embedding matrices I want NumPy views or memory-mapped files, not `list(embeddings)`.
- **Hashability as a feature:** frozen dataclass / `tuple` keys for a cache of `(model, prompt_hash, toolset_version)`.
- **When a deque wins:** sliding-window rate limiter, last-N conversation turns with `maxlen`.

I mention complexity only when it is the bottleneck: set/dict average O(1) lookup vs list O(n) “is this doc already in the context?” at 200 chunks.

**Weak answer.** “Lists are for arrays, dicts are for JSON, tuples are like lists but faster.” No mutability, no hashability, no AI-shaped example.

**Follow-ups.**

- *Why can’t a list be a dict key?* It is mutable, so its hash would be unstable. You would lose the entry after mutation.
- *Is a dict ordered?* Yes, insertion order since 3.7 (language guarantee). Do not rely on order if the payload came from a JSON object that another language serialized without order.
- *When is a set the wrong dedupe?* When you need first-seen order. Use a dict as an ordered set (`dict.fromkeys`) or explicitly track both.
- *What does `is` vs `==` do with interned small ints and None?* `None` checks should be `is None`. Do not use `is` for strings or numbers you care about by value.

### Q. What is the mutable default argument bug, and why does it show up in LLM helpers?

**Why they ask.** It is a 20-second filter for “has this person been burned in production.” Chat helpers, tool registries, and retry configs all use defaults.

**30 seconds.**
Default arguments are bound at **function definition time**, not call time. A mutable default (`[]`, `{}`) is one object shared across calls. Later calls see previous mutations. Fix: default to `None`, create a new list/dict inside.

**2 minutes.**
```python
def call_llm(prompt: str, history: list | None = None, extra_headers: dict | None = None):
    history = list(history) if history is not None else []
    headers = dict(extra_headers) if extra_headers is not None else {}
```
Copying on the way in also protects the caller from us appending a system message onto *their* list. That is the second half of the bug: even a correctly allocated default can mutate a caller-owned list if you append in place.

**Senior.**
I treat inputs as read-only unless the function is explicitly a mutating builder. For message lists I copy; for large arrays I document that I do not copy. In Pydantic I use `Field(default_factory=list)`, which is the equivalent fix at the model layer.

**Weak answer.** “Never use default arguments.”

**Follow-ups.** *Does `def f(x=datetime.now())` have the same class of bug?* Yes — the timestamp is frozen at import. Use `None` or a factory.

### Collections you should be fluent with

| Type | AI use | Trap |
| --- | --- | --- |
| `list` | chunks, batches, messages | accidental sharing, `list.remove` in a loop |
| `tuple` | spans, composite cache keys | single-element tuple is `(x,)`, not `(x)` |
| `dict` | JSON, metadata, tool args | `d[k]` vs `d.get`; nested mutation |
| `set` | dedupe ids, ACL role intersection | unhashable dicts inside |
| `deque` | rate-limit window, last-N turns | not JSON-serializable |
| `defaultdict` | grouping chunks by doc_id | silently creating keys on read |
| `Counter` | token/tool-call histograms | not a schema |
| `NamedTuple` / `dataclass` | in-process records | still not validation |
| `Pydantic BaseModel` | API and tool boundaries | do not use as a tightly looped inner type without measuring |

Comprehensions are expected: `[c.text for c in chunks if c.score >= t]`. Nested comprehensions that parse JSON are a readability fail — use a loop or a validator.

Unpacking shows up constantly: `role, content = message["role"], message["content"]`; `*parts, last = turns`; `**metadata` into a constructor. Teach yourself `zip(*matrix, strict=True)` for pairing embeddings with ids.

---

## 2. Functions, lambda, closures

### Q. How do you design functions around LLM and tool calls?

**Why they ask.** They want small, testable units with explicit side effects — not a 200-line `run()` that calls OpenAI, writes a file, and updates a DB.

**Keywords.** pure vs I/O, `*args/**kwargs`, keyword-only, closures, partial, first-class functions

**30 seconds.**
Keep I/O at the edges. A function that *builds* a prompt should not *send* it. Use keyword-only args for flags that are easy to swap (`*, temperature: float = 0`). Lambdas are for one-line sort keys, not business logic. Closures are how decorators and retry wrappers capture config.

**2 minutes.**
Signature I actually use:

```python
async def complete(
    client: LLMClient,
    messages: list[Message],
    *,
    model: str,
    temperature: float = 0,
    max_tokens: int = 1024,
    timeout_s: float = 30,
) -> Completion:
    ...
```

The client is injected, so tests pass a fake. Timeout is a first-class argument, not a global. I do not default `model` to whatever I used last week — that becomes a silent production change.

Lambda: `chunks.sort(key=lambda c: c.score, reverse=True)` is fine. A 15-line lambda that parses tool JSON is not — it is an untestable function without a name.

**Senior.**
I separate **policy** from **mechanism**. Retry, timeout, and logging are decorators or wrappers. The core function raises typed errors (`RateLimitError`, `TimeoutError`, `SchemaError`). Closures that bind loop variables need default args (`lambda c=c: ...`) or they all see the last value — a bug that shows up when you spawn tasks in a `for tool in tools` loop.

`functools.partial` is how I pre-bind a tenant’s model router without a new class. `*args, **kwargs` in a wrapper must be forwarded carefully: inspect or type the inner callable so you do not swallow a misspelled `temparature=`.

**Weak answer.** “I just write `def process(data):` and put everything in it.”

**Follow-ups.**

- *Why keyword-only?* Prevents `complete(client, msgs, "gpt-x", 0, 1024, 30)` from silently swapping timeout and max tokens.
- *Are nested functions OK?* Yes for one-off adapters; if it needs tests, promote it.

---

## 3. Decorators

### Q. What is a decorator, and why do AI codebases use them so much?

**Why they ask.** Timing, tracing, retry, auth, and “log every LLM call” are decorator-shaped. They also reveal whether you understand closures and `functools.wraps`.

**Keywords.** wrapper, `functools.wraps`, parameterized decorator, async decorator, side effects

**30 seconds.**
A decorator is a function that takes a function and returns a new function, usually adding behavior before/after the call. `@trace` on `complete()` is how you log model, latency, tokens, and error without polluting the body. Always use `@functools.wraps(fn)` so `__name__` and type hints survive.

**2 minutes.**
Two layers for a parameterized decorator:

```python
def timed(logger):
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            t0 = time.perf_counter()
            try:
                return fn(*args, **kwargs)
            finally:
                logger.info("fn=%s ms=%.1f", fn.__name__, (time.perf_counter() - t0) * 1000)
        return wrapper
    return deco
```

For async functions you must `async def wrapper` and `await fn(...)`. A sync wrapper around a coroutine just returns an un-awaited coroutine object — a silent production bug.

**Senior.**
I decorate at **service boundaries**, not inner loops. A decorator that logs full prompts will leak PII and blow log volume; I log hashes, token counts, latency, status, and a correlation id. I make retry a decorator only when the error taxonomy is clean; otherwise retry lives in an explicit loop so the caller can set a budget.

Stacked decorators apply bottom-up: `@retry` then `@timed` times the whole retry loop; reverse them and you time each attempt. That order is an interview question.

For FastAPI, decorators are the wrong tool for auth — use dependencies. For LangGraph/tool functions, a decorator that injects tracing context (OpenTelemetry span) is the right tool.

**Weak answer.** “A decorator is `@app.get`.” No closure, no wraps, no async.

**Follow-ups.** See Exercise 13 for a full timing/logging decorator aimed at LLM calls.

---

## 4. Generators, iterators, and streaming

### Q. Generator vs list — when must you not materialize?

**Why they ask.** AI work includes 10 GB JSONL eval sets, token streams, and log traces. Candidates who `list(open(path))` fail the “can they run this on a laptop / in a worker with 512 MB” test.

**Keywords.** lazy, `__iter__`/`__next__`, `yield`, `yield from`, generator expression, backpressure, streaming

**30 seconds.**
An iterator produces values on demand. A generator is a function with `yield` that is an iterator. Use it when the full collection does not fit in memory, or when the consumer might stop early (first match, first N tokens). A generator is single-pass; a list is random-access and reusable.

**2 minutes.**
Reading a JSONL eval file:

```python
def iter_jsonl(path: Path) -> Iterator[dict]:
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)
```

I never `records = [json.loads(l) for l in f]` on a file I have not `stat`’d. For embedding, I batch the generator (`batched(iter_jsonl(p), 64)`) so I get memory bounds *and* vectorized calls.

Token streams from an LLM are conceptually generators: `async for chunk in client.stream(...)`. You apply backpressure by simply not pulling the next chunk until the previous one was flushed to the client.

**Senior.**
I distinguish **iterators** (protocol) from **generators** (one implementation). A class with `__iter__` can be reused; a generator cannot. `yield from subgen` delegates and passes `send`/`throw`. For pipeline stages (read → chunk → embed → upsert) I prefer generators until I need parallelism; then I put a bounded queue between stages so a fast reader cannot OOM the embedder.

Generator expressions `(c for c in chunks if c.score > t)` are lazy; list comprehensions are not. Mixing them with `any()`/`next()` is how you short-circuit a scan.

Trap: `def f(): yield 1` vs `return [1]` — if a caller does `len(f())` it TypeErrors. Document the return type as `Iterator[T]` and do not pretend it is a sequence.

**Weak answer.** “Generators are faster than lists.” Sometimes they are slower (function call per item) and they are never indexable.

**Follow-ups.** Exercise 12 is a file-processing generator. Also: *Can you `pickle` a generator?* No. Do not put one on a job queue; pass the path and offset.

---

## 5. Classes, OOP, inheritance

### Q. How much OOP do you want in an LLM client?

**Why they ask.** They have seen both a 2,000-line `AIManager` god class and a pile of untyped functions. They want composition, a small interface, and test seams.

**Keywords.** composition over inheritance, Protocol/ABC, dataclass vs Pydantic, dependency injection, law of demeter

**30 seconds.**
I model **interfaces**, not a hierarchy of models. An `Embedder` protocol with `embed(texts: list[str]) -> list[list[float]]` lets me swap OpenAI, a local model, and a fake. I inherit only when I have a true “is-a” and shared invariants. For data, I use dataclass (in-process) or Pydantic (boundary). I do not inherit from a vendor SDK class just to wrap it.

**2 minutes.**
```python
class Embedder(Protocol):
    def embed(self, texts: list[str], *, model: str) -> list[list[float]]: ...

@dataclass
class CachedEmbedder:
    inner: Embedder
    cache: MutableMapping[tuple[str, str], list[float]]

    def embed(self, texts: list[str], *, model: str) -> list[list[float]]:
        ...
```

This is composition: caching, retries, and logging wrap the same protocol. Tests inject a stub. Inheritance (`class OpenAICachedEmbedder(OpenAIEmbedder)`) explodes combinatorially (retry+cache+batch for every vendor).

**Senior.**
In 2026 AI services the useful OOP pieces are:

1. **Protocols** for embed, complete, rerank, retrieve.
2. **Adapters** at the vendor boundary (translate exceptions, normalize usage).
3. **Policy objects** (timeouts, routing, budgets) that are data, not subclasses.
4. **Never** a `BaseAgent` with 15 overridable hooks unless you are writing a framework.

MRO and diamond inheritance are a smell here. If I need a mixin, I probably needed a wrapper.

`__init__` should be cheap. Connecting to a DB or warming a model belongs in an explicit `start()` or a context manager so tests and FastAPI lifespan can control it.

**Weak answer.** “I would make a BaseModel class and subclass GPT, Claude, Llama.” That is an inheritance tree shaped like a marketing page.

**Follow-ups.**

- *dataclass vs Pydantic?* dataclass is for trusted in-process records (fast, no validation). Pydantic is for untrusted input and serialization. Do not validate 10k chunks per request with a heavy model unless you measured it.
- *What is `__slots__` for?* Memory on millions of small objects (graph nodes). Irrelevant for a handful of service objects.

---

## 6. Exceptions and error taxonomy

### Q. How should an AI service fail?

**Why they ask.** The difference between a senior and a junior in this round is often exception handling: what you retry, what you surface, what you log.

**Keywords.** typed errors, retryable vs not, exception chaining, `except Exception`, timeout vs 429 vs 400, `raise X from e`

**30 seconds.**
Catch the narrowest exception you can handle. Retry only retryable failures (timeouts, 429, 5xx). Never swallow with bare `except:` or `except Exception: pass`. Convert vendor errors into *your* types at the adapter boundary so the rest of the app does not import `openai`. Chain with `raise MyErr(...) from e` to keep the traceback.

**2 minutes.**
Taxonomy I actually use:

| Class | Examples | Retry? | User sees |
| --- | --- | --- | --- |
| `RetryableProviderError` | 429, 503, timeout | yes, budgeted | “slow / busy”, maybe fallback model |
| `PermanentProviderError` | 401, 400 bad request | no | fail the request, alert if 401 |
| `SchemaError` | tool args fail Pydantic | no | model retry with validation message, capped |
| `GuardrailError` | injection, ACL miss | no | refusal / filtered |
| `BudgetExceeded` | max tokens, max steps | no | partial result + stop reason |

```python
try:
    return await client.complete(...)
except httpx.TimeoutException as e:
    raise RetryableProviderError("timeout") from e
```

**Senior.**
I attach `retry_after`, `status_code`, `request_id`, and `is_retryable` to the exception so the retry loop does not parse message strings. I log at the boundary with a correlation id, not at every layer (duplicate logs hide the first cause). `finally` closes resources; `else` on try runs only on success — useful to record metrics without counting failed calls as success.

For agents, I distinguish **tool errors** (the weather API 500’d — the model may retry or skip) from **system errors** (we could not parse our own state — abort). Mixing them is how agents loop.

`contextlib.suppress` is for expected, local, tiny cases (missing optional cache file), not HTTP.

**Weak answer.** `try: ... except Exception as e: print(e); return None`

**Follow-ups.** Exercise 2 (backoff). *Do you retry on 400?* Almost never; it will fail the same way and cost money.

---

## 7. Context managers

### Q. Why do interviewers care about `with`?

**Why they ask.** Files, HTTP clients, DB sessions, tracing spans, and GPU memory all leak if you forget `close()`. `with` is the protocol that makes cleanup reliable under exceptions.

**Keywords.** `__enter__`/`__exit__`, `contextlib.contextmanager`, `AsyncExitStack`, lifespan, deterministic cleanup

**30 seconds.**
A context manager sets something up and guarantees teardown in `__exit__`, even if the block raises. Use `with path.open() as f`, `async with httpx.AsyncClient() as client`, `with tracer.start_as_current_span("retrieve")`. Write your own with `@contextmanager` or a class when you have a resource pair (lock, temp dir, monkeypatch).

**2 minutes.**
```python
@contextmanager
def log_span(name: str):
    t0 = time.perf_counter()
    logging.info("start %s", name)
    try:
        yield
    except Exception:
        logging.exception("fail %s", name)
        raise
    else:
        logging.info("ok %s ms=%.1f", name, (time.perf_counter() - t0) * 1000)
```

FastAPI lifespan is an async context manager around the app: create the embedding client on startup, close it on shutdown. Creating a new `httpx.AsyncClient` per request is a common slow leak of sockets.

**Senior.**
`__exit__(exc_type, exc, tb)` returning `True` swallows the exception — almost never what you want. For multiple resources I use `ExitStack` / `AsyncExitStack` so a failure in resource 3 still closes 1 and 2. Locks should be context managers; holding a lock across an LLM await is a deadlock waiting to happen — acquire, copy what you need, release, then await.

**Weak answer.** “`with` is for files.” True but incomplete.

**Follow-ups.** *How does this interact with generators?* `yield` inside `with` keeps the file open for the life of the generator — that is a feature (streaming) and a leak if the consumer never finishes. Document it; prefer `for line in f: yield` inside the `with` so the caller iterates to completion, or close in a `finally` on generator close (`GeneratorExit`).

---

## 8. Type hints

### Q. Why type hints are not optional in a 2026 AI interview

**Why they ask.** Pydantic, FastAPI, OpenAI/Anthropic tool schemas, and `TypedDict` for message objects are how we keep JSON from becoming production incidents. Types are a communication tool for the interviewer too.

**Keywords.** `list[str]`, `Optional`/`X | None`, `TypedDict`, `Protocol`, `Generic`, `Literal`, `TypedDict` total=False, pydantic, mypy/pyright

**30 seconds.**
Hints document the contract and enable validation at the edges. I use `list[str]` not `List[str]` (3.9+). Optional fields are `str | None`. I do not type everything as `Any`. For JSON blobs I either define a TypedDict/Pydantic model or I explicitly type `dict[str, Any]` and parse immediately.

**2 minutes.**
Useful forms:

```python
Role = Literal["system", "user", "assistant", "tool"]

class Message(TypedDict):
    role: Role
    content: str

class ToolCall(BaseModel):
    name: str
    arguments: dict[str, Any]

async def complete(messages: Sequence[Message]) -> str: ...
```

`Sequence` in, `list` out: I accept tuples of messages but I return a concrete list of chunks. `Callable[[str], Awaitable[str]]` for a hook. `TypeVar` only when I write a generic cache.

**Senior.**
I treat types as **runtime-enforced at trust boundaries** (Pydantic on HTTP and tool args) and **static everywhere else**. I do not run Pydantic on every inner loop. I use `Literal` for model names I control, `str` for model names the user can set, and I validate against an allowlist.

`from __future__ import annotations` postpones evaluation so forward refs work. In 3.12, `type Json = dict[str, Json] | list[Json] | str | int | float | None` is a type alias for nested JSON.

A type hint is not a check. `def f(x: int):` still accepts `"1"` at runtime. That is why FastAPI+Pydantic is the interview combo: the framework actually validates.

**Weak answer.** “I skip types because Python is dynamic.” In this loop that reads as “I ship dicts and debug in production.”

**Follow-ups.** *TypedDict vs dataclass vs Pydantic?* TypedDict is a structural view of a dict (JSON in memory). Dataclass is an object without validation. Pydantic validates and serializes. Pick by trust and direction (in vs out).

---

## 9. Async/await

### Q. Explain async as if you were about to parallelize 20 embedding requests.

**Why they ask.** LLM work is I/O-bound. Candidates who “just use threads” or who sprinkle `async` without `await` both fail. This is one of the highest-probability Python topics in 2026 applied loops.

**Keywords.** event loop, coroutine, await, Task, gather, wait_for, cancellation, cooperative, I/O-bound, `httpx.AsyncClient`

**30 seconds.**
`async def` returns a coroutine. Nothing runs until it is awaited or scheduled as a Task on the event loop. Await *yields* control so other tasks can run during I/O. Perfect for many simultaneous HTTP calls to an LLM or embed API. It is still one thread: CPU-heavy work blocks the loop. Always set timeouts (`asyncio.wait_for` or httpx timeout). `asyncio.gather(*tasks)` runs them concurrently; pass `return_exceptions=True` if one failure should not kill the batch.

**2 minutes.**
```python
async def embed_all(client, texts: list[str], *, batch=64, timeout=30.0):
    batches = [texts[i:i+batch] for i in range(0, len(texts), batch)]
    tasks = [asyncio.wait_for(client.embed(b), timeout) for b in batches]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    out: list[list[float]] = []
    for r in results:
        if isinstance(r, Exception):
            raise EmbedError("batch failed") from r
        out.extend(r)
    return out
```

Pitfalls I name unprompted:

- Forgetting `await` → you pass a coroutine object into JSON and then wonder why.
- `time.sleep` in async code blocks the loop; use `await asyncio.sleep`.
- Creating `httpx.AsyncClient()` per call; reuse one.
- `gather` without timeout → a hung socket hangs the request.
- Fire-and-forget `asyncio.create_task` without keeping a reference or handling exceptions → “Task exception was never retrieved.”

**Senior.**
Cancellation is part of the design. When the user disconnects a streaming chat, I cancel the provider read so we stop spending tokens. `asyncio.TaskGroup` (3.11+) cancels siblings on first exception; that is often what I want for a fan-out. For *best-effort* parallel retrieval (BM25 + dense + SQL), I use `return_exceptions=True` and proceed with whatever arrived.

I never hold a `threading.Lock` across `await`. I use `asyncio.Lock` for in-loop shared state (a token bucket), or I put shared mutable state in a service that is safe.

CPU work (tiktoken on 10k docs, numpy over a big matrix) belongs in `asyncio.to_thread` or a process pool, with a bound on concurrency so I do not explode RAM.

**Weak answer.** “Async makes Python multithreaded so it is faster.” It does not.

**Follow-ups.** Exercise 10. *sync FastAPI def vs async def?* A sync `def` runs in a threadpool; an `async def` that calls blocking I/O blocks the loop for everyone. Do not mix.

---

## 10. Threading vs asyncio vs multiprocessing, and the GIL

### Q. What is the GIL, and which concurrency tool do you pick for an AI worker?

**Why they ask.** This is the classic senior-filter question. They want a *decision procedure*, not a Wikipedia paragraph.

**Keywords.** GIL, bytecode, I/O release, CPU-bound, embedding, tokenization, process vs thread vs async, pickle, shared memory

**30 seconds.**
The **Global Interpreter Lock** allows only one thread at a time to execute Python bytecode in a process. Threads **do** help for I/O because the GIL is released around I/O waits. Threads **do not** speed up pure-Python CPU loops. Multiprocessing uses separate interpreters (separate GILs) and helps CPU-bound work at the cost of memory and pickle. Asyncio is single-threaded cooperative concurrency for I/O. For 50 parallel OpenAI calls: asyncio (or threads). For CPU tokenization of a 20 GB corpus: processes or a C-extension that releases the GIL (NumPy, tiktoken’s C/Rust core).

**2 minutes.**
Decision table I draw on the whiteboard:

| Workload | Tool | Why |
| --- | --- | --- |
| Many LLM / embed HTTP calls | `asyncio` + `httpx.AsyncClient` | I/O wait; cheap concurrency; timeouts native |
| Blocking vendor SDK (sync only) | `ThreadPoolExecutor` | GIL released on I/O; easiest wrap |
| FastAPI sync endpoints | framework threadpool | do not block the event loop |
| Heavy Python CPU (parsing, regex on huge text) | `ProcessPoolExecutor` | bypass GIL |
| NumPy / tokenization in C | threads *or* just vectorize | C code often releases GIL |
| Shared in-memory cache of embeddings | threads or async in one process | processes need shared memory / Redis |
| Isolation / crash containment | processes | a segfault in a tokenizer should not kill the API |

GIL details at interview depth: it is a mutex on the interpreter, per process. Reference count updates are why it exists (memory safety). A thread doing `for x in huge: s += x` holds the GIL almost the whole time. `time.sleep`, disk, and network release it. Some C extensions release it around tight loops (`numpy.add`). The GIL is why `threading` can make CPU-bound code *slower* (contention).

**Senior.**
I measure. I also name the 2026 caveats:

- **free-threaded CPython (PEP 703)** exists as an experimental/optional build in the 3.13+ line. I do not write production code that *assumes* no GIL yet; I write code that is correct with a GIL and does not explode without one (no data races in C extensions, `asyncio` still single-threaded).
- **True parallelism for LLM serving** is not a Python threading problem — it is vLLM / TensorRT-LLM / a GPU worker. The API process should be a thin async I/O layer.
- **Batching beats concurrency** for embeddings: one HTTP call with 64 inputs is cheaper than 64 tasks of 1 input.
- **Multiprocessing costs:** each process copies the parent (copy-on-write, but large Python object graphs still hurt). Spawn vs fork: on Linux fork can copy a CUDA context badly — use spawn for GPU.
- **Shared state:** a process-local token bucket does not enforce a *global* TPM limit. Use Redis or the provider’s rate limit and accept 429s.

If they push on “how does asyncio coexist with threads?”: the event loop is not thread-safe. Use `asyncio.run_coroutine_threadsafe` or `loop.call_soon_threadsafe`. Default: don’t share the loop across threads.

**Weak answer.** “The GIL means Python cannot do two things at once, so we always use multiprocessing.” That would be a disaster for I/O-bound LLM fan-out.

**Follow-ups.**

- *Would you thread 1,000 OpenAI calls?* No. You will 429, OOM the connection pool, and stall. Bound concurrency (`Semaphore(20)`), batch, backoff.
- *Does `multiprocessing` share a dict?* No. Use `multiprocessing.Manager` (slow), shared memory, or Redis.
- *Why not just `async` everything?* Blocking SDKs, CPU sections, and simple scripts do not need it. Async spreads through a call stack (“function coloring”).

---

## 11. API calls and JSON

### Q. What do you always do when you call an LLM HTTP API?

**Why they ask.** This is the job. Missing timeouts are a production outage. Missing JSON schema checks are a tool-call incident.

**Keywords.** timeout, retries, status codes, streaming, `response.json()`, schema, httpx vs requests, connection pooling

**30 seconds.**
Set connect and read timeouts. Check status (`raise_for_status` or explicit 429 handling). Parse JSON with a schema (Pydantic), not a chain of `["choices"][0]["message"]["content"]`. Reuse a client (connection pool). Never log the raw `Authorization` header. For streams, iterate chunks and enforce a total time budget.

**2 minutes.**
`requests` is fine for sync scripts. In async services I use `httpx.AsyncClient` with:

```python
timeout = httpx.Timeout(connect=5.0, read=60.0, write=10.0, pool=5.0)
limits = httpx.Limits(max_connections=100, max_keepalive_connections=20)
```

JSON traps: `NaN`/`Infinity` are not valid JSON but Python’s `json` can emit them with the wrong flags; `datetime` is not JSON-serializable; tuples become lists; `set` crashes; keys must be strings. `orjson` / `pydantic` dump is faster and stricter. I never `json.loads` without a size cap on untrusted input.

Defensive parse:

```python
data = response.json()
content = (
    data.get("choices", [{}])[0]
        .get("message", {})
        .get("content")
)
```
…is still weak. I prefer a Pydantic model of the provider response, or a tiny adapter that raises `SchemaError` with the `request_id`.

**Senior.**
I separate **transport errors** (DNS, connect, TLS, timeout) from **application errors** (200 with `{"error": ...}` — some providers do this). I pass `Idempotency-Key` when the API supports it (payments, booking tools). I bound body size. I treat streaming as a state machine: if the connection dies mid-SSE, I decide whether the partial text is usable and whether to retry (usually not, because completion is not idempotent unless the server supports it).

`json.dumps` default `ensure_ascii=True` escapes non-ASCII — ugly for prompts, extra tokens if you round-trip. I set `ensure_ascii=False` when I control the pipe.

**Weak answer.** `requests.get(url).json()["choices"][0]["message"]["content"]` with no timeout.

**Follow-ups.** Exercises 1, 2, 8. Chapter 08 for HTTP semantics.

---

## 12. Pydantic

### Q. Why is Pydantic a default 2026 interview topic?

**Why they ask.** FastAPI, structured output, tool arguments, and config all sit on it. It is how you show you treat LLM output as **untrusted data**.

**Keywords.** BaseModel, `model_validate`, `model_dump`, Field, validator, `ValidationError`, schema, v2

**30 seconds.**
Pydantic models declare types and constraints; `model_validate(data)` parses untrusted dicts/JSON and raises `ValidationError` with field paths. I use it on HTTP requests, tool-call arguments, and sometimes on model JSON output. I do not use it as a general ORM. v2 (`model_validate` / `model_dump`) is the current API; I mention v1 `parse_obj` only if the codebase is old.

**2 minutes.**
```python
class QueryIn(BaseModel):
    tenant_id: UUID
    question: str = Field(min_length=1, max_length=4000)
    top_k: int = Field(default=8, ge=1, le=50)
    filters: dict[str, str] = Field(default_factory=dict)

    @field_validator("question")
    @classmethod
    def not_blank(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("empty")
        return v
```

`model_dump(mode="json")` for serialization. `model_json_schema()` is the starting point for tool JSON Schema. Extra fields: `model_config = ConfigDict(extra="forbid")` on inbound API models so a typo `topK` fails instead of being dropped.

**Senior.**
LLM structured output still fails schema. I validate, and on failure I either (a) retry the model with the validator error text, capped at 1–2 retries, or (b) fall back to a safer path. I never `model_validate` in a tight inner loop over 100k chunks without a reason — use dataclass or a TypedDict after the first check.

Nested models beat `dict[str, Any]` for tool args (`BookFlightArgs`). Coercion: Pydantic will turn `"8"` into `8` by default; I disable that on security-sensitive fields if it hides client bugs (`strict=True`).

Settings: `pydantic-settings` for env (`OPENAI_API_KEY`), not `os.environ[...]` sprinkled in code. Secrets should be `SecretStr` so `repr` does not leak.

**Weak answer.** “Pydantic is like dataclass but fancier.”

**Follow-ups.** Exercise 4 and 9.

---

## 13. FastAPI

### Q. What does a production FastAPI endpoint for RAG/chat look like in an interview?

**Why they ask.** FastAPI is in ~10.7% of JDs and a much higher share of take-homes. They want validation, auth dependency, timeouts, and a streaming path — not `print` in an endpoint.

**Keywords.** path/query/body, dependency injection, Pydantic, status codes, `StreamingResponse`, lifespan, background vs queue

**30 seconds.**
Declare a Pydantic body, return a Pydantic response, inject dependencies (`get_current_user`, `get_retriever`). Use `async def` only if you await. Validate with types, not `if` forests. For chat tokens, `StreamingResponse` with SSE. For heavy work, enqueue; do not `BackgroundTasks` a 2-minute embed job on the web process.

**2 minutes.**
Shape:

- `POST /v1/query` → 200 with citations, 401/403, 422 validation, 429, 504
- Dependency: authn → tenant → ACL
- Body: `QueryIn` (Exercise 4)
- Handler: retrieve → generate with timeout → `QueryOut`
- Lifespan: shared `httpx.AsyncClient`, DB pool
- Middleware: correlation id, access log without secrets

I do not put business logic in the router module. The router maps HTTP to a service function that is unit-testable without ASGI.

**Senior.**
I mention:

- **Idempotency** for POSTs that book tickets or send mail (see Chapter 08).
- **SSE vs WebSocket** for tokens (Chapter 08) — SSE is the default for chat.
- **Cancellation:** if the client drops, cancel the upstream LLM call.
- **Gunicorn/Uvicorn workers:** each has its own memory; embedding models in-process multiply RAM. Prefer a sidecar model server.
- **Pydantic validation errors** already map to 422; I customize only to avoid leaking internals.
- **Sync SDK in async route** is a footgun; wrap with `to_thread` and a semaphore.

**Weak answer.** A `@app.get` that calls OpenAI with the user’s raw query and returns `.content`.

**Follow-ups.** Exercise 4. *How do you test?* `TestClient` / `httpx.ASGITransport` with dependency overrides.

---

## 14. Unit tests

### Q. What do you test in an AI service, given that the model is non-deterministic?

**Why they ask.** Evaluation is the 2026 differentiator. Unit tests are the layer *under* evals: they lock the glue (parsing, retries, ACL, chunking) so evals measure the model, not your JSON bugs.

**Keywords.** pytest, mock, fixture, monkeypatch, contract test, golden file, property, determinism

**30 seconds.**
I unit-test everything that is deterministic: parsers, chunkers, backoff sleep schedule, Pydantic schemas, ACL filters, prompt assembly, tool-schema emission. I **mock** the LLM. I do not assert on exact model prose in a unit test. Quality of answers is an eval suite with a golden set, run in CI on a sample, not `assert "Paris" in output`.

**2 minutes.**
pytest patterns:

```python
def test_chunker_overlap_and_meta():
    chunks = chunk_text("abcdefghij", size=4, overlap=1, doc_id="d1")
    assert chunks[0].text == "abcd"
    assert chunks[1].text == "defg"  # overlap 1 → start at index 3
    assert [c.metadata["chunk_index"] for c in chunks] == list(range(len(chunks)))
    assert all(c.metadata["doc_id"] == "d1" for c in chunks)

def test_retry_gives_up_on_400(mocker):
    ...
```

I use `respx` or `httpx.MockTransport` for HTTP, not a patched `json` blob in 12 places. Fixtures build a tenant, a retriever with three documents, and a fake clock for backoff (`freezegun` or injected `sleep`).

**Senior.**
Test pyramid for LLM apps:

1. **Unit** — parsers, chunking, rate limiter, validators, prompt templates (snapshot the *rendered* prompt for a frozen input).
2. **Contract** — our adapter vs a recorded provider payload (VCR-style, sanitized). Replay, do not hit live APIs in PR CI.
3. **Eval** — golden questions, graded by rubric / LLM-as-judge with a pinned judge model, plus human spot checks. Fail the build on regression vs last release, not on a single flaky item.
4. **Smoke** — one live call in a nightly job with a budget cap.

I test failure paths: 429, empty retrieval, schema-invalid tool args, timeout, tenant mismatch. Those are the interviews that matter.

**Weak answer.** “You can’t unit test AI.” You can test the 80% that is software.

**Follow-ups.** *How do you mock time in backoff?* Inject `sleep` and `clock`. *What is a property test here?* For a chunker: joining chunks with overlap reconstructed covers the original (with a defined rule).

---

## 15. Logging

### Q. How do you log an LLM request without getting fired?

**Why they ask.** Prompt logs contain PII, secrets, and customer data. JWT and API keys in logs are a Chapter 08 scenario. Interviewers want structured logs with a redaction policy.

**Keywords.** structured logging, correlation id, redaction, log levels, metrics vs logs vs traces

**30 seconds.**
Use the `logging` module, not `print`. Structured fields: `correlation_id`, `tenant_id`, `model`, `latency_ms`, `input_tokens`, `output_tokens`, `status`. Default: **do not log full prompts or completions** in production. Log hashes or truncated previews behind a flag. Never log `Authorization`, cookies, or API keys. `exc_info` on errors.

**2 minutes.**
```python
logger.info(
    "llm.complete",
    extra={
        "model": model,
        "latency_ms": ms,
        "input_tokens": usage.in_tokens,
        "output_tokens": usage.out_tokens,
        "ok": True,
        "request_id": provider_id,
    },
)
```

JSON logs to stdout for Kubernetes. A `Filter` redacts keys matching `(?i)(authorization|api[-_]?key|password|cookie|token|jwt|secret)`. Debug-level prompt logging is opt-in per request for support, sampled, with retention limits.

**Senior.**
Logs are not traces. I emit an OpenTelemetry span per retrieve / complete / tool with those fields as attributes, and I keep logs for discrete events (retry attempt 3, fallback to model B). Cost is a metric (`tokens_total{model=}`). I include `prompt_version` and `index_version` so I can join to evals.

`logger.error` in a hot retry loop can DOS the log pipeline — log first and last attempt at error, middle at debug.

**Weak answer.** `print(response.json())`.

---

## 16. Memory and performance

### Q. Where does Python actually burn memory and time in AI pipelines?

**Why they ask.** Chunking, embeddings, and JSONL evals OOM more often than they CPU-starve. They want you to profile before rewriting in Rust.

**Keywords.** copies vs views, generator vs list, intern, `__slots__`, CPython allocations, vectorize, batching, profiling, tiktoken, numpy

**30 seconds.**
Avoid materializing huge lists; stream. Avoid copies: list slices copy; NumPy slices are views. Do not embed one string at a time (HTTP and Python overhead dominate). Profile with `cProfile` / `py-spy` / `tracemalloc` before guessing. Prefer vectorized NumPy/pandas over Python loops on arrays. Cache tokenization and embeddings with an explicit key and eviction, not an unbounded dict.

**2 minutes.**
Hot spots I have actually seen:

1. **Loading an entire PDF corpus as Python strings**, then slicing overlapping windows — each slice copies. For large docs, work in a memory map or at least keep one string and store `(start, end)` offsets; materialize text only when embedding.
2. **`df.iterrows()`** over eval results — use vectorized ops or `itertuples`.
3. **JSON parse of a 500 MB trace dump** — ijson / line-delimited, not `json.load` of the whole file.
4. **Appending to a string in a loop** — use `join` or a list of parts (CPython strings are immutable).
5. **Unbounded conversation memory in a dict keyed by session** — eviction, TTL, or a store.

`sys.getsizeof` lies for nested objects (it does not walk). `tracemalloc` plus a peak snapshot is the honest tool.

**Senior.**
I talk about **levels**:

- Algorithm: batch, stream, index, don’t recompute embeddings.
- Data layout: offsets instead of copied strings; `array('f')` or NumPy for vectors; avoid lists of millions of pydantic models.
- Interpreter: GIL, method call overhead — if the inner loop is Python cosine similarity over 2M vectors, that is a NumPy/`orjson`/vector DB problem, not a “use `__slots__`” problem.
- Process: workers × model size = RAM. Don’t load 7B weights into each of 8 Uvicorn workers.
- I/O: connection pools, HTTP/2, pipelining, keepalive.

`lru_cache` on an embed function without a maxsize keyed by text will grow without bound. Caches must have a policy.

Micro-optimizations I do **not** lead with: `__slots__`, local-variable binding, avoiding dots. I mention them only if a profile points there.

**Weak answer.** “Python is slow so we should rewrite the service in Go.” Not before a profile and not for the I/O-bound LLM proxy.

**Follow-ups.** *How do you compute cosine at interview speed?* Exercise 6. *How do you process a 20 GB file?* Exercise 12.

---

# Part II — Conceptual drills (compressed)

Use these as 30–60 second spoken cards. Full answers above.

| Topic | 30s spine | Senior add-on |
| --- | --- | --- |
| Mutability | lists/dicts mutate in place; tuples/frozensets do not; defaults bind once | copy at API boundaries; Pydantic `default_factory` |
| Hashability | keys must be immutable; list ≠ key | frozen dataclass as cache key |
| `*args **kwargs` | forwarding in wrappers | don’t hide typos; type the inner |
| Iterator protocol | `__iter__` returns `__next__` | generators are single-pass |
| MRO | C3 linearization | don’t diamond-inherit clients |
| `__enter__/__exit__` | setup/teardown | returning True swallows |
| `async` coloring | await all the way down | TaskGroup, cancellation |
| GIL | one bytecode thread | C-ext release; PEP 703 not assumed |
| Pydantic v2 | `model_validate` | strict, extra=forbid, SecretStr |
| FastAPI DI | `Depends` | override in tests, lifespan |
| pytest | arrange-act-assert + mock I/O | evals ≠ unit tests |

---

# Part III — Coding exercises

Format for every exercise: difficulty, time, concept, hints, a solution you can type in a round, a tighter version, follow-ups.

Narrate while you type: signature → types → happy path → failure path → test.

---

## Exercise 1 — Parse nested API JSON

| | |
| --- | --- |
| **Difficulty** | Easy–medium |
| **Expected time** | 12–18 min |
| **Concept tested** | Defensive JSON, tool calls, missing fields, schema |

**Problem.**
You receive a chat-completions-style payload that may contain assistant text, one or more tool calls, and usage. Write `parse_completion(payload: dict) -> ParsedCompletion` that:

- Extracts `id`, assistant `content` (may be `null` if tool-only), `finish_reason`
- Extracts tool calls as `name`, `call_id`, parsed `arguments` (JSON string → dict)
- Extracts `usage.prompt_tokens` / `completion_tokens` if present
- Raises `ParseError` with a clear message on structural problems
- Does **not** crash on extra fields

Example payload:

```python
payload = {
    "id": "cmpl_123",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_9",
                        "type": "function",
                        "function": {
                            "name": "search",
                            "arguments": '{"q": "kv cache", "k": 5}',
                        },
                    }
                ],
            },
            "finish_reason": "tool_calls",
        }
    ],
    "usage": {"prompt_tokens": 110, "completion_tokens": 27},
}
```

**Hints.**

1. Do not chain `payload["choices"][0]["message"]["tool_calls"][0]...` without checks.
2. `arguments` is a **string** of JSON in this protocol, not a dict.
3. Empty `choices` is an error; `content` of `None` is valid.

**Solution.**

```python
from __future__ import annotations

import json
from dataclasses import dataclass, field


class ParseError(ValueError):
    pass


@dataclass
class ToolCall:
    call_id: str
    name: str
    arguments: dict


@dataclass
class ParsedCompletion:
    id: str
    content: str | None
    finish_reason: str | None
    tool_calls: list[ToolCall] = field(default_factory=list)
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise ParseError(msg)


def parse_completion(payload: dict) -> ParsedCompletion:
    _require(isinstance(payload, dict), "payload must be an object")
    cid = payload.get("id")
    _require(isinstance(cid, str) and cid, "missing id")

    choices = payload.get("choices")
    _require(isinstance(choices, list) and choices, "choices empty or missing")
    choice = choices[0]
    _require(isinstance(choice, dict), "choice must be an object")

    message = choice.get("message")
    _require(isinstance(message, dict), "missing message")
    content = message.get("content")
    _require(content is None or isinstance(content, str), "content must be str or null")

    tool_calls_raw = message.get("tool_calls") or []
    _require(isinstance(tool_calls_raw, list), "tool_calls must be a list")
    tool_calls: list[ToolCall] = []
    for i, tc in enumerate(tool_calls_raw):
        _require(isinstance(tc, dict), f"tool_calls[{i}] not an object")
        fn = tc.get("function") or {}
        _require(isinstance(fn, dict), f"tool_calls[{i}].function missing")
        name = fn.get("name")
        _require(isinstance(name, str) and name, f"tool_calls[{i}] missing name")
        args_raw = fn.get("arguments", "{}")
        if isinstance(args_raw, dict):
            args = args_raw
        elif isinstance(args_raw, str):
            try:
                args = json.loads(args_raw) if args_raw else {}
            except json.JSONDecodeError as e:
                raise ParseError(f"tool_calls[{i}] arguments not JSON") from e
            _require(isinstance(args, dict), f"tool_calls[{i}] arguments not an object")
        else:
            raise ParseError(f"tool_calls[{i}] arguments has bad type")
        call_id = tc.get("id") or f"idx_{i}"
        tool_calls.append(ToolCall(call_id=str(call_id), name=name, arguments=args))

    usage = payload.get("usage") or {}
    pt = usage.get("prompt_tokens") if isinstance(usage, dict) else None
    ct = usage.get("completion_tokens") if isinstance(usage, dict) else None

    return ParsedCompletion(
        id=cid,
        content=content,
        finish_reason=choice.get("finish_reason"),
        tool_calls=tool_calls,
        prompt_tokens=pt if isinstance(pt, int) else None,
        completion_tokens=ct if isinstance(ct, int) else None,
    )
```

**Optimized solution.**
Use a Pydantic model of the provider response (`model_validate`) and map to your domain type. Stricter, better error paths, a bit more setup. In a 15-minute round, the dataclass + `_require` version is enough if you mention Pydantic as the production version.

```python
from pydantic import BaseModel, Field, ValidationError


class FunctionPayload(BaseModel):
    name: str
    arguments: str | dict = "{}"


class ToolCallPayload(BaseModel):
    id: str | None = None
    function: FunctionPayload


class MessagePayload(BaseModel):
    content: str | None = None
    tool_calls: list[ToolCallPayload] = Field(default_factory=list)


class ChoicePayload(BaseModel):
    message: MessagePayload
    finish_reason: str | None = None


class UsagePayload(BaseModel):
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


class CompletionPayload(BaseModel):
    id: str
    choices: list[ChoicePayload]
    usage: UsagePayload | None = None


def parse_completion_v2(payload: dict) -> ParsedCompletion:
    try:
        m = CompletionPayload.model_validate(payload)
    except ValidationError as e:
        raise ParseError(str(e)) from e
    if not m.choices:
        raise ParseError("choices empty")
    ch = m.choices[0]
    tools = []
    for i, tc in enumerate(ch.message.tool_calls):
        raw = tc.function.arguments
        args = raw if isinstance(raw, dict) else json.loads(raw or "{}")
        if not isinstance(args, dict):
            raise ParseError("arguments not an object")
        tools.append(ToolCall(tc.id or f"idx_{i}", tc.function.name, args))
    u = m.usage
    return ParsedCompletion(
        m.id, ch.message.content, ch.finish_reason, tools,
        None if u is None else u.prompt_tokens,
        None if u is None else u.completion_tokens,
    )
```

**Interviewer follow-ups.**

- Multiple `choices` (n>1): take all or forbid?
- `arguments` that JSON-decode to a list — reject.
- Provider returns `200` with `{"error": {...}}` — detect before parsing choices.
- How do you version this when Anthropic’s shape differs? An adapter per vendor, one domain `ParsedCompletion`.
- Token usage missing on streams until the last event — make usage optional, as above.

---

## Exercise 2 — Retry with exponential backoff + jitter

| | |
| --- | --- |
| **Difficulty** | Medium |
| **Expected time** | 15–20 min |
| **Concept tested** | Error taxonomy, time, jitter, budgets |

**Problem.**
Implement `retry(fn, *, attempts, base_delay, max_delay, retry_on)` that:

- Calls `fn()`
- Retries only if the exception is an instance of `retry_on`
- Sleeps `min(max_delay, base_delay * 2**k) * U(0.5, 1.0)` after failure `k` (full-ish jitter)
- Raises the last exception if attempts are exhausted
- Does not retry on anything else

Then wrap a mock `complete()` that fails with 429 twice then succeeds.

**Hints.**

1. Jitter exists to avoid thundering herds. Name that.
2. Inject `sleep` and `rng` so the function is testable.
3. `attempts=3` means 3 tries, 2 sleeps.

**Solution.**

```python
from __future__ import annotations

import random
import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def retry(
    fn: Callable[[], T],
    *,
    attempts: int = 5,
    base_delay: float = 0.25,
    max_delay: float = 8.0,
    retry_on: tuple[type[BaseException], ...] = (TimeoutError,),
    sleep: Callable[[float], None] = time.sleep,
    rng: Callable[[], float] = random.random,
) -> T:
    if attempts < 1:
        raise ValueError("attempts must be >= 1")
    last: BaseException | None = None
    for k in range(attempts):
        try:
            return fn()
        except retry_on as e:
            last = e
            if k == attempts - 1:
                break
            exp = min(max_delay, base_delay * (2 ** k))
            delay = exp * (0.5 + 0.5 * rng())  # in [0.5, 1.0] * exp
            sleep(delay)
    assert last is not None
    raise last
```

Usage with a fake provider:

```python
class RateLimitError(Exception):
    pass


class FakeLLM:
    def __init__(self):
        self.n = 0

    def complete(self) -> str:
        self.n += 1
        if self.n < 3:
            raise RateLimitError("429")
        return "ok"


def call():
    return retry(FakeLLM().complete, retry_on=(RateLimitError,), attempts=5)
```

**Optimized solution.**
Honor `Retry-After` when the exception carries it; cap by a **total deadline**, not only attempt count (a 60s user request cannot sleep 8+8+8); distinguish 429 from 503; make an async version with `await asyncio.sleep`; log attempt number.

```python
async def retry_async(fn, *, attempts=5, base=0.25, cap=8.0, deadline=s, retry_on=(Exception,)):
    t0 = time.monotonic()
    for k in range(attempts):
        remaining = deadline - (time.monotonic() - t0)
        if remaining <= 0:
            raise TimeoutError("retry budget exhausted")
        try:
            return await asyncio.wait_for(fn(), timeout=remaining)
        except retry_on as e:
            if k == attempts - 1:
                raise
            delay = min(cap, base * 2**k) * (0.5 + 0.5 * random.random())
            retry_after = getattr(e, "retry_after", None)
            if retry_after is not None:
                delay = min(max(delay, float(retry_after)), remaining)
            await asyncio.sleep(min(delay, remaining))
```

**Interviewer follow-ups.**

- Why jitter? Synchronized clients retry in lockstep after a shared outage.
- Full jitter vs equal jitter vs decorrelated jitter (AWS architecture blog). Equal jitter: `exp/2 + U(0, exp/2)`.
- Do you retry POSTs that booked a ticket? Only if idempotent (Chapter 08).
- Sleep in a FastAPI handler vs a queue worker: in the request path, fail fast to a 503 after a small budget; in a worker, you can wait longer.
- Circuit breaker vs retry: retries amplify load; a breaker stops calling a dead provider.

---

## Exercise 3 — Token-bucket rate limiter

| | |
| --- | --- |
| **Difficulty** | Medium |
| **Expected time** | 15–20 min |
| **Concept tested** | Concurrency, time, algorithm choice |

**Problem.**
Implement an in-process **token bucket** limiter: `rate` tokens per second, `capacity` burst. `acquire(n=1) -> bool` or a blocking `wait()`. Then mention a sliding-window alternative.

Use it to cap outbound LLM calls at 20 rps with burst 40.

**Hints.**

1. Refill based on elapsed time: `tokens = min(capacity, tokens + elapsed * rate)`.
2. Protect with a lock. For asyncio, `asyncio.Lock`.
3. Do not use `time.time()` if you care about NTP jumps; `monotonic` is the default.

**Solution.**

```python
from __future__ import annotations

import threading
import time


class TokenBucket:
    def __init__(self, rate: float, capacity: float):
        if rate <= 0 or capacity <= 0:
            raise ValueError("rate and capacity must be > 0")
        self.rate = rate
        self.capacity = capacity
        self._tokens = capacity
        self._t = time.monotonic()
        self._lock = threading.Lock()

    def _refill_unlocked(self) -> None:
        now = time.monotonic()
        elapsed = now - self._t
        self._t = now
        self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)

    def acquire(self, n: float = 1.0) -> bool:
        with self._lock:
            self._refill_unlocked()
            if self._tokens >= n:
                self._tokens -= n
                return True
            return False

    def wait(self, n: float = 1.0) -> None:
        while True:
            with self._lock:
                self._refill_unlocked()
                if self._tokens >= n:
                    self._tokens -= n
                    return
                deficit = n - self._tokens
                delay = deficit / self.rate
            time.sleep(delay)
```

**Optimized solution.**
Async + sliding window (accurate RPM over a rolling 60s, which is how many providers define it):

```python
import asyncio
from collections import deque


class SlidingWindowLimiter:
    """Allow up to `limit` events in the last `window` seconds."""

    def __init__(self, limit: int, window: float):
        self.limit = limit
        self.window = window
        self._events: deque[float] = deque()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            cutoff = now - self.window
            while self._events and self._events[0] <= cutoff:
                self._events.popleft()
            if len(self._events) >= self.limit:
                delay = self._events[0] + self.window - now
                # release lock while sleeping
            else:
                self._events.append(now)
                return
        await asyncio.sleep(max(delay, 0))
        await self.acquire()  # retry; depth is small because we waited out one slot
```

Production: this limiter is **per process**. Six Uvicorn workers = 6× the rate. For a global TPM cap use Redis (`INCR` + TTL, or a token-bucket Lua script) plus handling 429s from the provider as the source of truth.

**Interviewer follow-ups.**

- Token bucket vs leaky bucket vs sliding window vs fixed window. Fixed window is simple and bursts at boundaries (100 calls at 00:59 and 100 at 01:00). Sliding window is smoother. Token bucket allows configured bursts — good for chat spikes.
- Do you rate-limit tokens or requests? Providers have both RPM and TPM. A TPM bucket subtracts `n = estimated_prompt_tokens`.
- Fairness across tenants: one bucket per tenant, plus a global bucket.
- Holding `asyncio.Lock` across `sleep` starves others — the sliding-window sketch releases first.

---

## Exercise 4 — FastAPI POST with Pydantic validation

| | |
| --- | --- |
| **Difficulty** | Medium |
| **Expected time** | 15–25 min |
| **Concept tested** | FastAPI, Pydantic, status codes, DI |

**Problem.**
Build `POST /v1/query` that accepts:

```json
{
  "tenant_id": "11111111-1111-1111-1111-111111111111",
  "question": "What is our refund policy?",
  "top_k": 8,
  "filters": {"product": "cards"}
}
```

Rules:

- `question` 1–4000 chars after strip
- `top_k` 1–50, default 8
- unknown fields → 422
- unauthenticated → 401 (dependency)
- returns `{ "answer": str, "citations": [{"doc_id": str, "score": float}] }`

Stub the retriever.

**Hints.**

1. `ConfigDict(extra="forbid")`.
2. `Depends(get_principal)` for auth.
3. Keep the router thin.

**Solution.**

```python
from __future__ import annotations

from uuid import UUID

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, field_validator


class QueryIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenant_id: UUID
    question: str = Field(min_length=1, max_length=4000)
    top_k: int = Field(default=8, ge=1, le=50)
    filters: dict[str, str] = Field(default_factory=dict)

    @field_validator("question")
    @classmethod
    def strip_question(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("question must not be blank")
        return v


class Citation(BaseModel):
    doc_id: str
    score: float


class QueryOut(BaseModel):
    answer: str
    citations: list[Citation]


class Principal(BaseModel):
    sub: str
    tenant_id: UUID


async def get_principal(authorization: str | None = Header(default=None)) -> Principal:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing token")
    # Interview stub: a real impl verifies JWT (Chapter 08).
    token = authorization.removeprefix("Bearer ").strip()
    if token != "test-token":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "bad token")
    return Principal(sub="user_1", tenant_id=UUID("11111111-1111-1111-1111-111111111111"))


app = FastAPI()


@app.post("/v1/query", response_model=QueryOut)
async def query(body: QueryIn, principal: Principal = Depends(get_principal)) -> QueryOut:
    if body.tenant_id != principal.tenant_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "tenant mismatch")
    # Stub retrieve + generate
    citations = [Citation(doc_id="pol-refund-1", score=0.86)]
    return QueryOut(
        answer="Refunds are available within 30 days with a receipt.",
        citations=citations,
    )
```

**Optimized solution.**
Extract a `QueryService`; add timeout; stream; dependency-override in tests:

```python
from fastapi.testclient import TestClient

def test_rejects_extra_field_and_blank_question():
    app.dependency_overrides[get_principal] = lambda: Principal(
        sub="u", tenant_id=UUID("11111111-1111-1111-1111-111111111111")
    )
    c = TestClient(app)
    r = c.post("/v1/query", json={
        "tenant_id": "11111111-1111-1111-1111-111111111111",
        "question": "   ",
        "topK": 3,
    })
    assert r.status_code == 422
```

Also: request size limit, correlation-id middleware, `response_model_exclude_none`, OpenAPI description for the Solutions-engineer demo.

**Interviewer follow-ups.**

- Why 403 vs 404 on tenant mismatch? 403 admits the resource space exists; some teams always 404 to reduce enumeration. Pick and justify.
- Where does ACL on documents happen? In the retriever, using `principal`, never after generation.
- How do you stream this? `StreamingResponse` with `media_type="text/event-stream"`.
- Why not `BackgroundTasks` for the LLM call? The client needs the answer; background is for side effects (write audit row) after the response is on the wire — and even then a queue is safer.

---

## Exercise 5 — Document chunker (overlap + metadata)

| | |
| --- | --- |
| **Difficulty** | Medium |
| **Expected time** | 15–20 min |
| **Concept tested** | Offsets, overlap, metadata, edge cases |

**Problem.**
`chunk_text(text, *, size, overlap, doc_id, extra_meta=None) -> list[Chunk]`

- Character windows of `size` with `overlap` (`0 <= overlap < size`)
- Last chunk may be shorter; drop empty
- Each chunk carries `doc_id`, `chunk_index`, `start`, `end`, `n_chars`, and any extra metadata
- Do not mutate `extra_meta`

**Hints.**

1. Step is `size - overlap`.
2. Guard against overlap >= size (infinite loop).
3. Store offsets so you can cite the original.

**Solution.**

```python
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Chunk:
    text: str
    metadata: dict = field(compare=False)


def chunk_text(
    text: str,
    *,
    size: int,
    overlap: int,
    doc_id: str,
    extra_meta: dict | None = None,
) -> list[Chunk]:
    if size <= 0:
        raise ValueError("size must be > 0")
    if overlap < 0 or overlap >= size:
        raise ValueError("overlap must be in [0, size)")
    if not text:
        return []

    step = size - overlap
    extra = dict(extra_meta) if extra_meta else {}
    chunks: list[Chunk] = []
    start = 0
    n = len(text)
    idx = 0
    while start < n:
        end = min(start + size, n)
        piece = text[start:end]
        if piece:
            meta = {
                **extra,
                "doc_id": doc_id,
                "chunk_index": idx,
                "start": start,
                "end": end,
                "n_chars": end - start,
            }
            chunks.append(Chunk(text=piece, metadata=meta))
            idx += 1
        if end == n:
            break
        start += step
    return chunks
```

**Optimized solution.**
Token-aware chunking (tiktoken) with sentence-boundary snap; keep character offsets by mapping tokens back; do not split inside a table or a code fence; carry `source`, `title`, `acl_roles`, `content_hash`. For a 20 GB corpus, yield chunks from a generator (Exercise 12) instead of returning a list.

```python
def chunk_by_tokens(text: str, enc, *, size: int, overlap: int, **meta) -> Iterator[Chunk]:
    ids = enc.encode(text)
    step = size - overlap
    for i, start in enumerate(range(0, len(ids), step)):
        window = ids[start:start + size]
        if not window:
            break
        yield Chunk(enc.decode(window), {**meta, "chunk_index": i, "tok_start": start})
        if start + size >= len(ids):
            break
```

**Interviewer follow-ups.**

- Why overlap? So a sentence split across a boundary is still fully present in at least one chunk. Cost: more chunks, more embeddings, possible duplicate citations — dedupe by `doc_id` at retrieve time.
- Character vs token vs semantic (embedding-similarity breakpoints) vs recursive (markdown headers). Interview-safe default: token windows with heading metadata, then a reranker.
- Tiny last chunk: merge with previous if `len < overlap` to avoid embedding noise.
- How do you cite? Offsets into the original, not into the chunk only.

---

## Exercise 6 — Cosine similarity

| | |
| --- | --- |
| **Difficulty** | Easy |
| **Expected time** | 8–12 min |
| **Concept tested** | Vectors, numerical edge cases, batching |

**Problem.**
Implement `cosine(a, b) -> float` and `top_k(query, matrix, k) -> list[tuple[int, float]]` where `matrix` is a list of vectors. Handle zero vectors without raising. Do not use a vector DB.

**Hints.**

1. Cosine = dot / (||a|| ||b||). Zero norm → score 0.0 (or skip).
2. Prefer one pass to precompute document norms.
3. NumPy if allowed; otherwise pure Python is fine for N≪10k in an interview.

**Solution.**

```python
from __future__ import annotations

import math


def cosine(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        raise ValueError("dimension mismatch")
    dot = na = nb = 0.0
    for x, y in zip(a, b, strict=True):
        dot += x * y
        na += x * x
        nb += y * y
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / math.sqrt(na * nb)


def top_k(
    query: list[float],
    matrix: list[list[float]],
    k: int,
) -> list[tuple[int, float]]:
    if k <= 0:
        return []
    scored = [(i, cosine(query, row)) for i, row in enumerate(matrix)]
    scored.sort(key=lambda t: t[1], reverse=True)
    return scored[:k]
```

**Optimized solution.**

```python
import numpy as np

def top_k_np(query: np.ndarray, matrix: np.ndarray, k: int) -> list[tuple[int, float]]:
    q = query / (np.linalg.norm(query) + 1e-12)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True) + 1e-12
    m = matrix / norms
    scores = m @ q
    k = min(k, scores.shape[0])
    idx = np.argpartition(-scores, kth=k-1)[:k]
    idx = idx[np.argsort(-scores[idx])]
    return [(int(i), float(scores[i])) for i in idx]
```

`argpartition` is O(n) vs full sort O(n log n). Mention that at >100k vectors you want HNSW / IVF, not this.

**Interviewer follow-ups.**

- Why cosine vs L2 vs inner product? Cosine is scale-invariant; many embedding models are already L2-normalized, in which case cosine = inner product. If they are normalized, skip the division.
- Did you mutate `matrix` when normalizing? Work on a copy or keep a parallel `norms` array.
- Empty matrix, k > n, NaN in a vector — name the guards.

---

## Exercise 7 — Simple in-memory retrieval

| | |
| --- | --- |
| **Difficulty** | Medium |
| **Expected time** | 15–20 min |
| **Concept tested** | Glue: chunk store, embed stub, cosine, metadata filter, tenant |

**Problem.**
Build `InMemoryIndex` with `add(chunks)`, `search(query, *, tenant_id, k, where=None)`. Filter by `metadata["tenant_id"]` **before** scoring (correctness and fairness). Return text + score + metadata.

**Hints.**

1. Do not search other tenants and then drop — that is an ACL bug waiting for a log leak.
2. Inject the embedder.
3. Precompute embeddings on `add`.

**Solution.**

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class Embedder(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...


@dataclass
class Hit:
    text: str
    score: float
    metadata: dict


class InMemoryIndex:
    def __init__(self, embedder: Embedder):
        self.embedder = embedder
        self._texts: list[str] = []
        self._meta: list[dict] = []
        self._vecs: list[list[float]] = []

    def add(self, texts: list[str], metadatas: list[dict]) -> None:
        if len(texts) != len(metadatas):
            raise ValueError("length mismatch")
        vecs = self.embedder.embed(texts)
        self._texts.extend(texts)
        self._meta.extend(dict(m) for m in metadatas)
        self._vecs.extend(vecs)

    def search(
        self,
        query: str,
        *,
        tenant_id: str,
        k: int = 8,
        where: dict | None = None,
    ) -> list[Hit]:
        qv = self.embedder.embed([query])[0]
        where = where or {}
        cand_i = []
        cand_v = []
        for i, meta in enumerate(self._meta):
            if meta.get("tenant_id") != tenant_id:
                continue
            if any(meta.get(key) != val for key, val in where.items()):
                continue
            cand_i.append(i)
            cand_v.append(self._vecs[i])
        ranked = top_k(qv, cand_v, k)  # from Exercise 6
        return [
            Hit(self._texts[cand_i[i]], score, dict(self._meta[cand_i[i]]))
            for i, score in ranked
        ]
```

**Optimized solution.**
Keep a `dict[tenant_id, list[int]]` inverted index so you do not scan the world. L2-normalize on add. Deduplicate by `doc_id` keeping max score. Add a keyword path (BM25) and say “hybrid is the 2026 default; this is the dense half.”

**Interviewer follow-ups.**

- Filter before vs after ANN? Pre-filter is correct for ACL; some ANN indexes do it poorly — for in-memory brute force, filter first is both correct and faster.
- How would this become pgvector? Same metadata filters in SQL `WHERE`, then `ORDER BY embedding <=> $q LIMIT k` (Chapter 07).
- Empty result: do not invent; return `[]` and let the generator refuse or ask a clarifying question.

---

## Exercise 8 — Call an LLM-style API (mock)

| | |
| --- | --- |
| **Difficulty** | Medium |
| **Expected time** | 15–20 min |
| **Concept tested** | httpx, timeouts, JSON, testing without spend |

**Problem.**
Write `LLMClient.complete(messages, *, model, timeout_s)` against `POST {base}/v1/chat/completions`. Parse content. Raise typed errors on 429 / 5xx / timeout. Provide a mock transport so tests never hit the network.

**Hints.**

1. `httpx.MockTransport` or a fake `handler(request) -> Response`.
2. Always pass `timeout`.
3. Do not put the API key in query params.

**Solution.**

```python
from __future__ import annotations

import httpx


class LLMError(Exception):
    def __init__(self, message: str, *, status: int | None = None, retryable: bool = False):
        super().__init__(message)
        self.status = status
        self.retryable = retryable


class LLMClient:
    def __init__(self, base_url: str, api_key: str, transport: httpx.BaseTransport | None = None):
        self._client = httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            transport=transport,
            timeout=httpx.Timeout(30.0),
        )

    def close(self) -> None:
        self._client.close()

    def complete(self, messages: list[dict], *, model: str, timeout_s: float = 30.0) -> str:
        try:
            r = self._client.post(
                "/v1/chat/completions",
                json={"model": model, "messages": messages, "temperature": 0},
                timeout=timeout_s,
            )
        except httpx.TimeoutException as e:
            raise LLMError("timeout", retryable=True) from e
        except httpx.TransportError as e:
            raise LLMError("transport", retryable=True) from e

        if r.status_code == 429:
            raise LLMError("rate limited", status=429, retryable=True)
        if r.status_code >= 500:
            raise LLMError("provider 5xx", status=r.status_code, retryable=True)
        if r.status_code >= 400:
            raise LLMError(f"client error {r.status_code}", status=r.status_code, retryable=False)

        data = r.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as e:
            raise LLMError("unexpected payload") from e
        if not isinstance(content, str):
            raise LLMError("content not a string")
        return content
```

Mock:

```python
def handler(request: httpx.Request) -> httpx.Response:
    assert request.headers.get("Authorization") == "Bearer sk-test"
    return httpx.Response(200, json={
        "choices": [{"message": {"role": "assistant", "content": "hello"}}]
    })

def test_complete():
    c = LLMClient("https://api.example.com", "sk-test", transport=httpx.MockTransport(handler))
    assert c.complete([{"role": "user", "content": "hi"}], model="demo") == "hello"
```

**Optimized solution.**
Async client; reuse connections; parse with Exercise 1; attach `Retry-After`; stream; record `usage` for cost. Context manager (`__enter__` closes). Do not log `request.content` (may contain PII) or headers.

**Interviewer follow-ups.**

- Where do retries live — client or caller? A thin client that *marks* retryable, a policy layer that retries with budget. Mixing both double-retries.
- How do you keep tests from accidentally hitting prod? Default `base_url` required, no implicit env in unit tests, MockTransport, CI network sandbox.

---

## Exercise 9 — Tool / function JSON schema

| | |
| --- | --- |
| **Difficulty** | Medium |
| **Expected time** | 12–18 min |
| **Concept tested** | Pydantic → JSON Schema, untrusted LLM args |

**Problem.**
Given a Pydantic args model, emit an OpenAI-style tool definition. Then `parse_tool_args(model, raw_json: str)` that validates. Include a `book_ticket` example (used again in Chapter 08).

**Hints.**

1. `model_json_schema()`.
2. Strip Pydantic extras you do not want the model to see (`title` noise is OK; internal fields are not).
3. LLM args are untrusted: extra fields forbid, ranges enforced.

**Solution.**

```python
from __future__ import annotations

import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError


class BookTicketArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confirmation_style: Literal["email", "sms"] = "email"
    flight_id: str = Field(min_length=3, max_length=32)
    passenger_name: str = Field(min_length=1, max_length=80)
    seats: int = Field(default=1, ge=1, le=9)


def tool_spec(name: str, description: str, args_model: type[BaseModel]) -> dict:
    schema = args_model.model_json_schema()
    schema.pop("title", None)
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": schema,
        },
    }


def parse_tool_args(args_model: type[BaseModel], raw: str | dict):
    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
        return args_model.model_validate(data)
    except (json.JSONDecodeError, ValidationError) as e:
        raise ValueError(f"invalid tool args: {e}") from e


BOOK_TICKET_TOOL = tool_spec(
    "book_ticket",
    "Book a flight. Irreversible. Only call after the user confirms flight_id and seats.",
    BookTicketArgs,
)
```

**Optimized solution.**
Add `strict` JSON Schema (`additionalProperties: false` is already implied by `extra="forbid"` in v2 for the model, but nested dicts need care). Include examples in the description, not hallucinated `default` that the model always picks. For enums, use `Literal`. Never expose an `admin` tool in the same list as user-facing tools without a policy gate — schema visibility *is* authorization in LLM land.

**Interviewer follow-ups.**

- What if the model omits `flight_id`? ValidationError → return the error to the model once, then abort.
- What if it adds `discount_code`? `extra="forbid"` rejects. Good.
- How does this relate to MCP tools? Same idea: JSON Schema parameters, but MCP adds a server, resources, and a gateway (Chapter 12). In-app function calling is enough for one service.

---

## Exercise 10 — Async gather with timeout

| | |
| --- | --- |
| **Difficulty** | Medium |
| **Expected time** | 12–18 min |
| **Concept tested** | asyncio.gather, wait_for, cancellation, partial success |

**Problem.**
Fan out to three retrievers (dense, keyword, SQL). Return whatever succeeded within `timeout_s`. Cancel the rest. Do not crash if one raises.

**Hints.**

1. `return_exceptions=True`.
2. `asyncio.wait` with `timeout` or `wait_for` on the gather.
3. Cancel pending tasks in `finally`.

**Solution.**

```python
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Sequence
from typing import TypeVar

T = TypeVar("T")


async def gather_with_timeout(
    coros: Sequence[Awaitable[T]],
    *,
    timeout_s: float,
) -> list[T | BaseException | None]:
    tasks = [asyncio.create_task(c) for c in coros]
    done, pending = await asyncio.wait(tasks, timeout=timeout_s)
    for p in pending:
        p.cancel()
    if pending:
        await asyncio.gather(*pending, return_exceptions=True)

    out: list[T | BaseException | None] = []
    for t in tasks:
        if t.cancelled() or not t.done():
            out.append(None)  # timed out
            continue
        exc = t.exception() if not t.cancelled() else None
        if exc is not None:
            out.append(exc)
        else:
            out.append(t.result())
    return out
```

Caller:

```python
dense, bm25, sql = await gather_with_timeout(
    [retrieve_dense(q), retrieve_bm25(q), retrieve_sql(q)],
    timeout_s=0.4,
)
hits = merge(x for x in (dense, bm25, sql) if isinstance(x, list))
```

**Optimized solution.**
Use `asyncio.timeout(timeout_s)` (3.11) around a `TaskGroup` if you want all-or-nothing. For retrieval, partial success is usually better. Bound each subcall with its own timeout so a hung SQL pool does not eat the whole budget. Log which branch failed. Do not create tasks from a closing loop.

**Interviewer follow-ups.**

- What happens to the HTTP request if you cancel? You want an explicit `aclose()` on the stream so the provider stops generating (cost).
- `gather` vs `wait` vs `as_completed` — `as_completed` for “first good reranker result wins.”
- Threading equivalent? `concurrent.futures.wait(timeout=...)` then `cancel()`.

---

## Exercise 11 — Debug broken Python (two snippets, plus a third)

Interviewers paste broken code more often than they ask you to write from scratch. Talk out loud: reproduce, hypothesize, fix, add a test.

### Snippet A — mutable default + swallowed errors + no timeout

**Difficulty.** Easy. **Time.** 6–8 min. **Concept.** defaults, exceptions, HTTP hygiene.

```python
import requests

def ask(prompt, history=[], model="gpt-x"):
    try:
        history.append({"role": "user", "content": prompt})
        r = requests.post(
            "https://api.example.com/v1/chat",
            json={"model": model, "messages": history},
        )
        text = r.json()["choices"][0]["message"]["content"]
        history.append({"role": "assistant", "content": text})
        return text, history
    except:
        return "", history
```

**What is wrong (say this first).**

1. `history=[]` is shared across calls — conversations leak into each other.
2. Mutates the caller’s list even if they passed one.
3. Bare `except:` catches `KeyboardInterrupt` / `SystemExit` in py<3.8 thinking, and *everything* including `NameError`.
4. No timeout — hung socket, hung worker.
5. No status check — a 429 HTML body will blow up in `r.json()` and then get swallowed.
6. No API key / header handling; JSON key chain is fragile.

**Fix.**

```python
def ask(prompt: str, history: list[dict] | None = None, *, model: str, timeout_s: float = 30.0) -> tuple[str, list[dict]]:
    msgs = list(history or [])
    msgs.append({"role": "user", "content": prompt})
    try:
        r = requests.post(
            "https://api.example.com/v1/chat",
            json={"model": model, "messages": msgs},
            timeout=timeout_s,
        )
        r.raise_for_status()
        data = r.json()
        text = data["choices"][0]["message"]["content"]
    except (requests.RequestException, KeyError, IndexError, TypeError, ValueError) as e:
        raise LLMError(str(e)) from e
    msgs.append({"role": "assistant", "content": text})
    return text, msgs
```

**Follow-ups.** Should `ask` retry? Not inside this function unless named `ask_with_retry`. Should it log `prompt`? Not by default.

---

### Snippet B — async that is not async, plus late-binding closure

**Difficulty.** Medium. **Time.** 8–10 min. **Concept.** await, closures in loops, gather.

```python
import asyncio, httpx

client = httpx.AsyncClient()

async def embed_many(texts):
    tasks = []
    for t in texts:
        async def one():
            r = client.post("/embed", json={"text": t})
            return r.json()["vector"]
        tasks.append(one())
    return asyncio.gather(*tasks)
```

**What is wrong.**

1. `client.post` is awaited never — `r` is a coroutine, `.json()` is nonsense. Need `r = await client.post(...)`.
2. `return asyncio.gather(*tasks)` returns a coroutine that the caller must await; also `gather` is not awaited here, so exceptions are delayed/lost. Use `return await asyncio.gather(...)`.
3. Closure late binding: every `one` sees the **last** `t`. Fix with `async def one(t=t):` or `async def one(text): ...` and `one(t)`.
4. No timeout, no semaphore, no `raise_for_status`.
5. Global `AsyncClient` never closed; no lifespan.
6. Creating N tasks of one text instead of batching.

**Fix.**

```python
async def embed_many(texts: list[str], client: httpx.AsyncClient) -> list[list[float]]:
    sem = asyncio.Semaphore(8)

    async def one(text: str) -> list[float]:
        async with sem:
            r = await client.post("/embed", json={"text": text}, timeout=15.0)
            r.raise_for_status()
            return r.json()["vector"]

    return await asyncio.gather(*(one(t) for t in texts))
```

Better: batch into groups of 64.

**Follow-ups.** Why `Semaphore`? Provider RPM. Why pass `client` in? Tests and shutdown.

---

### Snippet C — (bonus) iterator / file leak / JSON lines

**Difficulty.** Easy. **Time.** 5 min.

```python
def load_evals(path):
    f = open(path)
    return (json.loads(line) for line in f)
```

**What is wrong.** Generator is lazy so `open` stays open; if the caller never iterates, leak. If they iterate twice, the generator is exhausted. No encoding, no skip of blank lines, no size guard.

**Fix:** Exercise 12.

---

## Exercise 12 — Generator for large file processing

| | |
| --- | --- |
| **Difficulty** | Easy–medium |
| **Expected time** | 10–15 min |
| **Concept tested** | Generators, context managers, batching, memory |

**Problem.**
Stream a JSONL eval file (possibly multi-GB). Yield validated records. Provide `batched(it, n)` for embedding. Do not load the file into memory.

**Hints.**

1. `with open` wrapping `yield` keeps the file open for the consumer — that is OK if documented.
2. Skip bad lines but count them; don’t fail a 10M-row job on one corrupt line unless `strict=`.
3. `batched` can be a generator of lists.

**Solution.**

```python
from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel, ValidationError

T = TypeVar("T")


class EvalRow(BaseModel):
    id: str
    question: str
    expected: str
    tags: list[str] = []


def iter_eval_rows(path: Path, *, strict: bool = False) -> Iterator[EvalRow]:
    n_bad = 0
    with path.open(encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield EvalRow.model_validate_json(line)
            except (ValidationError, json.JSONDecodeError):
                n_bad += 1
                if strict:
                    raise
    # Note: n_bad is only known after full iteration; for a running counter,
    # yield a header/stats object or log periodically.


def batched(it: Iterable[T], n: int) -> Iterator[list[T]]:
    if n <= 0:
        raise ValueError("n must be > 0")
    batch: list[T] = []
    for item in it:
        batch.append(item)
        if len(batch) == n:
            yield batch
            batch = []
    if batch:
        yield batch


def embed_eval_file(path: Path, embedder: Embedder) -> Iterator[tuple[EvalRow, list[float]]]:
    for rows in batched(iter_eval_rows(path), 64):
        vecs = embedder.embed([r.question for r in rows])
        yield from zip(rows, vecs, strict=True)
```

**Optimized solution.**
Memory-map binary formats; use `ijson` for huge nested JSON (not JSONL); parallelize batches with a process pool for CPU tokenization while keeping read single-threaded; checkpoint offset (`f.tell()`) so a crash can resume. If `Pydantic` is too slow at 100k rows/s, switch to a tighter parser after a sample validation.

**Interviewer follow-ups.**

- What if the consumer breaks out of the `for` early? `with` still closes on generator close (`GeneratorExit`).
- Encoding errors: `errors="replace"` vs fail — eval data should fail; logs might replace.
- Why JSONL not JSON array? You can stream JSONL; a top-level array requires a streaming parser.

---

## Exercise 13 — Decorator for timing / logging LLM calls

| | |
| --- | --- |
| **Difficulty** | Medium |
| **Expected time** | 12–18 min |
| **Concept tested** | Decorators, wraps, async vs sync, redaction |

**Problem.**
Write `@log_llm(logger)` that works on sync and async callables. Logs `name`, `latency_ms`, `ok`, and optional `model` kwarg. Does **not** log messages/prompts. Reraises exceptions. Preserves `__name__`.

**Hints.**

1. Detect coroutine functions with `inspect.iscoroutinefunction`.
2. `functools.wraps`.
3. `try/except/else` or `try/finally` with a success flag.

**Solution.**

```python
from __future__ import annotations

import functools
import inspect
import logging
import time
from collections.abc import Callable
from typing import Any, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def log_llm(logger: logging.Logger | None = None) -> Callable[[F], F]:
    log = logger or logging.getLogger("llm")

    def deco(fn: F) -> F:
        if inspect.iscoroutinefunction(fn):
            @functools.wraps(fn)
            async def awrapper(*args: Any, **kwargs: Any):
                t0 = time.perf_counter()
                ok = False
                try:
                    result = await fn(*args, **kwargs)
                    ok = True
                    return result
                finally:
                    ms = (time.perf_counter() - t0) * 1000
                    log.info(
                        "llm.call",
                        extra={
                            "fn": fn.__name__,
                            "model": kwargs.get("model"),
                            "latency_ms": round(ms, 1),
                            "ok": ok,
                        },
                    )
            return awrapper  # type: ignore[return-value]

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any):
            t0 = time.perf_counter()
            ok = False
            try:
                result = fn(*args, **kwargs)
                ok = True
                return result
            finally:
                ms = (time.perf_counter() - t0) * 1000
                log.info(
                    "llm.call",
                    extra={
                        "fn": fn.__name__,
                        "model": kwargs.get("model"),
                        "latency_ms": round(ms, 1),
                        "ok": ok,
                    },
                )
        return wrapper  # type: ignore[return-value]

    return deco


@log_llm()
async def complete(*, model: str, messages: list[dict]) -> str:
    ...
```

**Optimized solution.**
Pull `usage` from the result if it has `.prompt_tokens`. Add `correlation_id` from contextvars. Do not time the decorator of a retry wrapper if you wanted per-attempt timing — stack order matters (`@log_llm` under `@retry` logs each try; above logs the total). Support generators / streaming by logging on stream close, not on first chunk.

```python
# stack meaning
@log_llm()   # times the whole retry loop
@retry(...)
async def complete(...): ...
```

**Interviewer follow-ups.**

- How do you unit-test this? Inject a `logger` with `list` handler, fake clock.
- Will this log PII? Only if you add `messages` to `extra`. Don’t.
- OpenTelemetry: a span is better than a log line for latency; keep both thin.

---

# Part IV — Putting a 45-minute round together

A realistic combined prompt you should be able to do:

> “Here is a nested tool-call payload. Parse it, validate args with Pydantic, call a mock HTTP tool with retries and a token bucket, and expose a FastAPI POST that does this. Stream nothing yet. Write two tests.”

Order of attack:

1. Types and Pydantic models (5 min)
2. Parser (5)
3. HTTP client + timeout (5)
4. Retry + limiter (8)
5. Endpoint (7)
6. Tests (7)
7. Narrate what you would add: SSE, ACL, evals (the rest)

If you stall on the limiter, leave a correct `acquire()` and say the sliding-window version out loud. A complete, tested happy path beats an unfinished clever algorithm.

---

# Part V — Weak patterns that fail this round

| Pattern | Why it fails |
| --- | --- |
| No timeout on HTTP | Instant “has not shipped” signal |
| `except Exception: return None` | Hides the bug they planted |
| `json()["choices"][0]...` with no schema | Crashes on the first provider change |
| `async def` + blocking `requests` | Blocks the event loop |
| Unbounded `create_task` fan-out | 429 + memory |
| Logging full prompts and headers | Security fail, even if code “works” |
| God class `AIManager` | Untestable |
| Exact-string assert on model output | Flaky test, wrong layer |
| `history=[]` default | They will ask you to find it |
| Chunker without overlap or metadata | RAG that cannot cite |
| Filter ACL after vector search in a shared list, then log hits | Tenant leak |

---

# Part VI — Rapid-fire (30–45 seconds each)

1. **`is` vs `==`?** Identity vs value. `None` with `is`.
2. **`sort` vs `sorted`?** In-place vs new list.
3. **`deepcopy` needed?** Nested mutable in caches / default configs. Messages: copy the list, and do not share dicts.
4. **`__slots__`?** Memory on many instances; not your first lever.
5. **`walrus` `:=`?** Fine in a parser loop; don’t be cute.
6. **`dataclasses.replace`?** Immutable updates.
7. **`enumerate` / `zip(..., strict=True)`?** Use them; `strict` catches length bugs in embedding joins.
8. **`pathlib` vs `os.path`?** `pathlib` by default.
9. **`f-string` vs `format` for logs?** Use lazy `%s` or structured `extra` in hot logs so you don’t interpolate when the level is off.
10. **GIL + NumPy?** Many ops release the GIL; don’t assume your Python loop does.
11. **`asyncio.run` inside FastAPI?** No — already in a loop. `create_task` or just await.
12. **`model_dump` vs `dict()` in Pydantic v2?** `model_dump`. `dict()` is v1.
13. **Why `SecretStr`?** `repr` and logs won’t leak the key.
14. **What is a contextvar?** Per-task context (request id) that unlike `threading.local` works with async.
15. **When is multiprocessing the wrong answer for OpenAI fan-out?** Always, relative to asyncio; you pay RAM and pickle for I/O waits.

---

# Part VII — Interviewer scorecard (Python)

Use this after a mock.

| Dimension | 1 | 3 | 5 |
| --- | --- | --- | --- |
| HTTP hygiene | no timeout | timeout, status check | timeout, taxonomy, retry budget, no leaked headers |
| Data/JSON | key chains | defensive get | schema, vendor adapter |
| Async/concurrency | confuses threads and async | picks asyncio for I/O | bounds, cancellation, GIL-accurate |
| Types/Pydantic | none | hints on signatures | boundary validation, extra=forbid |
| Tests | none | one happy-path | failure path + mock transport |
| Memory | loads everything | generators named | offsets, batching, cache policy |
| Communication | silent typing | narrates | trade-offs unprompted |

A passing mid-level Python round in 2026 is **not** “knows metaclasses.” It is: *timeouts, schemas, a mock, and a chunker that carries metadata.*

---

**Related chapters.** 07 SQL (metadata filters, tenancy). 08 APIs (HTTP, SSE, 429, JWT). 10 RAG (chunking in context). 11 Agentic (tool schemas, retries in a loop). 17 LLMOps (logging, evals, traces).
