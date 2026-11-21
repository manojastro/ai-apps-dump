from app.models.domain import KnowledgeDocument

DOCUMENTS = [
    KnowledgeDocument(
        id="RUNBOOK-001",
        title="Customer schema compatibility",
        content="When customer_id becomes customerId, map the source field to customer_id. "
        "Keep the warehouse schema intact and validate downstream customer joins.",
    ),
    KnowledgeDocument(
        id="RULE-002",
        title="Currency conversion contract",
        source_type="schema",
        document_type="business_rule",
        content="amount_cents is an integer in cents. Divide by 100 for amount. "
        "Compare every transaction to the independent ledger, not just the total.",
    ),
    KnowledgeDocument(
        id="RUNBOOK-003",
        title="Null customer enrichment",
        content="Restore missing customer identifiers from the trusted transaction "
        "customer master. Never invent IDs or drop rows to pass a null check.",
    ),
    KnowledgeDocument(
        id="RUNBOOK-004",
        title="Duplicate retry ingestion",
        content="Deduplicate byte-equivalent transaction rows by transaction_id. "
        "Conflicting duplicates require human investigation and must not be silently lost.",
    ),
    KnowledgeDocument(
        id="RUNBOOK-005",
        title="Upstream dependency retries",
        content="Retry transient 503 errors at most three times. Configuration changes "
        "require human approval. Stop if the dependency remains unavailable.",
    ),
    KnowledgeDocument(
        id="INCIDENT-006",
        title="Previous amount deployment regression",
        source_type="incident",
        document_type="history",
        content="A deployment removed the cents conversion. Schema checks passed but "
        "per-transaction reconciliation failed. Restoring divisor 100 recovered totals.",
    ),
]


class LocalKnowledge:
    async def retrieve(
        self, query: str, pipeline_id: str, environment: str
    ) -> list[KnowledgeDocument]:
        # The database-backed hybrid retriever replaces this minimal core-graph test adapter.
        terms = set(query.lower().replace("_", " ").split())
        matched = [
            document
            for document in DOCUMENTS
            if document.pipeline_id == pipeline_id and document.environment == environment
        ]
        return sorted(
            matched, key=lambda d: len(terms & set(d.content.lower().split())), reverse=True
        )[:4]
