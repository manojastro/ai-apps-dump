import os

import pytest
from fastapi.testclient import TestClient

from citation_guard.config import load_config
from citation_guard.gate import AnswerResult, Verdict
from citation_guard.judges import BudgetExceeded, CallBudget, MockJudge
from citation_guard.pipeline import ClaimIn, JudgeUnavailable, verify_answer, verify_claims

CFG = load_config()

GOOD = ClaimIn(claim_id="g", claim='Use of the "iss" claim is optional.', quote="Use of this claim is OPTIONAL.", section_id="4.1.1")
FAB = ClaimIn(claim_id="f", claim="JWTs must be signed.", quote="All JWTs MUST be signed using an asymmetric algorithm.", section_id="8")
FAB2 = ClaimIn(claim_id="f2", claim="aud is required.", quote="Use of this claim is REQUIRED.", section_id="4.1.3")


class LiveMock(MockJudge):
    """A mock that pretends to be a live API judge (for budget / error tests)."""

    is_live = True


class AuthenticationError(Exception):
    pass


class FailingJudge(MockJudge):
    def __init__(self, exc):
        super().__init__()
        self.exc = exc

    async def judge(self, claim, quote, passage):
        self.calls += 1
        raise self.exc


async def test_fabricated_quotes_never_call_the_judge(rfc_doc):
    judge = MockJudge()
    out = await verify_claims(rfc_doc, [FAB, FAB2], judge, CFG, judge_name="mock", run_id="t")
    assert judge.calls == 0
    assert all(d.verdict == Verdict.FAIL_FABRICATED_QUOTE for d in out)
    assert all(not d.judge_called and d.probabilities is None for d in out)


async def test_found_quote_is_judged_and_logged(rfc_doc):
    judge = MockJudge(script={GOOD.claim: {"supports": 0.9, "contradicts": 0.05, "says_nothing": 0.05}})
    (d,) = await verify_claims(rfc_doc, [GOOD], judge, CFG, judge_name="mock", run_id="t")
    assert judge.calls == 1
    assert d.verdict == Verdict.PASS and d.mock and d.mode == "MOCK"
    assert d.offsets["section_id"] == "4.1.1" and d.offsets["raw_line"] > 0


async def test_budget_stops_run_before_any_call(rfc_doc):
    judge = LiveMock()
    claims = [GOOD.model_copy(update={"claim_id": f"g{i}"}) for i in range(3)]
    with pytest.raises(BudgetExceeded):
        await verify_claims(rfc_doc, claims, judge, CFG, judge_name="jev", run_id="t", budget=CallBudget(2))
    assert judge.calls == 0


async def test_auth_error_aborts_run(rfc_doc):
    with pytest.raises(JudgeUnavailable):
        await verify_claims(rfc_doc, [GOOD], FailingJudge(AuthenticationError("401")), CFG, judge_name="llm", run_id="t")


async def test_other_errors_go_to_review_not_pass(rfc_doc):
    judge = FailingJudge(TimeoutError("slow"))
    claims = [GOOD, GOOD.model_copy(update={"claim_id": "g2"})]
    script_ok = MockJudge()

    # One failing judge for all claims -> whole run unavailable.
    with pytest.raises(JudgeUnavailable):
        await verify_claims(rfc_doc, claims, judge, CFG, judge_name="mock", run_id="t")

    # Mixed: first call fails, second succeeds -> failed claim is HUMAN_REVIEW.
    class Flaky(MockJudge):
        async def judge(self, claim, quote, passage):
            self.calls += 1
            if self.calls == 1:
                raise TimeoutError("slow")
            return await script_ok.judge(claim, quote, passage)

    out = await verify_claims(rfc_doc, claims, Flaky(), CFG.model_copy(update={"run": CFG.run.model_copy(update={"concurrency": 1})}),
                              judge_name="mock", run_id="t")
    failed = [d for d in out if d.error]
    assert len(failed) == 1 and failed[0].verdict == Verdict.HUMAN_REVIEW


async def test_stringmatch_baseline_passes_found_quotes(rfc_doc):
    res = await verify_answer(rfc_doc, [GOOD, FAB], "stringmatch", CFG)
    v = {d.claim_id: d.verdict for d in res.claims}
    assert v == {"g": Verdict.PASS, "f": Verdict.FAIL_FABRICATED_QUOTE}
    assert res.answer_result == AnswerResult.BLOCK and res.mode == "NO-MODEL"


def test_api_health_and_verify():
    from citation_guard.api import app

    client = TestClient(app)
    assert client.get("/health").json()["status"] == "ok"
    r = client.post("/v1/verify", json={"doc_id": "rfc7519", "answer": "x", "judge": "mock",
                                        "claims": [GOOD.model_dump(), FAB.model_dump()]})
    assert r.status_code == 200
    body = r.json()
    assert body["mode"] == "MOCK" and body["answer_result"] == "BLOCK"
    assert {c["claim_id"]: c["verdict"] for c in body["claims"]}["f"] == "FAIL_FABRICATED_QUOTE"
    assert client.post("/v1/verify", json={"doc_id": "nope", "claims": []}).status_code == 404


@pytest.mark.skipif(not os.environ.get("TYPESAFE_API_KEY"), reason="TYPESAFE_API_KEY not set")
async def test_live_jev_smoke(rfc_doc, request):
    if not request.config.getoption("--live"):
        pytest.skip("pass --live to run live API tests")
    from citation_guard.judges.jev import JevJudge

    async with JevJudge(CFG) as judge:
        out = await verify_claims(rfc_doc, [GOOD], judge, CFG, judge_name="jev", run_id="smoke")
    d = out[0]
    assert d.mode == "LIVE" and not d.mock and d.error is None
    assert set(d.probabilities) == {"supports", "contradicts", "says_nothing"}
    assert d.request_id
