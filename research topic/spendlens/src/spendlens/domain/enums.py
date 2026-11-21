"""Canonical enumerations. Values are persisted as strings."""

from enum import StrEnum


class CloudProvider(StrEnum):
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"


class Role(StrEnum):
    VIEWER = "viewer"
    ANALYST = "analyst"
    APPROVER = "approver"
    ADMINISTRATOR = "administrator"


class DataMode(StrEnum):
    DEMO = "demo"
    LAB = "lab"
    LIVE_READ = "live_read"
    MIXED = "mixed"


class ModelMode(StrEnum):
    DETERMINISTIC = "deterministic"
    XAI = "xai"
    UNAVAILABLE = "unavailable"


class ExecutionMode(StrEnum):
    PR_ONLY = "pr_only"
    DIRECT_DISABLED = "direct_disabled"
    DIRECT_OPTED_IN = "direct_opted_in"


class ConnectorStatus(StrEnum):
    NOT_CONFIGURED = "not_configured"
    CONNECTED = "connected"
    DEGRADED = "degraded"
    DENIED = "denied"
    UNAVAILABLE = "unavailable"
    SYNTHETIC = "synthetic"


class CostMetric(StrEnum):
    UNBLENDED = "unblended_cost"
    AMORTIZED = "amortized_cost"
    NET_UNBLENDED = "net_unblended_cost"
    NET_AMORTIZED = "net_amortized_cost"
    EFFECTIVE = "effective_cost"
    LIST_PRICE = "list_price"


class AttributionLevel(StrEnum):
    RESOURCE = "resource"
    SERVICE = "service"
    ACCOUNT = "account"
    SHARED = "shared"
    UNALLOCATED = "unallocated"


class PurchaseModel(StrEnum):
    ON_DEMAND = "on_demand"
    SAVINGS_PLAN = "savings_plan"
    RESERVED = "reserved"
    SPOT = "spot"


class ResourceType(StrEnum):
    EC2_INSTANCE = "ec2.instance"
    EBS_VOLUME = "ebs.volume"
    ENI = "ec2.network_interface"
    RDS_INSTANCE = "rds.instance"
    ASG = "autoscaling.group"
    S3_BUCKET = "s3.bucket"
    LAB_SERVICE = "lab.service"
    UNKNOWN = "unknown"


class RecommendationKind(StrEnum):
    EC2_RIGHTSIZE = "ec2_rightsize"
    NONPROD_SCHEDULE = "nonprod_schedule"
    IDLE_ORPHAN = "idle_orphan"
    RDS_SIZE = "rds_size"
    SPEND_ANOMALY = "spend_anomaly"
    CONTAINER_TRADEOFF = "container_tradeoff"
    COMMITMENT_AWARENESS = "commitment_awareness"
    REQUEST_FOR_DATA = "request_for_data"
    COMBINED_SCENARIO = "combined_scenario"


class RecommendationStatus(StrEnum):
    DISCOVERED = "discovered"
    NEEDS_DATA = "needs_data"
    ANALYZED = "analyzed"
    PROPOSED = "proposed"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    CHANGE_PREPARED = "change_prepared"
    APPLIED = "applied"
    PERFORMANCE_VERIFYING = "performance_verifying"
    BILLING_PENDING = "billing_pending"
    EVALUATED = "evaluated"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    STALE = "stale"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    INCONCLUSIVE = "inconclusive"


class LedgerState(StrEnum):
    IDENTIFIED_POTENTIAL = "identified_potential"
    APPROVED_ESTIMATE = "approved_estimate"
    CHANGE_PREPARED = "change_prepared"
    CHANGE_APPLIED = "change_applied"
    PERFORMANCE_VERIFIED = "performance_verified"
    BILLING_OBSERVATION_PENDING = "billing_observation_pending"
    OBSERVED_BILLED_COST_CHANGE = "observed_billed_cost_change"
    ESTIMATED_ATTRIBUTABLE_SAVINGS = "estimated_attributable_savings"
    REJECTED = "rejected"
    EXPIRED = "expired"
    REVERSED = "reversed"


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    INVALIDATED = "invalidated"


class ChangeStatus(StrEnum):
    DRAFT = "draft"
    PR_OPEN = "pr_open"
    PR_MERGED = "pr_merged"
    VALIDATION_LIMITED = "validation_limited"
    APPLIED = "applied"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    BLOCKED = "blocked"


class ActionKind(StrEnum):
    TERRAFORM_PR = "terraform_pr"
    EC2_STOP = "ec2_stop"
    EC2_START = "ec2_start"
    EC2_MODIFY_INSTANCE_TYPE = "ec2_modify_instance_type"
    LAB_RESIZE = "lab_resize"
    DIRECT_UNAVAILABLE = "direct_unavailable"


class QualitySeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    BLOCKER = "blocker"


class IngestionStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    PARTIAL = "partial"
    FAILED = "failed"
    CANCELLED = "cancelled"


class EstimateKind(StrEnum):
    LIST_PRICE_OPPORTUNITY = "list_price_opportunity"
    EFFECTIVE_COST_OPPORTUNITY = "effective_cost_opportunity"
    ESTIMATED_AVOIDABLE_CASH = "estimated_avoidable_cash"


class VerificationOutcome(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    INCONCLUSIVE = "inconclusive"
    PENDING = "pending"
    SKIPPED = "skipped"
