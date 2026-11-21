from datetime import UTC, date, datetime

from app.core import detector
from app.core.impact import estimate
from app.core.models import ConflictType, CustomerRecord, MatchLink, System, UnifiedCustomer
from app.core.normalize import normalize_email, normalize_plan

AS_OF = date(2026, 11, 1)
NOW = datetime(2026, 11, 1, tzinfo=UTC)


def cust(status="active", plan="pro", email="ava.patel@x.example", billing=(), marketing=()):
    crm = CustomerRecord(system=System.CRM, record_id="ACC-1", crm_account_id="ACC-1", name="ava patel",
                         raw_name="Ava Patel", email=email, raw_email=email, status=status, plan=plan)
    return UnifiedCustomer(customer_key="ACC-1", crm=crm, billing=list(billing), marketing=list(marketing))


def b(cid="BC-1", status="active", plan="pro", email="ava.patel@x.example", amount=399.0, past_due_since=None,
      merged_into=None, method="id"):
    rec = CustomerRecord(system=System.BILLING, record_id=cid, crm_account_id="ACC-1", name="ava patel",
                         email=normalize_email(email), raw_email=email, status=status, plan=normalize_plan(plan),
                         attrs={"subscription_id": cid.replace("BC", "SUB"), "monthly_amount": amount,
                                "currency": "USD", "next_charge_date": None, "past_due_since": past_due_since,
                                "merged_into": merged_into})
    return MatchLink(record=rec, method=method, confidence=1.0 if method == "id" else 0.95)


def m(subscribed=True, stage="onboarding", email="ava.patel@x.example"):
    rec = CustomerRecord(system=System.MARKETING, record_id="MC-1", name="ava patel", email=normalize_email(email),
                         raw_email=email, status=stage,
                         attrs={"subscribed": subscribed, "lifecycle_stage": stage, "last_campaign": "onboarding_day7"})
    return MatchLink(record=rec, method="email", confidence=0.95)


def types(c):
    return {x.type for x in detector.detect([c], AS_OF, now=NOW)}


# ---- each rule fires on its planted pattern -----------------------------------------------
def test_cancelled_but_billing_active():
    c = cust(status="cancelled", billing=[b()])
    hit = detector.rule_cancelled_but_billing_active(c, AS_OF, NOW)
    assert hit and hit.evidence["crm_status"] == "cancelled"
    assert hit.evidence["billing"][0]["billing_status"] == "active"
    assert hit.evidence["billing"][0]["subscription_id"] == "SUB-1"
    assert estimate(hit).amount == 399.0


def test_plan_mismatch_with_evidence_and_impact():
    hit = detector.rule_plan_mismatch(cust(plan="starter", billing=[b(plan="pro")]), AS_OF, NOW)
    assert hit and hit.evidence["crm_plan"] == "starter" and hit.evidence["billing"][0]["billing_plan"] == "pro"
    assert estimate(hit).amount == 399.0 - 49.0


def test_churned_still_marketed():
    c = cust(status="cancelled", billing=[b(status="cancelled")], marketing=[m(subscribed=True)])
    assert types(c) == {ConflictType.CHURNED_STILL_MARKETED}
    hit = detector.rule_churned_still_marketed(c, AS_OF, NOW)
    assert hit.evidence["marketing"][0]["contact_id"] == "MC-1"
    assert estimate(hit).monetary is False


def test_email_mismatch():
    c = cust(billing=[b(email="billing@x.example")])
    assert types(c) == {ConflictType.EMAIL_MISMATCH}
    hit = detector.rule_email_mismatch(c, AS_OF, NOW)
    assert hit.evidence["mismatches"][0]["other_email"] == "billing@x.example"


def test_duplicate_customer():
    c = cust(billing=[b("BC-1"), b("BC-2", method="email")])
    assert ConflictType.DUPLICATE_CUSTOMER in types(c)
    hit = detector.rule_duplicate_customer(c, AS_OF, NOW)
    assert [x["billing_customer_id"] for x in hit.evidence["billing"]] == ["BC-1", "BC-2"]
    assert estimate(hit).amount == 399.0


def test_past_due_over_threshold():
    c = cust(billing=[b(status="past_due", past_due_since="2026-09-01")])
    hit = detector.rule_past_due_but_crm_active(c, AS_OF, NOW)
    assert hit and hit.evidence["billing"][0]["days_past_due"] == 61
    assert estimate(hit).amount == 399.0 * 3


# ---- noise that must NOT fire ---------------------------------------------------------------
def test_noise_email_case_and_spaces_is_not_a_conflict():
    assert types(cust(billing=[b(email="  AVA.PATEL@X.example ")], marketing=[m(subscribed=False, stage="customer",
                                                                               email="Ava.Patel@x.example")])) == set()


def test_noise_plus_addressing_is_not_a_conflict():
    assert types(cust(billing=[b(email="ava.patel+billing@x.example")])) == set()


def test_noise_plan_case_is_not_a_conflict():
    assert types(cust(billing=[b(plan="Pro ")])) == set()
    assert types(cust(billing=[b(plan="PROFESSIONAL")])) == set()


def test_noise_trial_without_billing_is_not_a_conflict():
    assert types(cust(status="trial", billing=[], marketing=[m(subscribed=True)])) == set()


def test_noise_past_due_at_or_under_threshold_is_not_a_conflict():
    assert types(cust(billing=[b(status="past_due", past_due_since="2026-10-02")])) == set()  # exactly 30 days
    assert types(cust(billing=[b(status="past_due", past_due_since="2026-10-20")])) == set()


def test_noise_properly_cancelled_customer_is_not_a_conflict():
    assert types(cust(status="cancelled", billing=[b(status="cancelled")],
                      marketing=[m(subscribed=False, stage="churned")])) == set()


def test_merged_duplicate_is_ignored():
    assert types(cust(billing=[b("BC-1"), b("BC-2", status="cancelled", merged_into="BC-1")])) == set()


def test_conflict_ids_are_deterministic_and_suppressible():
    c = cust(status="cancelled", billing=[b()])
    first = detector.detect([c], AS_OF, now=NOW)
    again = detector.detect([c], AS_OF, now=NOW)
    assert [x.id for x in first] == [x.id for x in again]
    assert detector.detect([c], AS_OF, suppressed_ids={first[0].id}, now=NOW) == []
