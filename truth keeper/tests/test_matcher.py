from app.core.matcher import match
from app.core.models import CustomerRecord, System
from app.core.normalize import normalize_email, normalize_name, normalize_plan


def crm(i, name, email):
    return CustomerRecord(system=System.CRM, record_id=i, crm_account_id=i, name=normalize_name(name),
                          email=normalize_email(email), status="active", plan="pro")


def bill(i, name, email, ref=None):
    return CustomerRecord(system=System.BILLING, record_id=i, crm_account_id=ref, name=normalize_name(name),
                          email=normalize_email(email), status="active", plan="pro")


def test_normalisers():
    assert normalize_email("  John.Smith+billing@ACME.example ") == "john.smith@acme.example"
    assert normalize_name("GARCÍA,  José ") == "jose garcia"
    assert normalize_plan(" Pro ") == "pro"
    assert normalize_plan("Professional") == "pro"
    assert normalize_email(None) is None


def test_match_order_id_then_email_then_fuzzy():
    c = [crm("A1", "Ava Patel", "ava.patel@x.example"), crm("A2", "Leo Rossi", "leo.rossi@y.example")]
    b = [
        bill("B1", "Someone Else", "other@z.example", ref="A1"),     # id wins even if email differs
        bill("B2", "Leo Rossi", "LEO.ROSSI@y.example "),             # email after normalisation
        bill("B3", "ROSSI, Leo", "billing@y.example"),               # fuzzy name + domain
        bill("B4", "Nobody", "nobody@nowhere.example"),              # unmatched
    ]
    r = match(c, b, [])
    by = {x.customer_key: x for x in r.customers}
    assert [(link.record.record_id, link.method) for link in by["A1"].billing] == [("B1", "id")]
    methods = {link.record.record_id: link.method for link in by["A2"].billing}
    assert methods == {"B2": "email", "B3": "fuzzy_name_domain"}
    assert [x.record_id for x in r.unmatched["billing"]] == ["B4"]
    conf = {link.record.record_id: link.confidence for link in by["A2"].billing}
    assert conf["B2"] == 0.95 and 0 < conf["B3"] <= 0.9


def test_fuzzy_requires_same_domain():
    c = [crm("A1", "Ava Patel", "ava.patel@x.example")]
    r = match(c, [bill("B1", "Ava Patel", "ava@other.example")], [])
    assert r.unmatched["billing"] and not r.customers[0].billing


def test_ambiguous_fuzzy_match_is_refused():
    c = [crm("A1", "Ava Patel", "ava.patel@x.example"), crm("A2", "Ava Patel", "a.patel@x.example")]
    r = match(c, [bill("B1", "Ava Patel", "billing@x.example")], [])
    assert len(r.unmatched["billing"]) == 1


def test_name_only_strategy_links_wrong_people():
    """Debugging exercise: name-only matching links two different companies' Ava Patel."""
    c = [crm("A1", "Ava Patel", "ava.patel@x.example"), crm("A2", "Ava Patel", "ava.patel@y.example")]
    b = [bill("B1", "Ava Patel", "ava.patel@x.example"), bill("B2", "Ava Patel", "ava.patel@y.example")]
    r = match(c, b, [], strategy="name_only")
    by = {x.customer_key: x for x in r.customers}
    assert len(by["A1"].billing) == 2 and not by["A2"].billing
