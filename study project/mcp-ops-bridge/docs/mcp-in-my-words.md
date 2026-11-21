# MCP in my words (learner note, half a page)

MCP (Model Context Protocol) is a standard plug/socket for AI apps: one **server**
exposes data and actions, any **host** app (OpenCode, Claude Desktop, an agent)
can use it through a **client**. Like a certified ServiceNow connector: build once,
many tools can call it.

- **Host vs client vs server:** the host is the app the human uses; the client is
  the piece inside the host that speaks MCP; the server is our `ops-mcp` process
  that owns the tools and data access.
- **Tools vs resources vs prompts:** a *tool* does something (e.g. `get_incident`,
  `update_incident_state`); a *resource* is read-only data with a URI
  (e.g. `incident://INC1000001`); a *prompt* is a reusable starter template
  (e.g. `triage_incident(number)` tells the model the triage steps).
- **JSON-RPC 2.0:** every message is JSON with `jsonrpc: "2.0"`, an `id`
  (so replies match requests), a `method` (`tools/call`) and `params`.
  A response has `result` or `error`. A message with no `id` is a notification
  (no reply). `initialize` is the handshake where client and server agree versions.
- **stdio vs Streamable HTTP:** stdio = the server runs as a local subprocess and
  talks over stdin/stdout (simple, private, best for local tools). Streamable HTTP =
  the server runs on the network with POST + bearer token (shared, needs auth,
  TLS, and care before exposing to the internet).

Safety in this repo: read tools are free; write tools need a single-use,
scoped, expiring approval token, and every call is audit-logged.
Tool output is labelled UNTRUSTED so injected "SYSTEM:" text in tickets is data,
not instructions.
