"""Deterministic scanner-to-CMDB asset correlation.

Confidence values are *rule confidences* attached to each documented matching rule, not
model outputs. Ambiguous or weak matches are never merged silently; they are routed to
human review.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.enterprise import Asset

RULES = {
    "defender_device_id": 0.99,
    "fqdn_exact": 0.97,
    "hostname_and_ip": 0.95,
    "hostname_unique": 0.9,
    "ip_only": 0.6,
}
AUTO_ACCEPT_THRESHOLD = 0.85


@dataclass
class MatchResult:
    status: str  # matched | ambiguous | unmatched
    asset_id: str | None
    confidence: float | None
    rule: str | None
    candidates: list[dict[str, object]] = field(default_factory=list)
    explanation: str = ""


def _candidate(a: Asset, rule: str) -> dict[str, object]:
    return {
        "asset_id": a.id,
        "hostname": a.hostname,
        "fqdn": a.fqdn,
        "ip_address": a.ip_address,
        "environment": a.environment,
        "operational_status": a.operational_status,
        "rule": rule,
    }


def correlate_asset(db: Session, identifier: str | None, ip: str | None = None, device_id: str | None = None) -> MatchResult:
    ident = (identifier or "").strip().lower()
    short = ident.split(".")[0] if ident else ""

    if device_id:
        hits = list(db.scalars(select(Asset).where(Asset.defender_device_id == device_id)))
        if len(hits) == 1:
            return MatchResult(
                "matched",
                hits[0].id,
                RULES["defender_device_id"],
                "defender_device_id",
                [_candidate(hits[0], "defender_device_id")],
                "Defender device id recorded on CMDB CI",
            )

    if ident and "." in ident:
        hits = list(db.scalars(select(Asset).where(func.lower(Asset.fqdn) == ident)))
        if len(hits) == 1:
            return MatchResult(
                "matched", hits[0].id, RULES["fqdn_exact"], "fqdn_exact", [_candidate(hits[0], "fqdn_exact")], "Exact FQDN match"
            )

    host_hits: list[Asset] = []
    if short:
        host_hits = list(
            db.scalars(select(Asset).where(or_(func.lower(Asset.hostname) == short, func.lower(Asset.hostname) == ident)))
        )
    if host_hits:
        if ip:
            both = [a for a in host_hits if a.ip_address == ip]
            if len(both) == 1:
                return MatchResult(
                    "matched",
                    both[0].id,
                    RULES["hostname_and_ip"],
                    "hostname_and_ip",
                    [_candidate(both[0], "hostname_and_ip")],
                    "Hostname and IP address agree",
                )
        if len(host_hits) == 1:
            return MatchResult(
                "matched",
                host_hits[0].id,
                RULES["hostname_unique"],
                "hostname_unique",
                [_candidate(host_hits[0], "hostname_unique")],
                "Unique hostname match",
            )
        return MatchResult(
            "ambiguous",
            None,
            round(1 / len(host_hits), 2),
            "hostname_multiple",
            [_candidate(a, "hostname_multiple") for a in host_hits],
            f"{len(host_hits)} CMDB records share hostname '{short}'; human review required",
        )

    if ip:
        ip_hits = list(db.scalars(select(Asset).where(Asset.ip_address == ip)))
        if len(ip_hits) == 1:
            # An IP-only match is below the auto-accept threshold (DHCP reuse, NAT).
            return MatchResult(
                "ambiguous",
                None,
                RULES["ip_only"],
                "ip_only",
                [_candidate(ip_hits[0], "ip_only")],
                "Only the IP address matches; requires confirmation",
            )
        if len(ip_hits) > 1:
            return MatchResult(
                "ambiguous",
                None,
                round(1 / len(ip_hits), 2),
                "ip_multiple",
                [_candidate(a, "ip_multiple") for a in ip_hits],
                "Multiple CMDB records share this IP",
            )

    return MatchResult("unmatched", None, None, None, [], "No CMDB record matches the scanner identifiers")
