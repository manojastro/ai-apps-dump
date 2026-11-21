"""Load and validate the control matrix. A typo in the YAML fails loudly at load time."""

import hashlib
import json
from decimal import Decimal
from pathlib import Path
from typing import Literal, Self

import yaml
from pydantic import Field, model_validator

from invoiceflow.core.findings import Finding, FindingReason
from invoiceflow.core.matcher import MatchParams
from invoiceflow.core.tolerance import ToleranceParams
from invoiceflow.data.models import Action, ExceptionCode, Frozen, Money, Role

DEFAULT_MATRIX_PATH = Path(__file__).resolve().parents[3] / "policy" / "control_matrix.yaml"


class ToleranceSpec(Frozen):
    price_variance_max_pct: Decimal
    price_variance_max_amount: Money
    source: str


class DuplicateSpec(Frozen):
    near_duplicate_window_days: int = Field(ge=0)
    source: str


class GstSpec(Frozen):
    tax_amount_tolerance: Money
    source: str


class ApprovalLimit(Frozen):
    role: Role
    max_gross_value: Money | None


class ExceptionPolicy(Frozen):
    allowed_actions: tuple[Action, ...] = Field(min_length=1)
    default_action: Action
    default_action_by_reason: dict[FindingReason, Action] = Field(default_factory=dict)
    required_role: Role | None = None
    requires_out_of_band_verification: bool = False
    source: str

    @model_validator(mode="after")
    def _defaults_are_allowed(self) -> Self:
        for action in (self.default_action, *self.default_action_by_reason.values()):
            if action not in self.allowed_actions:
                raise ValueError(f"default action {action} is not in allowed_actions")
        return self


class RuleSpec(Frozen):
    id: str = Field(pattern=r"^CM-[0-9]{2}$")
    title: str
    source: str


class ControlMatrix(Frozen):
    version: int
    synthetic: Literal[True]
    currency: Literal["INR"]
    tolerance: ToleranceSpec
    duplicates: DuplicateSpec
    gst: GstSpec
    approver_hierarchy: tuple[Role, ...] = Field(min_length=1)
    never_approve: tuple[Role, ...]
    approval_limits: tuple[ApprovalLimit, ...] = Field(min_length=1)
    actions_without_approval: tuple[Action, ...]
    exceptions: dict[ExceptionCode, ExceptionPolicy]
    minimum_role_by_action: dict[Action, Role] = Field(default_factory=dict)
    rules: tuple[RuleSpec, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        missing = set(ExceptionCode) - set(self.exceptions)
        if missing:
            raise ValueError(f"exceptions missing from matrix: {sorted(missing)}")
        if set(self.approver_hierarchy) & set(self.never_approve):
            raise ValueError("a role cannot be both an approver and never_approve")
        limit_roles = [limit.role for limit in self.approval_limits]
        if limit_roles != list(self.approver_hierarchy):
            raise ValueError("approval_limits must list approver_hierarchy roles in order")
        caps = [limit.max_gross_value for limit in self.approval_limits]
        if caps[-1] is not None or any(cap is None for cap in caps[:-1]):
            raise ValueError("only the last approval limit may be unlimited (null)")
        bounded = [cap for cap in caps if cap is not None]
        if bounded != sorted(bounded):
            raise ValueError("approval limits must increase")
        ids = [rule.id for rule in self.rules]
        if len(ids) != len(set(ids)):
            raise ValueError("rule ids must be unique")
        return self

    @property
    def version_hash(self) -> str:
        """SHA-256 of the matrix content (not its comments or layout)."""
        canonical = json.dumps(self.model_dump(mode="json"), sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def rule(self, rule_id: str) -> RuleSpec:
        return next(rule for rule in self.rules if rule.id == rule_id)

    def rank(self, role: Role) -> int:
        """Position in the approver hierarchy, or -1 for roles that never approve."""
        return self.approver_hierarchy.index(role) if role in self.approver_hierarchy else -1

    def role_for_value(self, gross_value: Decimal) -> Role:
        for limit in self.approval_limits:
            if limit.max_gross_value is None or gross_value <= limit.max_gross_value:
                return limit.role
        raise AssertionError("unreachable: the last approval limit is unlimited")

    def match_params(self) -> MatchParams:
        return MatchParams(
            tolerance=ToleranceParams(
                max_pct=self.tolerance.price_variance_max_pct,
                max_amount=self.tolerance.price_variance_max_amount,
            ),
            near_duplicate_window_days=self.duplicates.near_duplicate_window_days,
            tax_amount_tolerance=self.gst.tax_amount_tolerance,
        )

    def default_action(self, primary: ExceptionCode, findings: tuple[Finding, ...]) -> Action:
        policy = self.exceptions[primary]
        for finding in findings:
            if finding.code is primary and finding.reason in policy.default_action_by_reason:
                return policy.default_action_by_reason[finding.reason]
        return policy.default_action


def load_matrix(path: Path = DEFAULT_MATRIX_PATH) -> ControlMatrix:
    with path.open(encoding="utf-8") as handle:
        return ControlMatrix.model_validate(yaml.safe_load(handle))
