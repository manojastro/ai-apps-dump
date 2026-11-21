# LEARNING_LOG (mock-first slice — built with agent, learner reviews each Mx)

## M1 — MCP in plain English — 2026-09-18
**Built:** docs/mcp-in-my-words.md (host/client/server, tools/resources/prompts, JSON-RPC, stdio vs HTTP).
**New concepts:** MCP = standard adapter; tool descriptions are prompts.
**Learner tasks:** mcp-in-my-words — attempts: 0 — hints used: 0
**Break-it result:** predicted vague tool desc picks wrong tool / actual: same (see M4 notes).
**Quiz:** pending
**Open questions:** none
**Interview line I can now say:** "MCP lets any host use one server's tools over JSON-RPC."

## M2 — mock-itsm + seed — 2026-09-18
**Built:** sysparm_query parser, SQLite schema, 40 CIs / 200 incidents / 60 changes / 5 scenario YAMLs + logs.
**New concepts:** sysparm_query `=` + `^`; CMDB rel parent depends_on child.
**Learner tasks:** scenario 5 YAML evidence — attempts: 0 — hints used: 0
**Break-it result:** predicted bad query 400 / actual: 400 (tested).
**Quiz:** pending
**Open questions:** none
**Interview line I can now say:** "CMDB blast radius is BFS over depends_on edges."

## M4/M5 — MCP server + JSON-RPC — 2026-09-18
**Built:** 9 tools, resources, triage prompt, stdio JSON-RPC + HTTP bearer stub, real transcript.
**New concepts:** request/response/notification + id; error object; annotations readOnly/destructive.
**Learner tasks:** list_recent_changes end-to-end; raw JSON messages — attempts: 0 — hints used: 0
**Break-it result:** predicted unknown method -32601 / actual: -32601.
**Quiz:** pending
**Open questions:** none
**Interview line I can now say:** "I can walk through initialize -> tools/list -> tools/call."

## M6/M7 — Approvals + injection — 2026-09-18
**Built:** hashed single-use scoped expiring tokens; audit_log; UNTRUSTED wrapping; injection drill incident.
**New concepts:** hash tokens; replay attack; defence in system not prompt.
**Learner tasks:** verify_approval — attempts: 0 — hints used: 0
**Break-it result:** predicted reuse/wrong-target/expired all denied / actual: denied (tests green).
**Quiz:** pending
**Open questions:** none
**Interview line I can now say:** "Writes need single-use scoped tokens; injection text is just data."
