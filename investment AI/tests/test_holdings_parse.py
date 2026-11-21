from app.engine.holdings import parse_holdings_text


def test_pii_stripped_before_holdings_object():
    raw = (
        "EPF 850000\nPPF 200000 PAN ABCDE1234F Aadhaar 2345 6789 0121 "
        "account 123456789012 IFSC SBIN0001234 customer id CUST998877\nNifty SIP 150000"
    )
    holdings, meta = parse_holdings_text(raw)
    assert meta["redacted"] is True
    assert "ABCDE1234F" not in meta["redacted_text"]
    joined = " ".join(h.name + h.notes for h in holdings)
    assert "ABCDE1234F" not in joined
    assert "CUST998877" not in joined
    assert any("EPF" in h.name.upper() or h.vehicle_type == "epf" for h in holdings)
