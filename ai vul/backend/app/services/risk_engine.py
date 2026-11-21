"""Deterministic, explainable risk scoring.

The LLM never computes the authoritative score. This module does, from normalised inputs,
under a versioned and configurable policy. The default weights are a *demonstration
policy*, not an industry standard.

Missing data handling
---------------------
A missing factor is never silently scored as zero. For every missing factor the policy
imputes ``missing_factor_assumption`` x max points (default 50 %), reports the factor as
missing, and publishes an uncertainty band:

* ``score_lower`` - known factors only (missing = 0)
* ``score_upper`` - missing factors at their maximum
* ``coverage``    - share of the 100 points backed by real data

Low coverage forces human review.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any

from pydantic import BaseModel, Field, model_validator

POLICY_NAME = "aegis-demo-risk-policy"


class EpssBand(BaseModel):
    min_probability: float = Field(ge=0, le=1)
    points_fraction: float = Field(ge=0, le=1)


class RiskPolicy(BaseModel):
    """Configurable policy. Weights must total 100."""

    version: int = 1
    weights: dict[str, int] = Field(
        default_factory=lambda: {"cvss": 25, "epss": 25, "kev": 25, "asset_criticality": 15, "internet_exposure": 10}
    )
    epss_bands: list[EpssBand] = Field(
        default_factory=lambda: [
            EpssBand(min_probability=0.5, points_fraction=1.0),
            EpssBand(min_probability=0.1, points_fraction=0.7),
            EpssBand(min_probability=0.01, points_fraction=0.35),
            EpssBand(min_probability=0.0, points_fraction=0.1),
        ]
    )
    criticality_fractions: dict[str, float] = Field(
        default_factory=lambda: {"critical": 1.0, "high": 0.75, "medium": 0.45, "low": 0.2}
    )
    level_thresholds: dict[str, int] = Field(default_factory=lambda: {"critical": 85, "high": 70, "medium": 40})
    priority_by_level: dict[str, str] = Field(
        default_factory=lambda: {"critical": "P1", "high": "P2", "medium": "P3", "low": "P4"}
    )
    sla_days: dict[str, int] = Field(default_factory=lambda: {"P1": 7, "P2": 30, "P3": 90, "P4": 180})
    missing_factor_assumption: float = Field(default=0.5, ge=0, le=1)
    min_coverage_for_auto_routing: float = Field(default=0.75, ge=0, le=1)

    @model_validator(mode="after")
    def _check(self) -> RiskPolicy:
        required = {"cvss", "epss", "kev", "asset_criticality", "internet_exposure"}
        if set(self.weights) != required:
            raise ValueError(f"weights must define exactly {sorted(required)}")
        if sum(self.weights.values()) != 100:
            raise ValueError("weights must sum to 100")
        if any(w < 0 for w in self.weights.values()):
            raise ValueError("weights must be non-negative")
        t = self.level_thresholds
        if not (100 >= t["critical"] > t["high"] > t["medium"] >= 0):
            raise ValueError("thresholds must be strictly decreasing: critical > high > medium")
        self.epss_bands = sorted(self.epss_bands, key=lambda b: b.min_probability, reverse=True)
        return self

    @property
    def policy_version(self) -> str:
        digest = hashlib.sha256(json.dumps(self.model_dump(), sort_keys=True).encode()).hexdigest()[:8]
        return f"{POLICY_NAME}-v{self.version}-{digest}"


@dataclass
class RiskInputs:
    """Normalised inputs. ``None`` always means *unknown*, never *safe*."""

    cvss_score: float | None
    epss_probability: float | None
    kev_listed: bool | None
    asset_criticality: str | None
    internet_exposed: bool | None
    service_criticality: str | None = None
    environment: str | None = None
    sources: dict[str, str] = field(default_factory=dict)


@dataclass
class FactorResult:
    name: str
    label: str
    max_points: float
    points: float
    available: bool
    input_value: Any
    explanation: str
    source: str | None = None


@dataclass
class RiskResult:
    score: int
    score_lower: int
    score_upper: int
    risk_level: str
    priority: str
    business_impact: str
    coverage: float
    policy_version: str
    factors: dict[str, FactorResult]
    missing_factors: list[str]
    requires_immediate_review: bool
    rationale: list[str]
    sla_days: int

    def factors_dict(self) -> dict[str, Any]:
        return {k: asdict(v) for k, v in self.factors.items()}


def _r(x: float) -> float:
    return round(x, 2)


def score_cvss(policy: RiskPolicy, cvss: float | None) -> FactorResult:
    max_pts = policy.weights["cvss"]
    if cvss is None:
        return FactorResult("cvss", "CVSS base severity", max_pts, 0, False, None, "CVSS base score unavailable")
    if not 0 <= cvss <= 10:
        raise ValueError(f"CVSS score out of range: {cvss}")
    pts = _r(cvss / 10 * max_pts)
    return FactorResult("cvss", "CVSS base severity", max_pts, pts, True, cvss, f"CVSS {cvss}/10 x {max_pts} pts = {pts}")


def score_epss(policy: RiskPolicy, epss: float | None) -> FactorResult:
    max_pts = policy.weights["epss"]
    if epss is None:
        return FactorResult("epss", "EPSS exploitation probability", max_pts, 0, False, None, "EPSS probability unavailable")
    if not 0 <= epss <= 1:
        raise ValueError(f"EPSS probability out of range: {epss}")
    band = next(b for b in policy.epss_bands if epss >= b.min_probability)
    pts = _r(band.points_fraction * max_pts)
    return FactorResult(
        "epss",
        "EPSS exploitation probability",
        max_pts,
        pts,
        True,
        epss,
        f"EPSS {epss:.4f} falls in band >= {band.min_probability} -> {band.points_fraction:.0%} of {max_pts} pts "
        "(probability estimate, not proof of exploitation)",
    )


def score_kev(policy: RiskPolicy, kev: bool | None) -> FactorResult:
    max_pts = policy.weights["kev"]
    if kev is None:
        return FactorResult(
            "kev", "CISA KEV (confirmed exploitation)", max_pts, 0, False, None, "KEV status could not be verified"
        )
    pts = float(max_pts) if kev else 0.0
    text = "Listed in CISA KEV: exploitation confirmed in the wild" if kev else "Checked: not listed in CISA KEV"
    return FactorResult("kev", "CISA KEV (confirmed exploitation)", max_pts, pts, True, kev, text)


def score_criticality(policy: RiskPolicy, criticality: str | None) -> FactorResult:
    max_pts = policy.weights["asset_criticality"]
    if not criticality or criticality not in policy.criticality_fractions:
        return FactorResult(
            "asset_criticality",
            "Asset business criticality",
            max_pts,
            0,
            False,
            criticality,
            "Asset criticality unknown (no reliable CMDB match)",
        )
    frac = policy.criticality_fractions[criticality]
    pts = _r(frac * max_pts)
    return FactorResult(
        "asset_criticality",
        "Asset business criticality",
        max_pts,
        pts,
        True,
        criticality,
        f"{criticality} asset -> {frac:.0%} of {max_pts} pts",
    )


def score_exposure(policy: RiskPolicy, exposed: bool | None) -> FactorResult:
    max_pts = policy.weights["internet_exposure"]
    if exposed is None:
        return FactorResult("internet_exposure", "Internet exposure", max_pts, 0, False, None, "Internet exposure unknown")
    pts = float(max_pts) if exposed else 0.0
    return FactorResult(
        "internet_exposure",
        "Internet exposure",
        max_pts,
        pts,
        True,
        exposed,
        "Internet-facing asset" if exposed else "Not internet-facing",
    )


def classify(policy: RiskPolicy, score: int) -> str:
    t = policy.level_thresholds
    if score >= t["critical"]:
        return "critical"
    if score >= t["high"]:
        return "high"
    if score >= t["medium"]:
        return "medium"
    return "low"


def business_impact(asset_criticality: str | None, service_criticality: str | None, environment: str | None) -> str:
    rank = {"critical": 3, "high": 2, "medium": 1, "low": 0}
    best = max(rank.get(asset_criticality or "", -1), rank.get(service_criticality or "", -1))
    if best < 0:
        return "unknown"
    if environment in ("development", "test") and best > 0:
        best -= 1  # non-production copies carry less direct business impact
    return {3: "high", 2: "high", 1: "medium", 0: "low"}[best]


def calculate_risk(inputs: RiskInputs, policy: RiskPolicy | None = None) -> RiskResult:
    policy = policy or RiskPolicy()
    factors = {
        f.name: f
        for f in (
            score_cvss(policy, inputs.cvss_score),
            score_epss(policy, inputs.epss_probability),
            score_kev(policy, inputs.kev_listed),
            score_criticality(policy, inputs.asset_criticality),
            score_exposure(policy, inputs.internet_exposed),
        )
    }
    for name, f in factors.items():
        f.source = inputs.sources.get(name)
    known = sum(f.points for f in factors.values() if f.available)
    missing = [f.name for f in factors.values() if not f.available]
    missing_max = sum(f.max_points for f in factors.values() if not f.available)
    imputed = missing_max * policy.missing_factor_assumption
    score = round(known + imputed)
    lower, upper = round(known), round(known + missing_max)
    coverage = round(1 - missing_max / 100, 2)
    level = classify(policy, score)
    priority = policy.priority_by_level[level]
    impact = business_impact(inputs.asset_criticality, inputs.service_criticality, inputs.environment)

    rationale = [f"{f.label}: {f.explanation}" for f in factors.values()]
    if missing:
        rationale.append(
            f"Missing factors {missing} imputed at {policy.missing_factor_assumption:.0%} of max "
            f"({imputed:.1f} pts); true score lies in [{lower}, {upper}]"
        )
    review = level == "critical" or bool(inputs.kev_listed) or coverage < policy.min_coverage_for_auto_routing
    if coverage < policy.min_coverage_for_auto_routing:
        rationale.append(f"Coverage {coverage:.0%} below {policy.min_coverage_for_auto_routing:.0%}: human review required")
    return RiskResult(
        score=score,
        score_lower=lower,
        score_upper=upper,
        risk_level=level,
        priority=priority,
        business_impact=impact,
        coverage=coverage,
        policy_version=policy.policy_version,
        factors=factors,
        missing_factors=missing,
        requires_immediate_review=review,
        rationale=rationale,
        sla_days=policy.sla_days[priority],
    )
