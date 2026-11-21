# DEMO (90 seconds)

1. (20s) "Any LLM can read Acme incidents safely." Show `list_incidents(service=vpn)` then
   `get_incident INC1000001` over the MCP Inspector/stdio. Point at UNTRUSTED label.
2. (25s) "It reasons like on-call." `get_blast_radius(fw-edge-01,1)` -> vpn gateways;
   `list_recent_changes(fw-edge-01)` -> CHG1000001 20 min before; `get_logs vpn` -> IKE fails.
3. (20s) "Writes are gated." Call `update_incident_state -> Resolved` with NO token ->
   error `-32000 approval required`. Show seeded `SYSTEM: ...` text in INC1000004;
   "the model can read the attack, but the tool layer refuses."
4. (25s) "Human approves once." `POST /approvals` -> token; retry write -> success;
   retry again -> `token already used`. Show `audit_log` row. Close: "7 read, 2 gated
   writes, full audit — over stdio and HTTP."
