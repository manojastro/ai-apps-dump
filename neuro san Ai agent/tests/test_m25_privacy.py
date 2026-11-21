"""M25 tests: sanitize/vault, scanner sensitivity, proof PASS."""

from __future__ import annotations


def test_sanitize_deep_and_vault() -> None:
    from control_plane.privacy import SecureContext, sanitize_for_llm

    key = "AIza" + "V" * 35
    obj = {"a": f"key {key}", "nested": [{"b": "clean"}]}
    clean = sanitize_for_llm(obj)
    assert key not in str(clean) and clean["nested"][0]["b"] == "clean"

    vault = SecureContext({"USER_014": "Ada Lovelace"})
    assert vault.resolve("ticket for USER_014") == "ticket for Ada Lovelace"
    assert vault.cloak("ticket for Ada Lovelace") == "ticket for USER_014"
    assert vault.aliases() == ["USER_014"]
    try:
        vault.bind("", "x")
        raise AssertionError("empty bind must raise")
    except ValueError:
        pass


def test_scanner_catches_planted_secrets(tmp_path) -> None:
    from evaluation.scan_secrets import scan_corpus, scan_text

    key = "AIza" + "W" * 35
    assert scan_text(f"leaked {key}")["api_key_google"] == 1
    assert scan_text("hello world") == {}
    assert scan_corpus(["clean", f"bad {key} AKIA{'Z' * 16}"])["api_key_google"] == 1


def test_repo_proof_passes(tmp_path) -> None:
    from evaluation.scan_secrets import check_env_example, run_proof, write_proof

    assert check_env_example() == []
    results = run_proof(tmp_path)
    assert results["verdict"] == "PASS"
    assert results["prompts_inspected"] > 50
    proof = tmp_path / "proof.md"
    write_proof(proof, results)
    text = proof.read_text(encoding="utf-8")
    for line in ("API keys exposed: 0", "credentials exposed: 0",
                 "hostnames exposed: 0", "IP addresses exposed: 0",
                 "PII exposed: 0", "**PASS**"):
        assert line in text
