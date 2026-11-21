# Target adapter guide

Every adapter returns `answer`, `contexts[{source_id,text}]`, `citations`, `tool_calls[{name,arguments}]`, optional `task_success`, `latency_ms`, tokens, and `cost_usd`.

- HTTP: `evalharness run --http-url URL`. The harness POSTs `{"case": {...}}` and validates the response shape.
- Python: expose a callable accepting a case dictionary and returning the response dictionary, then use `--python-callable module:function`.
- RAG: map retrieved chunks to `contexts` and canonical IDs to `citations`.
- Agent: additionally map the safe operational tool trace. Never include hidden model reasoning or credentials.

See `examples/demo_agent` for both HTTP and callable implementations. Adapter timeouts/errors become failed, inspectable samples instead of aborting an entire experiment.

