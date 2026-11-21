"""Synthetic data generator: three fake SaaS systems with planted, known conflicts.

Usage:
    python -m data.generator.generate --seed 42 --n 500
    python -m data.generator.generate --seed 7 --n 500 --profile hard \
        --out data/generated_seed7 --gt data/generated_seed7/ground_truth.json

Writes crm.db, billing.db and marketing.db into --out, plus a ground-truth JSON that lists
every planted conflict with its expected fix, and a manifest of the noise patterns added.
All names, emails and companies are synthetic (".example" domains). Same seed -> same bytes.
"""

from __future__ import annotations

import argparse
import json
import random
import sqlite3
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

from app.core.catalog import PLAN_PRICES, PLANS

ROOT = Path(__file__).resolve().parents[2]
AS_OF = date(2026, 11, 1)  # fixed "today" of the synthetic world, so runs are reproducible

CONFLICT_RATES = {
    "CANCELLED_BUT_BILLING_ACTIVE": 0.04,
    "PLAN_MISMATCH": 0.05,
    "CHURNED_STILL_MARKETED": 0.04,
    "EMAIL_MISMATCH": 0.04,
    "DUPLICATE_CUSTOMER": 0.03,
    "PAST_DUE_BUT_CRM_ACTIVE": 0.04,
}
EXPECTED_FIX = {
    "CANCELLED_BUT_BILLING_ACTIVE": "cancel_subscription",
    "PLAN_MISMATCH": "update_crm_plan",
    "CHURNED_STILL_MARKETED": "unsubscribe_contact",
    "EMAIL_MISMATCH": "flag_for_finance_review",
    "DUPLICATE_CUSTOMER": "merge_billing_duplicates",
    "PAST_DUE_BUT_CRM_ACTIVE": "flag_for_finance_review",
}
NEEDS_CANCELLED = {"CANCELLED_BUT_BILLING_ACTIVE", "CHURNED_STILL_MARKETED"}

PROFILES = {
    "default": dict(
        no_ref_rate=0.15, email_noise_rate=0.20, plan_case_rate=0.15, short_past_due_rate=0.04,
        accents=False, last_first_rate=0.0, plus_tag_rate=0.0, upper_domain_rate=0.0,
        boundary_past_due_rate=0.0, plan_alias_rate=0.0,
    ),
    "hard": dict(
        no_ref_rate=0.40, email_noise_rate=0.35, plan_case_rate=0.30, short_past_due_rate=0.06,
        accents=True, last_first_rate=0.25, plus_tag_rate=0.10, upper_domain_rate=0.15,
        boundary_past_due_rate=0.03, plan_alias_rate=0.10,
    ),
}

FIRST = [
    "Ava", "Liam", "Maya", "Noah", "Zara", "Ethan", "Priya", "Lucas", "Amara", "Oliver", "Hana", "Mateo",
    "Chloe", "Arjun", "Elena", "Kai", "Nadia", "Leo", "Sofia", "Omar", "Iris", "Felix", "Leila", "Jonas",
    "Mei", "Theo", "Anya", "Ravi", "Clara", "Diego", "Freya", "Samir", "Lena", "Tomas", "Yara", "Ivan",
]
LAST = [
    "Patel", "Nguyen", "Okafor", "Schmidt", "Rossi", "Kowalski", "Tanaka", "Silva", "Haddad", "Larsen",
    "Moreau", "Novak", "Mensah", "Ibrahim", "Fischer", "Costa", "Varga", "Lindqvist", "Reyes", "Sato",
    "Duarte", "Brennan", "Kaur", "Petrov", "Achebe", "Romero", "Holm", "Yilmaz", "Dubois", "Marsh",
]
ACCENTED = {"Elena": "Eléna", "Sofia": "Sofía", "Tomas": "Tomás", "Iris": "Íris", "Costa": "Côsta",
            "Moreau": "Moréau", "Reyes": "Reyés", "Dubois": "Dubóis", "Yilmaz": "Yılmaz", "Zara": "Zára"}
