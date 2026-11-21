"""Import every model so Alembic autogenerate and ``Base.metadata`` see the full schema."""

from app.models.enterprise import Asset, AssetDependency, BusinessService
from app.models.identity import AppSetting, User
from app.models.remediation import ApprovalDecision, ApprovalRequest, RemediationPlan, RiskAssessment
from app.models.servicenow import ServiceNowRecord, ServiceNowSyncAttempt, SnSimActivity, SnSimRecord
from app.models.simulation import SimDevice, SimDeviceSoftware
from app.models.vulnerability import Finding, ScanEvidence, ScanImport, ThreatIntelCache, Vulnerability
from app.models.workflow import (
    AgentExecution,
    AuditEvent,
    EvaluationCaseResult,
    EvaluationRun,
    ToolCall,
    WorkflowEvent,
    WorkflowRun,
)

__all__ = [
    "AgentExecution",
    "AppSetting",
    "ApprovalDecision",
    "ApprovalRequest",
    "Asset",
    "AssetDependency",
    "AuditEvent",
    "BusinessService",
    "EvaluationCaseResult",
    "EvaluationRun",
    "Finding",
    "RemediationPlan",
    "RiskAssessment",
    "ScanEvidence",
    "ScanImport",
    "ServiceNowRecord",
    "ServiceNowSyncAttempt",
    "SimDevice",
    "SimDeviceSoftware",
    "SnSimActivity",
    "SnSimRecord",
    "ThreatIntelCache",
    "ToolCall",
    "User",
    "Vulnerability",
    "WorkflowEvent",
    "WorkflowRun",
]
