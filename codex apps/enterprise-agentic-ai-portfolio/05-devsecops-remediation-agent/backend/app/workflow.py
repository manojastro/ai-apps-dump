from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from .database import Repository
from .models import (
    ApprovalRequest,
    InvestigationResult,
    ValidationResult,
    WorkflowStatus,
)
from .scanner import (
    DeterministicSecurityScanner,
    ExploitabilityAgent,
    RemediationAgent,
    SafePatchExecutor,
    ValidationAgent,
    release_risk_after,
    release_risk_before,
    source_hash,
)
from .simulator import SCENARIOS, SafeDemoSourceAdapter, SourceAdapter


class WorkflowConflict(RuntimeError):
    pass


class IncidentNotFound(KeyError):
    pass


ROOT_CAUSES = {
    "sql_injection": "attacker-controlled API input reaches dynamically constructed SQL",
    "command_injection": "attacker-controlled file paths reach a command shell",
    "hardcoded_secret": "credential material is stored in version-controlled source",
}


class RemediationWorkflow:
    def __init__(self, repository: Repository, workspace_root: str | Path,
                 source_adapter: SourceAdapter | None = None):
        self.repository = repository
        self.workspace_root = Path(workspace_root).resolve()
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        self.source_adapter = source_adapter or SafeDemoSourceAdapter()
        self.scanner = DeterministicSecurityScanner()
        self.exploitability_agent = ExploitabilityAgent()
        self.remediation_agent = RemediationAgent()
        self.executor = SafePatchExecutor()
        self.validator = ValidationAgent(self.scanner)

    def investigate(self, scenario_name: str) -> dict[str, Any]:
        scenario = self.source_adapter.scenario(scenario_name)
        source = scenario.vulnerable_source
        findings = self.scanner.scan(scenario, source)
        if len(findings) != 1:
            raise WorkflowConflict("fixture scan did not produce exactly one expected finding")
        finding = findings[0]
        exploitability = self.exploitability_agent.assess(scenario, finding)
        remediation = self.remediation_agent.propose(scenario)
        risk = release_risk_before(finding, exploitability)
        incident_id = f"sec-{uuid4().hex[:12]}"
        investigation = InvestigationResult(
            incident_id=incident_id, scenario=scenario_name,
            probable_root_cause=ROOT_CAUSES[scenario_name], confidence=0.98,
            finding=finding, exploitability=exploitability, remediation=remediation,
            release_risk_before=risk,
        )
        workspace_file = self._workspace_file(incident_id, scenario.filename)
        workspace_file.parent.mkdir(parents=True, exist_ok=False)
        workspace_file.write_text(source, encoding="utf-8")
        self.repository.create_incident({
            "incident_id": incident_id, "scenario": scenario_name,
            "status": WorkflowStatus.awaiting_approval.value,
            "before_source": source, "investigation": investigation.model_dump(mode="json"),
            "finding_valid": bool(findings) == scenario.ground_truth_finding,
            "expected_finding": scenario.ground_truth_finding,
            "detected_finding": bool(findings),
            "true_exploitability": scenario.ground_truth_exploitability,
            "predicted_exploitability": exploitability.classification,
        })
        self.repository.audit(
            incident_id, "security-finding-agent", "DeterministicSecurityScanner.scan", "scan_source",
            {"file": scenario.filename, "source_sha256": source_hash(source)},
            {"finding_id": finding.finding_id, "rule_id": finding.rule_id}, "finding_validated",
        )
        self.repository.audit(
            incident_id, "release-risk-agent", "ExploitabilityAgent.assess", "classify_and_propose",
            {"evidence_ids": exploitability.evidence_ids},
            {"exploitability": exploitability.classification, "risk_score": risk.score,
             "action_id": remediation.action_id}, "block_release_and_request_approval",
        )
        return self.get(incident_id)

    def approve(
        self,
        incident_id: str,
        request: ApprovalRequest,
        *,
        approved_by: str,
        approver_role: str,
    ) -> dict[str, Any]:
        if approver_role != "approver":
            raise WorkflowConflict("approval requires a verified approver identity")
        incident = self._required(incident_id)
        approval_states = {
            WorkflowStatus.awaiting_approval.value,
            WorkflowStatus.reapproval_required.value,
        }
        if incident["status"] not in approval_states:
            raise WorkflowConflict(f"incident is {incident['status']}, not awaiting approval")
        remediation = incident["investigation"]["remediation"]
        scenario = self.source_adapter.scenario(incident["scenario"])
        current_preview = RemediationAgent._diff(scenario.vulnerable_source, scenario.fixed_source)
        if (
            remediation["patch_sha256"] != source_hash(remediation["patch_preview"])
            or remediation["patch_sha256"] != source_hash(current_preview)
            or remediation["fixed_source_sha256"] != source_hash(scenario.fixed_source)
        ):
            raise WorkflowConflict("proposed remediation artifact changed before approval")
        new_status = WorkflowStatus.approved if request.approved else WorkflowStatus.rejected
        self.repository.record_approval(
            incident_id, request.approved, approved_by, approver_role, request.reason,
            remediation["action_id"], remediation["patch_sha256"], remediation["fixed_source_sha256"],
        )
        self.repository.update_status(incident_id, new_status.value)
        self.repository.audit(
            incident_id, approved_by, "approval-api", "review_remediation",
            {"reason": request.reason, "verified_role": approver_role},
            {"approved": request.approved, "action_id": remediation["action_id"],
             "patch_sha256": remediation["patch_sha256"],
             "fixed_source_sha256": remediation["fixed_source_sha256"]},
            new_status.value,
        )
        return self.get(incident_id)

    def remediate_and_validate(
        self,
        incident_id: str,
        *,
        executed_by: str,
        executor_role: str,
    ) -> dict[str, Any]:
        if executor_role != "executor":
            raise WorkflowConflict("remediation requires a verified executor identity")
        incident = self._required(incident_id)
        if incident["status"] != WorkflowStatus.approved.value:
            raise WorkflowConflict("remediation requires explicit approval")
        approval = incident.get("approval")
        if not approval or not approval["approved"]:
            raise WorkflowConflict("approved artifact attestation is missing")
        if approval["approved_by"] == executed_by:
            raise WorkflowConflict("approver and executor identities must be distinct")
        remediation = incident["investigation"]["remediation"]
        scenario = self.source_adapter.scenario(incident["scenario"])
        before = incident["before_source"]
        if source_hash(remediation["patch_preview"]) != approval.get("patch_sha256"):
            raise WorkflowConflict("persisted patch preview does not match the approved artifact hash")
        try:
            after = self.executor.apply(
                scenario,
                before,
                approved_action_id=approval.get("action_id") or "",
                expected_action_id=remediation["action_id"],
                approved_patch_sha256=approval.get("patch_sha256") or "",
                expected_patch_sha256=remediation["patch_sha256"],
                approved_fixed_source_sha256=approval.get("fixed_source_sha256") or "",
                expected_fixed_source_sha256=remediation["fixed_source_sha256"],
            )
        except ValueError as exc:
            raise WorkflowConflict(str(exc)) from exc
        if source_hash(after) != approval["fixed_source_sha256"]:
            raise WorkflowConflict("fixed source does not match the approved artifact hash")
        workspace_file = self._workspace_file(incident_id, scenario.filename)
        if not workspace_file.exists() or source_hash(workspace_file.read_text(encoding="utf-8")) != source_hash(before):
            raise WorkflowConflict("incident workspace changed after review; refusing to apply")
        self._atomic_write(workspace_file, after)

        findings_before = []
        findings_after = []
        validation_error: str | None = None
        try:
            findings_before = self.scanner.scan(scenario, before)
            findings_after = self.scanner.scan(scenario, after)
            checks = self.validator.validate(scenario, before, after)
        except Exception as exc:
            checks = {"validator_available": False}
            validation_error = type(exc).__name__
        risk_after = release_risk_after(checks)
        passed = (
            validation_error is None
            and all(checks.values())
            and len(findings_before) == 1
            and len(findings_after) == 0
        )
        validation = ValidationResult(
            incident_id=incident_id, passed=passed, checks=checks,
            findings_before=len(findings_before), findings_after=len(findings_after),
            source_hash_before=source_hash(before), source_hash_after=source_hash(after),
            release_risk_after=risk_after,
            summary=("Finding removed; syntax, public contract, safe construct, and regression guardrails passed"
                     if passed else "Remediation failed validation and the workspace was rolled back"),
        )
        final_status = WorkflowStatus.validated if passed else WorkflowStatus.validation_failed
        rolled_back = not passed
        if rolled_back:
            self._atomic_write(workspace_file, before)
        try:
            self.repository.record_validation_outcome(
                incident_id,
                validation.model_dump(mode="json"),
                status=final_status.value,
                after_source=after if passed else None,
                actor=executed_by,
                input_data={
                    "before_sha256": source_hash(before),
                    "finding_count": len(findings_before),
                    "verified_role": executor_role,
                    "approved_action_id": approval["action_id"],
                },
                output_data={
                    "attempted_after_sha256": source_hash(after),
                    "finding_count": len(findings_after),
                    "checks": checks,
                    "rolled_back": rolled_back,
                    "error_type": validation_error,
                },
                decision=(
                    WorkflowStatus.validated.value
                    if passed else "VALIDATION_FAILED_ROLLED_BACK"
                ),
            )
        except Exception:
            if passed:
                self._atomic_write(workspace_file, before)
            raise
        return self.get(incident_id)

    @staticmethod
    def _atomic_write(target: Path, content: str) -> None:
        temporary = target.with_name(f".{target.name}.{uuid4().hex}.tmp")
        try:
            temporary.write_text(content, encoding="utf-8")
            temporary.replace(target)
        finally:
            if temporary.exists():
                temporary.unlink()

    def _workspace_file(self, incident_id: str, filename: str) -> Path:
        target = (self.workspace_root / incident_id / filename).resolve()
        if self.workspace_root not in target.parents:
            raise WorkflowConflict("invalid workspace target")
        return target

    def get(self, incident_id: str) -> dict[str, Any]:
        record = self._required(incident_id)
        before, after = record.pop("before_source"), record.pop("after_source")
        record["source"] = {
            "before_sha256": source_hash(before),
            "after_sha256": source_hash(after) if after else None,
            "workspace": f"data/workspaces/{incident_id}/{record['investigation']['finding']['file']}",
        }
        return record

    def _required(self, incident_id: str) -> dict[str, Any]:
        record = self.repository.incident(incident_id)
        if not record:
            raise IncidentNotFound(incident_id)
        return record
