# Architecture

## System architecture

```mermaid
flowchart TB
  subgraph Experience
    DASH[ForgeGuard release dashboard]
    DOCS[OpenAPI]
  end
  subgraph Control_Plane
    AUTH[Verified viewer / approver / executor identities]
    API[FastAPI /api/v1]
    OBS[Health / readiness / metrics]
  end
  subgraph Agent_Workflow
    FIND[Security Finding Agent]
    EXP[Exploitability Agent]
    RISK[Release Risk Agent]
    REM[Remediation Agent]
    GATE[Human Approval Gate]
    EXEC[Safe Exact Patch Executor]
    VAL[Validation Agent]
  end
  subgraph Safe_Local_Adapters
    FIX[Inert fixture catalog]
    RULES[Transparent scanner rules]
    AST[Python AST parser]
    WS[Isolated incident workspace]
  end
  DB[(SQLite evidence and audit store)]
  DASH --> API
  DOCS --> API
  AUTH --> API
  API --> FIND --> EXP --> RISK --> REM --> GATE --> EXEC --> VAL
  FIND --> RULES
  REM --> FIX
  EXEC --> WS
  VAL --> RULES
  VAL --> AST
  FIND & EXP & RISK & REM & GATE & EXEC & VAL --> DB
  API --> OBS
```

## Agent workflow

```mermaid
stateDiagram-v2
  [*] --> FixtureSelected
  FixtureSelected --> StaticFinding
  StaticFinding --> ExploitabilityAssessed
  ExploitabilityAssessed --> ReleaseBlocked
  ReleaseBlocked --> AwaitingApproval
  AwaitingApproval --> Rejected: reviewer rejects
  AwaitingApproval --> ReapprovalRequired: legacy artifact binding cannot be proven
  ReapprovalRequired --> Approved: new exact preview + fixed-source attestation
  AwaitingApproval --> Approved: approver attests exact hashes
  Approved --> Refused: source hash changed
  Approved --> Fixed: reviewed hash matches
  Fixed --> RolledBack: any guardrail fails or validator unavailable
  RolledBack --> ValidationFailed: atomic failure evidence persisted
  Fixed --> Validated: all static + AST checks pass
  Validated --> AllowWithReview
  Rejected --> [*]
  Refused --> [*]
  ValidationFailed --> [*]
  AllowWithReview --> [*]
```

## Validation workflow

```mermaid
sequenceDiagram
  participant R as Remediation Agent
  participant H as Verified Approver
  participant X as Distinct Executor
  participant E as Exact Patch Executor
  participant A as AST Validator
  participant S as Static Scanner
  participant P as Release Policy
  R->>H: diff, risk, blast radius, rollback, source hash
  H->>E: immutable action + patch + fixed-source hash attestation
  X->>E: separately authenticated execution request
  E->>E: verify attestation + input + workspace hashes
  E->>E: select exact allow-listed fixed source
  E->>A: parse only; never import or execute
  A-->>E: exact canonical module/function/call/return AST
  E->>S: deterministic rescan
  S-->>E: original finding count 1→0
  E->>P: regression checks and evidence
  P-->>H: ALLOW_WITH_REVIEW or BLOCK + restore before-source
```

## Persistence and filesystem boundary

SQLite persists incident source snapshots, structured investigations, approvals,
validation results, evaluation ground truth, and audit events. Database triggers deny
audit updates and deletes. Each incident receives a generated-ID directory beneath the
configured workspace root. Resolved path containment and source-hash checks prevent a
caller from selecting another filesystem target.

The service never imports fixture or workspace modules. `ast.parse` constructs syntax
trees without running the source. The exact transformation catalog is the only source
of after-content.
