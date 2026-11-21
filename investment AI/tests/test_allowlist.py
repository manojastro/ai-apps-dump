from app.data.allowlist import is_allowlisted


def test_allowlist_hostname_not_substring():
    assert is_allowlisted("https://www.rbi.org.in/scripts/faq")
    assert is_allowlisted("https://rbi.org.in/")
    assert not is_allowlisted("https://evil-rbi.org.in/")
    assert not is_allowlisted("https://rbi.org.in.attacker.com/")
    assert not is_allowlisted("https://telegram.me/tips")
