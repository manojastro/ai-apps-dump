from app.security.pii_redactor import redact_pii


def test_redacts_pan_aadhaar_account_ifsc_customer():
    raw = (
        "EPF 850000 PAN ABCDE1234F Aadhaar 2345 6789 0121 account 123456789012 "
        "IFSC SBIN0001234 customer id CUST998877"
    )
    result = redact_pii(raw)
    assert result.redacted
    assert "ABCDE1234F" not in result.text
    assert "2345 6789 0121" not in result.text
    assert "SBIN0001234" not in result.text
    assert "CUST998877" not in result.text
    assert "PAN" in result.kinds or "pan" in result.kinds
    assert "aadhaar" in result.kinds
    assert "ifsc" in result.kinds


def test_does_not_redact_ordinary_amounts():
    raw = "Nifty SIP 150000 liquid fund 20000"
    result = redact_pii(raw)
    assert "150000" in result.text
    assert "20000" in result.text
