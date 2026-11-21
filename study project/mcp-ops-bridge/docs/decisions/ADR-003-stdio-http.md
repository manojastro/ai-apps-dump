# ADR-003 — stdio + Streamable HTTP (minimal JSON-RPC, no SDK)

Status: accepted. Date: 2026-09-18.

Context: MCP spec moves fast; the Python SDK is heavy for an offline teaching slice,
but learners must SEE the protocol (initialize/tools.list/tools.call).

Decision: hand-rolled minimal JSON-RPC 2.0 in `src/ops_mcp/server.py`:
line-delimited JSON over stdio (`initialize`, `tools/list`, `tools/call`,
`resources/*`, `prompts/*`, `ping`) plus a FastAPI `POST /mcp` bearer-token stub
for remote use. Tool annotations mark `readOnlyHint/destructiveHint`.

Alternatives: official MCP Python SDK (heavier, version churn — revisit for P4/P6),
SSE transport (superseded by Streamable HTTP — not used).

Consequences: no new dependency; transcript in `docs/jsonrpc-transcript.md` is real;
HTTP stub needs `MCP_BEARER_TOKEN` + TLS + allowlist before any internet exposure.
stdio = local tool; HTTP = shared service.
