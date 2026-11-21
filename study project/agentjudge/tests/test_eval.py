"""Tests for mock faithfulness + stub target + mock judge + kappa + compare."""

from agentjudge.compare import compare_runs, detect_regressions
from agentjudge.gen_metrics import faithfulness, keywords
from agentjudge.judge import cohens_kappa, mock_judge_score
from agentjudge.schemas import GoldenRecord, TargetAnswer
from agentjudge.targets import StubTarget


def _rec(**kw: object) -> GoldenRecord:
    base: dict[str, object] = {
        "id": "AQ-001",
        "question": "How do I reset a POS password at Acme Retail?",
        "category": "answerable",
        "expected_doc_ids": ["DOC-001"],
        "reference_answer": "Reset the POS password in the till admin panel.",
        "must_refuse": False,
    }
    base.update(kw)
    return GoldenRecord.model_validate(base)


def test_keywords_drop_stopwords() -> None:
    assert "the" not in keywords("the password reset")
    assert "password" in keywords("the password reset")


def test_faithfulness_grounded_and_ungrounded() -> None:
    ctx = ["Reset the POS password in the till admin panel."]
    good = faithfulness("Reset the POS password in the till admin panel.", ctx)
    assert good["score"] == 1.0
    bad = faithfulness("Penguins migrate in winter.", ctx)
    assert bad["score"] == 0.0


def test_faithfulness_refusal_without_context() -> None:
    r = faithfulness("I can't answer that, no supporting doc, must refuse.", [])
    assert r["score"] == 1.0


def test_stub_target_refuses_must_refuse() -> None:
    rec = _rec(
        id="AQ-002",
        must_refuse=True,
        expected_doc_ids=[],
        reference_answer="",
        category="unanswerable",
        question="What is the CEO's salary?",
    )
    stub = StubTarget([rec])
    ans = stub.ask("What is the CEO's salary?")
    assert "must refuse" in ans.answer
    assert stub.search("What is the CEO's salary?") == []


def test_stub_target_returns_expected_docs() -> None:
    rec = _rec()
    stub = StubTarget([rec])
    assert stub.search(rec.question) == ["DOC-001"]
    assert stub.ask(rec.question).cost_usd == 0.0


def test_mock_judge_scores_reference_match_high() -> None:
    rec = _rec()
    ans = TargetAnswer(doc_ids=["DOC-001"], answer=rec.reference_answer)
    s = mock_judge_score(rec.question, ans, rec.reference_answer, False)
    assert s["correctness"] == 5 and s["safety"] == 5


def test_mock_judge_punishes_missing_refusal() -> None:
    ans = TargetAnswer(answer="The salary is $10.")
    s = mock_judge_score("salary?", ans, "", True)
    assert s["correctness"] == 1 and s["safety"] == 1


def test_cohens_kappa_perfect_and_chance() -> None:
    assert cohens_kappa([1, 2, 3], [1, 2, 3]) == 1.0
    k = cohens_kappa([5, 5, 5, 4, 4], [5, 5, 4, 4, 4])
    assert 0.0 < k < 1.0


def test_compare_and_regressions() -> None:
    base = {"summary": {"hit_rate_at_5": 0.9, "faithfulness": 0.9, "refusal_accuracy": 1.0}}
    cur = {"summary": {"hit_rate_at_5": 0.9, "faithfulness": 0.5, "refusal_accuracy": 1.0}}
    deltas = compare_runs(cur, base)
    assert deltas["faithfulness"]["delta"] == -0.4
    regs = detect_regressions(cur, base, tolerance=0.02)
    assert [r.metric for r in regs] == ["faithfulness"]
    assert detect_regressions(base, base) == []