COMPANY_A = [
    "Northwind", "Bluepeak", "Granite", "Lumen", "Cobalt", "Harbor", "Juniper", "Vertex", "Saffron", "Tidal",
    "Ember", "Quarry", "Willow", "Orbit", "Maple", "Falcon", "Copper", "Meridian", "Aspen", "Nimbus",
    "Basalt", "Coral", "Drift", "Fjord", "Glade", "Helix", "Indigo", "Kestrel", "Lantern", "Mosaic",
]
COMPANY_B = ["labs", "logistics", "health", "analytics", "foods", "studio", "systems", "retail"]
OWNERS = ["rep.alpha", "rep.bravo", "rep.charlie", "rep.delta", "rep.echo", "rep.foxtrot"]
CAMPAIGNS_ACTIVE = ["newsletter_oct", "product_update_q4", "webinar_invite"]


@dataclass
class Person:
    idx: int
    account_id: str
    first: str
    last: str
    domain: str
    email: str
    status: str = "active"
    plan: str = "starter"
    currency: str = "USD"
    conflict: str | None = None
    noise: list[str] = field(default_factory=list)

    @property
    def name(self) -> str:
        return f"{self.first} {self.last}"


def _weighted(rng: random.Random, options: dict[str, float]) -> str:
    keys = list(options)
    return rng.choices(keys, weights=[options[k] for k in keys], k=1)[0]


def _noisy_email(rng: random.Random, email: str, prof: dict, person: Person) -> str:
    """Return a variant of email that normalises back to the same value (noise, not conflict)."""
    local, domain = email.split("@")
    out_local, out_domain = local, domain
    if rng.random() < prof["email_noise_rate"]:
        out_local = out_local.title() if rng.random() < 0.5 else out_local.upper()
        person.noise.append("email_case_or_space")
    if rng.random() < prof["upper_domain_rate"]:
        out_domain = out_domain.upper()
        person.noise.append("email_upper_domain")
    if rng.random() < prof["plus_tag_rate"]:
        out_local = f"{out_local}+billing"
        person.noise.append("email_plus_addressing")
    result = f"{out_local}@{out_domain}"
    if "email_case_or_space" in person.noise and rng.random() < 0.5:
        result = f"  {result} "
    return result


def _noisy_plan(rng: random.Random, plan: str, prof: dict, person: Person) -> str:
    if rng.random() < prof["plan_alias_rate"] and plan == "pro":
        person.noise.append("plan_alias")
        return "Professional"
    if rng.random() < prof["plan_case_rate"]:
        person.noise.append("plan_case_or_space")
        return f"{plan.title()} " if rng.random() < 0.5 else plan.upper()
    return plan


