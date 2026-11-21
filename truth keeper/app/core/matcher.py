"""Link records for the same customer across systems.

The CRM account is the anchor (customer_key = CRM account id). For every billing and
marketing record we try, in order:
  1. id                - the record carries a CRM account reference          (confidence 1.0)
  2. email             - normalised email equals the CRM email               (confidence 0.95)
  3. fuzzy_name_domain - same email domain and name similarity >= threshold  (confidence 0.9 * similarity)
Records that match nothing are returned as unmatched (never silently dropped).

strategy="name_only" exists only for the debugging exercise in the build guide: it links on
normalised name alone and shows why that is a bad idea (name collisions across companies).
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from difflib import SequenceMatcher

from app.core.models import CustomerRecord, MatchLink, System, UnifiedCustomer
from app.core.normalize import email_domain

FUZZY_THRESHOLD = 0.88


@dataclass
class MatchResult:
    customers: list[UnifiedCustomer]
    unmatched: dict[str, list[CustomerRecord]] = field(default_factory=dict)

    def method_counts(self) -> dict[str, int]:
        counts: dict[str, int] = defaultdict(int)
        for c in self.customers:
            for link in c.billing + c.marketing:
                counts[f"{link.record.system.value}:{link.method}"] += 1
        return dict(sorted(counts.items()))


def name_similarity(a: str | None, b: str | None) -> float:
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    return SequenceMatcher(None, a, b).ratio()


class _Index:
    def __init__(self, crm: list[CustomerRecord]):
        self.by_id = {r.record_id: r for r in crm}
        self.by_email: dict[str, CustomerRecord] = {}
        self.by_domain: dict[str, list[CustomerRecord]] = defaultdict(list)
        self.by_name: dict[str, list[CustomerRecord]] = defaultdict(list)
        for r in crm:
            if r.email:
                self.by_email.setdefault(r.email, r)
                dom = email_domain(r.email)
                if dom:
                    self.by_domain[dom].append(r)
            if r.name:
                self.by_name[r.name].append(r)

    def link(self, rec: CustomerRecord, strategy: str) -> tuple[CustomerRecord, MatchLink] | None:
        if strategy == "name_only":
            cands = self.by_name.get(rec.name or "", [])
            if cands:  # deliberately naive: first account with that name wins
                return cands[0], MatchLink(record=rec, method="name_only", confidence=0.5)
            return None
        if rec.crm_account_id and rec.crm_account_id in self.by_id:
            return self.by_id[rec.crm_account_id], MatchLink(record=rec, method="id", confidence=1.0)
        if rec.email and rec.email in self.by_email:
            return self.by_email[rec.email], MatchLink(record=rec, method="email", confidence=0.95)
        dom = email_domain(rec.email)
        if dom and rec.name:
            scored = sorted(
                ((name_similarity(rec.name, c.name), c.record_id, c) for c in self.by_domain.get(dom, [])),
                key=lambda t: (-t[0], t[1]),
            )
            if scored and scored[0][0] >= FUZZY_THRESHOLD:
                # refuse ambiguous fuzzy matches (two candidates equally good)
                if len(scored) > 1 and scored[1][0] == scored[0][0]:
                    return None
                sim, _, crm = scored[0]
                return crm, MatchLink(record=rec, method="fuzzy_name_domain", confidence=round(0.9 * sim, 3))
        return None


def match(crm: list[CustomerRecord], billing: list[CustomerRecord], marketing: list[CustomerRecord],
          strategy: str = "default") -> MatchResult:
    index = _Index(crm)
    customers = {r.record_id: UnifiedCustomer(customer_key=r.record_id, crm=r) for r in crm}
    unmatched: dict[str, list[CustomerRecord]] = {System.BILLING.value: [], System.MARKETING.value: []}
    for system, records in ((System.BILLING, billing), (System.MARKETING, marketing)):
        for rec in records:
            hit = index.link(rec, strategy)
            if hit is None:
                unmatched[system.value].append(rec)
                continue
            crm_rec, link = hit
            target = customers[crm_rec.record_id]
            (target.billing if system == System.BILLING else target.marketing).append(link)
    return MatchResult(customers=list(customers.values()), unmatched=unmatched)
