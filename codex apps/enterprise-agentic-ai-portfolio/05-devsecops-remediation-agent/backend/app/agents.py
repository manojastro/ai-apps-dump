from .models import AgentDefinition


AGENTS = [
    AgentDefinition(
        name="Security Finding Agent",
        responsibility="Detect authored vulnerable patterns using transparent static rules",
        inputs=["inert source text", "scenario contract"],
        outputs=["typed security finding", "source-hash evidence"],
        tools=["DeterministicSecurityScanner"],
        permission_boundary="read-only; never imports or executes fixture source",
        failure_behavior="withholds the incident unless exactly one expected finding exists",
    ),
    AgentDefinition(
        name="Exploitability Agent",
        responsibility="Combine finding validity with explicit reachability context",
        inputs=["security finding", "fixture reachability context"],
        outputs=["typed exploitability assessment"],
        tools=["ExploitabilityAgent.assess"],
        permission_boundary="read-only evidence synthesis",
        failure_behavior="does not infer missing reachability facts",
    ),
    AgentDefinition(
        name="Remediation Agent",
        responsibility="Select a reviewed exact transformation and explain its risk",
        inputs=["known scenario", "reviewed source hash"],
        outputs=["typed remediation plan", "patch preview", "bound artifact hashes"],
        tools=["allow-listed transformation catalog"],
        permission_boundary="cannot run code, commands, or arbitrary patches",
        failure_behavior="refuses unrecognized scenarios or changed action, patch, fixed-source, input, or workspace hashes",
    ),
    AgentDefinition(
        name="Validation Agent",
        responsibility="Statically verify the fix and release guardrails",
        inputs=["before source", "after source"],
        outputs=["typed validation result", "release risk"],
        tools=["AST parser", "deterministic rescan", "signature and allow-list policy"],
        permission_boundary="parse and compare only; generated code is never executed",
        failure_behavior="blocks release when any check fails",
    ),
    AgentDefinition(
        name="Release Risk Agent",
        responsibility="Block vulnerable releases and lower risk only after validation",
        inputs=["finding", "exploitability", "validation checks"],
        outputs=["release decision and evidence-backed score"],
        tools=["deterministic risk policy"],
        permission_boundary="advisory decision; cannot deploy",
        failure_behavior="defaults to BLOCK",
    ),
]