def build_people(rng: random.Random, n: int, prof: dict) -> list[Person]:
    companies = [f"{a.lower()}-{b}.example" for a in COMPANY_A for b in COMPANY_B]
    rng.shuffle(companies)
    companies = companies[: max(20, n // 2)]
    seen_name_domain: set[tuple[str, str]] = set()
    seen_email: set[str] = set()
    people: list[Person] = []
    for i in range(n):
        while True:
            first, last, domain = rng.choice(FIRST), rng.choice(LAST), rng.choice(companies)
            if (first, last, domain) not in seen_name_domain:
                break
        seen_name_domain.add((first, last, domain))
        email = f"{first}.{last}@{domain}".lower()
        k = 2
        while email in seen_email:
            email = f"{first}.{last}{k}@{domain}".lower()
            k += 1
        seen_email.add(email)
        p = Person(idx=i, account_id=f"ACC-{i + 1:05d}", first=first, last=last, domain=domain, email=email)
        if prof["accents"] and (first in ACCENTED or last in ACCENTED) and rng.random() < 0.7:
            p.first, p.last = ACCENTED.get(first, first), ACCENTED.get(last, last)
            p.noise.append("accented_name_in_crm")
        people.append(p)
    return people


def assign_statuses(rng: random.Random, people: list[Person]) -> None:
    n = len(people)
    order = list(range(n))
    rng.shuffle(order)
    cursor = 0
    for ctype, rate in CONFLICT_RATES.items():
        count = round(n * rate)
        for j in order[cursor: cursor + count]:
            people[j].conflict = ctype
        cursor += count
    for p in people:
        p.plan = _weighted(rng, {"starter": 0.4, "growth": 0.3, "pro": 0.2, "enterprise": 0.1})
        p.currency = _weighted(rng, {"USD": 0.8, "EUR": 0.12, "GBP": 0.08})
        if p.conflict in NEEDS_CANCELLED:
            p.status = "cancelled"
        elif p.conflict:
            p.status = "active"
        else:
            p.status = _weighted(rng, {"active": 0.78, "trial": 0.10, "cancelled": 0.12})


def _create_schema(crm: sqlite3.Connection, billing: sqlite3.Connection, mkt: sqlite3.Connection) -> None:
    crm.execute(
        "CREATE TABLE accounts (id TEXT PRIMARY KEY, name TEXT, email TEXT, status TEXT, plan TEXT,"
        " owner TEXT, created_at TEXT)"
    )
    billing.execute(
        "CREATE TABLE customers (customer_id TEXT PRIMARY KEY, crm_account_id TEXT, name TEXT, email TEXT,"
        " created_at TEXT, merged_into TEXT)"
    )
    billing.execute(
        "CREATE TABLE subscriptions (subscription_id TEXT PRIMARY KEY, customer_id TEXT REFERENCES"
        " customers(customer_id), plan TEXT, status TEXT, monthly_amount REAL, currency TEXT,"
        " next_charge_date TEXT, past_due_since TEXT)"
    )
    billing.execute(
        "CREATE TABLE review_flags (flag_id TEXT PRIMARY KEY, conflict_id TEXT UNIQUE, customer_key TEXT,"
        " action_reason TEXT, created_at TEXT, status TEXT)"
    )
    billing.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT)")
    mkt.execute(
        "CREATE TABLE contacts (contact_id TEXT PRIMARY KEY, email TEXT, name TEXT, lifecycle_stage TEXT,"
        " subscribed INTEGER, last_campaign TEXT)"
    )


def generate(seed: int = 42, n: int = 500, out_dir: Path | None = None, gt_path: Path | None = None,
             profile: str = "default") -> dict:
    prof = PROFILES[profile]
    rng = random.Random(seed)
    out_dir = Path(out_dir or ROOT / "data" / "generated")
    gt_path = Path(gt_path or ROOT / "data" / "generator" / "ground_truth.json")
    out_dir.mkdir(parents=True, exist_ok=True)
    gt_path.parent.mkdir(parents=True, exist_ok=True)
    for name in ("crm.db", "billing.db", "marketing.db"):
        (out_dir / name).unlink(missing_ok=True)

    people = build_people(rng, n, prof)
    assign_statuses(rng, people)
    all_crm_emails = {p.email for p in people}
    used_billing_emails: set[str] = set()

    crm_rows, cust_rows, sub_rows, contact_rows, truth = [], [], [], [], []
    bc = 0  # billing customer counter
    mc = 0  # marketing contact counter

    def new_billing(p: Person, email: str, name: str, plan: str, status: str, with_ref: bool,
                    next_charge: str | None, past_due_since: str | None, amount: float) -> tuple[str, str]:
        nonlocal bc
        bc += 1
        cid, sid = f"BC-{bc:05d}", f"SUB-{bc:05d}"
        created = (AS_OF - timedelta(days=rng.randint(30, 900))).isoformat()
        cust_rows.append((cid, p.account_id if with_ref else None, name, email, created, None))
        sub_rows.append((sid, cid, plan, status, amount, p.currency, next_charge, past_due_since))
        return cid, sid

    for p in people:
        crm_rows.append((p.account_id, p.name, p.email, p.status, p.plan, rng.choice(OWNERS),
                         (AS_OF - timedelta(days=rng.randint(30, 1000))).isoformat()))
        with_ref = rng.random() >= prof["no_ref_rate"]
        if not with_ref:
            p.noise.append("billing_without_crm_ref")
        billing_name = p.name
        if prof["accents"] and "accented_name_in_crm" in p.noise:
            billing_name = f"{p.first} {p.last}".translate(str.maketrans("éíóúáôı", "eiouaoi"))
        if not with_ref and rng.random() < prof["last_first_rate"]:
            billing_name = f"{p.last.upper()}, {p.first}"
            p.noise.append("billing_name_last_first")
        next_charge = (AS_OF + timedelta(days=rng.randint(1, 28))).isoformat()
        price = PLAN_PRICES[p.plan]
        entry = {"customer_key": p.account_id, "type": p.conflict, "expected_fix": EXPECTED_FIX.get(p.conflict)}

        if p.status == "trial":
            p.noise.append("trial_without_billing")
        elif p.status == "cancelled":
            if p.conflict == "CANCELLED_BUT_BILLING_ACTIVE":
                _, sid = new_billing(p, _noisy_email(rng, p.email, prof, p), billing_name,
                                     _noisy_plan(rng, p.plan, prof, p), "active", with_ref, next_charge, None, price)
                entry["expected_params"] = {"subscription_id": sid}
            else:
                new_billing(p, _noisy_email(rng, p.email, prof, p), billing_name, p.plan, "cancelled", with_ref,
                            None, None, price)
        else:  # active
            status, past_due_since = "active", None
            billing_plan = p.plan
            billing_email = _noisy_email(rng, p.email, prof, p)
            amount = price
            if p.conflict == "PLAN_MISMATCH":
                billing_plan = rng.choice([x for x in PLANS if x != p.plan])
                amount = PLAN_PRICES[billing_plan]
                entry["expected_params"] = {"account_id": p.account_id, "new_plan": billing_plan}
            elif p.conflict == "PAST_DUE_BUT_CRM_ACTIVE":
                status = "past_due"
                past_due_since = (AS_OF - timedelta(days=rng.randint(31, 90))).isoformat()
            elif p.conflict == "EMAIL_MISMATCH":
                variants = [f"{p.first[0]}{p.last}", "billing", "accounts", f"{p.first}.{p.last}.finance",
                            f"{p.first}{p.last[0]}"]
                rng.shuffle(variants)
                for v in variants:
                    candidate = f"{v}@{p.domain}".lower()
                    if candidate not in all_crm_emails and candidate not in used_billing_emails:
                        billing_email = candidate
                        break
                else:  # pragma: no cover - extremely unlikely with the variant list above
                    raise RuntimeError("could not plant EMAIL_MISMATCH")
                used_billing_emails.add(billing_email)
            elif p.conflict is None and rng.random() < prof["short_past_due_rate"]:
                status = "past_due"
                past_due_since = (AS_OF - timedelta(days=rng.randint(3, 29))).isoformat()
                p.noise.append("past_due_under_threshold")
            elif p.conflict is None and rng.random() < prof["boundary_past_due_rate"]:
                status = "past_due"
                past_due_since = (AS_OF - timedelta(days=30)).isoformat()
                p.noise.append("past_due_exactly_threshold")
            plan_out = billing_plan if p.conflict == "PLAN_MISMATCH" else _noisy_plan(rng, billing_plan, prof, p)
            cid, sid = new_billing(p, billing_email, billing_name, plan_out, status, with_ref,
                                   next_charge if status == "active" else None, past_due_since, amount)
            if p.conflict == "PAST_DUE_BUT_CRM_ACTIVE":
                entry["expected_params"] = {}
            if p.conflict == "EMAIL_MISMATCH":
                entry["expected_params"] = {}
                entry["planted_billing_email"] = billing_email
                entry["billing_has_crm_ref"] = with_ref
            if p.conflict == "DUPLICATE_CUSTOMER":
                dup_email = _noisy_email(rng, p.email, prof, p)
                dup_cid, _ = new_billing(p, dup_email, billing_name, p.plan, "active", False,
                                         (AS_OF + timedelta(days=rng.randint(1, 28))).isoformat(), None, price)
                entry["expected_params"] = {"keep_customer_id": cid, "remove_customer_id": dup_cid}

        # marketing
        if p.status == "trial":
            stage, subscribed, campaign = "onboarding", 1, "onboarding_day3"
        elif p.status == "cancelled":
            if p.conflict == "CHURNED_STILL_MARKETED":
                stage, subscribed, campaign = "onboarding", 1, "onboarding_day7"
            elif rng.random() < 0.3:
                stage = None
                p.noise.append("cancelled_without_marketing_contact")
            else:
                stage, subscribed, campaign = "churned", 0, rng.choice(["winback_q3", None])
        else:
            stage, subscribed, campaign = "customer", int(rng.random() < 0.6), rng.choice(CAMPAIGNS_ACTIVE)
        if stage is not None:
            mc += 1
            contact_id = f"MC-{mc:05d}"
            contact_rows.append((contact_id, _noisy_email(rng, p.email, prof, p), p.name, stage, subscribed,
                                 campaign))
            if p.conflict == "CHURNED_STILL_MARKETED":
                entry["expected_params"] = {"contact_id": contact_id}

        if p.conflict:
            truth.append(entry)

    crm = sqlite3.connect(out_dir / "crm.db")
    billing = sqlite3.connect(out_dir / "billing.db")
    mkt = sqlite3.connect(out_dir / "marketing.db")
    try:
        _create_schema(crm, billing, mkt)
        crm.executemany("INSERT INTO accounts VALUES (?,?,?,?,?,?,?)", crm_rows)
        billing.executemany("INSERT INTO customers VALUES (?,?,?,?,?,?)", cust_rows)
        billing.executemany("INSERT INTO subscriptions VALUES (?,?,?,?,?,?,?,?)", sub_rows)
        billing.executemany("INSERT INTO meta VALUES (?,?)",
                            [("as_of", AS_OF.isoformat()), ("seed", str(seed)), ("profile", profile)])
        mkt.executemany("INSERT INTO contacts VALUES (?,?,?,?,?,?)", contact_rows)
        for c in (crm, billing, mkt):
            c.commit()
    finally:
        for c in (crm, billing, mkt):
            c.close()

    counts = Counter(t["type"] for t in truth)
    noise = Counter(x for p in people for x in p.noise)
    ground_truth = {
        "seed": seed,
        "n": n,
        "profile": profile,
        "as_of": AS_OF.isoformat(),
        "counts": {k: counts.get(k, 0) for k in CONFLICT_RATES},
        "noise": dict(sorted(noise.items())),
        "conflicts": sorted(truth, key=lambda t: (t["type"], t["customer_key"])),
    }
    gt_path.write_text(json.dumps(ground_truth, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return ground_truth


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--n", type=int, default=500)
    ap.add_argument("--profile", choices=sorted(PROFILES), default="default")
    ap.add_argument("--out", type=Path, default=None, help="output dir for the three .db files")
    ap.add_argument("--gt", type=Path, default=None, help="ground-truth JSON path")
    args = ap.parse_args(argv)
    gt = generate(args.seed, args.n, args.out, args.gt, args.profile)
    print(f"seed={gt['seed']} n={gt['n']} profile={gt['profile']} as_of={gt['as_of']}")
    print(f"{'conflict type':<32}{'planted':>8}{'rate':>8}")
    for k, v in gt["counts"].items():
        print(f"{k:<32}{v:>8}{v / gt['n']:>8.1%}")
    print(f"{'TOTAL':<32}{sum(gt['counts'].values()):>8}")
    print("\nnoise patterns (NOT conflicts):")
    for k, v in gt["noise"].items():
        print(f"  {k:<40}{v:>5}")


if __name__ == "__main__":
    main()
